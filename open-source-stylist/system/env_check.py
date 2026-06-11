#!/usr/bin/env python3
"""
Environment verification for the AI Stylist pipeline.

Checks: ComfyUI reachability + version + VRAM, LM Studio reachability + loaded models,
LM Studio chat round-trip.

Run from the project root:
    python system/env_check.py

Does NOT write to knowledge/verified.md — owner appends facts after reviewing output.
Exit 0 = all checks passed. Exit 1 = one or more failed.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from system.clients.comfyui import ComfyUIClient
from system.clients.lmstudio import LMStudioClient

COMFYUI_HOST = "localhost"
COMFYUI_PORT = 8000
LMSTUDIO_HOST = "localhost"
LMSTUDIO_PORT = 1234


def check_comfyui() -> dict:
    facts: dict = {}
    client = ComfyUIClient(COMFYUI_HOST, COMFYUI_PORT)
    try:
        t0 = time.monotonic()
        stats = client.system_stats()
        elapsed_ms = round((time.monotonic() - t0) * 1000)

        facts["comfyui_reachable"] = True
        facts["comfyui_url"] = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"
        facts["comfyui_response_ms"] = elapsed_ms

        system = stats.get("system", {})
        facts["comfyui_version"] = system.get(
            "comfyui_version", stats.get("version", "unknown")
        )
        facts["python_version"] = system.get("python_version", "unknown")

        devices = stats.get("devices", [])
        if devices:
            gpu = devices[0]
            vram_total = gpu.get("vram_total", 0)
            vram_free = gpu.get("vram_free", 0)
            facts["gpu_name"] = gpu.get("name", "unknown")
            facts["vram_total_mb"] = (
                round(vram_total / 1024 / 1024) if vram_total else "unknown"
            )
            facts["vram_free_mb"] = (
                round(vram_free / 1024 / 1024) if vram_free else "unknown"
            )
        else:
            facts["gpu_name"] = "none reported"

        ram_total = system.get("ram_total", 0)
        facts["ram_total_mb"] = (
            round(ram_total / 1024 / 1024) if ram_total else "unknown"
        )

    except Exception as e:
        facts["comfyui_reachable"] = False
        facts["comfyui_error"] = str(e)

    return facts


def check_lmstudio() -> dict:
    facts: dict = {}
    client = LMStudioClient(LMSTUDIO_HOST, LMSTUDIO_PORT)
    try:
        t0 = time.monotonic()
        models = client.list_models()
        elapsed_ms = round((time.monotonic() - t0) * 1000)

        facts["lmstudio_reachable"] = True
        facts["lmstudio_url"] = f"http://{LMSTUDIO_HOST}:{LMSTUDIO_PORT}"
        facts["lmstudio_response_ms"] = elapsed_ms
        facts["lmstudio_loaded_models"] = (
            [m.get("id", m.get("path", "?")) for m in models] if models else []
        )

    except Exception as e:
        facts["lmstudio_reachable"] = False
        facts["lmstudio_error"] = str(e)

    return facts


def check_lmstudio_chat(lmstudio_facts: dict) -> dict:
    if not lmstudio_facts.get("lmstudio_reachable"):
        return {
            "lmstudio_chat_ok": False,
            "lmstudio_chat_error": "server not reachable",
        }
    client = LMStudioClient(LMSTUDIO_HOST, LMSTUDIO_PORT)
    try:
        t0 = time.monotonic()
        reply = client.chat(
            [{"role": "user", "content": "Reply with the single word READY and nothing else."}],
            max_tokens=16,
        )
        elapsed_ms = round((time.monotonic() - t0) * 1000)
        return {
            "lmstudio_chat_ok": True,
            "lmstudio_chat_reply": reply.strip(),
            "lmstudio_chat_ms": elapsed_ms,
        }
    except Exception as e:
        return {"lmstudio_chat_ok": False, "lmstudio_chat_error": str(e)}


def _passed(facts: dict) -> bool:
    return all(
        facts.get(k)
        for k in ["comfyui_reachable", "lmstudio_reachable", "lmstudio_chat_ok"]
    )


def print_report(facts: dict) -> None:
    print("\n" + "=" * 50)
    print("  env_check — AI Stylist pipeline")
    print("=" * 50)
    width = max(len(k) for k in facts) + 2
    for k, v in facts.items():
        print(f"  {k:<{width}} {v}")
    print("=" * 50)
    ok = _passed(facts)
    status = "GREEN — all checks passed" if ok else "RED   — one or more checks failed"
    print(f"  RESULT: {status}")
    print("=" * 50 + "\n")


def main() -> None:
    all_facts: dict = {}

    print("Checking ComfyUI...")
    all_facts.update(check_comfyui())

    print("Checking LM Studio...")
    lmstudio_facts = check_lmstudio()
    all_facts.update(lmstudio_facts)

    print("LM Studio chat round-trip...")
    all_facts.update(check_lmstudio_chat(lmstudio_facts))

    print_report(all_facts)
    sys.exit(0 if _passed(all_facts) else 1)


if __name__ == "__main__":
    main()
