# -*- coding: utf-8 -*-
"""В-1: чи тримається вибір моделі, коли той самий перелік прийшов в ІНШОМУ порядку. Пул руки 1 сцени стенда;
способи перемикача `вибір`: «список» (складання з усього пулу), «оцінка» (що «fits»), «турнір» (переможці груп) —
кожен двома сідами порядку (у турнірі сід ділить і групи). Друкує збіг обраного (Жаккар), частку обраних першими й у
першій третині свого переліку проти рівного шансу, виклики й секунди. Модель: MODEL=<ід> (+ MODEL_URL, типово LM Studio
http://127.0.0.1:1234/v1; MODEL_TEMP; THINK=1) — живий замір на ноутбуці; без MODEL — заглушка, що бере ЗГОРИ.
Прогін: python3 проби/вибір_стабільність.py [список,оцінка,турнір]    (заглушка ~1.5 хв)"""
import json, os, sys, time, urllib.request
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП, протокол as ПР, порядок_запиту as ПЗ, уважний_вибір as УВ
B.виклик("запити", json.dumps(dict(json.load(open("стенд_вх.json", encoding="utf-8")), сід=7, каталог=Ф.каталог_на_диску("каталог_повний.xml")), ensure_ascii=False))
пак, лічба, Е = next(p for p in МП._КЕШ_ПАКЕТА.values() if p.get("кандидати")), [0], os.environ   # перший — рука 1
def заглушка(об, з):
    if з == "ОЦІНКИ_V1": return {"ratings": {x["n"]: ("fits" if і < len(р) // 2 else "colour") for р in об["items"].values() for і, x in enumerate(р)}}
    if з == "ТУРНІР_V1": return {"winners": {г: [x["n"] for x in р[:2]] for г, р in об["groups"].items()}}
    return {"образи": [{"ід": "о%d" % k, "речі": [р[k % min(3, len(р))]["н"] for р in об["пул"].values()]} for k in (1, 2, 3)]}
def модель(т):
    лічба[0] += 1; об = json.loads(т); з = (об.get("завдання") or об.get("task") or {})
    в = {"ITEM_RATINGS_V1": "ОЦІНКИ_V1", "TOURNAMENT_V1": "ТУРНІР_V1"}.get(з.get("answer"), з.get("відповідь") or з.get("answer"))
    if not Е.get("MODEL"): return json.dumps(dict({"version" if в in ("ОЦІНКИ_V1", "ТУРНІР_V1") else "версія": "1"}, **заглушка(об, в)))
    тіло = dict(model=Е["MODEL"], messages=[dict(role="user", content=т)], max_tokens=4000, **({"temperature": float(Е["MODEL_TEMP"])}
                if "MODEL_TEMP" in Е else {}), **({} if Е.get("THINK") else {"reasoning_effort": "none"}))
    з = urllib.request.Request(Е.get("MODEL_URL", "http://127.0.0.1:1234/v1").rstrip("/") + "/chat/completions",
                               json.dumps(тіло).encode("utf-8"), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(з, timeout=1800))["choices"][0]["message"]["content"] or ""
def вибір(спосіб, сід):
    if спосіб != "список": return УВ.прогнати(спосіб, пак, модель, сід)[1]
    пакет = dict(пак["пакет"], пул=ПЗ.перемішати_слоти(пак["пакет"]["пул"], сід))
    місця = {x["н"]: (і, len(р)) for р in пакет["пул"].values() for і, x in enumerate(р)}
    об = ПР.розбір_за_схемою(модель(json.dumps(пакет, ensure_ascii=False)), "ОБРАЗИ_V1")[0] or {}
    return [(н,) + місця[н] for о in (об.get("образи") or []) for н in {УВ.ключ_н(x) for x in (о.get("речі") or [])} if н in місця]
print("модель: %s · пул руки 1: %d речей у %d слотах" % (Е.get("MODEL") or "заглушка (бере згори)", sum(map(len, пак["пакет"]["пул"].values())), len(пак["пакет"]["пул"])))
for спосіб in (sys.argv[1].split(",") if len(sys.argv) > 1 else УВ.СПОСОБИ):
    лічба[0], поч = 0, time.time()
    а, б = вибір(спосіб, 11), вибір(спосіб, 29)
    А, Б, усі = {x[0] for x in а}, {x[0] for x in б}, а + б
    ч = lambda умова: 100.0 * sum(1 for _, і, L in усі if умова(і, L)) / max(len(усі), 1)
    print("%-7s обрано %3d і %3d · збіг (Жаккар) %.2f · першою %3.0f %% (рівний шанс %2.0f %%) · у першій третині %3.0f %% (33 %%) · викликів %d, %.0f с"
          % (спосіб, len(А), len(Б), len(А & Б) / max(len(А | Б), 1), ч(lambda і, L: і == 0),
             100.0 * sum(1.0 / L for _, _, L in усі) / max(len(усі), 1), ч(lambda і, L: і < L / 3.0), лічба[0], time.time() - поч))
