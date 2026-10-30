"""Перевіряє файлові межі на фрагментах Python і JS, не виконуючи продукт."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def головна():
    """Зіставляє семантичні очікування з місцями й наявністю файлових свідків."""
    корінь = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(корінь / "джерела/прилади"))
    п = importlib.import_module("корінь_річ_запис_речі")
    випадки = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf8"))
    вад = 0
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMP")) as т:
        for випадок in випадки:
            модулі = []
            п._ПІДВИРАЗИ.clear()
            for файл, код in випадок["джерела"].items():
                if файл.endswith(".py"):
                    модулі.append(п.розібрати_py(файл, код))
                else:
                    js = Path(т) / "проба.js"
                    js.write_text(код, encoding="utf8")
                    в = subprocess.run(["node", "--expose-internals", str(корінь / "джерела/прилади/корінь_річ_запис_речі_js.js"), str(js)], capture_output=True, encoding="utf8", check=True)
                    модулі.append(п.розібрати_js(файл, json.loads(в.stdout)[str(js)]))
            а = п.Аналіз(модулі, п.Реєстр(str(корінь)))
            а.пройти()
            місця = п.обчислити(а)
            пункти = sorted({пункт for _, _, пункт in місця})
            добре = пункти == випадок["пункти"] and all(а.свідки[к]["ланки"] for к in місця)
            вад += not добре
            print(json.dumps({"проба": випадок["назва"], "пункти": пункти, "очікувано": випадок["пункти"], "пройдено": добре}, ensure_ascii=False))
    return int(bool(вад))

if __name__ == "__main__":
    sys.exit(головна())
