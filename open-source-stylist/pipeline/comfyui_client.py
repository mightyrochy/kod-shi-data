"""HTTP client for a local ComfyUI server.

Covers the API surface the pipeline needs:
submit a workflow, wait for completion, download outputs,
upload input images, free VRAM, read system stats.
"""

import time
import uuid
from pathlib import Path

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8000"


class ComfyUIError(RuntimeError):
    pass


class ComfyUIClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client_id = uuid.uuid4().hex

    # -- server state ------------------------------------------------------

    def system_stats(self) -> dict:
        r = requests.get(f"{self.base_url}/system_stats", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def vram_free_gb(self) -> float:
        stats = self.system_stats()
        return stats["devices"][0]["vram_free"] / 1024**3

    def free(self, unload_models: bool = True, free_memory: bool = True) -> None:
        """Ask ComfyUI to unload models and/or free cached memory."""
        r = requests.post(
            f"{self.base_url}/free",
            json={"unload_models": unload_models, "free_memory": free_memory},
            timeout=self.timeout,
        )
        if r.status_code != 200:
            raise ComfyUIError(f"/free failed: {r.status_code} {r.text[:500]}")

    def interrupt(self) -> None:
        requests.post(f"{self.base_url}/interrupt", timeout=self.timeout)

    # -- workflow execution ------------------------------------------------

    def submit(self, workflow: dict) -> str:
        """Submit a workflow (API format) for execution. Returns prompt_id."""
        r = requests.post(
            f"{self.base_url}/prompt",
            json={"prompt": workflow, "client_id": self.client_id},
            timeout=self.timeout,
        )
        if r.status_code != 200:
            raise ComfyUIError(f"submit failed: {r.status_code} {r.text[:2000]}")
        data = r.json()
        if data.get("node_errors"):
            raise ComfyUIError(f"node errors: {data['node_errors']}")
        return data["prompt_id"]

    def wait(self, prompt_id: str, timeout: float = 1800.0, poll_interval: float = 2.0) -> dict:
        """Poll /history until the prompt completes. Returns the history entry."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            r = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=self.timeout)
            r.raise_for_status()
            history = r.json()
            if prompt_id in history:
                entry = history[prompt_id]
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    messages = status.get("messages", [])
                    raise ComfyUIError(f"workflow failed: {str(messages)[:2000]}")
                if status.get("completed") or entry.get("outputs"):
                    return entry
            time.sleep(poll_interval)
        raise ComfyUIError(f"timed out after {timeout}s waiting for prompt {prompt_id}")

    def run(self, workflow: dict, timeout: float = 1800.0) -> dict:
        """submit + wait in one call."""
        return self.wait(self.submit(workflow), timeout=timeout)

    # -- images ------------------------------------------------------------

    def output_images(self, history_entry: dict) -> list[dict]:
        """Image refs ({filename, subfolder, type}) from a history entry, save-nodes only."""
        images = []
        for node_output in history_entry.get("outputs", {}).values():
            for img in node_output.get("images", []):
                if img.get("type") == "output":
                    images.append(img)
        return images

    def download_image(self, image_ref: dict, dest_path: Path) -> Path:
        r = requests.get(
            f"{self.base_url}/view",
            params={
                "filename": image_ref["filename"],
                "subfolder": image_ref.get("subfolder", ""),
                "type": image_ref.get("type", "output"),
            },
            timeout=self.timeout,
        )
        r.raise_for_status()
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(r.content)
        return dest_path

    def upload_image(self, path: Path, overwrite: bool = True) -> str:
        """Upload an image into ComfyUI's input folder. Returns the server-side name
        to use in LoadImage nodes."""
        path = Path(path)
        with open(path, "rb") as f:
            r = requests.post(
                f"{self.base_url}/upload/image",
                files={"image": (path.name, f)},
                data={"overwrite": "true" if overwrite else "false"},
                timeout=self.timeout,
            )
        if r.status_code != 200:
            raise ComfyUIError(f"upload failed: {r.status_code} {r.text[:500]}")
        data = r.json()
        name = data["name"]
        subfolder = data.get("subfolder", "")
        return f"{subfolder}/{name}" if subfolder else name
