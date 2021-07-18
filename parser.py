import sys

from datetime import datetime as dt

import requests
import pandas as pd
import fake_useragent

from bs4 import BeautifulSoup


class DummyLogWriter:
    def __init__(self, name=""):
        self.name = name if name else "DummyLogger"

    def debug(self, msg):
        print(f"{dt.now()} {self.name} DEBUG: {msg}")

    def info(self, msg):
        print(f"{dt.now()} {self.name} INFO: {msg}")

    def warning(self, msg):
        print(f"{dt.now()} {self.name} WARNING: {msg}", file=sys.stderr)

    def error(self, msg):
        print(f"{dt.now()} {self.name} ERROR: {msg}", file=sys.stderr)

    def critical(self, msg):
        print(f"{dt.now()} {self.name} CRITICAL: {msg}", file=sys.stderr)


class Parser:
    def __init__(self, url, page_count, log=None):
        self.url = url
        self.page_count = page_count

        self.user_agent = fake_useragent.UserAgent().chrome
        self.headers = {"User-Agent": self.user_agent}

        self.log = log if log else DummyLogWriter()

    def still_data(self):
        params = {
            "deal_type": "sale",
            "engine": 2,
            "offer_type": "flat",
            "region": 1,
            "room1": 1,
            "room2": 1,
            "room3": 1,
            "room4": 1,
            "room5": 1,
            "room6": 1,
            "room9": 1,
            "sort": "price_object_order",
            "p": 1,
        }

        pages_data = []

        for num in range(1, self.page_count + 1):
            params["p"] = num
            page_data = self.process_search_page(params)
            if page_data:
                pages_data.append(page_data)
        return pages_data

    def process_search_page(self, params):
        page = self.get_search_page(params)
        flat_links = self.get_page_flats(page)
        return flat_links

    def get_search_page(self, params):
        response = requests.get(self.url, params=params, headers=self.headers)
        page = BeautifulSoup(response.text, "html.parser")
        return page

    def get_page_flats(self, search_page):
        flat_link_divs = search_page.find_all(attr={"data-name": "LinkArea"})
        if not flat_link_divs:
            return ()
        else:
            return (
                flat_data
                for flat_link_div in flat_link_divs
                if (flat_data := self.process_flat(flat_link_div))
            )

    def process_flat(self, flat_link_div):
        flat_link = self.get_flat_link(flat_link_div)
        flat_soup = self.get_flat_soup(flat_link)
        flat_data = self.get_flat_data(flat_soup)
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
        response = requests.get(flat_link, headers=self.headers)
        page = BeautifulSoup(response.text, "html.parser")
        return page

    def get_flat_data(self, flat_page):
        # agent failures
        flat_link_data = ...
        return flat_link_data

    @staticmethod
    def get_price(flat_page):
        price_tag = flat_page.find("span", attrs={"itemprop": "price"})
        raw_str_price_with_currency = price_tag.find("span").get("content")
        raw_str_price = raw_str_price_with_currency.rsplit(" ", maxsplit=1)[0]
        str_price = raw_str_price.replace(" ", "")
        price = int(str_price)
        return price

    @staticmethod
    def get_price_currency(flat_page):
        price_currency_tag = flat_page.find(
            "span", attrs={"itemprop": "priceCurrency"}
        )
        currency = price_currency_tag.find("span").get("content")
        return currency

    @staticmethod
    def get_description_length(flat_page):
        pass

    @staticmethod
    def get_build_year(flat_page):
        pass

    @staticmethod
    def get_building_type(flat_page):
        pass

    @staticmethod
    def get_ceil_height(flat_page):
        pass

    @staticmethod
    def get_wc_type(flat_page):
        pass

    @staticmethod
    def get_bathroom(flat_page):
        # type & count
        pass

    @staticmethod
    def get_facing(flat_page):
        pass

    @staticmethod
    def get_window_view(flat_page):
        pass

    @staticmethod
    def get_metro(flat_page):
        pass

    @staticmethod
    def get_district(flat_page):
        pass

    @staticmethod
    def get_metro_distance(flat_page):
        # type & time
        pass

    @staticmethod
    def get_parking(flat_page):
        pass

    @staticmethod
    def get_balcony(flat_page):
        pass

    @staticmethod
    def get_squares(flat_page):
        # common, living, kitchen, floor (e.g. 1st out of 4)
        pass


if __name__ == "__main__":
    # page_count = 2986
    # df = pd.DataFrame(Parser("https://www.cian.ru/cat.php?", 1).still_data())
    # df.to_csv("collected_data.csv")
    parser = Parser("https://www.cian.ru/cat.php?", 1)
    # flat_soup = parser.get_flat_soup("https://www.cian.ru/sale/flat/260420118/")
