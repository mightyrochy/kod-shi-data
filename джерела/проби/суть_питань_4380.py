# -*- coding: utf-8 -*-
"""4380: суть фактичної сім'ї питань на 96 образах каталогу; коди, стани й модельні визначення."""
import sys, os, json, re, itertools, collections, hashlib
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import стенд_знімок as СЗ, bridge as Б, pipeline as П, composer as К, fit as Т, colorspace as Ц
import внутрішня_мова as М
вх = json.load(open("стенд_вх.json"))
тіло = Т.тіло(float(вх["зріст"]), {к: float(в) for к, в in вх["обхвати"].items()})
колір = Ц.features(Ц.hx(вх["шкіра"]), Ц.hx(вх["волосся"][0]), Ц.hx(вх["очі"]))
питання, стани, образів, коди = [], collections.Counter(), 0, set()
for назва, сцена in СЗ.СЦЕНАРІЇ.items():
    вих = json.loads(Б.виклик("запити", json.dumps(dict(вх, сценарій=сцена, випадок=назва), ensure_ascii=False)))
    каталог = Б.каталог_останнього_пакета(); індекс = {р.get("id"): р for р in каталог}
    кандидати = вих.get("кандидати") or {}
    слоти = [[dict(індекс.get(р.get("id")) or р, слот=с) for р in (кандидати.get(с) or [])[:2]]
             for с in ("верх", "низ", "взуття", "сумка")]
    for набір in itertools.product(*[с for с in слоти if с]):
        образів += 1
        суд = П.перевірити_образ(колір, [К._у_річ(dict(р), р["слот"], тіло) for р in набір], тіло=тіло, **сцена)
        for _, з in СЗ._знахідки_рекурсивно(суд):
            if not П._питання_або_нуль(з): continue
            питання.append(з)
            стани[(з.get("правило"), з.get("сила"), з.get("регістр"), з.get("сила_нп"))] += 1
            коди.update(з.get("code") for з in (з.get("заяви") or []) if isinstance(з, dict))
фрази = [з for з in питання if re.search(r"[а-яіїєґ]{3,}", re.sub(r"\[[^\]]*\]", "", з.get("суть") or ""), re.I)]
print("каталог %d · SHA256 %s" % (len(каталог), hashlib.sha256(json.dumps(каталог, ensure_ascii=False, sort_keys=True).encode()).hexdigest()))
print("образів %d · питань %d · правил %d · фраз суті %d · визначень відсутніх %d" %
      (образів, len(питання), len({з.get("правило") for з in питання}), len(фрази), len(коди - set(М.ЗАЯВИ))))
print("стани: " + repr(sorted(стани.items(), key=str)))
print("фрази за правилом: " + repr(collections.Counter(з.get("правило") for з in фрази)))
