# -*- coding: utf-8 -*-
"""Вхід опису про обставини її дня ДО → ПІСЛЯ на записаних прогонах: «як людина» 4 (с8, с5) і нічний 15.11 (наряд
Е2-опора-пояснення-обставини).

ДО — що реально пішло в модель опису: «day» і «palette» дроту ОПИС з обмінів прогону, і визначення заяви
`sole_grip_unknown_ice` з бази гілки d1b8d542. ПІСЛЯ — той самий день через складач гілки: походження кожного ключа
(`сценарій.звідки_дня`) з картки, відновленої з `case.sources` того самого виклику (там стоїть те саме
`паспорт_поля.походження_поля` паспорта), і відбір `дріт_моделі.день_її_слів`; палітра — `дріт_моделі.палітра_опису` на
металі дроту ДО і джерелі підтону (`axes.source_hue`) з пакета складання того самого прогону. Повтор входу, не
відповідей: відповіді моделі правки не міряють. Запуск з кореня: python3 аудит/проби/Е2-опора-пояснення-обставини/обставини.py"""
import collections, glob, gzip, json, os, re, subprocess, sys
sys.path.insert(0, "джерела")
import дріт_моделі as Д, сценарій as С, внутрішня_мова as ВМ

ЗВОРОТНО = {v: к for к, v in Д.ПОЛЯ_ВИПАДКУ.items()}
МЕТАЛ_ЗВОРОТНО = {"gold": "золото", "silver": "срібло", "gold_and_silver": "і золото, і срібло"}


def тексти(запит):
    try:
        з = json.loads(запит) if isinstance(запит, str) else запит
    except ValueError:
        return []
    вих = []
    for m in з.get("messages", []):
        c = m.get("content")
        for b in (c if isinstance(c, list) else [dict(type="text", text=c)]):
            if isinstance(b, dict) and b.get("type") == "text":
                вих.append(b["text"])
    return вих


def дріт_опису(т):
    і = т.find('"outfit": {"id"')
    if і < 0 or "about_items" not in т:
        return None
    try:
        return json.JSONDecoder().raw_decode("{" + т[і:])[0]
    except ValueError:
        return None


def записи(шлях):
    if шлях.endswith(".gz"):
        for р in gzip.open(шлях, "rt"):
            yield json.loads(р)
    else:
        for ф in sorted(glob.glob(шлях + "/*.json")):
            yield json.load(open(ф))


def картка_з_джерел(джерела):
    """`case.sources` дроту → картка паспорта {поле: {джерело, уривок}} (ключ англійський → поле паспорта)."""
    return {"картка_запиту": {ЗВОРОТНО.get(к, к): {"джерело": з.get("kind"), "уривок": з.get("quote")}
                              for к, з in (джерела or {}).items() if isinstance(з, dict)}}


ШЛЯХИ = [("4", ш) for ш in sorted(glob.glob("аудит/проби/живий-як-людина-4/стенд/службове/с[58]_*/обміни.jsonl.gz"))] + \
        [("н", т + "/VIDPOVIDI/обмін") for т in sorted(glob.glob("аудит/проби/Е1-нічний-живий-20261115/ж*"))]
л = collections.Counter()
зняті = collections.Counter()
рядки = []
for прогін, шлях in ШЛЯХИ:
    сцена = шлях.split("/")[-2] if шлях.endswith(".gz") else шлях.split("/")[-3]
    джерело_hue = None
    виклики = []
    for і, з in enumerate(записи(шлях), 1):
        тт = тексти(з.get("запит"))
        for код, що in (("sole_grip_unknown_ice", "лід"), ("outer_composition_unknown_salt", "сіль")):
            if any(код in т for т in тт):
                л["викликів із заявою про %s (%s)" % (що, код)] += 1
                л["  %s: %s" % (що, сцена)] += 1
        for т in тт:
            м = re.search(r'source_hue\\*"\s*:\s*\\*"(\w+)', т)
            if м and not джерело_hue:
                джерело_hue = м.group(1)
        д = next((x for x in map(дріт_опису, тт) if x), None)
        if д:
            виклики.append((і, д))
    for і, д in виклики:
        л["викликів опису"] += 1
        день = д.get("day") or {}
        пасп = картка_з_джерел((д.get("case") or {}).get("sources"))
        звідки = С.звідки_дня(день, {}, пасп)
        після = Д.день_її_слів(dict(день, provenance=звідки)) or {}
        до_кл = [к for к in день if к not in ("season_source", "unknown")]
        л["фактів дня ДО"] += len(до_кл)
        л["фактів дня ПІСЛЯ"] += len(після)
        for к in до_кл:
            if к not in після:
                зняті["%s (%s)" % (к, звідки.get(к))] += 1
        пал_до = д.get("palette") or {}
        пал_після = Д.палітра_опису({"метал": МЕТАЛ_ЗВОРОТНО.get(пал_до.get("metal")),
                                     "axes": {"source_hue": джерело_hue}}) or {}
        л["палітра з металом ДО"] += 1 if пал_до.get("metal") else 0
        л["палітра з металом ПІСЛЯ"] += 1 if пал_після.get("metal") else 0
        л["палітра з найдальшими чи поєднаннями ДО"] += 1 if (пал_до.get("farthest") or пал_до.get("combinations")) else 0
        рядки.append("%s %-34s виклик %2d | день ДО %s | ПІСЛЯ %s | метал %s → %s (підтон: %s)" % (
            прогін, сцена, і, ",".join(до_кл), ",".join(після) or "—", пал_до.get("metal") or "—",
            пал_після.get("metal") or "—", джерело_hue or "?"))

print("\n".join(рядки))
print()
for к, v in л.items():
    print("%-46s %d" % (к, v))
print("знято з дня опису (ключ, походження):", ", ".join("%s ×%d" % кв for кв in зняті.most_common()))
до = subprocess.run(["git", "show", "d1b8d542fb76936cfda19760f093bca32ca8a071:джерела/внутрішня_мова.py"], capture_output=True, text=True).stdout
for код in ("sole_grip_unknown_ice", "outer_composition_unknown_salt"):
    м = re.search(r'"%s": ((?:"[^"]*"\s*)+),' % код, до)
    print(код, "ДО:", re.sub(r'"\s*"', "", м.group(1)).strip().strip('"') if м else "?")
    print(код, "ПІСЛЯ:", ВМ.ЗАЯВИ[код])
