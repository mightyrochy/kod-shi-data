# -*- coding: utf-8 -*-
"""ПУЛ-ДОЗА (рядки 2702, 5516, 6971): чи доходить доза пулу до образів — на ЗАПИСАНИХ вердиктах (руки 1–2). Позначки —
поля пулу складання: `branch` ≠ core (межа/розрив) і `below_band` (нижче смуги). По occasion · intent: частка в пулі, у речах
образів складання (10), показу вибору (після ремонту, 5) й обраного — фактом і «навмання» (частка позначених серед речей того
самого `type` у пулі), «≥1» — образів хоч з однією. Далі по intent · полюсу складання: з edge/break і «deliberate» (чи називає
edge). Запуск із кореня: python3 джерела/проби/пул_свобода_доза.py  (без шляхів — усі `аудит/**/вердикти.txt*`)"""
import collections, glob, gzip, json, re, sys
def obj(т):
    с = re.sub(r"^```(json)?", "", str(т or "").strip()).strip()
    try: return json.JSONDecoder().raw_decode(с)[0] if с[:1] == "{" else {}   # перший об'єкт; хвіст після нього — не наш
    except ValueError: return {}
def образи(в): return [о for о in (в.get("outfits") or (в.get("answer") or {}).get("outfits") or []) if isinstance(о, dict)]
def показ(з): return {(о.get("your_outfit") or {}).get("id"): [р.get("n") for р in (о.get("your_outfit") or {}).get("items") or []] for о in з.get("verdict") or []}
бачено, Л, П = set(), collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
for шлях in sys.argv[1:] or glob.glob("аудит/**/вердикти.txt*", recursive=True):
    with (gzip.open if шлях.endswith(".gz") else open)(шлях, "rb") as ф: д = obj(ф.read().decode("utf-8", "replace"))   # давні TSV — {}
    for п in д.get("прогони") or []:
        for в in п.get("вердикти") or []:
            ключ = (д.get("пристрій") or (д.get("спільне") or {}).get("пристрій"), п.get("прогін"), в.get("рука"), в.get("склад"))
            вк = {к.get("крок"): к for к in ((в.get("етапи") or {}).get("виклики") or []) if isinstance(к, dict)}
            if ключ in бачено or str(в.get("рука")) not in "12" or "assembly" not in вк: continue
            бачено.add(ключ); зс = obj((вк["assembly"].get("запит") or {}).get("текст")); пул = зс.get("pool") or []
            if not пул: continue
            сц = "%s · %s" % ((зс.get("case") or {}).get("occasion"), (зс.get("case") or {}).get("intent")); зв = obj((вк.get("choice", {}).get("запит") or {}).get("текст")); вид = показ(зв); об = str(obj(вк.get("choice", {}).get("відповідь_сира")).get("chosen") or "")
            скл = образи(obj(вк["assembly"].get("відповідь_сира"))); за_н = {р.get("n"): р for р in пул}
            стадії = {"скл": [о.get("items") or [] for о in скл], "показ": list(вид.values()), "обр": [вид[об]] if об in вид else []}
            відомо = {"межа/розрив": "branch" in (зс.get("pool_keys") or {}) or any("branch" in р for р in пул), "нижче смуги": any(р.get("below_band") for р in пул)}
            for о in скл if відомо["межа/розрив"] else []:   # «deliberate»: чи пише його образ з річчю edge і чи називає саме її
                ее = [за_н[н] for н in о.get("items") or [] if н in за_н and за_н[н].get("branch") == "edge"]; дл = json.dumps(о.get("deliberate") or [], ensure_ascii=False)
                for c in (П[((зс.get("case") or {}).get("intent"), о.get("pole"))], П[("усі", "крім полюса break" if о.get("pole") != "break" else "break")]): c["о"] += 1; c["edge"] += bool(ее); c["break"] += any(за_н[н].get("branch") == "break" for н in о.get("items") or [] if н in за_н); c["delib з edge" if ее else "delib без edge"] += дл != "[]"; c["називає edge"] += any(р["n"] in дл or (р.get("name") or "~")[:15] in дл for р in ее)
            for мітка, є in (("межа/розрив", lambda р: р.get("branch") not in (None, "core")), ("нижче смуги", lambda р: bool(р.get("below_band")))):
                if not відомо[мітка]: continue   # поля ще не було (below_band — з ВІДСІВ-1, 02.10); усі core при відомому branch — нуль
                тип = collections.defaultdict(list); [тип[р.get("type")].append(є(р)) for р in пул]
                for c in (Л[(сц, мітка)], Л[("УСІ СЦЕНИ", мітка)]):
                    c["зап"] += 1; c["пул"] += len(пул); c["пул+"] += sum(map(є, пул))
                    for ст, оо in стадії.items():
                        for о in оо: рр = [за_н[н] for н in о if н in за_н]; c[ст + "о"] += 1; c[ст + "≥1"] += any(map(є, рр)); c[ст] += len(рр); c[ст + "+"] += sum(map(є, рр)); c[ст + "~"] += sum(sum(тип[р.get("type")]) / len(тип[р.get("type")]) for р in рр)
відс = lambda a, b: "%4.1f" % (100.0 * a / b) if b else "  — "; print("сцена · записів | позначка | пул % | складання % (навмання) ≥1 | показ % (навмання) ≥1 | обраний % (навмання) ≥1")
for (сц, мітка), c in sorted((x for x in Л.items() if x[1]["зап"] >= 4), key=lambda x: (x[0][1], -x[1]["зап"])): print("%s · %d | %s | %s | %s" % (сц, c["зап"], мітка, відс(c["пул+"], c["пул"]), " | ".join("%s (%s) %s" % (відс(c[ст + "+"], c[ст]), відс(c[ст + "~"], c[ст]), відс(c[ст + "≥1"], c[ст + "о"])) for ст in ("скл", "показ", "обр"))))
for (н, по), c in sorted((x for x in П.items() if x[1]["о"] >= 20), key=lambda x: -x[1]["о"]): print("%s · %s: образів %d · з edge %d · з break %d · deliberate: з edge %d (називає її %d), без edge %d з %d" % (н, по, c["о"], c["edge"], c["break"], c["delib з edge"], c["називає edge"], c["delib без edge"], c["о"] - c["edge"]))
