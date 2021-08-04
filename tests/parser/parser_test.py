import pytest

from bs4 import BeautifulSoup

from src.parser import Parser


def test___init__(
    parser,
    init_parser_fields,
    exp_parser_fields,
    exp_is_instance_parser_fields,
):
    parser_ = Parser(**init_parser_fields)
    for field in exp_parser_fields:
        assert getattr(parser_, field) == getattr(parser, field)
    for field in exp_is_instance_parser_fields:
        assert isinstance(
            getattr(parser_, field), getattr(parser_, field).__class__
        )


def test_still_data():
    pass


def test_process_search_page(parser, mocker):
    test_url = "test_url"
    test_return_value = ["beautiful soup object"]
    get_search_page_mock = mocker.patch.object(parser, "get_search_page",)
    get_page_flats_mock = mocker.patch.object(parser, "get_page_flats")

    assert get_search_page_mock.called_with(test_url)
    assert get_page_flats_mock.called_with(test_return_value)


def test_get_search_page(parser, mocker, capsys, get_search_page_params):
    test_url = "test_url"
    input_page, exp_output = get_search_page_params

    def mock_page_source(_):
        parser.driver.page_source = input_page

    mocker.patch.object(parser.driver, "get", side_effect=mock_page_source)

    page = parser.get_search_page(test_url)
    _, err = capsys.readouterr()

    assert (
        exp_output["err"] in err
        if exp_output["err"]
        else exp_output["err"] == err
    )
    assert exp_output["page"] == page


def test_get_page_flats(parser, mocker, get_page_flats_params):
    class SearchPageMock:
        def __init__(self, return_value):
            self.return_value = return_value
            self.attrs = []

        def find_all(self, attrs):
            self.attrs = attrs
            return self.return_value

    def mock_process_flat_cb(flat_link_div):
        return flat_link_div

    mock_process_flat = mocker.patch.object(
        parser, "process_flat", side_effect=mock_process_flat_cb
    )

    (
        search_return_value,
        exp_process_flat_called,
        exp_collected_data,
    ) = get_page_flats_params

    parser.get_page_flats(SearchPageMock(search_return_value))

    assert mock_process_flat.call_count == exp_process_flat_called
    assert parser.collected_data == exp_collected_data


@pytest.mark.parametrize(
    "should_raise,exp_flat_data,exp_err",
    [
        (False, {"link": "flat_link", "flat_data": "some_data"}, ""),
        (True, {}, "Got an error"),
    ],
)
def test_process_flat(
    parser, mocker, capsys, should_raise, exp_flat_data, exp_err
):
    if should_raise:
        get_flat_link_mock = mocker.patch.object(
            parser, "get_flat_link", side_effect=Exception
        )
        get_flat_soup_mock = mocker.patch.object(parser, "get_flat_soup")
        get_flat_data_mock = mocker.patch.object(parser, "get_flat_data")
    else:
        get_flat_link_mock = mocker.patch.object(
            parser, "get_flat_link", return_value=exp_flat_data["link"]
        )
        get_flat_soup_mock = mocker.patch.object(
            parser, "get_flat_soup", return_value="flat_soup",
        )
        get_flat_data_mock = mocker.patch.object(
            parser,
            "get_flat_data",
            return_value={"flat_data": exp_flat_data["flat_data"]},
        )

    flat_link_div = "test_div"
    flat_data = parser.process_flat(flat_link_div)
    _, err = capsys.readouterr()

    assert get_flat_link_mock.called_with(flat_link_div)
    if not should_raise:
        assert get_flat_soup_mock.called_with(exp_flat_data["link"])
        assert get_flat_data_mock.called_with("flat_soup")
    else:
        assert not get_flat_soup_mock.called
        assert not get_flat_data_mock.called

    assert flat_data == exp_flat_data
    assert exp_err in err if exp_err else exp_err == err


