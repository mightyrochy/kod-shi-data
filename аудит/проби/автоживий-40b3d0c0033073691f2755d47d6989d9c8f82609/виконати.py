"""Відтворювані команди та докази одного призначеного живого прогону."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUILD = ROOT
SHA = "a42a1290d0af56e42d4bdb9ff3b08841c57a6180"
MODELS = {"qwen/qwen3.5-9b": 57344, "mamaylm-gemma-3-12b-it-v2.0": 16384}
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
           NODE_PATH=r"C:\Users\Admin\kod-shi-test-node\node_modules")
EVENTS = []


def save():
    (OUT / "команди.json").write_text(json.dumps(EVENTS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(args, name, cwd=ROOT):
    event = {"час_utc": datetime.now(timezone.utc).isoformat(), "команда": list(map(str, args)), "cwd": str(cwd)}
    print(name, flush=True)
    with (OUT / (name + ".txt")).open("w", encoding="utf-8") as log:
        result = subprocess.run(list(map(str, args)), cwd=cwd, env=ENV, stdout=log, stderr=subprocess.STDOUT)
    event["rc"] = result.returncode
    EVENTS.append(event)
    save()
    print(name + ": rc=" + str(result.returncode), flush=True)
    return result.returncode


def api(suffix="", data=None):
    request = urllib.request.Request("http://127.0.0.1:1234/api/v1/models" + suffix,
        data=None if data is None else json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.load(response)
        EVENTS.append({"час_utc": datetime.now(timezone.utc).isoformat(), "url": request.full_url,
                       "метод": request.get_method(), "тіло": data, "http": response.status, "відповідь": result})
        save()
        return result


def main():
    assert run(["git", "merge-base", "--is-ancestor", SHA, "origin/main"], "предок-main") == 0
    assert run(["git", "rev-parse", "HEAD", "origin/main"], "sha-гілки") == 0
    assert run(["git", "rev-parse", "HEAD"], "sha-дерева", BUILD) == 0
    assert (BUILD / "build.txt").read_text().strip() == "40b3d0c0033073691f2755d47d6989d9c8f82609"
    assert run(["node", "-e", "console.log(require.resolve('playwright')); console.log(require('playwright').chromium.executablePath())"], "playwright") == 0
    assert run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader"], "gpu-до") == 0
    before = api()
    assert not any(m["loaded_instances"] for m in before["models"]), "Моделі зайняті іншою сесією"
    available = {m["key"]: m for m in before["models"]}
    for model, context in MODELS.items():
        assert available[model]["max_context_length"] >= context
        own = None
        try:
            loaded = api("/load", {"model": model, "context_length": context, "parallel": 1, "echo_load_config": True})
            own = loaded.get("instance_id")
            assert loaded["status"] == "loaded" and own
            state = api()
            instance = next(i for m in state["models"] if m["key"] == model for i in m["loaded_instances"] if i["id"] == own)
            assert instance["config"]["context_length"] == context and instance["config"]["parallel"] == 1
        finally:
            if own:
                api("/unload", {"instance_id": own})
    return scene()


def scene():
    rc = run([sys.executable, BUILD / "аудит/проби/записати_сцену.py", BUILD,
              r"C:\Users\Admin\stend-nout\pyodide", OUT / "б1_концерт_стримано", "--сцена", "б1_концерт_стримано"], "запис-сцени")
    api()
    run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader"], "gpu-після")
    return rc


if __name__ == "__main__":
    if "--продовжити" in sys.argv:
        EVENTS.extend(json.loads((OUT / "команди.json").read_text(encoding="utf-8")))
        (OUT / "запис-сцени.txt").rename(OUT / "запис-сцени_1.txt")
        raise SystemExit(scene())
    raise SystemExit(main())
