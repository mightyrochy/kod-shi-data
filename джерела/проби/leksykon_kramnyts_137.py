# -*- coding: utf-8 -*-
"""Рядок 137: слова поля кольору крамниць — у лексикон з вікном із розподілу каталогу. ДО — verify з main
7040096 (git show), ПІСЛЯ — чинний; каталог_повний. Друкує вікна з даних, 828 записів до/після, нові спори, lab.
Запуск: cd джерела && python3 проби/leksykon_kramnyts_137.py"""
import collections as К, math, os, subprocess, sys, types
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed, фід_каталог as FK, фід_збагачення as FZ, фід_розбір as FR, verify as V, colorspace as cs
до_V = types.ModuleType("verify"); до_V.__file__ = V.__file__; до_V.не_колір_крамниці = lambda ч: None
exec(subprocess.run(["git", "show", "7040096:джерела/verify.py"], capture_output=True, text=True, check=True).stdout, до_V.__dict__)
шлях = feed.каталог_на_диску(); сир = {o["id"]: o.get("колір_сирий") for o in FR.читати_yml(шлях)[0]}
FK.V = FZ.V = до_V; до = {r["id"]: r for r in FK._прочитати_каталог(шлях, 0)["каталог"]}
FK.V = FZ.V = V; після = {r["id"]: r for r in FK._прочитати_каталог(шлях, 0)["каталог"]}
н = lambda s: " ".join(str(s or "").lower().split())
слова = {т: ц for т, ц in list(V.СЛОВА_КРАМНИЦЬ_ПОЛЯ.items()) + list(V.СЛОВА_КРАМНИЦЬ_ЛАТИНКОЮ.items())
         if ц in V.ВІКНА_КРАМНИЦЬ or т in ("бургунді", "пломбір")}
пт, сім = К.defaultdict(list), К.defaultdict(К.Counter)
for i, r in до.items():   # однослівне поле кольору, колір з фото (ДО) — вибірка вікна
    г = слова.get(н(сир.get(i)))
    if г and r.get("колір_hex_фото") and r["джерело_кольору"] == "фото":
        г = г if г in V.ВІКНА_КРАМНИЦЬ else н(сир[i]); пт[г].append(cs.lch(cs.hx(r["колір_hex_фото"]))); сім[г][V.сім_я_слова(r["колір_назва_фото"])] += 1
def пц(xs, p): xs = sorted(xs); k = (len(xs) - 1) * p; a = int(k); b = min(a + 1, len(xs) - 1); return xs[a] + (xs[b] - xs[a]) * (k - a)
print("ФАКТ · слово | речей | L* p5/p95 | C* p5/p95 | тон p5/p95 (речей з C*≥10) | сім'я з фото | у лексиконі")
for г, т in sorted(пт.items(), key=lambda kv: -len(kv[1])):
    hs = [h for _, c, h in т if c >= 10]; m = math.degrees(math.atan2(sum(math.sin(math.radians(h)) for h in hs), sum(math.cos(math.radians(h)) for h in hs)))
    д = [((h - m + 180) % 360) - 180 for h in hs]; дуга = tuple(round((m + пц(д, p)) % 360) for p in (.05, .95)) if len(hs) >= 5 else None
    в = (math.floor(пц([x[0] for x in т], .05)), math.ceil(пц([x[0] for x in т], .95)), math.floor(пц([x[1] for x in т], .05)), math.ceil(пц([x[1] for x in т], .95)), дуга)
    ціль = г if г in V.ВІКНА_КРАМНИЦЬ else V.слово_крамниці(г)["ім"]; збіг = V.ЛЕКСИКОН[ціль] == в if г in V.ВІКНА_КРАМНИЦЬ else V.вікно_всередині(в, V.ЛЕКСИКОН[ціль])
    print("   %-10s %3d | %s–%s | %s–%s | %s (%d) | %s | %s %s" % (г, len(т), *в[:4], дуга, len(hs), dict(сім[г].most_common(2)), ціль, "=" if г in V.ВІКНА_КРАМНИЦЬ and збіг else "⊂" if збіг else "✗"))
спір = lambda к: {i for i, r in к.items() if r.get("колір_спір")}; x = [i for i, r in до.items() if r.get("колір_назва_джерело") == "фото" and r.get("колір_назва_крамниці")]
клас, чому = К.Counter(), К.Counter()
for i in x:
    п = після[i]; к = "спір" if п.get("колір_спір") else п["колір_назва_джерело"]; клас[к] += 1
    if к == "фото": з = п["колір_назва_за_чим"]; чому[з[з.index("(") + 1:-1] if "не колір (" in з else "іншої сім'ї" if "сім'ї" in з else "лексикон не знає: " + н(п["колір_назва_крамниці"])] += 1
print("ФАКТ · 828 (крамниця дала слово, назва з фото ДО): %d → %s" % (len(x), dict(клас)))
print("   лишились на фото: %s" % чому.most_common())
нові = спір(після) - спір(до); тс = sum("поріг" in після[i]["колір_спір"]["чому"] for i in нові)
print("ФАКТ · спорів %d → %d: нових %d (та сама сім'я, згода v2 < 0.9: %d; інша сім'я: %d), знято %d" % (len(спір(до)), len(спір(після)), len(нові), тс, len(нові) - тс, len(спір(до) - спір(після))))
print("   найчастіші пари нових (крамниця, фото): %s" % К.Counter((н(до[i]["колір_назва_крамниці"]), до[i]["колір_назва_фото"]) for i in нові).most_common(10))
lab = {i for i in до if до[i]["lab"] != після[i]["lab"]}; зс = спір(до) ^ спір(після)
print("ФАКТ · lab змінився: %d; з них змінили статус спору: %d; решта (спір лишився, змінилось перше кольорове слово поля): %s" % (len(lab), len(lab & зс), sorted(lab - зс)))
