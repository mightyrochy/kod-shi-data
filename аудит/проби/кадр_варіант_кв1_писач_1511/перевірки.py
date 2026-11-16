"""Батарея та автономні проби сім'ї одним запуском, із продовженням після провалів."""
import json
import os
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]


def main():
    """Зберігає коди виходу й повні журнали кожної перевірки поза продуктовими файлами."""
    вихід = Path(sys.argv[1]).resolve()
    вихід.mkdir(parents=True, exist_ok=True)
    середовище = dict(os.environ, PYTHONUTF8="1", NODE_PATH=str(КОРІНЬ / "джерела/node_modules"))
    команди = [([sys.executable, "-X", "utf8", назва] + аргументи, КОРІНЬ / "джерела")
               for назва, аргументи in [("стенд_знімок.py", ["--дим"]), ("тест_живого_шляху.py", []),
                    ("тест_протоколу.py", []), ("прилади/розділи_гейтів.py", []), ("audit_contracts.py", [])]]
    команди.append((["node", "тест_показу.js"], КОРІНЬ / "джерела"))
    зовнішні = {"кадр_варіант_каталог.py", "кадр_варіант_перезбір.py",
                "кадр_варіант_факти.py", "кадр_варіант_woo_факти.py"}
    команди.extend(([sys.executable, "-X", "utf8", "-W", "ignore", str(шлях)], КОРІНЬ)
                  for шлях in sorted((КОРІНЬ / "джерела/проби").glob("кадр_варіант_*.py"))
                  if шлях.name not in зовнішні)
    команди.append(([sys.executable, "-X", "utf8", "-W", "ignore",
                    "джерела/прилади/корінь_річ_кадр_варіант.py"], КОРІНЬ))
    результати = []
    for номер, (команда, тека) in enumerate(команди, 1):
        назва = str(номер).zfill(2) + ".txt"
        with (вихід / назва).open("w", encoding="utf-8") as журнал:
            процес = subprocess.run(команда, cwd=тека, env=середовище,
                                    stdout=журнал, stderr=subprocess.STDOUT)
        результати.append(dict(команда=команда[1:], тека=str(тека), код=процес.returncode, журнал=назва))
        print(номер, Path(команда[-1]).name, "код:", процес.returncode, flush=True)
    звіт = dict(перевірки=результати, пропущено_поза_каналом=sorted(зовнішні))
    (вихід / "перевірки.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(any(р["код"] for р in результати))


if __name__ == "__main__":
    main()
