# -*- coding: utf-8 -*-
"""Рядок 112, §4 п.14: останні 2 `except Exception` ядра (§5 п.17: 1 без докстрінга),
усі три в `міст_відповіді.py` (поза хвилею 103 — паралельно правив рядок 101).
Таблиця AST + ДО (мовчання) / ПІСЛЯ (`риси_чому`) на живому місці.
Прогін: cd джерела && python3 проби/vyniatky_112.py [БАЗА]"""
import ast, collections, json, os, subprocess, sys
ДЖ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ДЖ); os.chdir(ДЖ)
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "d997844"
ТАБЛИЦЯ = [("_вердикти_образів", 97, "composer._у_річ(речі пакета)", "чужий вхід·запис каталогу",
            "вузько KeyError/TypeError/ValueError → поле `риси_чому`"),
           ("_вердикти_образів", 197, "pipeline.перевірити_від_моделі(о_N)", "чужий вхід·склад від моделі",
            "вузько +IndexError/AttributeError → `чому` (дірка в номерах, `вердикт_v1`)")]
for р in ТАБЛИЦЯ: print("%-20s %4d  %s · %s · %s" % р)
широких = lambda т: sum(1 for x in ast.walk(ast.parse(т)) if isinstance(x, ast.ExceptHandler) and (
    x.type is None or (isinstance(x.type, ast.Name) and x.type.id in ("Exception", "BaseException"))))
старе_т = subprocess.run(["git", "show", "%s:джерела/міст_відповіді.py" % БАЗА], capture_output=True, text=True, check=True).stdout
нове_т = open("міст_відповіді.py", encoding="utf-8").read()
print("except Exception/голих: БАЗА %d → гілка %d" % (широких(старе_т), широких(нове_т)))
import feed as Ф, bridge as B, composer as _КМ, міст_відповіді as МВ
вх = json.load(open("стенд_вх.json", encoding="utf-8")); вх["каталог"] = Ф.каталог_на_диску("каталог_brief.xml"); вх["гілка"] = 0
json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
за_слот = collections.defaultdict(list)
for c in B.каталог_останнього_пакета(): за_слот[c.get("слот")].append(c["id"])
id1 = за_слот["верх"][0]; вх2 = dict(вх, ід=[id1, за_слот["низ"][0]])
_ОРИГ = _КМ._у_річ; _n = [0]
def _патч(r, слот, тіло, дистанція=None):
    # 1-й виклик id1 — `перевірити_від_моделі` (основний, лишається справним); 2-й — те саме id у `_повні`: тут ламається.
    if r.get("id") == id1:
        _n[0] += 1
        if _n[0] == 2: raise TypeError("зіпсований lab")
    return _ОРИГ(r, слот, тіло, дистанція)
_КМ._у_річ = _патч
exec(compile(старе_т, "міст_відповіді@" + БАЗА, "exec"), МВ.__dict__); _n[0] = 0
до = json.loads(МВ.від_моделі(json.dumps(вх2, ensure_ascii=False)))["образи"][0]
exec(compile(нове_т, "міст_відповіді.py", "exec"), МВ.__dict__); _n[0] = 0
після = json.loads(МВ.від_моделі(json.dumps(вх2, ensure_ascii=False)))["образи"][0]
_КМ._у_річ = _ОРИГ
print("ДО   (%s): риси.речей=%s риси_чому=%r (тиша)" % (БАЗА, до.get("риси", {}).get("речей"), до.get("риси_чому")))
print("ПІСЛЯ(гілка): риси.речей=%s риси_чому=%r" % (після.get("риси", {}).get("речей"), після.get("риси_чому")))
sys.exit(0 if (до.get("риси_чому") is None and після.get("риси_чому")) else 1)
