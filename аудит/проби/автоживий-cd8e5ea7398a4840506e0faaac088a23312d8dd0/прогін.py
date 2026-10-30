"""Відтворюваний запуск призначеного SHA; сервіси живуть лише до кінця команди.

За зразком спроби на 48ab630b (`спроба-48ab630b/прогін.py`) і автоживого bd628bb, під профілем Admin:
NODE_OPTIONS і PYTHONPATH обгортки лишаються (Chromium `--disable-gpu`)."""
import datetime
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.request

TEKA = Path(r"C:\Users\Admin\claude-run\w\20261030-013439-99f5b0842982\tmp")
ROOT = TEKA / "код-217cbecc"
STAND = TEKA / "стенд-217cbecc"
OUT = Path(__file__).resolve().parent
NODE = r"C:\Program Files\nodejs\node.exe"
NODE_PATH = r"C:\Users\Admin\kod-shi-test-node\node_modules"
PYODIDE = r"C:\Users\Admin\stend-nout\pyodide"
PYC = r"C:\Users\Admin\py3121\python.exe"
SHA = "217cbecc782b1a8d3287a585545217bb16311251"
STAMP = "cd8e5ea7398a4840506e0faaac088a23312d8dd0"  # build.txt і ЗБІРКА_ПОКАЗУ збірки CI в SHA
MODELS = {"qwen/qwen3.5-9b": 57344, "mamaylm-gemma-3-12b-it-v2.0": 16384}
SCENES = {
    "б1_концерт_стримано": ("ж8", "рок-концерт у клубі, п'ятниця ввечері, стоятиму в натовпі, хочу стримано й класично"),
    "ж1_вокал_просто_зручно": ("ж1", "увечері урок вокалу, надворі +18, хочеться дуже просто і зручне взуття"),
}


