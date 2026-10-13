"""Tests for ComfyUIClient polling and uploads.

poll() must raise immediately on a ComfyUI execution error rather than hanging
until the timeout (regression guard for the 2026-06-12 fix).

    python -m pytest system/tests/test_comfyui_poll.py -v
"""

import pytest

from system.clients.comfyui import ComfyUIClient, _extract_error


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeSession:
    """Returns a fixed /history payload for any GET."""
    def __init__(self, payload):
        self._payload = payload

    def get(self, *a, **k):
        return _FakeResp(self._payload)


class _UploadSession:
    def __init__(self):
        self.files = None
        self.data = None

    def post(self, *args, files, data, **kwargs):
        self.files = files
        self.data = data
        return _FakeResp({"name": files["image"][0]})


def test_poll_raises_on_execution_error_without_waiting():
    pid = "abc123"
    history = {
        pid: {
            "status": {
                "status_str": "error",
                "completed": False,
                "messages": [
                    ["execution_error", {
                        "node_type": "KSampler",
                        "exception_message": "CUDA out of memory",
                    }],
                ],
            },
            "outputs": {},
        }
    }
    client = ComfyUIClient()
    client._s = _FakeSession(history)

    with pytest.raises(RuntimeError) as exc:
        client.poll(pid, poll_interval=0.0, timeout=5.0)
    assert "KSampler" in str(exc.value)
    assert "CUDA out of memory" in str(exc.value)


def test_poll_returns_outputs_on_completion():
    pid = "ok123"
    history = {
        pid: {
            "status": {"status_str": "success", "completed": True},
            "outputs": {"9": {"images": [{"filename": "out.png"}]}},
        }
    }
    client = ComfyUIClient()
    client._s = _FakeSession(history)

    outputs = client.poll(pid, poll_interval=0.0, timeout=5.0)
    assert outputs == {"9": {"images": [{"filename": "out.png"}]}}


def test_extract_error_reads_execution_error_message():
    status = {
        "status_str": "error",
        "messages": [
            ["execution_start", {}],
            ["execution_error", {"node_type": "VAEDecode", "exception_message": "bad latent"}],
        ],
    }
    assert _extract_error(status) == "VAEDecode: bad latent"


def test_extract_error_falls_back_to_status_str():
    assert _extract_error({"status_str": "error", "messages": []}) == "error"


def test_upload_uses_content_qualified_name_and_real_mime(tmp_path):
    image = tmp_path / "shared name.jpg"
    image.write_bytes(b"jpeg bytes")
    session = _UploadSession()
    client = ComfyUIClient()
    client._s = session

    uploaded_name = client.upload_image(image)

    assert uploaded_name.startswith("shared name__")
    assert uploaded_name.endswith(".jpg")
    assert session.files["image"][0] == uploaded_name
    assert session.files["image"][2] == "image/jpeg"
    assert session.data == {"overwrite": "true"}


def test_upload_name_changes_when_same_basename_has_different_content(tmp_path):
    left = tmp_path / "left" / "same.png"
    right = tmp_path / "right" / "same.png"
    left.parent.mkdir()
    right.parent.mkdir()
    left.write_bytes(b"left")
    right.write_bytes(b"right")
    client = ComfyUIClient()
    client._s = _UploadSession()

    assert client.upload_image(left) != client.upload_image(right)
