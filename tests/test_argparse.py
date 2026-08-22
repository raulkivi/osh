import sys

import pytest

import osh


def test_no_arguments_gives_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["osh"])
    args = osh.parse_arguments()
    assert args.query == []
    assert args.ask is False
    assert args.init is False
    assert args.config is None
    assert args.model is None


def test_query_words_are_collected_as_positional_args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["osh", "list", "files", "here"])
    assert osh.parse_arguments().query == ["list", "files", "here"]


def test_ask_flag_short_form(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["osh", "-a", "do", "thing"])
    assert osh.parse_arguments().ask is True


def test_ask_flag_long_form(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["osh", "--ask", "do", "thing"])
    assert osh.parse_arguments().ask is True


def test_init_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["osh", "--init"])
    assert osh.parse_arguments().init is True


def test_config_path_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["osh", "--config", "/tmp/custom.json", "do", "thing"])
    assert osh.parse_arguments().config == "/tmp/custom.json"


def test_model_flag_short_form(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["osh", "-m", "llama3", "do", "thing"])
    assert osh.parse_arguments().model == "llama3"


def test_model_flag_long_form_accepts_dash_for_interactive_selection(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["osh", "--model", "-", "do", "thing"])
    assert osh.parse_arguments().model == "-"


def test_version_flag_prints_version_and_exits_zero(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["osh", "--version"])
    with pytest.raises(SystemExit) as exc_info:
        osh.parse_arguments()
    assert exc_info.value.code == 0
    assert f"osh {osh.__version__}" in capsys.readouterr().out


def test_unknown_flag_exits_with_usage_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["osh", "--bogus-flag"])
    with pytest.raises(SystemExit) as exc_info:
        osh.parse_arguments()
    assert exc_info.value.code == 2
    assert "usage" in capsys.readouterr().err.lower()
