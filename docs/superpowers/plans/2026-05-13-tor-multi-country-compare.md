# Tor Multi-Country Price Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--compare-countries` to `fli flights` CLI to run the same search from 8 country-specific Tor exit nodes and display a price comparison table.

**Architecture:** A new `fli/vpn/` package controls Tor circuits via `stem`. `Client` gains an optional `proxies` param that routes requests through `socks5://127.0.0.1:9050`. `search_all_countries()` iterates each country sequentially, retrying up to 2× on block, and returns structured `CountryResult` objects for display.

**Tech Stack:** `stem` (Tor control), `curl_cffi` (existing HTTP client with proxy support), `rich` (existing CLI display), `typer` (existing CLI framework)

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `fli/vpn/__init__.py` | Package init |
| Create | `fli/vpn/countries.py` | Country list + name lookup |
| Create | `fli/vpn/tor_manager.py` | Tor circuit switching via stem |
| Create | `fli/search/multi_country.py` | Sequential per-country search runner |
| Create | `tests/vpn/__init__.py` | Test package init |
| Create | `tests/vpn/test_countries.py` | Country list tests |
| Create | `tests/vpn/test_tor_manager.py` | TorManager tests (mock stem) |
| Create | `tests/vpn/test_multi_country.py` | Multi-country search tests (mock everything) |
| Modify | `fli/search/client.py:27-30` | Add `proxies` param to `Client.__init__` |
| Modify | `fli/search/flights.py:35-37` | Accept optional `client` in `SearchFlights.__init__` |
| Modify | `fli/cli/commands/flights.py` | Add `--compare-countries` and `--countries` flags |
| Modify | `pyproject.toml` | Add `stem` to optional `vpn` dependency group |

---

## Task 1: Setup — vpn package, countries list, stem dependency

**Files:**
- Create: `fli/vpn/__init__.py`
- Create: `fli/vpn/countries.py`
- Create: `tests/vpn/__init__.py`
- Create: `tests/vpn/test_countries.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write the failing tests**

Create `tests/vpn/__init__.py` (empty):
```python
```

Create `tests/vpn/test_countries.py`:
```python
from fli.vpn.countries import CHEAP_COUNTRIES, COUNTRY_NAMES, parse_countries_flag


def test_cheap_countries_has_eight_entries():
    assert len(CHEAP_COUNTRIES) == 8


def test_cheap_countries_tuples_have_code_and_name():
    for code, name in CHEAP_COUNTRIES:
        assert len(code) == 2
        assert len(name) > 0


def test_country_names_lookup():
    assert COUNTRY_NAMES["IN"] == "India"
    assert COUNTRY_NAMES["MX"] == "Mexico"


def test_parse_countries_flag_known_codes():
    result = parse_countries_flag("IN,MX")
    assert result == [("IN", "India"), ("MX", "Mexico")]


def test_parse_countries_flag_unknown_code_uses_code_as_name():
    result = parse_countries_flag("KR")
    assert result == [("KR", "KR")]


def test_parse_countries_flag_strips_whitespace():
    result = parse_countries_flag("IN, MX")
    assert result == [("IN", "India"), ("MX", "Mexico")]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/ph/dash_git_pre/fli
uv run pytest tests/vpn/test_countries.py -v
```

Expected: `ModuleNotFoundError: No module named 'fli.vpn'`

- [ ] **Step 3: Create the package and implementation**

Create `fli/vpn/__init__.py`:
```python
"""VPN/proxy utilities for geo-targeted flight searches."""
```

Create `fli/vpn/countries.py`:
```python
"""Country list for geo-targeted Tor exit node searches."""

# Add or remove entries here to change the default country list.
# Each entry is (ISO-2-letter-code, display-name).
CHEAP_COUNTRIES: list[tuple[str, str]] = [
    ("IN", "India"),
    ("MX", "Mexico"),
    ("TH", "Thailand"),
    ("TR", "Turkey"),
    ("BR", "Brazil"),
    ("ID", "Indonesia"),
    ("VN", "Vietnam"),
    ("MY", "Malaysia"),
]

COUNTRY_NAMES: dict[str, str] = {code: name for code, name in CHEAP_COUNTRIES}


