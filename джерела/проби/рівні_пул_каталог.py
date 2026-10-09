# -*- coding: utf-8 -*-
"""ПУЛ-6, вади Codex: скільки речей кожного рівня пізніх ключів (0 = не гірша за найкращу в слоті ні за одним ключем,
1 = гірша за одним, 2+ = за двома і більше) є в пулі руки 1 (каталог_повний, 17 слотів) і скільки дійшло до стилістки.
Рівень міряє ця проба сама («скільки ключів гірші»), не семплер — тож «до» і «після» на одній мірці.
Запуск: python3 проби/рівні_пул_каталог.py [сід]   (~30 с)"""
import sys, json, pathlib, os, collections
_К = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_К)); os.chdir(_К)
import bridge as B, семплер as С
зап = {}; _о = С.вибрати
def _з(к, *а, **kw):
    зап.setdefault("пул", {с: list(v) for с, v in к.items()}); return _о(к, *а, **kw)
С.вибрати = _з
вх = json.load(open(_К / "стенд_вх.json", encoding="utf-8")); вх.update(каталог="каталог_повний.xml", гілка=0)
if len(sys.argv) > 1: вх["сід"] = int(sys.argv[1])
вх["сценарій"] = dict(вх["сценарій"], ошатність=[4, 6], темп_c=5)
р = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
в, п = collections.Counter(), collections.Counter()
for с, речі in зап["пул"].items():
    ранги = [tuple(r.get("_ранг_пізній") or ()) for r in речі]
    краще = [min((х[i] for х in ранги if len(х) > i), default=0) for i in range(max(map(len, ранги), default=0))]
    взяті = {x["id"] for x in р["кандидати"][с]}
    for r, х in zip(речі, ранги):
        л = min(sum(1 for i in range(len(х)) if х[i] > краще[i]), 2); п[л] += 1; в[л] += r["id"] in взяті
print("рівень: у пулі → дійшло до стилістки; усього %d → %d" % (sum(п.values()), sum(в.values())))
for л in (0, 1, 2): print("  %d: %3d → %3d (%d%%)" % (л, п[л], в[л], 100 * в[л] // max(1, п[л])))
