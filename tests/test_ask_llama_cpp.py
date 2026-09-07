"""Tests for ask.py's llama.cpp `llama-server` backend support."""
import json
import urllib.error

import pytest

import ask


class FakeHTTPResponse:
    def __init__(self, body: dict):
        self._body = json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class TestLlamaCppChat:
    def test_sends_openai_compatible_request_and_parses_content(self, monkeypatch):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeHTTPResponse({"choices": [{"message": {"content": "hello"}}]})

        monkeypatch.setattr(ask.urllib.request, "urlopen", fake_urlopen)

        result = ask._llama_cpp_chat(
            host="http://localhost:38080",
            model="qwen2.5-coder",
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.3,
            max_tokens=2400,
        )

        assert result == "hello"
        assert captured["url"] == "http://localhost:38080/v1/chat/completions"
        assert captured["method"] == "POST"
        assert captured["body"]["model"] == "qwen2.5-coder"
        assert captured["body"]["temperature"] == 0.3
        assert captured["body"]["max_tokens"] == 2400
        assert captured["body"]["stream"] is False

    def test_strips_trailing_slash_from_host(self, monkeypatch):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["url"] = request.full_url
            return FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}]})

        monkeypatch.setattr(ask.urllib.request, "urlopen", fake_urlopen)

        ask._llama_cpp_chat(host="http://localhost:38080/", model="m", messages=[])

        assert captured["url"] == "http://localhost:38080/v1/chat/completions"

    def test_raises_friendly_error_when_server_unreachable(self, monkeypatch):
        def fake_urlopen(request, timeout=None):
            raise urllib.error.URLError("Connection refused")

        monkeypatch.setattr(ask.urllib.request, "urlopen", fake_urlopen)

        with pytest.raises(RuntimeError, match="Cannot reach llama.cpp server"):
            ask._llama_cpp_chat(host="http://localhost:38080", model="m", messages=[])

    def test_raises_runtime_error_on_http_error(self, monkeypatch):
        def fake_urlopen(request, timeout=None):
            raise urllib.error.HTTPError(
                request.full_url, 500, "Internal Server Error", None, __import__("io").BytesIO(b"boom")
            )

        monkeypatch.setattr(ask.urllib.request, "urlopen", fake_urlopen)

        with pytest.raises(RuntimeError, match="HTTP 500"):
            ask._llama_cpp_chat(host="http://localhost:38080", model="m", messages=[])

    def test_raises_runtime_error_on_unexpected_response_shape(self, monkeypatch):
        def fake_urlopen(request, timeout=None):
            return FakeHTTPResponse({"unexpected": "shape"})

        monkeypatch.setattr(ask.urllib.request, "urlopen", fake_urlopen)

        with pytest.raises(RuntimeError, match="Unexpected response"):
            ask._llama_cpp_chat(host="http://localhost:38080", model="m", messages=[])


class TestMainDispatchesToLlamaCpp:
    def test_uses_llama_cpp_backend_when_configured(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_dir = tmp_path / "osh"
        config_dir.mkdir()
        (config_dir / "config.json").write_text(json.dumps({
            "api": "llama_cpp",
            "llama_cpp_endpoint": "http://localhost:38080",
        }))

        calls = []

        def fake_llama_cpp_chat(**kwargs):
            calls.append(kwargs)
            return "42"

        monkeypatch.setattr(ask, "_llama_cpp_chat", fake_llama_cpp_chat)
        monkeypatch.setattr("sys.argv", ["ask", "what", "is", "6*7"])
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)

        ask.main()

        assert len(calls) == 1
        assert calls[0]["host"] == "http://localhost:38080"
        assert capsys.readouterr().out.strip() == "42"
