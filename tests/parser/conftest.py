import pytest
import os
import sys

from bs4 import BeautifulSoup

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)


from src.parser import Parser
from src.misc.dummy_log import DummyLogWriter


class MockWebdriver:
    class ChromeDriver:
        def __init__(self, path):
            self.path = path

        def get(self, url):
            pass

    def __init__(self):
        self.Chrome = self.ChromeDriver


@pytest.fixture()
def parser(mocker):
    mocker.patch("src.parser.webdriver", MockWebdriver())
    parser_ = Parser("test_url", 10)
    yield parser_


@pytest.fixture
def init_parser_fields():
    yield {"url": "test_url", "page_count": 10}


@pytest.fixture
def exp_parser_fields():
    yield {
        "url": "test_url",
        "page_count": 10,
        "_page_count": 10,
        "LAST_SORTED_PAGE": 53,
        "FLATS_PER_PAGE": 28,
        "collected_data": [],
        "_last_processed_price": 0,
        "QUERY_PARAMS": {
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
    }


@pytest.fixture
def exp_is_instance_parser_fields():
    yield {"log": DummyLogWriter, "driver": MockWebdriver.ChromeDriver}


@pytest.fixture(
    params=[
        (
            '<div id="captcha">what do u see here</div>',
            {
                "page": BeautifulSoup(
                    '<div id="captcha">what do u see here</div>', "html.parser"
                ),
                "err": "CAPTCHA FOUND",
            },
        ),
        (
            '<div id="ok">all is ok</div>',
            {
                "page": BeautifulSoup(
                    '<div id="ok">all is ok</div>', "html.parser"
                ),
                "err": "",
            },
        ),
    ]
)
def get_search_page_params(request):
    yield request.param


@pytest.fixture(
    params=[
        ([], 0, []),
        (
            ["flat_link_div_1", None, "flat_link_div_2"],
            3,
            ["flat_link_div_1", "flat_link_div_2"],
        ),
    ]
)
def get_page_flats_params(request):
    yield request.param
