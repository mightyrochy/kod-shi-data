"""Виконує батарею та сім'ю 5.3 послідовно до кінця, зберігаючи коди та вивід."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    """Пише докази кожного запуску й завершується ненульовим кодом за наявності провалів."""
    корінь = Path(__file__).resolve().parents[3]
    джерела = корінь / "джерела"
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", NODE_PATH=str(джерела / "node_modules"))
    батарея = [[sys.executable, *аргументи] for аргументи in (
        ["стенд_знімок.py", "--дим"], ["тест_живого_шляху.py"], ["тест_протоколу.py"],
        ["прилади/розділи_гейтів.py"], ["audit_contracts.py"]) ]
    батарея.append(["node", "тест_показу.js"])
    проби = [[sys.executable, str(ф)] for ф in sorted((джерела / "проби").glob("каталог_зависла_крамниця*.py"))]
    проби += [[sys.executable, str(джерела / "проби" / ф)] for ф in (
        "каталог_проблеми_г_стеля.py", "каталог_проблеми_г_крамниці.py")]
    довгі = "--довгі" in sys.argv
    if довгі:
        батарея = [к for к in батарея if к[1] in ("тест_живого_шляху.py", "прилади/розділи_гейтів.py")]
        проби = []
    збої = []
    with tempfile.TemporaryDirectory(prefix="obkhid-stan-2069-") as журнал:
        if not довгі:
            проби.append([sys.executable, str(джерела / "проби/каталог_обхід_стан.py"), журнал])
        for назва, команди in (("батарея", батарея), ("проби", проби)):
            if not команди:
                continue
            with Path(__file__).with_name(назва + ("_довгі" if довгі else "") + ".txt").open("w", encoding="utf-8", newline="\n") as журнал_виводу:
                for команда in команди:
                    журнал_виводу.write("КОМАНДА: " + " ".join(команда) + "\n")
                    журнал_виводу.flush()
                    try:
                        результат = subprocess.run(команда, cwd=джерела, env=середовище,
                                                   stdout=журнал_виводу, stderr=subprocess.STDOUT, timeout=1200)
                        код = результат.returncode
                        вивід = ""
                    except subprocess.TimeoutExpired as помилка:
                        код = 124
                        вивід = str(помилка)
                    журнал_виводу.write(вивід + f"\nКОД: {код}\n\n")
                    журнал_виводу.flush()
                    print(Path(команда[1]).name, "код", код, flush=True)
                    if код:
                        збої.append(Path(команда[1]).name)
    print("Провали:", збої, flush=True)
    return int(bool(збої))


if __name__ == "__main__":
    raise SystemExit(main())
