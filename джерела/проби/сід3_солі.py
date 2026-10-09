# -*- coding: utf-8 -*-
"""СІД-3 (рядок 760): солі перемішування поза порядок_запиту/уважний_вибір. Знімає КОЖЕН рядок сіда
`random.Random(…)` за повний прохід `запити` (3 сіди) і хеш пулу: до/після правки збігаються = порядок той самий.
Прогін: PYTHONPATH=. python3 проби/сід3_солі.py"""
import re, json, hashlib, gzip, shutil, tempfile, os, random, collections
import bridge as B
ЗНЯТО = collections.Counter(); _R = random.Random
class Р(_R):
    def __init__(я, x=None): ЗНЯТО[x if isinstance(x, str) else ""] += 1; super().__init__(x)
random.Random = Р
тека = tempfile.mkdtemp(prefix="сід3_"); шлях = os.path.join(тека, "к.xml")
with gzip.open("../каталог_повний.xml.gz", "rb") as г, open(шлях, "wb") as в: shutil.copyfileobj(г, в)
хеші = []
for сід in (4242, 7, 91):
    вх = dict(json.load(open("стенд_вх.json")), каталог=шлях, сід=сід)
    вих = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
    хеші.append(hashlib.sha256(json.dumps(вих["порядок_рук"], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12])
shutil.rmtree(тека, ignore_errors=True)
ключі = sorted(ЗНЯТО.items())
import ast, семплер
к = 0
for ф in ("композитор_слоти.py", "семплер.py", "пакет_моделі.py", "різноманітність_пулу.py"):
    for в in ast.walk(ast.parse(open(ф, encoding="utf-8").read())):
        if isinstance(в, ast.Call) and getattr(в.func, "attr", getattr(в.func, "id", "")) in ("Random", "_перемішати"):
            к += sum(1 for x in ast.walk(в) if isinstance(x, ast.Constant) and isinstance(x.value, str) and re.search("[а-яіїєґ]", x.value, re.I))
колишні = ["група", "доза", "цілком", "страти", "магазини", "межа", "розрив", "фолбек", "добір", "дуга", "словами", "бажання"]
print("порядок_рук (3 сіди):", хеші)
print("рядків сіда: %d різних, %d викликів · хеш %s" % (len(ключі), sum(ЗНЯТО.values()), hashlib.sha256(repr(ключі).encode()).hexdigest()[:12]))
print("кириличних літералів у солях цих файлів: %d · солі = колишні слова: %s" % (к, [семплер.сіль(c) for c in ("group","dose","whole","strata","shops","boundary","break","fallback","pick","arc","wish_words","wish")] == колишні))
