import json

from src.services.ollama_provider import OllamaModelProvider, OllamaProviderError


class FakeOllama(OllamaModelProvider):
    def __init__(self):
        super().__init__(model="test-model", host="http://127.0.0.1:11434")
        self.payloads = []

    def _post(self, path, payload):
        self.payloads.append((path, payload))
        return {"message": {"content": json.dumps({"ok": True, "items": ["scene_01"]})}}


def test_local_provider_uses_structured_json_schema():
    provider = FakeOllama()
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}, "items": {"type": "array", "items": {"type": "string"}}}, "required": ["ok", "items"]}
    result = provider.generate_json("test", {"scene": "scene_01"}, schema)
    assert result["ok"] is True
    assert provider.calls == 1
    assert provider.payloads[0][0] == "/api/chat"
    assert provider.payloads[0][1]["format"] == schema
    assert provider.payloads[0][1]["stream"] is False


def test_local_provider_exposes_helpful_connection_error(monkeypatch):
    import urllib.request
    import urllib.error

    provider = OllamaModelProvider(model="test-model", host="http://127.0.0.1:9", timeout_seconds=1)

    def fail(*args, **kwargs):
        raise urllib.error.URLError("refused")

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    try:
        provider.generate_json("test", {}, {"type": "object", "properties": {}, "required": []})
    except OllamaProviderError as exc:
        assert "Cannot reach Ollama" in str(exc)
    else:
        raise AssertionError("Expected OllamaProviderError")
