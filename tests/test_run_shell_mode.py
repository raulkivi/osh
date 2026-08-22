"""Tests for the interactive REPL loop in run_shell_mode.

_shell_prompt is stubbed everywhere so tests don't depend on git state, and
process_query/_ask_query/_shell_mode_help/_shell_mode_history are stubbed so
the REPL's own dispatch logic is what's under test, not the tools it calls.
"""
import pytest

import osh


def make_input(responses):
    """See tests/test_process_query.py for behavior notes."""
    it = iter(responses)

    def fake_input(*args, **kwargs):
        try:
            value = next(it)
        except StopIteration:
            raise AssertionError("input() called more times than the test expected")
        if isinstance(value, BaseException):
            raise value
        return value

    return fake_input


@pytest.fixture(autouse=True)
def stub_shell_prompt(monkeypatch):
    monkeypatch.setattr(osh, "_shell_prompt", lambda: "osh> ")


def test_eof_exits_loop_gracefully(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", make_input([EOFError()]))
    osh.run_shell_mode(object(), {}, "/bin/bash", False)
    assert "Exiting shell mode." in capsys.readouterr().out


def test_keyboard_interrupt_exits_loop_gracefully(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", make_input([KeyboardInterrupt()]))
    osh.run_shell_mode(object(), {}, "/bin/bash", False)
    assert "Exiting shell mode." in capsys.readouterr().out


def test_blank_lines_are_skipped_without_calling_process_query(monkeypatch):
    calls = []
    monkeypatch.setattr(osh, "process_query", lambda *a, **k: calls.append(a))
    monkeypatch.setattr("builtins.input", make_input(["", "   ", "!exit"]))

    osh.run_shell_mode(object(), {}, "/bin/bash", False)

    assert calls == []


def test_bang_exits_loop(monkeypatch):
    monkeypatch.setattr("builtins.input", make_input(["!"]))
    osh.run_shell_mode(object(), {}, "/bin/bash", False)


@pytest.mark.parametrize("phrase", ["!exit", "!EXIT", "!quit", "!QUIT"])
def test_bang_exit_and_quit_variants_exit_loop(monkeypatch, phrase):
    monkeypatch.setattr("builtins.input", make_input([phrase]))
    osh.run_shell_mode(object(), {}, "/bin/bash", False)


def test_natural_language_exit_phrase_exits_loop(monkeypatch):
    monkeypatch.setattr("builtins.input", make_input(["bye"]))
    osh.run_shell_mode(object(), {}, "/bin/bash", False)


def test_help_command_invokes_help_and_continues(monkeypatch):
    help_calls = []
    monkeypatch.setattr(osh, "_shell_mode_help", lambda: help_calls.append(1))
    monkeypatch.setattr("builtins.input", make_input(["!help", "!exit"]))

    osh.run_shell_mode(object(), {}, "/bin/bash", False)

    assert help_calls == [1]


def test_version_command_prints_version(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", make_input(["!version", "!exit"]))

    osh.run_shell_mode(object(), {}, "/bin/bash", False)

    assert f"osh version {osh.__version__}" in capsys.readouterr().out


def test_history_command_invokes_history(monkeypatch):
    history_calls = []
    monkeypatch.setattr(osh, "_shell_mode_history", lambda: history_calls.append(1))
    monkeypatch.setattr("builtins.input", make_input(["!history", "!exit"]))

    osh.run_shell_mode(object(), {}, "/bin/bash", False)

    assert history_calls == [1]


def test_unknown_bang_command_warns_and_continues(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", make_input(["!bogus", "!exit"]))

    osh.run_shell_mode(object(), {}, "/bin/bash", False)

    assert "Unknown command: !bogus" in capsys.readouterr().out


def test_question_prefix_triggers_ask_query(monkeypatch):
    ask_calls = []
    monkeypatch.setattr(osh, "_ask_query", lambda client, config, query: ask_calls.append(query))
    monkeypatch.setattr("builtins.input", make_input(["?what is a symlink", "!exit"]))

    osh.run_shell_mode("client", {}, "/bin/bash", False)

    assert ask_calls == ["what is a symlink"]


def test_bare_question_mark_does_not_call_ask_query(monkeypatch):
    ask_calls = []
    monkeypatch.setattr(osh, "_ask_query", lambda *a, **k: ask_calls.append(a))
    monkeypatch.setattr("builtins.input", make_input(["?", "!exit"]))

    osh.run_shell_mode(object(), {}, "/bin/bash", False)

    assert ask_calls == []


def test_regular_query_delegates_to_process_query(monkeypatch):
    pq_calls = []
    monkeypatch.setattr(
        osh,
        "process_query",
        lambda client, config, shell, prompt, ask_flag: pq_calls.append(
            (client, config, shell, prompt, ask_flag)
        ),
    )
    monkeypatch.setattr("builtins.input", make_input(["list files here", "!exit"]))

    osh.run_shell_mode("client-obj", {"k": "v"}, "/bin/zsh", True)

    assert pq_calls == [("client-obj", {"k": "v"}, "/bin/zsh", "list files here", True)]
