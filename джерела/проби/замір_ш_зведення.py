# -*- coding: utf-8 -*-
"""ЗАМІР-Ш (02.10): на кожен прогін — намір і мета паспорта, схема/основа, і ЧОМУ модель обрала образ (рук 1–2): за наміром чи за зауваженнями. Запуск: <тека з <прогін>/вердикти.txt.gz>."""
import gzip, json, re, sys, glob, collections as K
НАМ = re.compile(r"intent|bold|statement|stand ?out|memorable|expressive|striking|daring|distinct|eye-?catching|focal|wow|impact|personality|character", re.I)
НАГ = re.compile(r"occasion|date|office|register|polished|formal|dress code|evening|party|theat|wedding|work", re.I)
ЗАУ = re.compile(r"blocker|remark|finding|tension|fewest|lightest|mildest|lowest|milder|checks?\b|blandness|excess|problems?|gate|clean", re.I)
дж = lambda с: json.loads(с[с.index("{"):]) if с and "{" in с else {}
ПІДС = K.defaultdict(K.Counter)
for f in sorted(glob.glob(sys.argv[1] + "/*/вердикти.txt.gz")):
    н = f.split("/")[-2]; ж, схема, *_ = н.split("_"); D = json.load(gzip.open(f, "rt", encoding="utf-8")); п = D["прогони"][0]; пас = D["спільне"].get("паспорт", {}); сп = D["спільне"]
    print(f"{н}: намір={пас.get('намір')} мета={пас.get('мета')} база={сп.get('пал_база')} обрана(база/схема)={сп.get('пал_база_обрана')}/{сп.get('пал_схема_обрана')} гілка={сп.get('пал_гілка')}")
    for в in п["вердикти"]:
        if str(в["рука"]) not in "12": continue
        вб = [c for c in в["етапи"]["виклики"] if c["крок"] == "choice"]; why = дж(вб[-1]["відповідь_сира"]).get("why", "") if вб else ""
        кл = "+".join(k for k, р in (("намір", НАМ), ("зауваження", ЗАУ), ("нагода", НАГ)) if р.search(why)) or "інше"
        for гр in ((ж, схема), ("усі", схема)): ПІДС[гр]["образів"] += 1; ПІДС[гр].update(k for k, р in (("згадує намір", НАМ), ("згадує зауваження", ЗАУ), ("згадує нагоду", НАГ)) if р.search(why))
        print(f"   р{в['рука']} схема={в['пал_схема_руки']} ({кл}): {why[:230]}")
print("причина вибору по (жінка, схема):", {k: dict(v) for k, v in sorted(ПІДС.items())})
