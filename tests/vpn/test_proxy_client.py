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
