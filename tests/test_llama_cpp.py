"""Tests for llama.cpp `llama-server` backend support."""
import json
import urllib.error

import pytest

import nlsh


class FakeHTTPResponse:
    def __init__(self, body: dict):
        self._body = json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class TestLlamaCppModelChat:
    def test_sends_openai_compatible_request_and_parses_content(self, monkeypatch):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["headers"] = request.headers
            return FakeHTTPResponse({"choices": [{"message": {"content": "ls -la"}}]})

        monkeypatch.setattr(nlsh.urllib.request, "urlopen", fake_urlopen)

        client = nlsh.LlamaCppModel(host="http://localhost:38080")
        result = client.chat(
            model="qwen2.5-coder",
            messages=[{"role": "user", "content": "list files"}],
            temperature=0.3,
            max_tokens=2400,
        )

        assert result == "ls -la"
        assert captured["url"] == "http://localhost:38080/v1/chat/completions"
        assert captured["method"] == "POST"
        assert captured["body"]["model"] == "qwen2.5-coder"
        assert captured["body"]["messages"] == [{"role": "user", "content": "list files"}]
        assert captured["body"]["temperature"] == 0.3
        assert captured["body"]["max_tokens"] == 2400
        assert captured["body"]["stream"] is False
        assert captured["headers"]["Content-type"] == "application/json"

    def test_strips_trailing_slash_from_host(self, monkeypatch):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["url"] = request.full_url
            return FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}]})

        monkeypatch.setattr(nlsh.urllib.request, "urlopen", fake_urlopen)

        client = nlsh.LlamaCppModel(host="http://localhost:38080/")
        client.chat(model="m", messages=[])

        assert captured["url"] == "http://localhost:38080/v1/chat/completions"

    def test_omits_temperature_and_max_tokens_when_not_given(self, monkeypatch):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}]})

        monkeypatch.setattr(nlsh.urllib.request, "urlopen", fake_urlopen)

        nlsh.LlamaCppModel(host="http://localhost:38080").chat(model="m", messages=[])

        assert "temperature" not in captured["body"]
        assert "max_tokens" not in captured["body"]

    def test_raises_friendly_error_when_server_unreachable(self, monkeypatch):
        def fake_urlopen(request, timeout=None):
            raise urllib.error.URLError("Connection refused")

        monkeypatch.setattr(nlsh.urllib.request, "urlopen", fake_urlopen)

        client = nlsh.LlamaCppModel(host="http://localhost:38080")
        with pytest.raises(RuntimeError, match="Cannot reach llama.cpp server"):
            client.chat(model="m", messages=[])

    def test_raises_runtime_error_on_http_error(self, monkeypatch):
        def fake_urlopen(request, timeout=None):
            raise urllib.error.HTTPError(
                request.full_url, 500, "Internal Server Error", None, __import__("io").BytesIO(b"boom")
            )

        monkeypatch.setattr(nlsh.urllib.request, "urlopen", fake_urlopen)

        client = nlsh.LlamaCppModel(host="http://localhost:38080")
        with pytest.raises(RuntimeError, match="HTTP 500"):
            client.chat(model="m", messages=[])

    def test_raises_runtime_error_on_unexpected_response_shape(self, monkeypatch):
        def fake_urlopen(request, timeout=None):
            return FakeHTTPResponse({"unexpected": "shape"})

        monkeypatch.setattr(nlsh.urllib.request, "urlopen", fake_urlopen)

        client = nlsh.LlamaCppModel(host="http://localhost:38080")
        with pytest.raises(RuntimeError, match="Unexpected response"):
            client.chat(model="m", messages=[])


class TestGetModelClient:
    def test_defaults_to_ollama(self):
        config = nlsh.DEFAULT_CONFIG.copy()
        client = nlsh.get_model_client(config)
        assert isinstance(client, nlsh.OllamaModel)

    def test_dispatches_to_llama_cpp_when_configured(self):
        config = nlsh.DEFAULT_CONFIG.copy()
        config["api"] = "llama_cpp"
        config["llama_cpp_endpoint"] = "http://localhost:38080"

        client = nlsh.get_model_client(config)

        assert isinstance(client, nlsh.LlamaCppModel)
        assert client.host == "http://localhost:38080"

    def test_llama_cpp_ignores_cloud_suffix_on_model(self):
        # api=llama_cpp is a purely local backend; a ":cloud" model suffix
        # (an Ollama-only convention) must not route to Ollama's cloud path.
        config = nlsh.DEFAULT_CONFIG.copy()
        config["api"] = "llama_cpp"
        config["model"] = "some-model:cloud"

        client = nlsh.get_model_client(config)

        assert isinstance(client, nlsh.LlamaCppModel)
