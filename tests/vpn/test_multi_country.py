from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from fli.models import Airline, Airport, FlightLeg, FlightResult
from fli.search.multi_country import CountryResult, search_all_countries


def _make_flight(price: float) -> FlightResult:
    return FlightResult(
        price=price,
        duration=180,
        stops=0,
        legs=[
            FlightLeg(
                airline=Airline.DL,
                flight_number="DL1",
                departure_airport=Airport.JFK,
                arrival_airport=Airport.LAX,
                departure_datetime=datetime.now(),
                arrival_datetime=datetime.now() + timedelta(hours=3),
                duration=180,
            )
        ],
    )


def test_country_result_success():
    flights = [_make_flight(300.0)]
    result = CountryResult(country_code="IN", country_name="India", flights=flights, error=None)
    assert result.error is None
    assert result.flights[0].price == 300.0


def test_country_result_failure():
    result = CountryResult(country_code="TR", country_name="Turkey", flights=None, error="blocked")
    assert result.flights is None
    assert result.error == "blocked"


def test_search_all_countries_returns_result_per_country():
    mock_flights = [_make_flight(250.0)]
    countries = [("IN", "India"), ("MX", "Mexico")]

    with patch("fli.search.multi_country.TorManager") as mock_tor, \
         patch("fli.search.multi_country.Client") as mock_client_cls, \
         patch("fli.search.multi_country.SearchFlights") as mock_search_cls:
        mock_search_cls.return_value.search.return_value = mock_flights

        results = search_all_countries(MagicMock(), countries=countries)

    assert len(results) == 2
    assert results[0].country_code == "IN"
    assert results[0].flights == mock_flights
    assert results[0].error is None


def test_search_all_countries_continues_after_single_country_failure():
    countries = [("IN", "India"), ("MX", "Mexico")]

    def search_side_effect(filters):
        if search_side_effect.call_count <= 3:  # IN fails 3 times (initial + 2 retries)
            return None
        return [_make_flight(300.0)]

    search_side_effect.call_count = 0

    def counting_search(filters):
        search_side_effect.call_count += 1
        return search_side_effect(filters)

    with patch("fli.search.multi_country.TorManager"), \
         patch("fli.search.multi_country.Client"), \
         patch("fli.search.multi_country.SearchFlights") as mock_search_cls:
        mock_search_cls.return_value.search.side_effect = counting_search

        results = search_all_countries(MagicMock(), countries=countries)

    assert len(results) == 2
    assert results[0].error == "blocked"
    assert results[1].flights is not None


def test_search_all_countries_retries_on_empty_result():
    countries = [("IN", "India")]
    call_count = {"n": 0}

    def search_side_effect(filters):
        call_count["n"] += 1
        if call_count["n"] < 2:
            return None  # first attempt empty
        return [_make_flight(200.0)]

    with patch("fli.search.multi_country.TorManager"), \
         patch("fli.search.multi_country.Client"), \
         patch("fli.search.multi_country.SearchFlights") as mock_search_cls:
        mock_search_cls.return_value.search.side_effect = search_side_effect

        results = search_all_countries(MagicMock(), countries=countries)

    assert results[0].flights is not None
    assert call_count["n"] == 2  # retried once


def test_search_all_countries_uses_default_cheap_countries_when_none():
    with patch("fli.search.multi_country.TorManager"), \
         patch("fli.search.multi_country.Client"), \
         patch("fli.search.multi_country.SearchFlights") as mock_search_cls, \
         patch("fli.search.multi_country.CHEAP_COUNTRIES",
               [("IN", "India"), ("MX", "Mexico")]):
        mock_search_cls.return_value.search.return_value = [_make_flight(100.0)]
        results = search_all_countries(MagicMock(), countries=None)

    assert len(results) == 2
