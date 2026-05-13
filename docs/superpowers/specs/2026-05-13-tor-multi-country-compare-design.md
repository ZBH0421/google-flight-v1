# Tor Multi-Country Price Comparison

**Date:** 2026-05-13  
**Status:** Approved

## Goal

Add a `--compare-countries` flag to the `fli flights` CLI command that automatically runs the same flight search from 8 country-specific Tor exit nodes and returns a price comparison table. Helps identify geographic price differences on Google Flights.

## Target Countries

Known to show lower prices due to regional market pricing:

| Country | Code |
|---------|------|
| India | IN |
| Mexico | MX |
| Thailand | TH |
| Turkey | TR |
| Brazil | BR |
| Indonesia | ID |
| Vietnam | VN |
| Malaysia | MY |

## Architecture

```
fli/
├── vpn/
│   ├── __init__.py
│   ├── tor_manager.py      # Tor circuit control via stem
│   └── countries.py        # load from countries.toml, fallback to defaults
├── search/
│   ├── client.py           # Add optional proxies param
│   └── multi_country.py    # Sequential per-country search runner
└── cli/
    └── main.py             # Add --compare-countries + --countries flags
fli/vpn/countries.toml      # user-editable country list (bundled default)
```

## Query Flow

```
fli flights TPE NRT 2026-10-25 --compare-countries
  ↓
MultiCountrySearch.search_all_countries(filters)
  ↓ for each country in CHEAP_COUNTRIES:
  TorManager.switch_country("IN")
    → stem: SETCONF ExitNodes={IN} StrictNodes=1
    → stem: SIGNAL NEWNYM
    → poll until circuit ready (max 30s)
  Client(proxies={"http": "socks5://127.0.0.1:9050", ...}).search(filters)
  → store CountryResult
  ↓
print comparison table, highlight cheapest
```

## Components

### `fli/vpn/tor_manager.py`

```python
class TorManager:
    def switch_country(country_code: str) -> None
    def is_tor_running() -> bool
```

- `switch_country`: connects to ControlPort 9051, sets ExitNodes, signals NEWNYM, polls for new circuit (max 30s), restores ExitNodes="" on exit
- `is_tor_running`: checks ports 9050 (SOCKS) and 9051 (Control) are listening; raises with setup instructions if not

### `fli/vpn/countries.toml` (user-editable)

```toml
# Add or remove countries here — no code changes needed
[[countries]]
code = "IN"
name = "India"

[[countries]]
code = "MX"
name = "Mexico"

# ... etc for all 8 defaults
```

### `fli/vpn/countries.py`

Loads `countries.toml` from the package directory. Provides `load_countries() -> list[tuple[str, str]]`.

### CLI `--countries` flag (temporary override)

```bash
# Use default list from countries.toml
fli flights TPE NRT 2026-10-25 --compare-countries

# Override with a custom list for this run only
fli flights TPE NRT 2026-10-25 --compare-countries --countries IN,MX,KR
```

### `fli/search/multi_country.py`

```python
@dataclass
class CountryResult:
    country_code: str
    country_name: str
    flights: list[FlightResult] | None
    error: str | None          # "circuit timeout" | "blocked" | None

def search_all_countries(filters: FlightSearchFilters) -> list[CountryResult]
```

- Iterates countries sequentially
- Per-country retry: on 403/429/empty result, issues `SIGNAL NEWNYM` and retries up to 2 times before marking `error="blocked"`
- Single country failure does not abort the run
- Returns all results including failed ones

### `fli/search/client.py` (minor change)

Add `proxies: dict | None = None` parameter to `Client.__init__`, pass to `curl_cffi` Session.

### CLI output

```
Comparing prices from 8 countries... (this may take 3-5 minutes)

  India (IN)       ✓  $298   3 flights
  Mexico (MX)      ✓  $410   1 flight
  Thailand (TH)    ✓  $312   2 flights
  Turkey (TR)      ✗  blocked
  Brazil (BR)      ✓  $389   2 flights
  Indonesia (ID)   ✓  $301   4 flights
  Vietnam (VN)     ✓  $275   2 flights
  Malaysia (MY)    ✗  circuit timeout

Cheapest: Vietnam (VN)  $275
```

## Error Handling

| Layer | Condition | Behavior |
|-------|-----------|----------|
| Tor not running | Port 9050/9051 not listening | Print setup instructions, exit cleanly |
| Circuit timeout | Exit node unavailable after 30s | Mark country as `error="circuit timeout"`, continue |
| Google blocks Tor IP | 403 / 429 / empty result | SIGNAL NEWNYM + retry up to 2×; if all fail, mark `error="blocked"`, continue |

## Prerequisites (user-side)

```bash
brew install tor
brew services start tor
# Enable ControlPort in torrc:
# echo "ControlPort 9051\nCookieAuthentication 1" >> /usr/local/etc/tor/torrc
# brew services restart tor
pip install stem
```

## Testing

```
tests/vpn/
  test_tor_manager.py    # mock stem; test switch_country logic and timeout
  test_multi_country.py  # mock Client; test sequential flow and per-country failure isolation
```

No integration tests requiring a live Tor connection. Real-world acceptance testing done manually via CLI.

## Out of Scope

- MCP server integration (CLI only for now)
- Result persistence / history comparison
- Persistent per-country block history (always retries fresh each run)
- Parallel execution (can be added later if sequential is too slow)
