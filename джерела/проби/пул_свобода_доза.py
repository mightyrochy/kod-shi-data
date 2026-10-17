# -*- coding: utf-8 -*-
"""ПУЛ-ДОЗА (рядки 2702, 5516): чи доходить доза пулу до образів — на ЗАПИСАНИХ вердиктах (руки 1–2). Позначки речі —
поля пулу складання: `branch` ≠ core (межа/розрив) і `below_band` (нижче смуги, ВІДСІВ-1). По сцені (occasion · intent):
частка позначених у пулі; у речах образів складання (10), показу вибору (після ремонту, 5) й обраного — фактом і
«навмання» (сума частки позначених серед речей того самого `type` у пулі); «≥1» — частка образів хоч з однією такою.
Запуск із кореня: python3 джерела/проби/пул_свобода_доза.py  (без шляхів — усі `аудит/**/вердикти.txt*`)"""
import collections, glob, gzip, json, re, sys
def obj(т):
    с = re.sub(r"^```(json)?", "", str(т or "").strip()).strip()
    try: return json.JSONDecoder().raw_decode(с)[0] if с[:1] == "{" else {}   # перший об'єкт; хвіст після нього — не наш
    except ValueError: return {}
def образи(в): return [о.get("items") or [] for о in (в.get("outfits") or (в.get("answer") or {}).get("outfits") or []) if isinstance(о, dict)]
def показ(з): return {(о.get("your_outfit") or {}).get("id"): [р.get("n") for р in (о.get("your_outfit") or {}).get("items") or []] for о in з.get("verdict") or []}
бачено, Л = set(), collections.defaultdict(collections.Counter)
for шлях in sys.argv[1:] or glob.glob("аудит/**/вердикти.txt*", recursive=True):
    with (gzip.open if шлях.endswith(".gz") else open)(шлях, "rb") as ф: д = obj(ф.read().decode("utf-8", "replace"))   # давні TSV — {}
    for п in д.get("прогони") or []:
        for в in п.get("вердикти") or []:
            ключ = (д.get("пристрій") or (д.get("спільне") or {}).get("пристрій"), п.get("прогін"), в.get("рука"), в.get("склад"))
            вк = {к.get("крок"): к for к in ((в.get("етапи") or {}).get("виклики") or []) if isinstance(к, dict)}
            if ключ in бачено or str(в.get("рука")) not in "12" or "assembly" not in вк: continue
            бачено.add(ключ); зс = obj((вк["assembly"].get("запит") or {}).get("текст")); пул = зс.get("pool") or []
            if not пул: continue
            сц = "%s · %s" % ((зс.get("case") or {}).get("occasion"), (зс.get("case") or {}).get("intent"))
            зв = obj((вк.get("choice", {}).get("запит") or {}).get("текст")); вид = показ(зв); об = str(obj(вк.get("choice", {}).get("відповідь_сира")).get("chosen") or "")
            стадії = {"скл": образи(obj(вк["assembly"].get("відповідь_сира"))), "показ": list(вид.values()), "обр": [вид[об]] if об in вид else []}
            for мітка, є in (("межа/розрив", lambda р: р.get("branch") not in (None, "core")), ("нижче смуги", lambda р: bool(р.get("below_band")))):
                за_н = {р.get("n"): р for р in пул}; тип = collections.defaultdict(list)
                for р in пул: тип[р.get("type")].append(є(р))
                if not any(map(є, пул)): continue   # позначки ще не було (below_band — з ВІДСІВ-1, 02.10)
                for c in (Л[(сц, мітка)], Л[("УСІ СЦЕНИ", мітка)]):
                    c["зап"] += 1; c["пул"] += len(пул); c["пул+"] += sum(map(є, пул))
                    for ст, оо in стадії.items():
                        for о in оо:
                            рр = [за_н[н] for н in о if н in за_н]; c[ст + "о"] += 1; c[ст + "≥1"] += any(map(є, рр))
                            c[ст] += len(рр); c[ст + "+"] += sum(map(є, рр)); c[ст + "~"] += sum(sum(тип[р.get("type")]) / len(тип[р.get("type")]) for р in рр)
відс = lambda a, b: "%4.1f" % (100.0 * a / b) if b else "  — "
print("сцена · записів | позначка | пул % | складання % (навмання) ≥1 | показ % (навмання) ≥1 | обраний % (навмання) ≥1")
for (сц, мітка), c in sorted(Л.items(), key=lambda x: (x[0][1], -x[1]["зап"])):
    if c["зап"] >= 4: print("%s · %d | %s | %s | %s" % (сц, c["зап"], мітка, відс(c["пул+"], c["пул"]), " | ".join("%s (%s) %s" % (відс(c[ст + "+"], c[ст]), відс(c[ст + "~"], c[ст]), відс(c[ст + "≥1"], c[ст + "о"])) for ст in ("скл", "показ", "обр"))))
