# -*- coding: utf-8 -*-
"""Виконує одну сцену доказу середовища й прибирає власні процеси та моделі."""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.request

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
СТИЛІСТКА = "qwen/qwen3.5-9b"
МОВА = "mamaylm-gemma-3-12b-it-v2.0"
СЦЕНА = "б1_концерт_стримано"


def api(шлях="", тіло=None):
    """Звертається до локального REST API з обов'язковою перевіркою помилок."""
    дані = None if тіло is None else json.dumps(тіло).encode()
    запит = urllib.request.Request("http://127.0.0.1:1234/api/v1/models" + шлях,
                                  data=дані, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(запит, timeout=300) as відповідь:
        вміст = json.load(відповідь)
    if "error" in вміст:
        raise RuntimeError(вміст)
    return вміст


def головна():
    """Тримає проксі та стенд дочірніми процесами до завершення одного прогону."""
    налаштування = Path(__file__).resolve().parent
    тека = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else налаштування
    тека.mkdir(parents=True, exist_ok=True)
    ТЕКА = тека
    середовище = json.loads((налаштування / "середовище.json").read_text(encoding="utf-8-sig"))
    env = dict(os.environ, NODE_PATH=середовище["NODE_PATH"], LMS_MODE="http", PORT="1235",
               MODEL=СТИЛІСТКА, MODEL_MOVA=МОВА, MODEL_URL="http://127.0.0.1:1235/v1",
               CTX=json.dumps({СТИЛІСТКА: 57344, МОВА: 16384}), OTSINKA="0", ODNOCHASNO="1",
               ZHINKA=str(КОРІНЬ / "аудит/проби/жінки/ж8.json"),
               CHAT_TEXT="рок-концерт у клубі, п'ятниця ввечері, стоятиму в натовпі, хочу стримано й класично",
               ZNIMKY=str(ТЕКА / "знімки"), VIDPOVIDI=str(ТЕКА / "відповіді"),
               ZVIT_OUT=str(ТЕКА / "вердикти.txt"), PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               NODE_USE_SYSTEM_CA="1")
    for ключ in ("FOTO", "DO", "SCENA", "CHROMIUM", "PASPORT", "ZHYVA", "NODE_OPTIONS", "NODE_TLS_REJECT_UNAUTHORIZED"):
        env.pop(ключ, None)
    env["PATH"] = str(Path(середовище["node_path"]).parent) + os.pathsep + env["PATH"]
    до = api()
    if any(m["loaded_instances"] for m in до["models"]):
        raise RuntimeError("LM Studio вже тримає чужу модель")
    межа = time.monotonic() + 1800
    while True:
        gpu = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
                             capture_output=True, text=True, check=True)
        (ТЕКА / "gpu-до.txt").write_text(gpu.stdout or "Нема обчислювальних процесів\n", encoding="utf-8")
        if not gpu.stdout.strip():
            break
        if time.monotonic() >= межа:
            raise RuntimeError("GPU зайнята понад 30 хвилин")
        print("GPU зайнята, чекаю", flush=True)
        time.sleep(15)
    with socket.socket() as перевірка:
        перевірка.bind(("127.0.0.1", 1235))
    стендТека = Path(середовище["stand_root"])
    html = (стендТека / "index.html").read_text(encoding="utf-8")
    sha = re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"', html)[1]
    (ТЕКА / "збірка-код.txt").write_text(sha + "\n", encoding="utf-8")
    голова = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=КОРІНЬ, text=True).strip()
    (ТЕКА / "код.txt").write_text(f"{sha} {СЦЕНА} ПІСЛЯ {СТИЛІСТКА}+{МОВА}\n", encoding="utf-8")
    команда = [середовище["node_path"], str(КОРІНЬ / "аудит/проби/рв6_стенд.js"),
               "http://127.0.0.1:8765", str(стендТека),
               str(Path(env["USERPROFILE"]) / "pyodide"), "3"]
    (ТЕКА / "запуск.json").write_text(json.dumps({"sha-збірки": sha, "sha-приладів": голова, "сцена": СЦЕНА, "команда": команда,
        "змінні": {k: env[k] for k in ("NODE_PATH", "LMS_MODE", "CTX", "MODEL", "MODEL_MOVA", "MODEL_URL",
                                      "OTSINKA", "ODNOCHASNO", "CHAT_TEXT", "ZHINKA", "NODE_USE_SYSTEM_CA")}}, ensure_ascii=False, indent=2), encoding="utf-8")
    стенд = проксі = None
    rc = None
    try:
        with (ТЕКА / "проксі.txt").open("w", encoding="utf-8") as лог:
            проксі = subprocess.Popen([середовище["node_path"], str(КОРІНЬ / "аудит/ноутбук_стенд_2/проксі_почергове.js")],
                                     cwd=КОРІНЬ, env=env, stdout=лог, stderr=subprocess.STDOUT,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            for _ in range(50):
                if проксі.poll() is not None:
                    raise RuntimeError("Проксі завершився до старту стенда")
                try:
                    with socket.create_connection(("127.0.0.1", 1235), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Проксі не відкрив порт")
            print(f"Проксі PID={проксі.pid}; сцена {СЦЕНА}; початок UTC={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}", flush=True)
            with (ТЕКА / "лог.txt").open("w", encoding="utf-8") as логСтенда:
                стенд = subprocess.Popen(команда, cwd=КОРІНЬ, env=env, stdout=логСтенда, stderr=subprocess.STDOUT,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                rc = стенд.wait(timeout=1800)
            print(f"Стенд завершився: rc={rc}", flush=True)
    finally:
        if стенд and стенд.poll() is None:
            стенд.terminate()
            стенд.wait(timeout=30)
        if проксі and проксі.poll() is None:
            проксі.terminate()
            проксі.wait(timeout=30)
        # Windows terminate не доставляє SIGTERM; право на unload засвідчує журнал власного проксі.
        лог = (ТЕКА / "проксі.txt").read_text(encoding="utf-8") if (ТЕКА / "проксі.txt").exists() else ""
        власні = set(re.findall(r"HTTP власний екземпляр (.+)", лог))
        вивантажено = []
        for m in api()["models"]:
            for i in m["loaded_instances"]:
                if i["id"] in власні:
                    вивантажено.append(api("/unload", {"instance_id": i["id"]}))
        (ТЕКА / "прибирання.json").write_text(json.dumps({"вивантажено": вивантажено,
            "моделі-після": api()}, ensure_ascii=False, indent=2), encoding="utf-8")
        (ТЕКА / "done.txt").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) +
                                      f" {СЦЕНА} rc={rc}\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(головна())
