"""Відтворюваний запуск призначеного SHA; сервіси живуть лише до кінця команди."""
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

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
STAND = ROOT.parent / "стенд-webp"
NODE = r"C:\Users\gemini\tools\node-v24.22.1-win-x64\node.exe"
SHA = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
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
    env = dict(os.environ, NODE_PATH=r"C:\Users\gemini\kod-shi-test-node\node_modules",
        LMS_MODE="http", PORT="1235", MODEL="qwen/qwen3.5-9b",
        MODEL_MOVA="mamaylm-gemma-3-12b-it-v2.0", MODEL_URL="http://127.0.0.1:1235/v1",
        CTX=json.dumps(MODELS), OTSINKA="0", ODNOCHASNO="1", PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8", NODE_USE_SYSTEM_CA="1", LYUSTERKO_CATALOG="повний",
        LYUSTERKO_PYC_PYTHON=r"C:\Users\gemini\tools\python-3.12.1\python.exe")
    env["PATH"] = str(Path(NODE).parent) + os.pathsep + env["PATH"]
    for key in ["FOTO", "DO", "SCENA", "CHROMIUM", "PASPORT", "ZHYVA", "NODE_OPTIONS", "NODE_TLS_REJECT_UNAUTHORIZED"]:
        env.pop(key, None)
    return env


def main():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == SHA
    env = environment()
    if sys.argv[1] == "збірка":
        STAND.mkdir(exist_ok=True)
        command = [sys.executable, "-X", "utf8", str(ROOT / "джерела/build_артефакт.py"), str(ROOT / "джерела"), str(STAND / "index.html"), "показ-повний"]
        save(OUT, "збірка-команда.json", {"команда": command, "cwd": str(ROOT), "sha": SHA})
        with (OUT / "збірка.txt").open("w", encoding="utf-8") as log:
            rc = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        save(OUT, "збірка-результат.json", {"rc": rc})
        print(f"Збірка rc={rc}", flush=True)
        return rc
    scene = sys.argv[1]
    woman, text = SCENES[scene]
    folder = OUT / scene
    folder.mkdir(exist_ok=True)
    if (folder / "done.txt").exists():
        raise RuntimeError("Сцену вже виконано; автоматичного повтору немає")
    before = api()
    save(folder, "моделі-до.json", before)
    assert not any(model["loaded_instances"] for model in before["models"]), "Сервер тримає чужу модель"
    gpu = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"], capture_output=True, text=True, check=True)
    assert not gpu.stdout.strip(), "GPU зайнята чужим обчислювальним процесом"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 1235))
    html = (STAND / "index.html").read_text(encoding="utf-8")
    build_sha = re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"', html)[1]
    assert not subprocess.check_output(['git', 'diff', '--name-only', build_sha, SHA, '--',
        'джерела', 'аудит/проби/рв6_стенд.js', 'аудит/проби/кадр_моделі.js'], cwd=ROOT), 'Код відрізняється від збірки'
    env.update(ZHINKA=str(ROOT / f"аудит/проби/жінки/{woman}.json"), CHAT_TEXT=text,
        ZNIMKY=str(folder / "знімки"), VIDPOVIDI=str(folder / "відповіді"), ZVIT_OUT=str(folder / "вердикти.txt"))
    command = [NODE, str(ROOT / "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:8765", str(STAND), r"C:\Users\gemini\pyodide", "3"]
    proxy_command = [NODE, str(ROOT / "аудит/ноутбук_стенд_2/проксі_почергове.js")]
    save(folder, "запуск.json", {"sha-збірки": build_sha, "sha-приладів": SHA, "сцена": scene,
        "команда": command, "команда-проксі": proxy_command, "cwd": str(ROOT),
        "змінні": {key: env[key] for key in ["NODE_PATH", "LMS_MODE", "CTX", "MODEL", "MODEL_MOVA", "MODEL_URL", "OTSINKA", "ODNOCHASNO", "CHAT_TEXT", "ZHINKA", "NODE_USE_SYSTEM_CA"]}})
    (folder / "код.txt").write_text(f"{build_sha} {scene} ПІСЛЯ qwen/qwen3.5-9b+mamaylm-gemma-3-12b-it-v2.0\n", encoding="utf-8")
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
