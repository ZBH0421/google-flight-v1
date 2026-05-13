"""Tor circuit manager for country-specific exit node switching."""

import socket
import time
from collections.abc import Generator
from contextlib import contextmanager

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