def save(folder, name, data):
    (folder / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def api(path="", data=None):
    request = urllib.request.Request("http://127.0.0.1:1234/api/v1/models" + path,
        data=None if data is None else json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)


def environment():
    env = dict(os.environ, NODE_PATH=NODE_PATH,
        LMS_MODE="http", PORT="1235", MODEL="qwen/qwen3.5-9b",
        MODEL_MOVA="mamaylm-gemma-3-12b-it-v2.0", MODEL_URL="http://127.0.0.1:1235/v1",
        CTX=json.dumps(MODELS), OTSINKA="0", ODNOCHASNO="1", PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8", NODE_USE_SYSTEM_CA="1", LYUSTERKO_CATALOG="повний",
        LYUSTERKO_PYC_PYTHON=PYC)
    env["PATH"] = str(Path(NODE).parent) + os.pathsep + env["PATH"]
    for key in ["FOTO", "DO", "SCENA", "CHROMIUM", "PASPORT", "ZHYVA", "NODE_TLS_REJECT_UNAUTHORIZED"]:
        env.pop(key, None)
    return env


def run(command, **kw):
    p = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    return {"команда": command, "rc": p.returncode, "вивід": (p.stdout + p.stderr).strip()[-2000:]}


def check_environment(env):
    models = api()
    data = {
        "час_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "HEAD_дерева": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "предок_origin_main": run(["git", "merge-base", "--is-ancestor", SHA, "origin/main"], cwd=ROOT),
        "node": run([NODE, "--version"]),
        "NODE_OPTIONS": env.get("NODE_OPTIONS"), "PYTHONPATH": env.get("PYTHONPATH"),
        "playwright": json.loads(Path(NODE_PATH, "playwright", "package.json").read_text(encoding="utf-8"))["version"],
        "chromium": sorted(p.name for p in Path(os.environ["LOCALAPPDATA"], "ms-playwright").iterdir()),
        "pyodide": json.loads(Path(PYODIDE, "pyodide-lock.json").read_text(encoding="utf-8"))["info"]["version"],
        "pyc_python": run([PYC, "--version"]),
        "моделі": {m["key"]: {"max_context_length": m["max_context_length"], "завантажено": len(m["loaded_instances"])}
                   for m in models["models"] if m["key"] in MODELS},
        "чужі_завантажені": [m["key"] for m in models["models"] if m["loaded_instances"]],
        "gpu": run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"]),
        "gpu_процеси": run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"]),
    }
    for port in (1235, 8765):
        with socket.socket() as sock:
            data[f"порт_{port}_вільний"] = sock.connect_ex(("127.0.0.1", port)) != 0
    save(OUT, "середовище.json", data)
    ok = (data["HEAD_дерева"] == SHA and data["предок_origin_main"]["rc"] == 0 and len(data["моделі"]) == 2
          and all(v["max_context_length"] >= MODELS[k] for k, v in data["моделі"].items()))
    print(json.dumps({k: data[k] for k in ["node", "playwright", "pyodide", "моделі", "чужі_завантажені"]}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == SHA
    env = environment()
    if sys.argv[1] == "середовище":
        return check_environment(env)
    if sys.argv[1] == "збірка":
        # Локальна збірка потребує рівно CPython 3.12.1 (build_байткод.py:19); на ноутбуці лише 3.12.10,
        # тож стенд бере показ-повний, який CI зібрав у призначеному коміті (build.txt = STAMP).
        import hashlib, shutil
        STAND.mkdir(exist_ok=True)
        shutil.copyfile(ROOT / "index.html", STAND / "index.html")
        html = (STAND / "index.html").read_bytes()
        stamp = re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"', html.decode("utf-8"))
        data = {"джерело": str(ROOT / "index.html"), "sha_коміту": SHA,
            "build.txt": (ROOT / "build.txt").read_text(encoding="utf-8").strip(),
            "ЗБІРКА_ПОКАЗУ": stamp[1] if stamp else None,
            "sha256": hashlib.sha256(html).hexdigest(), "байтів": len(html),
            "автор_index": subprocess.check_output(["git", "log", "-1", "--format=%H %an %s", "--", "index.html"], cwd=ROOT, text=True).strip()}
        save(OUT, "збірка.json", data)
        ok = data["build.txt"] == STAMP == data["ЗБІРКА_ПОКАЗУ"]
        print(json.dumps(data, ensure_ascii=False), flush=True)
        return 0 if ok else 1
    scene = sys.argv[1]
    woman, text = SCENES[scene]
    folder = OUT / scene
    folder.mkdir(exist_ok=True)
    if (folder / "done.txt").exists():
        raise RuntimeError("Сцену вже виконано; автоматичного повтору немає")
    before = api()
    save(folder, "моделі-до.json", before)
    assert not any(model["loaded_instances"] for model in before["models"]), "Сервер тримає чужу модель"
    gpu = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"], capture_output=True, text=True, check=True)
    (folder / "gpu-до.txt").write_text(gpu.stdout, encoding="utf-8")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 1235))
    html = (STAND / "index.html").read_text(encoding="utf-8")
    assert re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"', html)[1] == STAMP
    env.update(ZHINKA=str(ROOT / f"аудит/проби/жінки/{woman}.json"), CHAT_TEXT=text,
        ZNIMKY=str(folder / "знімки"), VIDPOVIDI=str(folder / "відповіді"), ZVIT_OUT=str(folder / "вердикти.txt"))
    command = [NODE, str(ROOT / "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:8765", str(STAND), PYODIDE, "3"]
    proxy_command = [NODE, str(ROOT / "аудит/ноутбук_стенд_2/проксі_почергове.js")]
    save(folder, "запуск.json", {"sha-збірки": STAMP, "коміт-збірки": SHA, "sha-приладів": SHA, "сцена": scene,
        "команда": command, "команда-проксі": proxy_command, "cwd": str(ROOT),
        "змінні": {key: env.get(key) for key in ["NODE_PATH", "NODE_OPTIONS", "LMS_MODE", "CTX", "MODEL", "MODEL_MOVA", "MODEL_URL", "OTSINKA", "ODNOCHASNO", "CHAT_TEXT", "ZHINKA", "NODE_USE_SYSTEM_CA"]}})
    (folder / "код.txt").write_text(f"{SHA} {scene} ПІСЛЯ qwen/qwen3.5-9b+mamaylm-gemma-3-12b-it-v2.0\n", encoding="utf-8")
    proxy = stand = None
    rc = None
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    begin = time.monotonic()
    try:
        with (folder / "проксі.txt").open("w", encoding="utf-8") as log:
            proxy = subprocess.Popen(proxy_command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            for _ in range(50):
                if proxy.poll() is not None:
                    raise RuntimeError("Проксі завершився до старту стенда")
                try:
                    with socket.create_connection(("127.0.0.1", 1235), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Проксі не відкрив порт")
            with (folder / "лог.txt").open("w", encoding="utf-8") as stand_log:
                stand = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stand_log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
                save(folder, "процеси.json", {"проксі": proxy.pid, "стенд": stand.pid, "початок_utc": started})
                print(f"{scene}: проксі {proxy.pid}, стенд {stand.pid}; {started}", flush=True)
                rc = stand.wait(timeout=1800)
    finally:
        for proc in [stand, proxy]:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=30)
        log = (folder / "проксі.txt").read_text(encoding="utf-8") if (folder / "проксі.txt").exists() else ""
        own = set(re.findall(r"HTTP власний екземпляр (.+)", log))
        unloaded = []
        for model in api()["models"]:
            for instance in model["loaded_instances"]:
                if instance["id"] in own:
                    unloaded.append(api("/unload", {"instance_id": instance["id"]}))
        save(folder, "прибирання.json", {"вивантажено": unloaded, "моделі-після": api(),
            "власні-процеси-завершені": all(proc is None or proc.poll() is not None for proc in [stand, proxy])})
        ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(folder, "результат.json", {"rc": rc, "початок_utc": started, "кінець_utc": ended, "секунди": time.monotonic() - begin})
        (folder / "done.txt").write_text(f"{ended} {scene} rc={rc}\n", encoding="utf-8")
    print(f"{scene}: rc={rc}, {time.monotonic() - begin:.1f} с", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
