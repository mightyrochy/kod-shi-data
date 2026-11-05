"""Повторює наявні записи мосту, зберігаючи результати поряд із доказами доробки."""
from pathlib import Path
import os
import subprocess
import sys


if __name__ == "__main__":
    тут = Path(__file__).resolve().parent
    скрипт = тут.parent / "річ-утримання/сцени.py"
    текст = скрипт.read_text("utf-8").replace(
        'Д = Path(__file__).resolve().parent',
        'Д = Path(__file__).resolve().parent.parent / "річ-опис-person"')
    режим = sys.argv[1] if len(sys.argv) > 1 else "після"
    if режим == "до-опису":
        накладка = Path(os.environ["TEMP"]) / "person-до"
        накладка.mkdir(exist_ok=True)
        код = subprocess.check_output(["git", "show",
            "944b1ff579e7e8293a608c87a3569661230d91a9:джерела/вибір_палітри.py"])
        (накладка / "вибір_палітри.py").write_bytes(код)
        текст = текст.replace('import feed\n', 'sys.path.insert(0, %r)\nimport feed\n' % str(накладка))
    sys.argv = [str(скрипт), режим]
    exec(compile(текст, str(скрипт), "exec"), dict(__file__=str(скрипт), __name__="__main__"))
