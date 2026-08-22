import io
import json

import osh


class TestCheckAndActivateVenvNoConfig:
    def test_noop_when_no_venv_configured(self, tmp_path, monkeypatch):
        execv_calls = []
        monkeypatch.setattr(osh.os, "execv", lambda *a, **k: execv_calls.append(a))
        osh.check_and_activate_venv(str(tmp_path / "missing.json"))
        assert execv_calls == []


class TestCheckAndActivateVenvPathTraversal:
    def test_pyenv_traversal_attempt_is_blocked(self, tmp_path, monkeypatch, capsys):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"python_venv": "pyenv:../../etc/passwd"}))
        execv_calls = []
        monkeypatch.setattr(osh.os, "execv", lambda *a, **k: execv_calls.append(a))

        osh.check_and_activate_venv(str(config_path))

        assert execv_calls == []
        assert "path traversal detected" in capsys.readouterr().err

    def test_pyenv_absolute_path_escape_is_blocked(self, tmp_path, monkeypatch, capsys):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"python_venv": "pyenv:/etc/passwd"}))
        execv_calls = []
        monkeypatch.setattr(osh.os, "execv", lambda *a, **k: execv_calls.append(a))

        osh.check_and_activate_venv(str(config_path))

        assert execv_calls == []
        assert "path traversal detected" in capsys.readouterr().err


class TestCheckAndActivateVenvMissingInterpreter:
    def test_warns_and_continues_when_venv_python_missing(self, tmp_path, monkeypatch, capsys):
        config_path = tmp_path / "config.json"
        missing_venv = tmp_path / "nonexistent-venv"
        config_path.write_text(json.dumps({"python_venv": f"venv:{missing_venv}"}))
        execv_calls = []
        monkeypatch.setattr(osh.os, "execv", lambda *a, **k: execv_calls.append(a))

        osh.check_and_activate_venv(str(config_path))

        assert execv_calls == []
        assert "not found" in capsys.readouterr().err


class TestCheckAndActivateVenvAlreadyActive:
    def test_noop_when_display_name_already_in_sys_prefix(self, tmp_path, monkeypatch):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"python_venv": "pyenv:myenv"}))
        monkeypatch.setattr(osh.sys, "prefix", "/home/user/.pyenv/versions/myenv")
        execv_calls = []
        monkeypatch.setattr(osh.os, "execv", lambda *a, **k: execv_calls.append(a))

        osh.check_and_activate_venv(str(config_path))

        assert execv_calls == []


class TestCheckAndActivateVenvActivation:
    def test_execs_into_venv_python_when_it_exists(self, tmp_path, monkeypatch):
        venv_dir = tmp_path / "myvenv"
        bin_dir = venv_dir / "bin"
        bin_dir.mkdir(parents=True)
        python_path = bin_dir / "python"
        python_path.write_text("#!/bin/sh\n")

        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"python_venv": f"venv:{venv_dir}"}))

        monkeypatch.setattr(osh.sys, "prefix", "/unrelated/prefix")
        execv_calls = []
        monkeypatch.setattr(osh.os, "execv", lambda path, argv: execv_calls.append((path, argv)))

        osh.check_and_activate_venv(str(config_path))

        assert len(execv_calls) == 1
        called_path, called_argv = execv_calls[0]
        assert called_path == str(python_path)
        assert called_argv[0] == str(python_path)


class TestGetSafeShell:
    def test_returns_configured_shell_when_listed_in_etc_shells(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/bin/zsh")
        monkeypatch.setattr(
            osh, "open", lambda *a, **k: io.StringIO("/bin/bash\n/bin/zsh\n"), raising=False
        )
        assert osh.get_safe_shell() == "/bin/zsh"

    def test_falls_back_to_bin_sh_when_shell_not_listed(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/opt/weird/shell")
        monkeypatch.setattr(
            osh, "open", lambda *a, **k: io.StringIO("/bin/bash\n/bin/zsh\n"), raising=False
        )
        assert osh.get_safe_shell() == "/bin/sh"

    def test_falls_back_to_hardcoded_allowlist_when_etc_shells_missing(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/bin/fish")

        def raise_not_found(*a, **k):
            raise FileNotFoundError()

        monkeypatch.setattr(osh, "open", raise_not_found, raising=False)
        assert osh.get_safe_shell() == "/bin/fish"

    def test_falls_back_to_bin_sh_when_etc_shells_missing_and_shell_unrecognized(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/opt/custom/shell")

        def raise_not_found(*a, **k):
            raise FileNotFoundError()

        monkeypatch.setattr(osh, "open", raise_not_found, raising=False)
        assert osh.get_safe_shell() == "/bin/sh"


class TestMissingPosixDisplay:
    def test_true_when_display_unset(self, monkeypatch):
        monkeypatch.delenv("DISPLAY", raising=False)
        assert osh.missing_posix_display() is True

    def test_true_when_display_empty(self, monkeypatch):
        monkeypatch.setenv("DISPLAY", "")
        assert osh.missing_posix_display() is True

    def test_false_when_display_set(self, monkeypatch):
        monkeypatch.setenv("DISPLAY", ":0")
        assert osh.missing_posix_display() is False
