"""HTTP client for LM Studio.

Two API surfaces:
- OpenAI-compatible /v1/chat/completions for text and vision calls,
  with optional JSON-schema-enforced structured output.
- Native /api/v1/models for listing, loading, and unloading models
  (VRAM sequencing requires explicit unload).
"""

import base64
import json
import mimetypes
from pathlib import Path

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:1234"


class LMStudioError(RuntimeError):
    pass


class LMStudioClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 600.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # -- model management ----------------------------------------------------

    def list_models(self) -> list[dict]:
        r = requests.get(f"{self.base_url}/api/v1/models", timeout=30)
        r.raise_for_status()
        return r.json().get("models", [])

    def loaded_models(self) -> list[dict]:
        return [m for m in self.list_models() if m.get("loaded_instances")]

    def load(self, model_key: str, ttl_seconds: int | None = None) -> dict:
        payload: dict = {"model": model_key}
        if ttl_seconds is not None:
            payload["ttl"] = ttl_seconds
        r = requests.post(f"{self.base_url}/api/v1/models/load", json=payload, timeout=self.timeout)
        if r.status_code != 200:
            raise LMStudioError(f"load failed: {r.status_code} {r.text[:500]}")
        return r.json()

    def unload(self, model_key: str) -> None:
        """Unload by model key or instance id (LM Studio accepts either in practice;
        verified against the local install by the smoke test)."""
        for field in ("instance_id", "model"):
            r = requests.post(
                f"{self.base_url}/api/v1/models/unload",
                json={field: model_key},
                timeout=30,
            )
            if r.status_code == 200:
                return
        raise LMStudioError(f"unload failed: {r.status_code} {r.text[:500]}")

    # -- chat ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        model: str,
        json_schema: dict | None = None,
        schema_name: str = "response",
        temperature: float = 0.1,
        max_tokens: int = 4000,
        ttl_seconds: int | None = None,
    ):
        """Send a chat completion. Returns the content string, or a parsed dict
        when json_schema is given (structured output enforced server-side)."""
        payload: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if ttl_seconds is not None:
            payload["ttl"] = ttl_seconds
        if json_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": json_schema},
            }
        r = requests.post(
            f"{self.base_url}/v1/chat/completions", json=payload, timeout=self.timeout
        )
        if r.status_code != 200:
            raise LMStudioError(f"chat failed: {r.status_code} {r.text[:2000]}")
        content = r.json()["choices"][0]["message"]["content"]
        if json_schema is not None:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise LMStudioError(f"model returned invalid JSON: {e}\n{content[:2000]}")
        return content

    def vision_chat(
        self,
        prompt: str,
        image_paths: list[Path],
        model: str,
        system: str | None = None,
        **chat_kwargs,
    ):
        """Chat with images attached (base64 data URLs)."""
        content: list[dict] = [{"type": "text", "text": prompt}]
        for path in image_paths:
            content.append(_image_content(path))
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})
        return self.chat(messages, model=model, **chat_kwargs)


def _image_content(path: Path) -> dict:
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
