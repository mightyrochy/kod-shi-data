# -*- coding: utf-8 -*-
"""Рядки 4310/4311 (МОВА-КОДИ-7) на повному каталозі: `бракує` записів «без входу» кольору фразою чи
кодом (будь-де у виході суду); питання — вага `вага_питання` за правилом і скільки «вимкнених осей»
відсіяв `_питання_або_нуль`.
Сцени — `стенд_знімок.СЦЕНАРІЇ`, образи — перші 2 кандидати верху/низу/взуття/сумки (16 на сцену).
Прогін: python3 проби/без_входу_кодом_4310.py — однаково на базі й на гілці, різниця друку і є до/після."""
import sys, os, json, re, itertools, collections
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import стенд_знімок as СЗ, bridge as B, pipeline as PL, composer as КМ, fit as ПС, colorspace as cs
вх = json.load(open("стенд_вх.json"))
T = ПС.тіло(float(вх["зріст"]), {k: float(v) for k, v in вх["обхвати"].items()})
F = cs.features(cs.hx(вх["шкіра"]), cs.hx(вх["волосся"][0]), cs.hx(вх["очі"]))
бр, форми, вага, вісь, образів = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter(), 0
for назва, сцен in СЗ.СЦЕНАРІЇ.items():
    r = json.loads(B.виклик("запити", json.dumps(dict(вх, сценарій=сцен, випадок=назва), ensure_ascii=False)))
    кат, к = {x.get("id"): x for x in B.каталог_останнього_пакета()}, r.get("кандидати") or {}
    слоти = [[dict(кат.get(c.get("id")) or c, слот=с) for c in (к.get(с) or [])[:2]] for с in ("верх", "низ", "взуття", "сумка")]
    for набір in itertools.product(*[с for с in слоти if с]):
        образів += 1
        вих = PL.перевірити_образ(F, [КМ._у_річ(dict(c), c["слот"], T) for c in набір], тіло=T, **сцен)
        стек = [вих]
        while стек:                                   # `бракує` будь-де у виході: чеклісти, записи, стани
            о = стек.pop()
            стек += list(о.values()) if isinstance(о, dict) else list(о) if isinstance(о, (list, tuple)) else []
            б = о.get("бракує") if isinstance(о, dict) else None
            if isinstance(б, str) and re.search("колір_не_вимір|джерело_площі|вимір_hex_шум|вимір (кольору|світлоти) з фото", б):
                бр["фразою (« або центр вікна)" if re.search("«колір_не_вимір»|центр вікна слова|«джерело_площі»", б) else "кодом"] += 1
                форми[re.sub(r"\[[^\]]*\]|\d+(\.\d+)?|«[^»]*»|ж-\d+@[\w.\-]+", "·", б)[:90]] += 1
        for _, z in СЗ._знахідки_рекурсивно(вих):
            if PL._питання_або_нуль(z):
                вага[(z.get("правило"), PL.вага_питання(z))] += 1
                вісь[z.get("правило")] += (z.get("сила") != "питання" and float(z.get("сила_нп") or 0) > 0)
print("образів %d · `бракує` з полем кольору чи площі: %s" % (образів, dict(бр)))
print("форм `бракує` %d:" % len(форми))
for ф, n in форми.most_common(8):
    print("  %4d  %s" % (n, ф))
print("питання (правило, вага): " + ", ".join("%s=%d" % ("%s·%d" % k, n) for k, n in sorted(вага.items())))
print("вимкнена вісь із силою >0, відсіяна з зауважень: %s" % {k: n for k, n in вісь.items() if n})
