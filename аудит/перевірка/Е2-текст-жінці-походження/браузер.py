"""Повторює сцену 01 через штатний сервер записів і браузерний стенд; живої моделі немає."""
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading


if __name__ == "__main__":
    корінь = Path.cwd()
    докази = Path(__file__).resolve().parent
    стан = sys.argv[1] if len(sys.argv) > 1 else "після"
    збірка = Path(os.environ["TEMP"]) / ("е2-показ" if стан == "після" else "е2-показ-до")
    знімки = Path(os.environ["TEMP"]) / ("е2-браузер-" + стан + "-знімки")
    знімки.mkdir(exist_ok=True)
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    сцена = корінь / "аудит/проби/б1/ПІСЛЯ-Е3/01_б1_концерт_стримано"
    готовність = queue.Queue()
    with (докази / f"браузер-{стан}-проксі.txt").open("w", encoding="utf-8") as журнал:
        сервер = subprocess.Popen([sys.executable, "аудит/проби/replay_сцени.py", str(сцена), "0", "--за-порядком"],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                  encoding="utf-8", env=середовище)

        def читати():
            """Пише весь журнал сервера й передає фактичну адресу після готовності слухача."""
            for рядок in сервер.stdout:
                журнал.write(рядок)
                журнал.flush()
                if рядок.startswith("REPLAY_READY "):
                    готовність.put(рядок.split(maxsplit=1)[1].strip())

        потік = threading.Thread(target=читати)
        потік.start()
        try:
            адреса = готовність.get(timeout=30)
            середовище.update(MODEL_URL=адреса, MODEL="qwen/qwen3.5-9b",
                MODEL_MOVA="mamaylm-gemma-3-12b-it-v2.0", OTSINKA="0", FOTO="0", ODNOCHASNO="1",
                ZNIMKY=str(знімки), ZVIT_OUT=str(Path(os.environ["TEMP"]) / ("е2-браузер-" + стан + "-вердикти.json")),
                ZHINKA=str(корінь / "аудит/проби/жінки/ж8.json"),
                CHAT_TEXT="рок-концерт у клубі, п'ятниця ввечері, стоятиму в натовпі, хочу стримано й класично")
            with (докази / f"браузер-{стан}.txt").open("wb") as вихід:
                результат = subprocess.run(["node", "аудит/проби/рв6_стенд.js", "http://127.0.0.1:8765",
                    str(збірка), str(Path(os.environ["TEMP"]) / "pyodide"), "3"],
                    env=середовище, stdout=вихід, stderr=subprocess.STDOUT)
            print(f"Браузер {стан}: код {результат.returncode}", flush=True)
        finally:
            сервер.terminate()
            сервер.wait()
            потік.join()
    sys.exit(результат.returncode)