@pytest.mark.parametrize(
    "get_flat_link_params",
    [
        ('<div><a href="flat_link">here is link</a></div>', "flat_link", ""),
        (
            "<div><span>there is no any a</span></div>",
            None,
            "flat_link not found",
        ),
        ("<div><a class=no-href>misc</a></div>", None, "href not found"),
    ],
)
def test_get_flat_link(parser, capsys, get_flat_link_params):
    flat_link_div, exp_flat_link, exp_out = get_flat_link_params
    flat_link_div = BeautifulSoup(flat_link_div, "html.parser")
    flat_link = parser.get_flat_link(flat_link_div)
    out, _ = capsys.readouterr()
    assert flat_link == exp_flat_link
    assert exp_out in out if exp_out else out == exp_out


@pytest.mark.parametrize(
    "input_page,exp_page",
    [
        (
            '<div id="ok">all is ok</div>',
            BeautifulSoup('<div id="ok">all is ok</div>', "html.parser"),
        ),
    ],
)
def test_get_flat_soup(parser, mocker, input_page, exp_page):
    def mock_page_source(_):
        parser.driver.page_source = input_page

    mocker.patch.object(parser.driver, "get", side_effect=mock_page_source)

    flat_link = "flat_link"
    page = parser.get_flat_soup(flat_link)
    assert page == exp_page


@pytest.mark.parametrize(
    "exp_flat_data",
    [
        {
            k: k
            for k in (
                "agent_warning",
                "price",
                "price_currency",
                "description_len",
                "general_info",
                "additional_features",
                "bti_house_data",
                "transport",
                "address",
                "title",
                "offer_dt",
                "offer_statistics",
            )
        }
    ],
)
def test_get_flat_data(parser, mocker, exp_flat_data):
    flat_page = "flat_page"

    mockers = list()
    mockers.append(
        mocker.patch.object(
            parser,
            "get_agent_warning",
            return_value=exp_flat_data.get("agent_warning"),
        )
    )
    mockers.append(
        mocker.patch.object(
            parser, "get_price", return_value=exp_flat_data.get("price")
        )
    )
    mockers.append(
        mocker.patch.object(
            parser,
            "get_price_currency",
            return_value=exp_flat_data.get("price_currency"),
        )
    )
    mockers.append(
        mocker.patch.object(
            parser,
            "get_description_length",
            return_value=exp_flat_data.get("description_len"),
        )
    )
    mockers.append(
        mocker.patch.object(
            parser,
            "get_general_info",
            return_value={"general_info": exp_flat_data.get("general_info")},
        )
    )

    mockers.append(
        mocker.patch.object(
            parser,
            "get_additional_features",
            return_value={
                "additional_features": exp_flat_data.get("additional_features")
            },
        )
    )
    mockers.append(
        mocker.patch.object(
            parser,
            "get_bti_house_data",
            return_value={
                "bti_house_data": exp_flat_data.get("bti_house_data")
            },
        )
    )
    mockers.append(
        mocker.patch.object(
            parser,
            "get_transport",
            return_value={"transport": exp_flat_data.get("transport")},
        )
    )
    mockers.append(
        mocker.patch.object(
            parser, "get_address", return_value=exp_flat_data.get("address")
        )
    )
    mockers.append(
        mocker.patch.object(
            parser, "get_offer_title", return_value=exp_flat_data.get("title"),
        )
    )
    mockers.append(
        mocker.patch.object(
            parser,
            "get_date_offer_placement",
            return_value=exp_flat_data.get("offer_dt"),
        )
    )
    mockers.append(
        mocker.patch.object(
            parser,
            "get_offer_statistics",
            return_value={
                "offer_statistics": exp_flat_data.get("offer_statistics")
            },
        )
    )

    flat_data = parser.get_flat_data(flat_page)

    assert flat_data == exp_flat_data
    for mocker_ in mockers:
        assert mocker_.called_with(flat_page)


@pytest.mark.parametrize(
    "agent_warning_flat_page,exp_warning",
    [
        (
            BeautifulSoup(
                '<div data-name="WarningsFlexible">warning</div>',
                "html.parser",
            ),
            True,
        ),
        (BeautifulSoup("<div>no warning</div>", "html.parser"), False),
    ],
)
def test_get_agent_warning(parser, agent_warning_flat_page, exp_warning):
    assert parser.get_agent_warning(agent_warning_flat_page) == exp_warning


