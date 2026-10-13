"""ComfyUI HTTP client - submit workflow, poll, download, and free."""

import hashlib
import mimetypes
import time
from pathlib import Path

import requests


def _content_digest(path: Path, length: int = 12) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:length]


def _extract_error(status: dict) -> str:
    """Pull a human-readable error message out of a ComfyUI history status block."""
    for entry in status.get("messages", []):
        # messages are [event_type, data] pairs; execution_error carries details
        if isinstance(entry, (list, tuple)) and len(entry) == 2 and entry[0] == "execution_error":
            data = entry[1] or {}
            node = data.get("node_type", "?")
            msg = data.get("exception_message", "")
            return f"{node}: {msg}"
    return status.get("status_str", "unknown error")


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
        """Block until prompt_id completes in /history; return its outputs dict.

        Raises RuntimeError immediately if ComfyUI reports an execution error,
        rather than hanging until the timeout (a failed prompt never sets
        status.completed=True).
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            resp = self._s.get(f"{self.base}/history/{prompt_id}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if prompt_id in data:
                entry = data[prompt_id]
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    raise RuntimeError(
                        f"ComfyUI prompt {prompt_id!r} failed: "
                        f"{_extract_error(status)}"
                    )
                if status.get("completed", False):
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
        """Upload an image under a content-qualified filename.

        Two different local files with the same basename must not overwrite each
        other in ComfyUI's shared input directory. Re-uploading identical bytes
        intentionally produces the same filename.
        """
        image_path = Path(image_path)
        if not image_path.is_file():
            raise FileNotFoundError(f"Cannot upload missing image: {image_path}")

        digest = _content_digest(image_path)
        upload_name = f"{image_path.stem}__{digest}{image_path.suffix.lower()}"
        mime_type = mimetypes.guess_type(upload_name)[0] or "application/octet-stream"
        with image_path.open("rb") as fh:
            resp = self._s.post(
                f"{self.base}/upload/image",
                files={"image": (upload_name, fh, mime_type)},
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
