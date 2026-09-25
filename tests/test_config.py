import json
import os
from datetime import datetime, timedelta

import nlsh


class TestGetConfigPath:
    def test_respects_xdg_config_home(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        assert nlsh.get_config_path() == os.path.join(str(tmp_path), "nlsh", "config.json")

    def test_falls_back_to_dot_config(self, monkeypatch, tmp_path):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        assert nlsh.get_config_path() == os.path.join(str(tmp_path), ".config", "nlsh", "config.json")


class TestGetStateDir:
    def test_respects_xdg_state_home(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        assert nlsh.get_state_dir() == os.path.join(str(tmp_path), "nlsh")

    def test_falls_back_to_dot_local_state(self, monkeypatch, tmp_path):
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        assert nlsh.get_state_dir() == os.path.join(str(tmp_path), ".local", "state", "nlsh")


class TestGetDailyLogFile:
    def test_uses_todays_date_under_state_dir(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        expected = os.path.join(str(tmp_path), "nlsh", f"{datetime.now():%Y%m%d}.log")
        assert nlsh.get_daily_log_file() == expected


class TestLoadConfig:
    def test_returns_defaults_when_file_missing(self, tmp_path):
        config = nlsh.load_config(str(tmp_path / "missing.json"))
        assert config == nlsh.DEFAULT_CONFIG

    def test_merges_user_values_over_defaults(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"model": "custom-model", "temperature": 0.9}))
        config = nlsh.load_config(str(config_path))
        assert config["model"] == "custom-model"
        assert config["temperature"] == 0.9
        assert config["qa_review"] == nlsh.DEFAULT_CONFIG["qa_review"]

    def test_falls_back_to_defaults_on_malformed_json(self, tmp_path, capsys):
        config_path = tmp_path / "config.json"
        config_path.write_text("{not valid json")
        config = nlsh.load_config(str(config_path))
        assert config == nlsh.DEFAULT_CONFIG
        assert "Error loading config" in capsys.readouterr().err


class TestGetPythonVenvEarly:
    def test_defaults_when_file_missing(self, tmp_path):
        result = nlsh.get_python_venv_early(str(tmp_path / "missing.json"))
        assert result == nlsh.DEFAULT_CONFIG["python_venv"]

    def test_reads_configured_value(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"python_venv": "pyenv:py312"}))
        assert nlsh.get_python_venv_early(str(config_path)) == "pyenv:py312"

    def test_defaults_on_malformed_json(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text("{not valid json")
        result = nlsh.get_python_venv_early(str(config_path))
        assert result == nlsh.DEFAULT_CONFIG["python_venv"]


class TestCleanOldLogs:
    def test_removes_files_older_than_retention(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        state_dir = tmp_path / "nlsh"
        state_dir.mkdir()
        old_file = state_dir / f"{(datetime.now() - timedelta(days=40)):%Y%m%d}.log"
        recent_file = state_dir / f"{(datetime.now() - timedelta(days=1)):%Y%m%d}.log"
        old_file.write_text("old")
        recent_file.write_text("recent")

        nlsh.clean_old_logs(retention_days=30)

        assert not old_file.exists()
        assert recent_file.exists()

    def test_noop_when_retention_not_positive(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        state_dir = tmp_path / "nlsh"
        state_dir.mkdir()
        log_file = state_dir / "20200101.log"
        log_file.write_text("old")

        nlsh.clean_old_logs(retention_days=0)

        assert log_file.exists()

    def test_noop_when_state_dir_missing(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "does-not-exist"))
        nlsh.clean_old_logs(retention_days=30)  # must not raise