@pytest.mark.parametrize(
    "price_flat_page,exp_price",
    [
        (
            BeautifulSoup(
                '<span itemprop="price" content="42 RUB">42 R</span>',
                "html.parser",
            ),
            42,
        ),
    ],
)
def test_get_price(parser, price_flat_page, exp_price):
    assert parser.get_price(price_flat_page) == exp_price


@pytest.mark.parametrize(
    "price_currency_flat_page,exp_price_currency",
    [
        (
            BeautifulSoup(
                '<span itemprop="priceCurrency" content="RUB">RUBLES</span>',
                "html.parser",
            ),
            "RUB",
        ),
    ],
)
def test_get_price_currency(
    parser, price_currency_flat_page, exp_price_currency
):
    assert (
        parser.get_price_currency(price_currency_flat_page)
        == exp_price_currency
    )


@pytest.mark.parametrize(
    "description_len_flat_page,exp_description_len",
    [
        (
            BeautifulSoup(
                '<div id="description"><p itemprop="description">awesome description</p></div>',
                "html.parser",
            ),
            19,
        ),
        (BeautifulSoup("<div>empty div</div>", "html.parser"), 0),
    ],
)
def test_get_description_length(
    parser, description_len_flat_page, exp_description_len
):
    assert (
        parser.get_description_length(description_len_flat_page)
        == exp_description_len
    )


def test_get_general_info():
    pass


def test_get_additional_features():
    pass


def test_get_bti_house_data():
    pass


def test_get_transport():
    pass


@pytest.mark.parametrize(
    "undergrounds,exp_time_to_underground,exp_err",
    [
        (
            {
                "Ольховая": "3 мин. на транспорте",
                "Филатов луг": "17 мин. пешком",
            },
            15,
            "",
        ),
        (
            {"Новослободвская": "неизвестно"},
            None,
            "Can't convert time_to_underground",
        ),
        ({"Кунцевская": "2 мин. пешком"}, 2, ""),
    ],
)
def test_get_time_to_underground(
    parser, capsys, undergrounds, exp_time_to_underground, exp_err
):
    time_to_underground = parser.get_time_to_underground(undergrounds)
    _, err = capsys.readouterr()
    assert time_to_underground == exp_time_to_underground
    assert exp_err in err if exp_err else err == exp_err


@pytest.mark.parametrize(
    "highways,exp_distance_to_mkad",
    [
        (
            {
                "Калужское шоссе": "17 км от МКАД",
                "Боровское шоссе": "12 км от МКАД",
            },
            12,
        )
    ],
)
def test_get_distance_to_mkad(parser, highways, exp_distance_to_mkad):
    assert parser.get_distance_to_mkad(highways) == exp_distance_to_mkad


@pytest.mark.parametrize(
    "address_flat_page,exp_address",
    [
        (
            BeautifulSoup(
                '<div data-name="Geo"><span content="ЦАО, ул. Мясницкая 42">addr</span></div>',
                "html.parser",
            ),
            "ЦАО, ул. Мясницкая 42",
        )
    ],
)
def test_get_address(parser, address_flat_page, exp_address):
    assert parser.get_address(address_flat_page) == exp_address


@pytest.mark.parametrize(
    "offer_title_flat_page,exp_offer_title",
    [
        (
            BeautifulSoup(
                '<div data-name="OfferTitle"><h1>студия 16 м</h1></div>',
                "html.parser",
            ),
            "студия 16 м",
        )
    ],
)
def test_get_offer_title(parser, offer_title_flat_page, exp_offer_title):
    assert parser.get_offer_title(offer_title_flat_page) == exp_offer_title


def test_get_date_offer_placement():
    pass


@pytest.mark.parametrize(
    "offer_statistics_flat_page,exp_offer_statistics",
    [
        (
            BeautifulSoup(
                '<div data-name="OfferStats"><a data-name="Link">726 просмотров, 263 за сегодня</a></div>>',
                "html.parser",
            ),
            {"all_views": 726, "today_views": 263},
        )
    ],
)
def test_get_offer_statistics(
    parser, offer_statistics_flat_page, exp_offer_statistics
):

    assert (
        parser.get_offer_statistics(offer_statistics_flat_page)
        == exp_offer_statistics
    )


def test_signal_handler():
    pass
