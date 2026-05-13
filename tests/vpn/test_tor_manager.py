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

    with (
        patch.object(TorManager, "is_tor_running", return_value=True),
        patch("fli.vpn.tor_manager.Controller") as mock_ctrl_class,
        patch("fli.vpn.tor_manager.time.sleep"),
    ):
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

    def tracking_set_conf(k, v):
        if k == "ExitNodes" and v == "":
            restored["done"] = True

    mock_controller.set_conf.side_effect = tracking_set_conf

    with (
        patch.object(TorManager, "is_tor_running", return_value=True),
        patch("fli.vpn.tor_manager.Controller") as mock_ctrl_class,
        patch("fli.vpn.tor_manager.time.sleep"),
    ):
        mock_ctrl_class.from_port.return_value.__enter__ = lambda s: mock_controller
        mock_ctrl_class.from_port.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(RuntimeError):
            with TorManager.country_exit("IN"):
                raise RuntimeError("simulated search failure")

    assert restored["done"] is True
