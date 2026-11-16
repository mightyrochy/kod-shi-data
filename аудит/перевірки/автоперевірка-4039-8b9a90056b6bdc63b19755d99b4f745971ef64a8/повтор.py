"""Повтор збережених відповідей на точній збірці; усі дочірні процеси чекає або завершує."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

репо, збірка, вихід = map(lambda x: Path(x).resolve(), sys.argv[1:4])
pyodide = Path("C:/Users/gemini/pyodide")
chromium = Path(os.environ["LOCALAPPDATA"]) / "ms-playwright/chromium-1248/chrome-win64/chrome.exe"
проби = репо / "аудит/проби"
записи = проби / "Корені-нуль-живе-мірило-1511"
for сцена in sys.argv[4:]:
    тека = вихід / сцена
    for назва in ("знімки", "VIDPOVIDI"):
        (тека / назва).mkdir(parents=True, exist_ok=True)
    режим = "повне" if сцена in ("ж8_зима", "ж1_екскурсія_бруківка") else "розмова"
    змінні = json.loads(subprocess.check_output([
        sys.executable, str(проби / "записати_сцену.py"), "--сцена", сцена,
        "--режим", режим, "--лише-змінні"], encoding="utf-8"))
    сервер = subprocess.Popen([sys.executable, "-u", str(проби / "replay_сцени.py"),
        str(записи / сцена), "0"], cwd=проби, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8")
    try:
        with (тека / "повтор.txt").open("w", encoding="utf-8") as лог:
            for рядок in сервер.stdout:
                лог.write(рядок)
                лог.flush()
                if рядок.startswith("REPLAY_READY "):
                    адреса = рядок.strip().split(" ", 1)[1]
                    break
            else:
                raise RuntimeError("Сервер повтору завершився без REPLAY_READY")
        with socket.socket() as порт:
            порт.bind(("127.0.0.1", 0))
            адреса_стенда = "http://127.0.0.1:" + str(порт.getsockname()[1])
        env = dict(os.environ, **змінні)
        env.update(MODEL="claude-sonnet-5-5", MODEL_MOVA="claude-sonnet-5-5", MODEL_URL=адреса,
                   FOTO="1", CHROMIUM=str(chromium), NODE_PATH="C:/Users/gemini/kod-shi-test-node/node_modules",
                   VIDPOVIDI=str(тека / "VIDPOVIDI"), ZNIMKY=str(тека / "знімки"),
                   ZVIT_OUT=str(тека / "вердикти.txt"))
        with (тека / "лог.txt").open("w", encoding="utf-8") as лог:
            код = subprocess.run(["node", str(проби / "рв6_стенд.js"), адреса_стенда,
                                  str(збірка), str(pyodide), "3"], cwd=репо, env=env,
                                 stdout=лог, stderr=subprocess.STDOUT).returncode
        print(json.dumps(dict(сцена=сцена, код=код), ensure_ascii=False), flush=True)
    finally:
        сервер.terminate()
        сервер.wait()
