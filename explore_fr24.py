"""
Flightradar24-based route discovery.

Replaces explore_wiki.py with real-time schedule data from FR24's internal API.
Returns IATA codes directly — no city-name mapping needed.

Usage:
    from explore_fr24 import get_destinations
    dests = get_destinations("IAH")   # set of IATA codes
"""
import time
from functools import lru_cache

import requests

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.flightradar24.com",
    "Origin": "https://www.flightradar24.com",
})

_BASE = (
    "https://api.flightradar24.com/common/v1/airport.json"
    "?code={iata}&plugin=schedule"
    "&plugin-setting[schedule][mode]=departures"
    "&page={page}&limit=100"
)

_CACHE: dict[str, set[str]] = {}


def get_destinations(iata: str, max_pages: int = 10, verbose: bool = False) -> set[str]:
    """
    Return set of IATA codes currently served from the given airport.

    Fetches up to max_pages × 100 departure records from Flightradar24
    and extracts unique destination IATA codes.
    Falls back to explore_wiki if FR24 fails.
    """
    iata = iata.upper()
    if iata in _CACHE:
        return _CACHE[iata]

    dests: set[str] = set()
    for page in range(1, max_pages + 1):
        url = _BASE.format(iata=iata, page=page)
        try:
            r = _SESSION.get(url, timeout=15)
            if r.status_code == 429:
                if verbose:
                    print(f"  FR24 rate-limited at page {page}, stopping")
                break
            r.raise_for_status()
        except Exception as e:
            if verbose:
                print(f"  FR24 page {page} error: {e}")
            break

        data = r.json()
        try:
            schedule = (
                data["result"]["response"]["airport"]
                ["pluginData"]["schedule"]
            )
            dep_data = schedule.get("departures", {})
            flights = dep_data.get("data", [])
            total = dep_data.get("item", {}).get("total", 0)
        except (KeyError, TypeError):
            break

        added = 0
        for item in flights:
            try:
                dest_code = (
                    item["flight"]["airport"]["destination"]
                    ["code"]["iata"]
                )
                if dest_code and dest_code != iata:
                    dests.add(dest_code)
                    added += 1
            except (KeyError, TypeError):
                continue

        if verbose:
            print(f"  page {page}: +{added} → {len(dests)} unique ({total} total flights)")

        if len(flights) < 100 or page * 100 >= total:
            break
        time.sleep(0.3)  # polite delay between pages

    if not dests:
        if verbose:
            print("  FR24 returned nothing, falling back to Wikipedia")
        try:
            from explore_wiki import get_destinations as wiki_get
            dests = wiki_get(iata, verbose=verbose)
        except Exception as e:
            if verbose:
                print(f"  Wikipedia fallback also failed: {e}")

    _CACHE[iata] = dests
    return dests


def clear_cache():
    """Clear the in-memory destination cache."""
    _CACHE.clear()


if __name__ == "__main__":
    import sys
    iata = sys.argv[1].upper() if len(sys.argv) > 1 else "IAH"
    print(f"Fetching destinations from {iata} via FR24...", flush=True)
    dests = get_destinations(iata, verbose=True)
    print(f"\nTotal: {len(dests)} destinations")
    print(sorted(dests))
