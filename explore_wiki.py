"""Scrape Wikipedia airport page → set of direct-route IATA codes."""
import re
import requests
from bs4 import BeautifulSoup

from explore_city_map import lookup

# IATA → Wikipedia page slug
WIKI_SLUGS = {
    "TPE": "Taiwan_Taoyuan_International_Airport",
    "TSA": "Taipei_Songshan_Airport",
    "KHH": "Kaohsiung_International_Airport",
    "NRT": "Narita_International_Airport",
    "HND": "Haneda_Airport",
    "KIX": "Kansai_International_Airport",
    "NGO": "Chubu_Centrair_International_Airport",
    "CTS": "New_Chitose_Airport",
    "FUK": "Fukuoka_Airport",
    "OKA": "Naha_Airport",
    "HKG": "Hong_Kong_International_Airport",
    "MFM": "Macau_International_Airport",
    "ICN": "Incheon_International_Airport",
    "GMP": "Gimpo_International_Airport",
    "PUS": "Gimhae_International_Airport",
    "SIN": "Singapore_Changi_Airport",
    "KUL": "Kuala_Lumpur_International_Airport",
    "BKK": "Suvarnabhumi_Airport",
    "DMK": "Don_Mueang_International_Airport",
    "MNL": "Ninoy_Aquino_International_Airport",
    "CGK": "Soekarno%E2%80%93Hatta_International_Airport",
    "DPS": "Ngurah_Rai_International_Airport",
    "SGN": "Tan_Son_Nhat_International_Airport",
    "HAN": "Noi_Bai_International_Airport",
    "PEK": "Beijing_Capital_International_Airport",
    "PVG": "Shanghai_Pudong_International_Airport",
    "CAN": "Guangzhou_Baiyun_International_Airport",
    "SZX": "Shenzhen_Bao'an_International_Airport",
    "IAH": "George_Bush_Intercontinental_Airport",
    "DFW": "Dallas%2FFort_Worth_International_Airport",
    "LAX": "Los_Angeles_International_Airport",
    "SFO": "San_Francisco_International_Airport",
    "JFK": "John_F._Kennedy_International_Airport",
    "ORD": "O%27Hare_International_Airport",
    "LHR": "Heathrow_Airport",
    "CDG": "Charles_de_Gaulle_Airport",
    "AMS": "Amsterdam_Airport_Schiphol",
    "FRA": "Frankfurt_Airport",
    "MUC": "Munich_Airport",
    "IST": "Istanbul_Airport",
    "DXB": "Dubai_International_Airport",
    "DOH": "Hamad_International_Airport",
    "AUH": "Abu_Dhabi_International_Airport",
    "DEL": "Indira_Gandhi_International_Airport",
    "BOM": "Chhatrapati_Shivaji_Maharaj_International_Airport",
}

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Mozilla/5.0 (explore_wiki.py research tool)"})


def _fetch_html(iata: str) -> str:
    slug = WIKI_SLUGS.get(iata.upper())
    if not slug:
        raise ValueError(f"No Wikipedia slug for {iata}. Add it to WIKI_SLUGS.")
    url = f"https://en.wikipedia.org/wiki/{slug}"
    r = _SESSION.get(url, timeout=20)
    r.raise_for_status()
    return r.text


def _clean_cell(cell) -> list[str]:
    """Extract destination name strings from a table cell, stripping refs/notes."""
    text = cell.get_text(separator=",")
    # Remove footnote references like [1], [citation needed]
    text = re.sub(r"\[[^\]]*\]", "", text)
    # Remove parenthetical notes like (ends 30 May 2026)
    text = re.sub(r"\([^)]*\)", "", text)
    # Split on comma or newline, strip each token
    parts = [p.strip() for p in re.split(r"[,\n]+", text)]
    return [p for p in parts if p and len(p) > 1]


def get_destinations(iata: str, verbose: bool = False) -> set[str]:
    """
    Fetch Wikipedia page for the given airport and return a set of IATA codes
    for all listed direct destinations.
    """
    html = _fetch_html(iata)
    soup = BeautifulSoup(html, "html.parser")

    # Find all wikitables that have an 'Airlines' + 'Destinations' header
    tables = soup.find_all("table", class_="wikitable")
    dest_iatas: set[str] = set()
    unmatched: set[str] = set()

    for table in tables:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if "airlines" not in headers and "airline" not in headers:
            continue
        if "destinations" not in headers and "destination" not in headers:
            continue

        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            # Destinations are always in the second column (index 1)
            for name in _clean_cell(cols[1]):
                # Skip section labels like "Charter:", "Seasonal:", etc.
                if name.endswith(":") or name.lower() in ("seasonal", "charter", "cargo"):
                    continue
                code = lookup(name)
                if code:
                    dest_iatas.add(code)
                else:
                    unmatched.add(name)

    if verbose:
        print(f"  Matched: {len(dest_iatas)} airports")
        if unmatched:
            print(f"  Unmatched ({len(unmatched)}): {sorted(unmatched)[:20]}")

    # Remove the origin airport itself if it crept in
    dest_iatas.discard(iata.upper())
    return dest_iatas
