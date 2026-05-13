from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from fli.cli.main import app
from fli.models import Airline, Airport, FlightLeg, FlightResult
from fli.search.multi_country import CountryResult


@pytest.fixture
def runner():
    return CliRunner()


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


def test_compare_countries_flag_calls_search_all_countries(runner):
    mock_results = [
        CountryResult("IN", "India", [_make_flight(250.0)], None),
        CountryResult("MX", "Mexico", None, "blocked"),
    ]
    with patch(
        "fli.cli.commands.flights.search_all_countries", return_value=mock_results
    ) as mock_search:
        result = runner.invoke(
            app,
            ["flights", "JFK", "LAX", datetime.now().strftime("%Y-%m-%d"), "--compare-countries"],
        )
    assert result.exit_code == 0
    mock_search.assert_called_once()


def test_compare_countries_with_custom_countries_list(runner):
    mock_results = [
        CountryResult("IN", "India", [_make_flight(200.0)], None),
    ]
    with patch(
        "fli.cli.commands.flights.search_all_countries", return_value=mock_results
    ):
        result = runner.invoke(
            app,
            [
                "flights",
                "JFK",
                "LAX",
                datetime.now().strftime("%Y-%m-%d"),
                "--compare-countries",
                "--countries",
                "IN",
            ],
        )
    assert result.exit_code == 0


def test_compare_countries_shows_tor_not_running_error(runner):
    from fli.vpn.tor_manager import TorNotRunningError

    with patch(
        "fli.cli.commands.flights.search_all_countries",
        side_effect=TorNotRunningError("Tor is not running"),
    ):
        result = runner.invoke(
            app,
            ["flights", "JFK", "LAX", datetime.now().strftime("%Y-%m-%d"), "--compare-countries"],
        )
    assert result.exit_code == 1
    assert "Tor is not running" in result.output
