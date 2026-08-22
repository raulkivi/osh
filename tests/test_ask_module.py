import json
import os

import ask
import osh


def test_default_config_shared_keys_match_osh():
    # ask.DEFAULT_CONFIG is intentionally a smaller subset of osh.DEFAULT_CONFIG
    # (ask has no QA review / logging / shell config), but both tools read the
    # same config.json, so keys present in both must default to the same value.
    for key, value in ask.DEFAULT_CONFIG.items():
        assert osh.DEFAULT_CONFIG[key] == value, f"{key!r} default drifted between ask.py and osh.py"


def test_get_config_path_matches_osh(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert ask.get_config_path() == osh.get_config_path()


def test_load_config_merges_user_values(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    config_dir = tmp_path / "osh"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(json.dumps({"model": "custom-model"}))

    config = ask.load_config()

    assert config["model"] == "custom-model"
    assert config["temperature"] == ask.DEFAULT_CONFIG["temperature"]


def test_load_config_defaults_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert ask.load_config() == ask.DEFAULT_CONFIG


def test_pyenv_path_traversal_is_blocked(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    config_dir = tmp_path / "osh"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        json.dumps({"python_venv": "pyenv:../../etc/passwd"})
    )
    execv_calls = []
    monkeypatch.setattr(ask.os, "execv", lambda *a, **k: execv_calls.append(a))

    ask.check_and_activate_venv()

    assert execv_calls == []
    assert "path traversal detected" in capsys.readouterr().err


def test_noop_when_no_venv_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    execv_calls = []
    monkeypatch.setattr(ask.os, "execv", lambda *a, **k: execv_calls.append(a))

    ask.check_and_activate_venv()

    assert execv_calls == []