def parse_countries_flag(countries_str: str) -> list[tuple[str, str]]:
    """Parse a comma-separated country code string into (code, name) tuples.

    Args:
        countries_str: Comma-separated ISO codes, e.g. "IN,MX,KR"

    Returns:
        List of (code, name) tuples. Unknown codes use the code itself as name.

    """
    codes = [c.strip().upper() for c in countries_str.split(",")]
    return [(code, COUNTRY_NAMES.get(code, code)) for code in codes if code]
```

- [ ] **Step 4: Add stem to pyproject.toml**

In `pyproject.toml`, add after the `mcp` optional group:
```toml
vpn = [
    "stem>=1.8.0",
]
all = [
    "flights[mcp]",
    "flights[vpn]",
]
```

(Replace the existing `all = ["flights[mcp]"]` line.)

- [ ] **Step 5: Install stem**

```bash
uv add --optional vpn stem
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
uv run pytest tests/vpn/test_countries.py -v
```

Expected: 6 tests PASSED

- [ ] **Step 7: Commit**

```bash
git add fli/vpn/__init__.py fli/vpn/countries.py tests/vpn/__init__.py tests/vpn/test_countries.py pyproject.toml uv.lock
git commit -m "feat: add vpn package with country list and stem dependency"
```

---

## Task 2: TorManager — Tor circuit switching

**Files:**
- Create: `fli/vpn/tor_manager.py`
- Create: `tests/vpn/test_tor_manager.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/vpn/test_tor_manager.py`:
```python
import socket
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from fli.vpn.tor_manager import TorManager, TorNotRunningError


def test_is_tor_running_false_when_ports_closed():
    with patch("socket.create_connection", side_effect=ConnectionRefusedError):
        assert TorManager.is_tor_running() is False


def test_is_tor_running_true_when_both_ports_open():
    mock_sock = MagicMock()
    mock_sock.__enter__ = lambda s: s
    mock_sock.__exit__ = MagicMock(return_value=False)
    with patch("socket.create_connection", return_value=mock_sock):
        assert TorManager.is_tor_running() is True


def test_country_exit_raises_when_tor_not_running():
    with patch.object(TorManager, "is_tor_running", return_value=False):
        with pytest.raises(TorNotRunningError, match="Tor is not running"):
            with TorManager.country_exit("IN"):
                pass


def test_country_exit_sets_exit_node_before_yielding():
    mock_controller = MagicMock()
    mock_controller.get_newnym_wait.return_value = 0
    set_conf_calls = []
    mock_controller.set_conf.side_effect = lambda k, v: set_conf_calls.append((k, v))

    with patch.object(TorManager, "is_tor_running", return_value=True), \
         patch("fli.vpn.tor_manager.Controller") as mock_ctrl_class, \
         patch("fli.vpn.tor_manager.time.sleep"):
        mock_ctrl_class.from_port.return_value.__enter__ = lambda s: mock_controller
        mock_ctrl_class.from_port.return_value.__exit__ = MagicMock(return_value=False)

        with TorManager.country_exit("IN"):
            # ExitNodes={IN} must be set before we enter the body
            assert ("ExitNodes", "{IN}") in set_conf_calls

    # ExitNodes must be restored after the body
    assert ("ExitNodes", "") in set_conf_calls


