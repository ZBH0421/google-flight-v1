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

COUNTRY_NAMES: dict[str, str] = dict(CHEAP_COUNTRIES)


def parse_countries_flag(countries_str: str) -> list[tuple[str, str]]:
    """Parse a comma-separated country code string into (code, name) tuples.

    Args:
        countries_str: Comma-separated ISO codes, e.g. "IN,MX,KR"

    Returns:
        List of (code, name) tuples. Unknown codes use the code itself as name.

    """
    codes = [c.strip().upper() for c in countries_str.split(",")]
    return [(code, COUNTRY_NAMES.get(code, code)) for code in codes if code]
