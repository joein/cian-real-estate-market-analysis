import sys
import signal
import traceback

from copy import copy
from datetime import datetime as dt
from datetime import timedelta

import pandas as pd

from tqdm import trange, tqdm
from bs4 import BeautifulSoup
from selenium import webdriver

from misc.dummy_log import DummyLogWriter


class Parser:
    LAST_SORTED_PAGE = 53
    FLATS_PER_PAGE = 28
    QUERY_PARAMS = {
        "deal_type": "sale",
        "engine_version": 2,
        "offer_type": "flat",
        "region": 1,
        "room1": 1,
        "room2": 1,
        "room3": 1,
        "room4": 1,
        "room5": 1,
        "room6": 1,
        "room7": 1,
        "room9": 1,
        "sort": "price_object_order",
        "p": 1,
        "minprice": 0,
    }

    def __init__(self, url, page_count, log=None):
        self.url = url
        self._page_count = page_count
        self.page_count = page_count

        self.collected_data = []
        self.log = log if log else DummyLogWriter()
        self.driver = webdriver.Chrome("../chromedriver")

        self._last_processed_price = 0

    def still_data(self, start_page=1, min_price=0):
        params = copy(self.QUERY_PARAMS)
        params["start_page"] = start_page
        params["minprice"] = min_price

        bootstrap = start_page > 1
        self._last_processed_price = min_price

        while self.page_count:
            if bootstrap:
                page = start_page
                bootstrap = False
            else:
                page = 1

            for num in trange(
                page,
                min(self.page_count + 1, self.LAST_SORTED_PAGE + 1),
                desc="outer progress bar",
            ):
                print()
                try:
                    params["minprice"] = self._last_processed_price
                    params["p"] = num
                    separate_str_params = (
                        f"{key}={value}" for key, value in params.items()
                    )
                    joined_str_params = "&".join(separate_str_params)
                    url = f"{self.url}?{joined_str_params}"
                    self.log.info(url)
                    self.process_search_page(url)
                    self.log.info(f"remains pages {self.page_count}")
                    self.log.info(
                        f"flats remains {(self.page_count - num) * self.FLATS_PER_PAGE}"
                    )
                    self.log.info(
                        f"flats collected {len(self.collected_data)}"
                    )
                except Exception:
                    self.log.error(
                        f"Unexpected error. Traceback is {traceback.format_exc()}"
                    )

            self.set_last_processed_price()
            self.page_count -= min(self.page_count, self.LAST_SORTED_PAGE)
        return self.collected_data

    def set_last_processed_price(self):
        i = 0
        collected_data_len = len(self.collected_data)
        while abs(i) != collected_data_len:
            i -= 1
            try:
                self._last_processed_price = self.collected_data[i]["price"]
                self.log.info(
                    f"last processed price {self._last_processed_price}"
                )
                break
            except KeyError:
                self.log.warning(
                    f"Price not found at {self.collected_data[-1]}"
                )

    def process_search_page(self, url):
        page = self.get_search_page(url)
        self.get_page_flats(page)

    def get_search_page(self, url):
        self.driver.get(url)

        page = BeautifulSoup(self.driver.page_source, "html.parser")
        captcha_found = page.find("div", id="captcha")
        if captcha_found:
            self.log.error("CAPTCHA FOUND")
        return page

    def get_page_flats(self, search_page):
        flat_link_divs = search_page.find_all(attrs={"data-name": "LinkArea"})
        if flat_link_divs:
            for flat_link_div in tqdm(
                flat_link_divs, desc="flats progress bar"
            ):
                print()
                flat_data = self.process_flat(flat_link_div)
                if flat_data:
                    self.collected_data.append(flat_data)

    def process_flat(self, flat_link_div):
        flat_data = {}
        try:
            flat_link = self.get_flat_link(flat_link_div)
            flat_data["link"] = flat_link
            flat_soup = self.get_flat_soup(flat_link)
            flat_data.update(self.get_flat_data(flat_soup))
        except Exception:
            self.log.error(f"Got an error. {traceback.format_exc()}")
        return flat_data

    def get_flat_link(self, flat_link_div):
        if flat_link_tag := flat_link_div.find("a"):
            if flat_link := flat_link_tag.get("href"):
                return flat_link
            else:
                self.log.info(
                    f"href not found in flat_link_tag: {flat_link_tag}"
                )
        else:
            self.log.info(
                f"flat_link not found in flat_link_div {flat_link_div}"
            )

    def get_flat_soup(self, flat_link):
        self.driver.get(flat_link)
        print(f"request sent to {flat_link}")
        page = BeautifulSoup(self.driver.page_source, "html.parser")
        return page

    def get_flat_data(self, flat_page):
        flat_link_data = dict()

        flat_link_data["agent_warning"] = self.get_agent_warning(flat_page)
        flat_link_data["price"] = self.get_price(flat_page)
        flat_link_data["price_currency"] = self.get_price_currency(flat_page)
        flat_link_data["description_len"] = self.get_description_length(
            flat_page
        )
        flat_link_data.update(self.get_general_info(flat_page))
        flat_link_data.update(self.get_additional_features(flat_page))
        flat_link_data.update(self.get_bti_house_data(flat_page))
        flat_link_data.update(self.get_transport(flat_page))
        flat_link_data["address"] = self.get_address(flat_page)
        flat_link_data["title"] = self.get_offer_title(flat_page)
        flat_link_data["offer_dt"] = self.get_date_offer_placement(flat_page)
        flat_link_data.update(self.get_offer_statistics(flat_page))
        self.log.info(flat_link_data)
        return flat_link_data

    @staticmethod
    def get_agent_warning(flat_page):
        warning = flat_page.find(
            "div", attrs={"data-name": "WarningsFlexible"}
        )
        return bool(warning)

    @staticmethod
    def get_price(flat_page):
        price_tag = flat_page.find("span", attrs={"itemprop": "price"})
        raw_str_price_with_currency = price_tag.get("content", "")
        raw_str_price = raw_str_price_with_currency.rsplit(" ", maxsplit=1)[0]
        str_price = raw_str_price.replace(" ", "")
        price = int(str_price)
        return price

    @staticmethod
    def get_price_currency(flat_page):
        price_currency_tag = flat_page.find(
            "span", attrs={"itemprop": "priceCurrency"}
        )
        currency = price_currency_tag.get("content", "")
        return currency

    @staticmethod
    def get_description_length(flat_page):
        try:
            description_div = flat_page.find("div", id="description")
            p_tag = description_div.find(
                "p", attrs={"itemprop": "description"}
            )
            description = p_tag.text
        except Exception:
            description = ""
        return len(description)

    @staticmethod
    def get_general_info(flat_page):
        description_div = flat_page.find("div", id="description")
        general_info = {}

        for div in description_div.findChild("div"):
            for inner_div in div.findChildren("div", recursive=False):
                title, value = None, None
                for info_div in inner_div.findChildren("div", recursive=False):
                    if "value" in (
                        div_classes := " ".join(
                            info_div.attrs.get("class", [])
                        )
                    ):
                        value = info_div.text
                    elif "title" in div_classes:
                        title = info_div.text
                    else:
                        print(f"UNEXPECTED INFO DIV {info_div}")
                general_info[title] = value
        return general_info

    @staticmethod
    def get_additional_features(flat_page):
        square_key = "Площадь комнат"
        article = flat_page.find(
            "article", attrs={"data-name": "AdditionalFeaturesGroup"}
        )
        spans = article.findChildren("span", recursive=True)

        keys, values = [], []
        for span in spans:
            text = span.text
            if "name" in (span_class := " ".join(span.attrs.get("class", []))):
                if square_key in text:
                    text = square_key
                    keys.append(text)
                else:
                    keys.append(text)
            elif "value" in span_class:
                if "+" in text or "-" in text:
                    possible_digits = (
                        text.replace("-", "+")
                        .replace(",", ".")
                        .replace("+", " ")
                        .split()
                    )
                    digits = str(
                        round(
                            sum(
                                float(x)
                                for x in possible_digits
                                if "." in x or x.isdigit()
                            ),
                            2,
                        )
                    )
                    values.append(digits)
                else:
                    values.append(text)
        additional_features = {key: value for key, value in zip(keys, values)}

        return additional_features

    @staticmethod
    def get_bti_house_data(flat_page):
        bti_div = flat_page.find("div", attrs={"data-name": "BtiHouseData"})
        bti_info = {}
        if not bti_div:
            return bti_info
        children = bti_div.findChildren(
            "div", attrs={"data-name": "Item"}, recursive=True
        )
        for div in children or ():
            name, value = None, None
            for item_div in div:
                if "value" in (
                    div_classes := " ".join(item_div.attrs.get("class", []))
                ):
                    value = item_div.text
                elif "name" in div_classes:
                    name = item_div.text
                else:
                    print(f"UNEXPECTED INFO DIV {item_div}")
            bti_info[name] = value
        return bti_info

    def get_transport(self, flat_page):
        geo_div = flat_page.find("div", attrs={"data-name": "Geo"})
        undergrounds = {}
        highways = {}

        underground_li = geo_div.findChildren(
            "li", attrs={"data-name": "renderUnderground"}
        )
        highway_li = geo_div.findChildren(
            "li", attrs={"data-name": "renderHighway"}
        )
        transport_info = {}
        for li in underground_li:
            underground_link_tag = li.findChild("a")
            underground = underground_link_tag.text
            span_tag = li.findChild("span")
            time_to_underground = span_tag.text if span_tag else None
            if time_to_underground:
                time_to_underground = (
                    time_to_underground.replace("⋅", "")
                    .strip()
                    .replace("<", "")
                )
                undergrounds[underground] = time_to_underground

        for li in highway_li:
            highway_link_tag = li.findChild("a")
            highway = highway_link_tag.text
            space_span_tag = li.findChild("span")
            if space_span_tag:
                distance_span_tag = space_span_tag.findChild("span")
                distance = distance_span_tag.text.strip()
                highways[highway] = distance

        transport_info["time_to_underground"] = self.get_time_to_underground(
            undergrounds
        )
        transport_info["distance_to_mkad"] = self.get_distance_to_mkad(
            highways
        )

        return transport_info

    def get_time_to_underground(self, undergrounds):
        min_time_to_underground = None
        for value in undergrounds.values():
            transport = "транспорт" in value
            try:
                time_to_underground = float(value.split(" ")[0])
            except ValueError:
                self.log.error(
                    f"Can't convert time_to_underground '{value}' to float"
                )
                continue
            if transport:
                time_to_underground *= 5
            if min_time_to_underground is None:
                min_time_to_underground = time_to_underground
            min_time_to_underground = min(
                min_time_to_underground, time_to_underground
            )
        return min_time_to_underground

    @staticmethod
    def get_distance_to_mkad(highways):
        min_distance_to_mkad = None
        for value in highways.values():
            distance_to_mkad = float(value.split(" ")[0])
            if min_distance_to_mkad is None:
                min_distance_to_mkad = distance_to_mkad
            min_distance_to_mkad = min(min_distance_to_mkad, distance_to_mkad)

        return min_distance_to_mkad

    @staticmethod
    def get_address(flat_page):
        geo_div = flat_page.find("div", attrs={"data-name": "Geo"})
        address_span = geo_div.findChild("span")
        address = address_span.attrs.get("content", "")
        return address

    @staticmethod
    def get_offer_title(flat_page):
        offer_title_div = flat_page.find(
            "div", attrs={"data-name": "OfferTitle"}
        )
        offer_title_tag = offer_title_div.find("h1")
        offer_title = offer_title_tag.text
        return offer_title

    @staticmethod
    def get_date_offer_placement(flat_page):
        month_to_number = {
            "янв": 1,
            "фев": 2,
            "мар": 3,
            "апр": 4,
            "май": 5,
            "июн": 6,
            "июл": 7,
            "авг": 8,
            "сен": 9,
            "окт": 10,
            "ноя": 11,
            "дек": 12,
        }
        offer_div = flat_page.find("div", attrs={"data-name": "OfferAdded"})
        offer_text = offer_div.text
        offer_date, offer_time = map(
            lambda x: x.strip(), offer_text.split(",")
        )
        hour, minute = map(lambda x: int(x), offer_time.split(":"))

        if offer_date == "сегодня":
            offer_date = dt.date(dt.today())
            offer_dt = dt(
                year=offer_date.year,
                month=offer_date.month,
                day=offer_date.day,
                hour=hour,
                minute=minute,
            )
        elif offer_date == "вчера":
            offer_date = dt.date(dt.today()) - timedelta(days=1)
            offer_dt = dt(
                year=offer_date.year,
                month=offer_date.month,
                day=offer_date.day,
                hour=int(hour),
                minute=int(minute),
            )
        else:
            day, month_cyr = offer_date.split()
            month = month_to_number[month_cyr]
            offer_dt = dt(
                year=dt.now().year,
                month=month,
                day=int(day),
                hour=int(hour),
                minute=int(minute),
            )
        return offer_dt

    @staticmethod
    def get_offer_statistics(flat_page):
        stats_div = flat_page.find("div", attrs={"data-name": "OfferStats"})
        a_tag = stats_div.find("a", attrs={"data-name": "Link"})
        raw_all_views, raw_today_views = a_tag.text.split(",")
        all_views = int(raw_all_views.rsplit(maxsplit=1)[0].replace(" ", ""))
        today_views = int(
            "".join(
                [
                    number
                    for number in raw_today_views.strip().split()
                    if number.isdigit()
                ]
            )
        )
        return {"all_views": all_views, "today_views": today_views}


def handler(sig_num, _):
    print(f"Got signal. SIGNUM is {sig_num}", file=sys.stderr)
    parser.driver.quit()
    df = pd.DataFrame(parser.collected_data)
    df.to_csv("test_sample3.csv")
    print("interrupted collected data has been written")
    raise KeyboardInterrupt


if __name__ == "__main__":
    # page_count = 2986

    parser = Parser("https://www.cian.ru/cat.php", 2000)
    signal.signal(signal.SIGINT, handler)

    df = pd.DataFrame(parser.still_data(start_page=1, min_price=9_750_000))
    df.to_csv("storage.csv")
