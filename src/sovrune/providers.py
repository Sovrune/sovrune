"""LLM provider seam with hosted and local adapters."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str


class ModelProvider:
    name = "provider"

    def complete(self, system: str, prompt: str) -> ModelResponse:  # pragma: no cover
        raise NotImplementedError

    def configured(self) -> bool:
        return True

    @staticmethod
    def _post(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode())
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ProviderError(f"provider request failed: {type(error).__name__}") from error


class OpenAICompatibleProvider(ModelProvider):
    name = "openai-compatible"

    def __init__(self, model: str, api_key: str | None = None, base_url: str = "https://api.openai.com/v1"):
        self.model, self.api_key, self.base_url = model, api_key, base_url.rstrip("/")

    def configured(self) -> bool:
        return bool(self.api_key) or self.base_url.startswith(("http://localhost", "http://127.0.0.1"))

    def complete(self, system: str, prompt: str) -> ModelResponse:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = self._post(f"{self.base_url}/chat/completions", headers, {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        })
        return ModelResponse(data["choices"][0]["message"]["content"], self.name, self.model)


class AnthropicProvider(ModelProvider):
    name = "anthropic"

    def __init__(self, model: str, api_key: str | None):
        self.model, self.api_key = model, api_key

    def configured(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, prompt: str) -> ModelResponse:
        data = self._post("https://api.anthropic.com/v1/messages", {
            "Content-Type": "application/json", "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
        }, {"model": self.model, "max_tokens": 2048, "system": system,
            "messages": [{"role": "user", "content": prompt}]})
        return ModelResponse("".join(x.get("text", "") for x in data.get("content", [])), self.name, self.model)


class GeminiProvider(ModelProvider):
    name = "gemini"

    def __init__(self, model: str, api_key: str | None):
        self.model, self.api_key = model, api_key

    def configured(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, prompt: str) -> ModelResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        data = self._post(url, {"Content-Type": "application/json"}, {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": prompt}]}],
        })
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return ModelResponse(text, self.name, self.model)


class OllamaProvider(ModelProvider):
    name = "ollama"

    def __init__(self, model: str, base_url: str = "http://127.0.0.1:11434"):
        self.model, self.base_url = model, base_url.rstrip("/")

    def complete(self, system: str, prompt: str) -> ModelResponse:
        data = self._post(f"{self.base_url}/api/chat", {"Content-Type": "application/json"}, {
            "model": self.model, "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        })
        return ModelResponse(data["message"]["content"], self.name, self.model)


def configured_provider() -> ModelProvider | None:
    provider = os.getenv("SOVRUNE_PROVIDER", "none").lower()
    model = os.getenv("SOVRUNE_MODEL", "")
    if provider in {"openai", "openai-compatible"}:
        return OpenAICompatibleProvider(model or "gpt-5", os.getenv("OPENAI_API_KEY"),
                                        os.getenv("SOVRUNE_OPENAI_BASE_URL", "https://api.openai.com/v1"))
    if provider == "anthropic":
        return AnthropicProvider(model or "claude-sonnet-4-5", os.getenv("ANTHROPIC_API_KEY"))
    if provider == "gemini":
        return GeminiProvider(model or "gemini-2.5-pro", os.getenv("GEMINI_API_KEY"))
    if provider == "ollama":
        return OllamaProvider(model or "qwen3", os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    return None
