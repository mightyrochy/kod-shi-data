"""Виконує сцену серії 2 через HTTP-проксі й зберігає повний живий обмін."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
import urllib.request

КОРІНЬ = Path(__file__).resolve().parents[2]


def api(шлях="", тіло=None):
    """Читає стан локального сервера або прибирає власний екземпляр моделі."""
    запит = urllib.request.Request("http://127.0.0.1:1234/api/v1/models" + шлях,
        data=None if тіло is None else json.dumps(тіло).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(запит, timeout=300) as відповідь:
        дані = json.load(відповідь)
    if "error" in дані:
        raise RuntimeError(дані)
    return дані


def виконати():
    """Чекає дочірній стенд до кінця та прибирає власні ресурси навіть при помилці."""
    а = argparse.ArgumentParser(description=__doc__)
    а.add_argument("збірка", type=Path)
    а.add_argument("кеш", type=Path)
    а.add_argument("вихід", type=Path)
    а.add_argument("--сцена", default="1", help="Номер архівної сцени або id з живі_сцени.txt")
    а.add_argument("--node", default="node")
    п = а.parse_args()
    if п.сцена.isdecimal():
        перелік = json.loads(subprocess.check_output([п.node, str(КОРІНЬ / "аудит/проби/приймання_записів.js"), "--перелік"],
            env=dict(os.environ, REPLAY_ARCHIVE="1"), cwd=КОРІНЬ, text=True, encoding="utf-8"))
        сцена = перелік[int(п.сцена) - 1]
    else:
        рядки = [р.split("|") for р in (КОРІНЬ / "аудит/проби/живі_сцени.txt").read_text(encoding="utf-8").splitlines()
                 if р.startswith(п.сцена + "|")]
        if len(рядки) != 1:
            raise ValueError("Нема єдиної сцени в реєстрі: " + п.сцена)
        id_, жінка, запит, змінні = рядки[0][:4]
        if змінні:
            raise ValueError("Сцена потребує окремого режиму: " + змінні)
        сцена = {"назва": id_, "сід": 3, "змінні": {"CHAT_TEXT": запит,
            "ZHINKA": str(КОРІНЬ / "аудит/проби/жінки" / (жінка + ".json")),
            "MODEL": "qwen/qwen3.5-9b", "MODEL_MOVA": "mamaylm-gemma-3-12b-it-v2.0", "FOTO": "1", "SCENA": id_}}
        env0 = None
    вихід = п.вихід.resolve()
    вихід.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    for ключ in tuple(env):
        if ключ.startswith("REPLAY_"):
            del env[ключ]
    env.pop('OTSINKA', None)
    env.update(сцена["змінні"])
    env.update(LMS_MODE="http", PORT="1235", CTX=json.dumps({env["MODEL"]: 57344, env["MODEL_MOVA"]: 16384}),
               MODEL_URL="http://127.0.0.1:1235/v1", ODNOCHASNO="1", VIDPOVIDI=str(вихід / "VIDPOVIDI"),
               ZNIMKY=str(вихід / "знімки"), ZVIT_OUT=str(вихід / "вердикти.txt"))
    до = api()
    if any(м["loaded_instances"] for м in до["models"]):
        raise RuntimeError("Сервер тримає чужу модель")
    with socket.socket() as перевірка:
        перевірка.bind(("127.0.0.1", 1235))
    html = (п.збірка / "index.html").read_text(encoding="utf-8")
    sha = re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"', html)[1]
    (вихід / "код.txt").write_text(f'{sha} {сцена["назва"]} ПІСЛЯ {env["MODEL"]}+{env["MODEL_MOVA"]}\n', encoding="utf-8")
    команда = [п.node, str(КОРІНЬ / "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:8765",
               str(п.збірка.resolve()), str(п.кеш.resolve()), str(сцена["сід"])]
    код_проксі = (КОРІНЬ / "аудит/ноутбук_стенд_2/проксі_почергове.js").read_bytes()
    результат = {"початок": datetime.now(timezone.utc).isoformat(), "sha": sha, "сцена": сцена["назва"],
        "проксі_sha256": hashlib.sha256(код_проксі).hexdigest(), "команда": команда, "змінні": {к: env[к] for к in
        (*сцена["змінні"], "LMS_MODE", "PORT", "CTX", "MODEL_URL", "ODNOCHASNO")}}
    проксі = стенд = None
    початок = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="Е1-проксі-") as тека:
        файл = Path(тека) / "проксі.js"
        файл.write_bytes(код_проксі)
        try:
            with (вихід / "проксі.txt").open("w", encoding="utf-8") as лог:
                проксі = subprocess.Popen([п.node, str(файл)], cwd=КОРІНЬ, env=env, stdout=лог, stderr=subprocess.STDOUT,
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
                print("Початок живої сцени " + сцена["назва"], flush=True)
                with (вихід / "лог.txt").open("w", encoding="utf-8") as лог_стенда:
                    стенд = subprocess.Popen(команда, cwd=КОРІНЬ, env=env, stdout=лог_стенда, stderr=subprocess.STDOUT,
                                             creationflags=subprocess.CREATE_NO_WINDOW)
                    результат["rc"] = стенд.wait(timeout=1800)
                print("Кінець живої сцени: rc=" + str(результат["rc"]), flush=True)
        finally:
            for процес in (стенд, проксі):
                if процес and процес.poll() is None:
                    процес.terminate()
                    процес.wait(timeout=30)
            лог = (вихід / "проксі.txt").read_text(encoding="utf-8") if (вихід / "проксі.txt").exists() else ""
            власні = set(re.findall(r"HTTP власний екземпляр (.+)", лог))
            результат["вивантажено"] = [api("/unload", {"instance_id": е["id"]})
                for м in api()["models"] for е in м["loaded_instances"] if е["id"] in власні]
            результат["моделі_після"] = [{"key": м["key"], "loaded_instances": м["loaded_instances"]} for м in api()["models"]]
            результат["кінець"] = datetime.now(timezone.utc).isoformat()
            результат["секунд"] = round(time.monotonic() - початок, 1)
            (вихід / "результат.json").write_text(json.dumps(результат, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return результат["rc"]


if __name__ == "__main__":
    raise SystemExit(виконати())
