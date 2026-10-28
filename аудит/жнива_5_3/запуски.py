"""Послідовні запуски наряду з журналами команд і кодів виходу."""
import os
from pathlib import Path
import subprocess
import sys

КОРІНЬ = Path(__file__).resolve().parents[2]
ТЕКА = Path(__file__).resolve().parent
ЖУРНАЛ = Path.home() / ".cache/liusterko/harvest-5.3-20261029"


def команда(аргументи, лог, cwd=КОРІНЬ):
    """Чекає передньопланову команду до кінця й зберігає її дослівний вивід."""
    print("ЗАПУСК", subprocess.list2cmdline(аргументи), flush=True)
    with лог.open("w", encoding="utf-8") as ф:
        ф.write("КОМАНДА: " + subprocess.list2cmdline(аргументи) + "\n"); ф.flush()
        код = subprocess.run(аргументи, cwd=cwd, stdout=ф, stderr=subprocess.STDOUT,
                             env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                                      NODE_PATH=str(Path.home() / "kod-shi-test-node/node_modules"))).returncode
        ф.write(f"\nКОД: {код}\n")
    print("КОД", код, "ЛОГ", лог, flush=True)
    return код


def main():
    """Виконує вибраний крок наряду, не лишаючи фонових процесів."""
    режим = sys.argv[1]
    if режим in ("проба", "обхід", "повтор"):
        ЖУРНАЛ.mkdir(parents=True, exist_ok=True)
        арг = [sys.executable, "-u", "zhnyvarka/обхід.py", "--журнал", str(ЖУРНАЛ),
               "--транспорт", "http,браузер,дім", "--паралельно", "6", "--секунд-на-магазин", "120",
               "--стеля", "300", "--циклів", "1"]
        if режим == "проба":
            арг += ["--магазини", "ricamare.com.ua,bella-bicchi.com,theoriginals.com.ua"]
        else:
            арг += ["--оновити-каталог"]
        return команда(арг, ЖУРНАЛ / (режим + ".txt"))
    if режим == "перевірка":
        файли = ["каталог_рецепт_повтор.py", "каталог_цикл_53.py", "картка_вузол_5_1.py"]
        файли += [ф.name for ф in sorted((КОРІНЬ / "джерела/проби").glob("каталог_зависла_крамниця*.py"))
                  if not ф.stem.endswith(("_до", "_проба"))]
        коди = [команда([sys.executable, "джерела/проби/" + ф], ТЕКА / ("проба-" + ф + ".txt")) for ф in файли]
        return int(any(коди))
    if режим == "батарея":
        команди = [[sys.executable, "стенд_знімок.py", "--дим"], [sys.executable, "тест_живого_шляху.py"],
                   [sys.executable, "тест_протоколу.py"], [sys.executable, "прилади/розділи_гейтів.py"],
                   [sys.executable, "audit_contracts.py"], ["node", "тест_показу.js"]]
        коди = [команда(арг, ТЕКА / (f"батарея-{н}.txt"), КОРІНЬ / "джерела") for н, арг in enumerate(команди, 1)]
        return int(any(коди))
    raise ValueError(режим)


if __name__ == "__main__":
    raise SystemExit(main())
