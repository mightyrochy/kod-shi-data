"""Браузерний повтор нічної сцени через записані відповіді; сервер завершується разом із прогоном."""
import json
import os
from pathlib import Path
import subprocess
import sys

КОРІНЬ = Path(__file__).resolve().parents[3]
ВИХІД = Path(__file__).resolve().parent


def головна():
    """Підняти штатний replay_сцени.py, дочекатися готовності та виконати стенд у Chromium."""
    збірка = Path(sys.argv[1]).resolve()
    браузер = sys.argv[2]
    pyodide = Path(sys.argv[3]).resolve()
    джерело = КОРІНЬ / "аудит/проби/нічні/20261028/б1_концерт_стримано"
    оточення = dict(os.environ, PYTHONUTF8="1")
    сервер = subprocess.Popen([sys.executable, "-W", "ignore", str(КОРІНЬ / "аудит/проби/replay_сцени.py"),
                               str(джерело), "0"], cwd=КОРІНЬ, env=оточення,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    початок = []
    try:
        while True:
            рядок = сервер.stdout.readline()
            if not рядок:
                raise RuntimeError("Сервер повтору не дійшов до REPLAY_READY: " + "".join(початок))
            початок.append(рядок)
            if рядок.startswith("REPLAY_READY "):
                адреса = рядок.split()[1]
                break
        оточення.update(NODE_PATH=str(КОРІНЬ / "джерела/node_modules"), CHROMIUM=браузер,
                        MODEL_URL=адреса, MODEL_MOVA_URL=адреса, MODEL="qwen/qwen3.5-9b",
                        MODEL_MOVA="mamaylm-gemma-3-12b-it-v2.0", ODNOCHASNO="1", OTSINKA="0", FOTO="1",
                        SCENA="б1_концерт_стримано", ZHINKA=str(КОРІНЬ / "аудит/проби/жінки/ж8.json"),
                        CHAT_TEXT="рок-концерт у клубі, п'ятниця ввечері, стоятиму в натовпі, хочу стримано й класично",
                        ZNIMKY=str(ВИХІД / "повтор"))
        команда = ["node", str(КОРІНЬ / "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:8765",
                   str(збірка), str(pyodide), "3"]
        print("Повтор готовий:", адреса, flush=True)
        with (ВИХІД / "повтор.txt").open("wb") as лог:
            запуск = subprocess.run(команда, cwd=КОРІНЬ, env=оточення, stdout=лог, stderr=subprocess.STDOUT)
        результат = dict(сцена="б1_концерт_стримано", джерело=str(джерело.relative_to(КОРІНЬ)),
                         спосіб="replay_сцени.py, записані відповіді; не живий виклик моделі", код=запуск.returncode)
        (ВИХІД / "повтор_результат.json").write_text(json.dumps(результат, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Повтор: код", запуск.returncode, flush=True)
        return запуск.returncode
    finally:
        сервер.terminate()
        решта, _ = сервер.communicate(timeout=10)
        (ВИХІД / "повтор_сервер.txt").write_text("".join(початок) + решта, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(головна())
