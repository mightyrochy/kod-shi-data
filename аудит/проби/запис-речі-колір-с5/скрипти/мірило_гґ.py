#!/usr/bin/env python3
"""Мірила (г) і (ґ) наряду Запис-речі-колір-мітка на шляху ядра (`обвязка.вхід_с5`, сцена с5): каталог — рядки
таблиці каталогу 207 речей вибірки (кеш `мірило_нового.каталог()` проби вибірки 300, `/tmp/каталог_рядки.pkl`).

(г) без ключа `мітки_речі` (перемикач вимкнено): sha256 кожного запиту моделі — код ДО (`main`) і ПІСЛЯ мусять дати
однакові байти. (ґ) токени на кандидата запиту складання (оцінка ядра `ядро/запит.py`: ⌈1,1 × `міра_токенів.токенів`⌉): без запису; із записом нового виду
без мітки «колір»; із ним цілим (Sonnet, Haiku).

Запуск: cd <корінь коду>/джерела && python3 <цей скрипт> <корінь коду> <вихід.json>"""
import hashlib, json, pickle, sys
from pathlib import Path

КОД = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(КОД / "джерела"))
ПРОБА = Path(__file__).resolve().parents[1]
from math import ceil  # noqa: E402
from ядро import протокол  # noqa: E402
from міра_токенів import токенів  # noqa: E402
from ядро.тести import обвязка  # noqa: E402

рядки = {р["id"].split("@")[0]: р for р in pickle.load(open("/tmp/каталог_рядки.pkl", "rb"))}
ід = [в["ід"].split("@")[0] for в in json.loads((ПРОБА / "дані/вибірка.json").read_text(encoding="utf-8"))["речі"]]
ід = [і for і in ід if і in рядки]


def оцінити(текст):
    return ceil(1.1 * токенів(текст))  # оцінка ядра, `ядро/запит.py` (вікно запиту)


def журнал(м):
    import запис_речі
    вихід = {}
    for л in (ПРОБА / f"дані/{м}.jsonl").open(encoding="utf-8"):
        з = json.loads(л)
        р = запис_речі.розібрати(з["текст"])
        вихід[з["ід"].split("@")[0]] = {"опис": р["опис"], "мітки": р["мітки"]}
    return вихід


def прогін(записи=None, без_кольору=False):
    кат = []
    for і in ід:
        р = dict(рядки[і])
        if записи and і in записи:
            з = json.loads(json.dumps(записи[і]))
            if без_кольору:
                з["мітки"].pop("колір", None)
            р["мітки_речі"] = з
        кат.append(р)
    в = обвязка.почати(протокол, обвязка.вхід_с5(каталог=кат))
    відбитки = [hashlib.sha256(json.dumps(з["модель"], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                for з in в["запити"]]
    запит = next(з for з in в["запити"] if з["вид"] == "складання")
    тіло = json.loads(запит["модель"]["messages"][0]["content"])
    пул = тіло["pool"]
    к = len(пул["rows"])
    пул_т = оцінити(json.dumps(пул["rows"], ensure_ascii=False, separators=(",", ":")))
    і_к = пул["cols"].index("color") if "color" in пул["cols"] else None
    return {"запитів": len(відбитки), "відбитки": відбитки, "кандидатів": к, "токенів_пулу": пул_т,
            "на_кандидата": round(пул_т / к, 1) if к else None, "колонок": len(пул["cols"]),
            "токенів_запиту": оцінити(запит["модель"]["messages"][0]["content"]),
            "color_невідомо": sum(r[і_к] == "unknown" for r in пул["rows"]) if і_к is not None else None}


вихід = {"код": str(КОД), "речей_у_каталозі": len(ід), "без запису (перемикач вимкнено)": прогін()}
try:
    from ядро import відтінки  # noqa: F401  — є лише ПІСЛЯ
    for м in ("sonnet", "haiku"):
        ж = журнал(м)
        вихід[f"{м}: запис без мітки «колір»"] = прогін(ж, без_кольору=True)
        вихід[f"{м}: запис із міткою «колір»"] = прогін(ж)
except ImportError:
    pass
Path(sys.argv[2]).write_text(json.dumps(вихід, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps({к: ({кк: вв for кк, вв in в.items() if кк != "відбитки"} if isinstance(в, dict) else в) for к, в in вихід.items()}, ensure_ascii=False, indent=1))
