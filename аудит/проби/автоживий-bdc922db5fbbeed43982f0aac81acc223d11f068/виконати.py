"""Послідовний запуск лише призначених сцен; реалізацію стенда не змінює."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ЗБІРКА = КОРІНЬ.parent / "tmp/збірка-cbd9342c"
КЕШ = Path("C:/Users/gemini/pyodide")
ПЛАН = json.loads((ТЕКА / "план.json").read_text(encoding="utf-8"))


def записати(текст):
    рядок = datetime.now(timezone.utc).isoformat() + " " + текст
    print(рядок, flush=True)
    with (ТЕКА / "done.txt").open("a", encoding="utf-8") as ф:
        ф.write(рядок + "\n")


def main():
    for і, сцена in enumerate(ПЛАН["scenes"]):
        вихід = ТЕКА / сцена
        результат = вихід / "результат.json"
        if результат.exists():
            записати("ЗАПИС УЖЕ Є, БЕЗ ПОВТОРУ: " + сцена)
            continue
        if і == 0:
            # Першу сцену вже запущено окремою командою, чекаємо завершення.
            while not результат.exists():
                time.sleep(2)
            rc = json.loads(результат.read_text(encoding="utf-8"))["rc"]
        else:
            env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                       NODE_PATH="C:/Users/gemini/kod-shi-test-node/node_modules")
            if сцена == "ж1_робота":
                env["MODEL_VYBIR"] = "assess"
            if сцена == "ж4_робота_стримано":
                env["ZAMINA_RUK"] = "1,2"
            команда = [sys.executable, "аудит/проби/записати_сцену.py",
                       str(ЗБІРКА), str(КЕШ), str(вихід), "--сцена", сцена]
            with (ТЕКА / "команди.jsonl").open("a", encoding="utf-8") as ф:
                ф.write(json.dumps({"сцена": сцена, "команда": команда,
                    "додаткові_змінні": {к: env[к] for к in ("MODEL_VYBIR", "ZAMINA_RUK") if к in env}},
                    ensure_ascii=False) + "\n")
            записати("ПОЧАТОК " + сцена)
            with (ТЕКА / (сцена + "_запуск.txt")).open("w", encoding="utf-8") as лог:
                rc = subprocess.run(команда, cwd=КОРІНЬ, env=env,
                                    stdout=лог, stderr=subprocess.STDOUT).returncode
        записати(f"КІНЕЦЬ {сцена} rc={rc}")
        subprocess.run(["git", "add", "--", str(ТЕКА)], cwd=КОРІНЬ, check=True)
        subprocess.run(["git", "commit", "-m", f"Записати живу сцену {сцена}: rc={rc}"],
                       cwd=КОРІНЬ, check=True)
        if rc >= 2:
            доказ = вихід / "знімки/доказ.json"
            факти = json.loads(доказ.read_text(encoding="utf-8")).get("факт", {}) if доказ.exists() else {}
            if not факти.get("живих_карток"):
                записати("ЗБІЙ ДО КАРТОК: " + сцена + "; наступні сцени ще не виконано")
                return rc
            записати("СЦЕНА НЕ ЗАВЕРШЕНА ПІСЛЯ КАРТОК: " + сцена + "; без повтору, далі інші сцени плану")
    записати("УСІ СЦЕНИ ПЛАНУ ОПРАЦЬОВАНО; коди виходу й повнота доказу — у записах")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
