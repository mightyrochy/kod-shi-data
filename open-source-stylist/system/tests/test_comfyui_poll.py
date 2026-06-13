"""Tests for ComfyUIClient.poll() error handling.

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