def test_country_exit_restores_exit_nodes_even_on_exception():
    mock_controller = MagicMock()
    mock_controller.get_newnym_wait.return_value = 0
    restored = {"done": False}
    original_set_conf = mock_controller.set_conf

    def tracking_set_conf(k, v):
        if k == "ExitNodes" and v == "":
            restored["done"] = True

    mock_controller.set_conf.side_effect = tracking_set_conf

    with patch.object(TorManager, "is_tor_running", return_value=True), \
         patch("fli.vpn.tor_manager.Controller") as mock_ctrl_class, \
         patch("fli.vpn.tor_manager.time.sleep"):
        mock_ctrl_class.from_port.return_value.__enter__ = lambda s: mock_controller
        mock_ctrl_class.from_port.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(RuntimeError):
            with TorManager.country_exit("IN"):
                raise RuntimeError("simulated search failure")

    assert restored["done"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/vpn/test_tor_manager.py -v
```

Expected: `ModuleNotFoundError: No module named 'fli.vpn.tor_manager'`

- [ ] **Step 3: Implement TorManager**

Create `fli/vpn/tor_manager.py`:
```python
"""Tor circuit manager for country-specific exit node switching."""

import socket
import time
from contextlib import contextmanager
from typing import Generator

from stem import Signal
from stem.control import Controller


class TorNotRunningError(RuntimeError):
    """Raised when Tor daemon is not accessible on expected ports."""


TOR_SOCKS_PORT = 9050
TOR_CONTROL_PORT = 9051

_SETUP_HINT = (
    "Tor is not running. Setup:\n"
    "  brew install tor\n"
    "  echo 'ControlPort 9051' >> /usr/local/etc/tor/torrc\n"
    "  echo 'CookieAuthentication 1' >> /usr/local/etc/tor/torrc\n"
    "  brew services restart tor"
)


class TorManager:
    """Controls Tor exit node selection via the stem library.

    Requires Tor running with ControlPort 9051 and CookieAuthentication enabled.
    """

    @staticmethod
    def is_tor_running() -> bool:
        """Return True if both Tor SOCKS and control ports are reachable."""
        for port in [TOR_SOCKS_PORT, TOR_CONTROL_PORT]:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    pass
            except (ConnectionRefusedError, OSError):
                return False
        return True

    @staticmethod
    @contextmanager
    def country_exit(country_code: str) -> Generator[None, None, None]:
        """Context manager that sets Tor exit node to country_code for its duration.

        ExitNodes is set BEFORE yielding and restored AFTER the body exits,
        even on exception. This ensures the search runs with the correct exit node.

        Args:
            country_code: ISO 2-letter country code, e.g. "IN"

        Raises:
            TorNotRunningError: If Tor ports are not reachable.

        """
        if not TorManager.is_tor_running():
            raise TorNotRunningError(_SETUP_HINT)

        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate()
            controller.set_conf("ExitNodes", f"{{{country_code}}}")
            controller.set_conf("StrictNodes", "1")
            controller.signal(Signal.NEWNYM)
            wait = controller.get_newnym_wait()
            if wait:
                time.sleep(wait)
            try:
                yield
            finally:
                controller.set_conf("ExitNodes", "")
                controller.set_conf("StrictNodes", "0")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/vpn/test_tor_manager.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add fli/vpn/tor_manager.py tests/vpn/test_tor_manager.py
git commit -m "feat: add TorManager with country_exit context manager for exit node control"
```

---

## Task 3: Proxy support in Client + optional client in SearchFlights

**Files:**
- Modify: `fli/search/client.py`
- Modify: `fli/search/flights.py`
- Create: `tests/vpn/test_proxy_client.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/vpn/test_proxy_client.py`:
```python
from unittest.mock import MagicMock, patch

from fli.search.client import Client, TOR_PROXIES
from fli.search.flights import SearchFlights


def test_client_stores_proxies():
    proxies = {"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"}
    client = Client(proxies=proxies)
    assert client._proxies == proxies


def test_client_no_proxies_by_default():
    client = Client()
    assert client._proxies is None


def test_client_post_passes_proxies_to_request():
    proxies = {"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"}
    client = Client(proxies=proxies)
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    with patch.object(client._client, "post", return_value=mock_response) as mock_post:
        client.post("https://example.com", data="test")
    _, kwargs = mock_post.call_args
    assert kwargs.get("proxies") == proxies


def test_tor_proxies_constant_points_to_localhost_9050():
    assert "9050" in TOR_PROXIES["http"]
    assert "socks5" in TOR_PROXIES["http"]


def test_search_flights_uses_custom_client():
    custom_client = MagicMock()
    search = SearchFlights(client=custom_client)
    assert search.client is custom_client


def test_search_flights_uses_default_client_when_none():
    with patch("fli.search.flights.get_client") as mock_get:
        mock_get.return_value = MagicMock()
        search = SearchFlights()
    mock_get.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/vpn/test_proxy_client.py -v
```

Expected: multiple FAILED with `ImportError` or `AssertionError`

- [ ] **Step 3: Modify Client to accept proxies**

In `fli/search/client.py`, replace lines 17-30 (the module-level `client = None` and `Client.__init__`):

```python
client = None

TOR_PROXIES: dict[str, str] = {
    "http": "socks5://127.0.0.1:9050",
    "https": "socks5://127.0.0.1:9050",
}


class Client:
    """HTTP client with built-in rate limiting, retry and user agent impersonation functionality."""

    DEFAULT_HEADERS = {
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    }

    def __init__(self, proxies: dict[str, str] | None = None):
        """Initialize a new client session with default headers."""
        self._client = requests.Session()
        self._client.headers.update(self.DEFAULT_HEADERS)
        self._proxies = proxies
```

Then update both `get` and `post` methods to inject proxies. Replace the `get` method body:

```python
    @sleep_and_retry
    @limits(calls=10, period=1)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(), reraise=True)
    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a rate-limited GET request with automatic retries."""
        if self._proxies:
            kwargs.setdefault("proxies", self._proxies)
        try:
            response = self._client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            raise Exception(f"GET request failed: {str(e)}") from e
```

Replace the `post` method body:

```python
    @sleep_and_retry
    @limits(calls=10, period=1)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(), reraise=True)
    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a rate-limited POST request with automatic retries."""
        if self._proxies:
            kwargs.setdefault("proxies", self._proxies)
        try:
            response = self._client.post(url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            raise Exception(f"POST request failed: {str(e)}") from e
```

- [ ] **Step 4: Modify SearchFlights to accept optional client**

In `fli/search/flights.py`, replace lines 35-37:

```python
    def __init__(self, client: "Client | None" = None):
        """Initialize the search client for flight searches."""
        from fli.search.client import Client, get_client
        self.client = client if client is not None else get_client()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/vpn/test_proxy_client.py -v
```

Expected: 6 tests PASSED

- [ ] **Step 6: Verify existing tests still pass**

```bash
uv run pytest tests/ -v --ignore=tests/vpn -x
```

Expected: all existing tests PASSED

- [ ] **Step 7: Commit**

```bash
git add fli/search/client.py fli/search/flights.py tests/vpn/test_proxy_client.py
git commit -m "feat: add proxy support to Client and optional client param to SearchFlights"
```

---

## Task 4: Multi-country sequential search runner

**Files:**
- Create: `fli/search/multi_country.py`
- Create: `tests/vpn/test_multi_country.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/vpn/test_multi_country.py`:
```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/vpn/test_multi_country.py -v
```

Expected: `ModuleNotFoundError: No module named 'fli.search.multi_country'`

- [ ] **Step 3: Implement multi_country.py**

Create `fli/search/multi_country.py`:
```python
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
            "  echo 'ControlPort 9051\\nCookieAuthentication 1'"
            " >> /usr/local/etc/tor/torrc\n"
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
            # country_exit keeps ExitNodes set for the entire search, then restores
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/vpn/test_multi_country.py -v
```

Expected: all tests PASSED

- [ ] **Step 5: Commit**

```bash
git add fli/search/multi_country.py tests/vpn/test_multi_country.py
git commit -m "feat: add sequential multi-country search with Tor exit node switching"
```

---

## Task 5: CLI integration — --compare-countries and --countries flags

**Files:**
- Modify: `fli/cli/commands/flights.py`
- Create: `tests/vpn/test_cli_compare.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/vpn/test_cli_compare.py`:
```python
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

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
    with patch("fli.cli.commands.flights.search_all_countries", return_value=mock_results) as mock_search, \
         patch("fli.cli.commands.flights.TorNotRunningError", Exception):
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
    with patch("fli.cli.commands.flights.search_all_countries", return_value=mock_results), \
         patch("fli.cli.commands.flights.TorNotRunningError", Exception):
        result = runner.invoke(
            app,
            ["flights", "JFK", "LAX", datetime.now().strftime("%Y-%m-%d"),
             "--compare-countries", "--countries", "IN"],
        )
    assert result.exit_code == 0


def test_compare_countries_shows_tor_not_running_error(runner):
    from fli.vpn.tor_manager import TorNotRunningError

    with patch("fli.cli.commands.flights.search_all_countries",
               side_effect=TorNotRunningError("Tor is not running")):
        result = runner.invoke(
            app,
            ["flights", "JFK", "LAX", datetime.now().strftime("%Y-%m-%d"), "--compare-countries"],
        )
    assert result.exit_code == 1
    assert "Tor is not running" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/vpn/test_cli_compare.py -v
```

Expected: FAILED — `--compare-countries` not recognised

- [ ] **Step 3: Add imports to flights.py**

At the top of `fli/cli/commands/flights.py`, add to the import block:

```python
from fli.search.multi_country import CountryResult, search_all_countries
from fli.vpn.countries import parse_countries_flag
from fli.vpn.tor_manager import TorNotRunningError
```

- [ ] **Step 4: Add _display_country_comparison helper**

Add this function before `_search_flights_core` in `fli/cli/commands/flights.py`:

```python
def _display_country_comparison(results: list[CountryResult]) -> None:
    """Print a Rich table comparing cheapest prices per country."""
    from rich import box
    from rich.table import Table

    from fli.cli.console import console

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Country", style="cyan", min_width=14)
    table.add_column("Code", width=6)
    table.add_column("Cheapest", justify="right", style="green", min_width=10)
    table.add_column("Flights", justify="right", width=8)
    table.add_column("Status", width=10)

    for r in results:
        if r.error:
            table.add_row(r.country_name, r.country_code, "-", "-", f"[red]{r.error}[/red]")
        else:
            cheapest = min(f.price for f in r.flights)
            table.add_row(
                r.country_name, r.country_code,
                f"${cheapest:.0f}", str(len(r.flights)),
                "[green]✓[/green]",
            )

    console.print(table)

    successful = [r for r in results if r.flights]
    if successful:
        best = min(successful, key=lambda r: min(f.price for f in r.flights))
        best_price = min(f.price for f in best.flights)
        console.print(
            f"\n[bold green]Cheapest: {best.country_name} ({best.country_code})"
            f"  ${best_price:.0f}[/bold green]"
        )
```

- [ ] **Step 5: Add --compare-countries and --countries flags to flights()**

In `flights()` function in `fli/cli/commands/flights.py`, add two new parameters after `currency`:

```python
    compare_countries: Annotated[
        bool,
        typer.Option(
            "--compare-countries",
            help="Search from multiple countries via Tor and compare prices",
        ),
    ] = False,
    countries: Annotated[
        str | None,
        typer.Option(
            "--countries",
            help="Comma-separated country codes to compare (e.g. IN,MX,TH). "
                 "Defaults to built-in cheap-country list.",
        ),
    ] = None,
```

- [ ] **Step 6: Add compare-countries branch in flights()**

At the end of the `flights()` function body, replace the final `_search_flights_core(...)` call with:

```python
    if compare_countries:
        country_list = parse_countries_flag(countries) if countries else None
        # Build filters using existing core logic then hand off to multi-country runner
        from fli.cli.commands.flights import _build_filters

        try:
            filters = _build_filters(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                departure_window=departure_window,
                airlines=airlines,
                cabin_class=cabin_class,
                max_stops=max_stops,
                sort_by=sort_by,
                exclude_basic_economy=exclude_basic_economy,
                layover=layover,
                emissions=emissions,
                checked_bags=checked_bags,
                carry_on=carry_on,
                all_results=all_results,
            )
        except Exception as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(1) from e

        typer.echo("Comparing prices from countries via Tor (this may take 3-5 minutes)...\n")
        try:
            results = search_all_countries(filters, countries=country_list)
        except TorNotRunningError as e:
            typer.echo(str(e))
            raise typer.Exit(1) from e
        _display_country_comparison(results)
        return

    _search_flights_core(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        departure_window=departure_window,
        airlines=airlines,
        cabin_class=cabin_class,
        max_stops=max_stops,
        sort_by=sort_by,
        exclude_basic_economy=exclude_basic_economy,
        layover=layover,
        emissions=emissions,
        checked_bags=checked_bags,
        carry_on=carry_on,
        all_results=all_results,
        output_format=output_format,
        currency=currency,
    )
```

- [ ] **Step 7: Extract _build_filters helper**

To avoid duplicating filter-building logic, extract the filter construction from `_search_flights_core` into a new `_build_filters` function. Move lines 69-132 of `_search_flights_core` into:

```python
def _build_filters(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None,
    departure_window: str | tuple[int, int] | None,
    airlines: list[str] | None,
    cabin_class: str,
    max_stops: str,
    sort_by: str,
    exclude_basic_economy: bool,
    layover: list[str] | None,
    emissions: str,
    checked_bags: int,
    carry_on: bool,
    all_results: bool,
) -> FlightSearchFilters:
    """Build FlightSearchFilters from CLI arguments.

    Raises:
        ParseError: On invalid airport, airline, or enum values.

    """
    departure_date = normalize_cli_date(departure_date)
    return_date = normalize_cli_date(return_date)
    departure_window = normalize_cli_time_range(departure_window)

    origin_airport = resolve_airport(origin)
    destination_airport = resolve_airport(destination)
    seat_type = parse_cabin_class(cabin_class)
    stops = parse_max_stops(max_stops)
    parsed_airlines = parse_airlines(airlines)
    sort = parse_sort_by(sort_by)
    emissions_filter = parse_emissions(emissions)

    time_restrictions = None
    if departure_window:
        from fli.models import TimeRestrictions
        time_restrictions = TimeRestrictions(
            earliest_departure=departure_window[0],
            latest_departure=departure_window[1],
        )

    segments, trip_type = build_flight_segments(
        origin=origin_airport,
        destination=destination_airport,
        departure_date=departure_date,
        return_date=return_date,
        time_restrictions=time_restrictions,
    )

    layover_restrictions = None
    if layover:
        layover_airports = [resolve_airport(code) for code in layover]
        layover_restrictions = LayoverRestrictions(airports=layover_airports)

    bags_filter = None
    if checked_bags > 0 or carry_on:
        bags_filter = BagsFilter(checked_bags=checked_bags, carry_on=carry_on)

    return FlightSearchFilters(
        trip_type=trip_type,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=segments,
        stops=stops,
        seat_type=seat_type,
        airlines=parsed_airlines,
        sort_by=sort,
        exclude_basic_economy=exclude_basic_economy,
        layover_restrictions=layover_restrictions,
        emissions=emissions_filter,
        bags=bags_filter,
        show_all_results=all_results,
    )
```

Then update `_search_flights_core` to call `_build_filters(...)` and use the returned `filters` object.

- [ ] **Step 8: Run tests to verify they pass**

```bash
uv run pytest tests/vpn/test_cli_compare.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 9: Run full test suite**

```bash
uv run pytest tests/ -v -x
```

Expected: all tests PASSED (no regressions)

- [ ] **Step 10: Lint**

```bash
uv run ruff check fli/vpn/ fli/search/multi_country.py fli/search/client.py fli/search/flights.py fli/cli/commands/flights.py
uv run ruff format fli/vpn/ fli/search/multi_country.py fli/search/client.py fli/search/flights.py fli/cli/commands/flights.py
```

- [ ] **Step 11: Commit**

```bash
git add fli/cli/commands/flights.py tests/vpn/test_cli_compare.py
git commit -m "feat: add --compare-countries and --countries CLI flags with Rich comparison table"
```

---

## Task 6: Manual acceptance test

**Prerequisites (run once):**

```bash
# Install Tor
brew install tor

# Enable control port
echo "ControlPort 9051" >> /usr/local/etc/tor/torrc
echo "CookieAuthentication 1" >> /usr/local/etc/tor/torrc

# Start Tor
brew services start tor

# Verify Tor is running (should show ESTABLISHED connections)
netstat -an | grep 9050
netstat -an | grep 9051

# Install with vpn extras
uv sync --all-extras
```

**Run the comparison:**

```bash
# Default 8 countries, Economy, cheapest sort
uv run fli flights TPE NRT 2026-07-01 --compare-countries

# Custom country subset
uv run fli flights TPE NRT 2026-07-01 --compare-countries --countries IN,TH,VN

# Verify Tor not running error message
brew services stop tor
uv run fli flights TPE NRT 2026-07-01 --compare-countries
# Expected: clear error message with setup instructions, exit code 1
brew services start tor
```

**Expected output:**
```
Comparing prices from countries via Tor (this may take 3-5 minutes)...

  Querying India (IN)...      ✓ $312
  Querying Mexico (MX)...     ✓ $445
  Querying Thailand (TH)...   ✓ $289
  Querying Turkey (TR)...     ✗ blocked
  ...

 Country         Code   Cheapest   Flights   Status
 India           IN      $312         3        ✓
 Mexico          MX      $445         1        ✓
 Thailand        TH      $289         2        ✓
 Turkey          TR       -           -      blocked
 ...

Cheapest: Thailand (TH)  $289
```
