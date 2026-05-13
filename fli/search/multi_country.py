"""Sequential multi-country flight search via Tor exit nodes."""

from dataclasses import dataclass

import typer

from fli.models import FlightResult, FlightSearchFilters
from fli.search.client import TOR_PROXIES, Client
from fli.search.flights import SearchFlights
from fli.vpn.countries import CHEAP_COUNTRIES
from fli.vpn.tor_manager import TorManager, TorNotRunningError

MAX_RETRIES = 2


@dataclass
class CountryResult:
    """Result of a flight search from a single country's Tor exit node."""

    country_code: str
    country_name: str
    flights: list[FlightResult] | None
    error: str | None


def search_all_countries(
    filters: FlightSearchFilters,
    countries: list[tuple[str, str]] | None = None,
) -> list[CountryResult]:
    """Run the same flight search from each country's Tor exit node sequentially.

    Args:
        filters: Flight search filters to use for every country query.
        countries: List of (code, name) tuples. Defaults to CHEAP_COUNTRIES.

    Returns:
        One CountryResult per country, including failed ones.

    Raises:
        TorNotRunningError: If Tor is not running before any search starts.

    """
    if not TorManager.is_tor_running():
        raise TorNotRunningError(
            "Tor is not running. Setup:\n"
            "  brew install tor\n"
            "  echo 'ControlPort 9051' >> /usr/local/etc/tor/torrc\n"
            "  echo 'CookieAuthentication 1' >> /usr/local/etc/tor/torrc\n"
            "  brew services restart tor"
        )

    target = countries if countries is not None else CHEAP_COUNTRIES
    results: list[CountryResult] = []

    for country_code, country_name in target:
        typer.echo(f"  Querying {country_name} ({country_code})...", nl=False)
        result = _search_one_country(filters, country_code, country_name)
        if result.error:
            typer.echo(f" ✗ {result.error}")
        else:
            cheapest = min(f.price for f in result.flights)
            typer.echo(f" ✓ ${cheapest:.0f}")
        results.append(result)

    return results


def _search_one_country(
    filters: FlightSearchFilters,
    country_code: str,
    country_name: str,
) -> CountryResult:
    for attempt in range(MAX_RETRIES + 1):
        try:
            with TorManager.country_exit(country_code):
                client = Client(proxies=TOR_PROXIES)
                flights = SearchFlights(client=client).search(filters)
            if flights:
                return CountryResult(country_code, country_name, flights, None)
            if attempt < MAX_RETRIES:
                continue  # empty result → retry with new circuit
        except TorNotRunningError:
            raise  # propagate immediately, don't retry
        except Exception:
            if attempt < MAX_RETRIES:
                continue
    return CountryResult(country_code, country_name, None, "blocked")
