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
