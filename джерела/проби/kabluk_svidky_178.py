# -*- coding: utf-8 -*-
"""Рядок 178: висота каблука з param крамниці проти інших свідків. Каталог_повний. Для кожної пари,
де крамниця дала `каблук_см` (param), шукаються суперечності з: словом назви/категорії/опису/решти
param (A: «без підборів/пласк» при param ≥ 3 без платформи; B: «на підборах/шпилька/танкетка» при param 0;
D: «високий каблук/шпилька» при param ≤ 5 — спірне, не доведене), числом у тексті (C: різниця > 1
см) і класом із фото, коли фото-читач його дав (E: «високий» при ≤ 5, «низький» при ≥ 7). Друкує
лічбу за крамницями й приклади. Запуск із `джерела`: PYTHONPATH=. python3 проби/kabluk_svidky_178.py"""
import json, re, sys, collections; sys.path.insert(0, ".")
import feed as Ф, bridge as B, фід_взуття as ФВ
offers, _ = Ф.читати_yml(Ф.каталог_на_диску())
json.loads(B.виклик("запити", json.dumps(json.load(open("стенд_вх.json", encoding="utf-8")), ensure_ascii=False)))
кат = {c["id"]: c for c in B.каталог_останнього_пакета()}
ПЛАСК, ПІДБ = ("без підбор", "без каблук", "на пласк", "на плоск"), ("на підбор", "на каблук", "шпильк", "танкет")
ВИС = re.compile(r"шпильк|стилет|stiletto|(?<![а-яіїєґ])висок\w*\s+(підбор|каблук)|на високих")
лік, прикл, всього = collections.defaultdict(collections.Counter), collections.defaultdict(list), collections.Counter()
for o in offers:
    п = o.get("параметри") or {}
    h = ФВ._число_см(п.get("каблук_см"))
    к = кат.get(o["id"]) or {}
    if h is None or к.get("слот") != "взуття":
        continue
    всього[o["id"].split("@")[1]] += 1
    текст = " ".join([str(o.get("назва") or ""), str(o.get("опис") or "")]
                     + ["%s %s" % (k, v) for k, v in п.items() if k not in ("каблук_см", "~висота підборів")]).lower()
    м = ФВ._ПРО_КАБЛУК.search(текст)
    кл = []
    if h >= 3 and any(x in текст for x in ПЛАСК) and "платформ" not in текст: кл.append("A")
    if h == 0 and any(x in текст for x in ПІДБ): кл.append("B")
    if м and abs(float(м.group(1).replace(",", ".")) - h) > 1: кл.append("C")
    if h <= 5 and ВИС.search(текст): кл.append("D")
    if (к.get("каблук_висота") == "високий" and h <= 5) or (к.get("каблук_висота") == "низький" and h >= 7): кл.append("E")
    for x in кл:
        лік[x][o["id"].split("@")[1]] += 1
        прикл[x].append("%s «%s» param %.1f" % (o["id"], str(o.get("назва"))[:40], h))
print("пар із param каблук_см: %d (%s)" % (sum(всього.values()), dict(всього.most_common(8))))
for x in "ABCDE":
    print("%s: %d · %s\n   %s" % (x, sum(лік[x].values()), dict(лік[x].most_common(6)), "; ".join(прикл[x][:6])))
print("ж-09123:", [x for x in "ABCDE" if any(s.startswith("ж-09123@") for s in прикл[x])] or "жоден свідок не суперечить param")
