"""Replay корпусу відповідей моделі через міст_відповіді.від_моделі.

Перевіряє роботу ендпойнта `від_моделі` на вибірці репрезентативних форм із корпусу
`аудит/корпус_3_1_а/*.json`. Запускає прогін двічі та перевіряє строгу ідемпотентність.
"""
import glob
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("джерела"))
import feed
import міст_відповіді

feed.каталог_на_диску("каталог_brief.xml")
каталог = os.path.abspath("джерела/каталог_brief.xml")
файли = sorted(glob.glob("аудит/корпус_3_1_а/*.json"))


def прогін():
    підсумок = []
    for ф in файли:
        вх = json.load(open(ф, encoding="utf-8"))
        вх["каталог"] = каталог
        out = json.loads(міст_відповіді.від_моделі(вх))
        підсумок.append({
            "файл": os.path.basename(ф),
            "перевірено": out.get("перевірено"),
            "образів": len(out.get("образи") or []),
            "чому": str(out.get("чому")),
            "розбір_ід": bool((out.get("розбір") or {}).get("ід")),
            "знахідок": len(out.get("знахідки") or []),
        })
    return підсумок


if __name__ == "__main__":
    rez1 = прогін()
    rez2 = прогін()
    assert rez1 == rez2, "Replay не ідемпотентний!"
    print(f"Ідемпотентність підтверджено: прогін 1 == прогін 2 ({len(rez1)} форм)\n")
    print(f"{'Файл':<42} | {'Перевірено':<10} | {'Образів':<8} | {'Чому / статус'}")
    print("-" * 85)
    for r in rez1:
        print(f"{r['файл']:<42} | {str(r['перевірено']):<10} | {r['образів']:<8} | {r['чому'][:35]}")
    print("-" * 85)
    print(f"РАЗОМ: {len(rez1)} форм успішно пройшли replay.")
