# -*- coding: utf-8 -*-
"""Ч-10 (рядок 223, аудит/ПРОДУКТ.md п.12 кошик В): `ноти_слотів` — КОДИ ЗАЯВ, а не речення коду.
На сідах 3 і 4 × намірах conventional/statement друкує: скільки нот, кириличних літер у
їхніх значеннях (мусить 0), кодів поза словником `ЗАЯВИ` (мусить 0), нот, що приїхали не
переліком заяв (мусить 0). Сторож проти повернення прози — СТАТИЧНИЙ: кириличні літерали
всередині самих виразів, що ноту складають (`заява`, `нота`, `дописати_ноту`, `_нота_слота`
і присвоєння в `ноти[…]` / `_нота…`), мусять бути 0. ФРАЗА проти ІД — та сама межа, що в
`шлях_шар_фрази_коду.py`: літерал із пробілом — речення, яке пише код (кошик В, мусить бути
0); літерал з одного слова — ключ ядра, який код ЧИТАЄ («верхній_шар», «причина», «схема»:
кошик Б, лишається). Літерали поза виразами нот проба не чіпає навмисно: `чому` й
`що_робити` збою збирання — сусіднє поле й окремий рядок дошки.
ВМ-3а (рядки 246, 247): ще кириличних літер у `break` дроту моделі і в `стеля.чому` (мусять 0).
Запуск із `джерела`: PYTHONPATH=. python3 проби/ч10_ноти_слотів.py"""
import ast, json, os, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent)); os.chdir(sys.path[0])
import bridge as B, feed as F, внутрішня_мова as ВМ
НОТОТВОРЦІ = ("заява", "нота", "дописати_ноту", "_нота_слота", "нота_пулу")
МІСЦЯ = ("композитор_збирання.py", "композитор_слоти.py", "міст_пакет.py", "регістр_уваги.py")
кир_літер = lambda x: len(re.findall(r"[а-яіїєґ]", json.dumps(x, ensure_ascii=False).lower()))
вх0 = json.load(open("стенд_вх.json", encoding="utf-8"))
вх0["каталог"] = F.каталог_на_диску("каталог_повний.xml")
нот = кир = поза = не_перелік = кир_розриву = кир_стелі = 0
коди = set()
for сід in (3, 4):
    for намір in ("conventional", "statement"):
        вих = json.loads(B.виклик("запити", json.dumps(dict(вх0, намір=намір, сід=сід), ensure_ascii=False)))
        ноти = вих.get("ноти_слотів") or {}
        кир_розриву += кир_літер(json.loads(вих["B"]).get("break")); кир_стелі += кир_літер((вих.get("стеля") or {}).get("чому"))
        for н in ноти.values():
            нот += 1
            if not isinstance(н, list) or not all(isinstance(з, dict) and з.get("code") for з in н):
                не_перелік += 1; continue
            кир += кир_літер(н)
            for з in н:
                коди.add(з["code"]); поза += з["code"] not in ВМ.ЗАЯВИ
        print("сід %s · %-14s нот %2d · заяв %d" % (сід, намір, len(ноти), sum(len(x) for x in ноти.values())))
фраз = []
for файл in МІСЦЯ:
    дерево = ast.parse(open(файл, encoding="utf-8").read())
    for в in ast.walk(дерево):
        ім = (getattr(в.func, "attr", None) or getattr(в.func, "id", None)) if isinstance(в, ast.Call) else None
        цілі = [t for t in getattr(в, "targets", ()) if (getattr(t, "id", "") or "").startswith(("нота", "_нота"))
                or (isinstance(t, ast.Subscript) and getattr(t.value, "id", "").startswith(("ноти", "_ноти")))]
        if ім not in НОТОТВОРЦІ and not цілі:
            continue
        фраз += ["%s: %s" % (файл, c.value[:60]) for c in ast.walk(в)
                 if isinstance(c, ast.Constant) and isinstance(c.value, str)
                 and re.search(r"[а-яіїєґ]", c.value.lower()) and " " in c.value.strip()]
# КОД, ЯКИЙ НА ЦЬОМУ КАТАЛОЗІ НЕ СПРАЦЮВАВ, ТЕЖ МУСИТЬ ІСНУВАТИ. `заява()` кидає KeyError на
# незнайомому коді, тож одруківка в рідкій гілці впала б лише на тій сцені, що її дістане;
# тут кожен код усіх гілок звіряється зі словником СТАТИЧНО, не чекаючи потрібної сцени.
статичні = [в.args[0].value for файл in МІСЦЯ for в in ast.walk(ast.parse(open(файл, encoding="utf-8").read()))
            if isinstance(в, ast.Call) and (getattr(в.func, "attr", None) or getattr(в.func, "id", None)) == "заява"
            and в.args and isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str)]
немає = sorted(к for к in set(статичні) if к not in ВМ.ЗАЯВИ)
print("НОТ %d · кодів у гілках коду %d, з них спрацювало тут %d · КОДІВ ПОЗА СЛОВНИКОМ %d (мусить 0)%s"
      % (нот, len(set(статичні)), len(коди), len(немає), (" — " + ", ".join(немає)) if немає else ""))
print("КИРИЛИЧНИХ ЛІТЕР У ЗНАЧЕННЯХ %d (мусить 0) · кодів поза словником %d (мусить 0) · "
      "нот не переліком %d (мусить 0) · КИРИЛИЧНИХ ЛІТЕРАЛІВ У ВИРАЗАХ НОТ %d (мусить 0)%s"
      % (кир, поза, не_перелік, len(фраз), (" — " + " | ".join(фраз)) if фраз else ""))
print("КИРИЛИЧНИХ ЛІТЕР У break ДРОТУ %d (мусить 0) · У стеля.чому %d (мусить 0)" % (кир_розриву, кир_стелі))
