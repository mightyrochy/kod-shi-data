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


# Режим з поля «режим» реєстру `живі_сцени.txt` (шапка реєстру, `живі_порядок.md`): основа + «+фото» + дужки «(стенд: сцени 6 і 6б)».
ОСНОВА_РЕЖИМУ = {"повне": {"OTSINKA": "0"}, "розмова": {"DO": "rozmova"}, "палітра": {"DO": "palitra"},
                 "коментар": {"DO": "koment"}, "оцінка": {"DO": "otsinka"}}
РЕЖИМ_РЕЄСТРУ = re.compile(r"(повне|розмова|палітра|коментар|оцінка|функція)(\s*\+\s*фото)?(?:\s*\((стенд: сцени 6(?: і 6б)?)\))?")


def змінні_режиму(id_, режим, вхід):
    """Змінні стенда з полів «режим» і «вхід» рядка реєстру; режим, якого прилад не вміє, — ValueError з причиною до старту."""
    м = РЕЖИМ_РЕЄСТРУ.fullmatch(режим.strip())
    if not м:
        raise ValueError(f"Сцена {id_}: режим «{режим}» приладу невідомий")
    основа, фото, сцена6 = м[1], bool(м[2]), bool(м[3])
    if основа == "функція":
        raise ValueError(f"Сцена {id_}: режим «функція» — код без моделі в Chromium, не запис на ноутбуці")
    змінні = dict(ОСНОВА_РЕЖИМУ[основа])
    if сцена6 and основа == "повне":
        del змінні["OTSINKA"]   # «стенд: сцени 6 і 6б» — «Оціни мій образ» входить у запис
    elif сцена6:
        raise ValueError(f"Сцена {id_}: «(стенд: сцени 6 і 6б)» лише при режимі «повне»")
    змінні["FOTO"] = "1" if фото else "0"
    for ознака in вхід.split():
        ключ, роздільник, значення = ознака.partition("=")
        if ознака.startswith("×") and ознака[1:].isdecimal():
            continue   # «×5» — число повторів, їх веде запускач, не змінна стенда
        if not роздільник or not ключ.isidentifier():
            raise ValueError(f"Сцена {id_}: ознака входу «{ознака}» не у вигляді ЗМІННА=значення")
        if ключ == "DO" and "DO" in змінні and змінні["DO"] != значення:
            raise ValueError(f"Сцена {id_}: вхід DO={значення} суперечить режиму «{режим}» (DO={змінні['DO']})")
        змінні[ключ] = значення
    return змінні


def сцена_реєстру(id_):
    """Єдиний рядок реєстру за id: змінні сцени за режимом і входом (не одні на всі сцени)."""
    рядки = [р.split("|") for р in (КОРІНЬ / "аудит/проби/живі_сцени.txt").read_text(encoding="utf-8").splitlines()
             if р.startswith(id_ + "|")]
    if len(рядки) != 1:
        raise ValueError("Нема єдиної сцени в реєстрі: " + id_)
    id_, жінка, запит, вхід, режим = рядки[0][:5]
    змінні = змінні_режиму(id_, режим, вхід)
    return {"назва": id_, "сід": 3, "змінні": dict(змінні, SCENA=id_, CHAT_TEXT=запит,
        ZHINKA=str(КОРІНЬ / "аудит/проби/жінки" / (жінка + ".json")),
        MODEL="qwen/qwen3.5-9b", MODEL_MOVA="mamaylm-gemma-3-12b-it-v2.0")}


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
    а.add_argument("збірка", type=Path, nargs="?")
    а.add_argument("кеш", type=Path, nargs="?")
    а.add_argument("вихід", type=Path, nargs="?")
    а.add_argument("--лише-змінні", action="store_true", help="Надрукувати змінні сцени за режимом реєстру й вийти до старту")
    а.add_argument("--сцена", default="1", help="Номер архівної сцени або id з живі_сцени.txt")
    а.add_argument("--node", default="node")
    п = а.parse_args()
    if п.лише_змінні:
        print(json.dumps(сцена_реєстру(п.сцена)["змінні"], ensure_ascii=False, indent=1))
        return 0
    if not (п.збірка and п.кеш and п.вихід):
        а.error("потрібні збірка, кеш і вихід (без --лише-змінні)")
    if п.сцена.isdecimal():
        перелік = json.loads(subprocess.check_output([п.node, str(КОРІНЬ / "аудит/проби/приймання_записів.js"), "--перелік"],
            env=dict(os.environ, REPLAY_ARCHIVE="1"), cwd=КОРІНЬ, text=True, encoding="utf-8"))
        сцена = перелік[int(п.сцена) - 1]
    else:
        сцена = сцена_реєстру(п.сцена)
    вихід = п.вихід.resolve()
    вихід.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    for ключ in tuple(env):
        if ключ.startswith("REPLAY_"):
            del env[ключ]
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
    try:
        raise SystemExit(виконати())
    except ValueError as відмова:   # режим чи сцена, яких прилад не вміє, — рядок причини до старту, без сліду
        raise SystemExit("ВІДМОВА: " + str(відмова))
