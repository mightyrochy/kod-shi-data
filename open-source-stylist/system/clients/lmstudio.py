"""LM Studio client — OpenAI-compatible inference + native lifecycle control."""

import base64
import json
from pathlib import Path

import requests


class LMStudioClient:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1234,
        model: str | None = None,
    ):
        self.base = f"http://{host}:{port}"
        self.model = model  # passed in every request; None lets the server use whatever is loaded
        self._s = requests.Session()

    # --- inference ---

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1024,
        ttl: int | None = None,
    ) -> str:
        """POST /v1/chat/completions; return assistant reply text."""
        payload: dict = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self.model:
            payload["model"] = self.model
        if ttl is not None:
            payload["ttl"] = ttl
        resp = self._s.post(
            f"{self.base}/v1/chat/completions", json=payload, timeout=120
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def vision(
        self,
        image_path: str | Path,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> str:
        """Send an image + text prompt; return assistant reply text."""
        path = Path(image_path)
        image_b64 = base64.b64encode(path.read_bytes()).decode()
        ext = path.suffix.lstrip(".").lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{image_b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens)

    def structured_json(
        self,
        messages: list[dict],
        schema: dict,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> dict:
        """POST /v1/chat/completions with json_schema response_format; return parsed dict."""
        payload: dict = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "output", "schema": schema, "strict": True},
            },
        }
        if self.model:
            payload["model"] = self.model
        resp = self._s.post(
            f"{self.base}/v1/chat/completions", json=payload, timeout=120
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        return json.loads(raw)

    # --- model lifecycle (native REST v1) ---

    def list_models(self) -> list[dict]:
        """GET /api/v1/models — return list of loaded model dicts."""
        resp = self._s.get(f"{self.base}/api/v1/models", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # native endpoint returns {"data": [...]}
        return data.get("data", data) if isinstance(data, dict) else data

    def unload(self, model_id: str) -> None:
        """POST /api/v1/models/unload — explicitly unload a model from VRAM."""
        resp = self._s.post(
            f"{self.base}/api/v1/models/unload",
            json={"identifier": model_id},
            timeout=30,
        )
        resp.raise_for_status()
