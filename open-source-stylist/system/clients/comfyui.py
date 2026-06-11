"""ComfyUI HTTP client — submit workflow, poll, download, free."""

import time

import requests


class ComfyUIClient:
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.base = f"http://{host}:{port}"
        self._s = requests.Session()

    # --- core operations ---

    def submit(self, workflow: dict) -> str:
        """POST /prompt with workflow dict; return prompt_id."""
        resp = self._s.post(f"{self.base}/prompt", json={"prompt": workflow}, timeout=30)
        resp.raise_for_status()
        return resp.json()["prompt_id"]

    def poll(
        self,
        prompt_id: str,
        poll_interval: float = 1.0,
        timeout: float = 300.0,
    ) -> dict:
        """Block until prompt_id completes in /history; return its outputs dict."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            resp = self._s.get(f"{self.base}/history/{prompt_id}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if prompt_id in data:
                entry = data[prompt_id]
                if entry.get("status", {}).get("completed", False):
                    return entry.get("outputs", {})
            time.sleep(poll_interval)
        raise TimeoutError(
            f"ComfyUI prompt {prompt_id!r} did not complete within {timeout}s"
        )

    def download(
        self, filename: str, subfolder: str = "", type_: str = "output"
    ) -> bytes:
        """GET /view; return raw image bytes."""
        params = {"filename": filename, "subfolder": subfolder, "type": type_}
        resp = self._s.get(f"{self.base}/view", params=params, timeout=60)
        resp.raise_for_status()
        return resp.content

    def free(self) -> None:
        """POST /free — unload models from VRAM."""
        resp = self._s.post(
            f"{self.base}/free",
            json={"unload_models": True, "free_memory": True},
            timeout=30,
        )
        resp.raise_for_status()

    def upload_image(self, image_path) -> str:
        """POST /upload/image — upload local file to ComfyUI input dir.

        Returns the filename as registered in ComfyUI (use in LoadImage node).
        """
        from pathlib import Path

        image_path = Path(image_path)
        with image_path.open("rb") as fh:
            resp = self._s.post(
                f"{self.base}/upload/image",
                files={"image": (image_path.name, fh, "image/png")},
                data={"overwrite": "true"},
                timeout=30,
            )
        resp.raise_for_status()
        return resp.json()["name"]

    # --- diagnostics ---

    def system_stats(self) -> dict:
        """GET /system_stats — ComfyUI version, VRAM, RAM."""
        resp = self._s.get(f"{self.base}/system_stats", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def queue_status(self) -> dict:
        """GET /queue — pending and running counts."""
        resp = self._s.get(f"{self.base}/queue", timeout=10)
        resp.raise_for_status()
        return resp.json()
