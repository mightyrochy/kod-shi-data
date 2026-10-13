# -*- coding: utf-8 -*-
"""ПОМІТНІСТЬ-1 (02.10): що з вечора нагоди дійшло до складання і що обрано. Запуск: <тека з <прогін>/вердикти.txt[.gz]> [фільтр].
Друкує на прогін: смугу паспорта, ціль K-KOH-05 суду (має = смузі, рядок 901), `evening_outing` у промпті, суконь у пулі / знято фото-балом;
на руку 1–2: обраний образ — тип, каблук, тканина, назва; позначки: ВЕЧ (шпилька/човники/туфлі, атлас/шовк/оксамит/мереживо/метал),
ДЕНЬ (лофери, балетки, вовна/овчина на взутті, солом'яна сумка, шопер)."""
import gzip, json, glob, os, re, sys, collections as K
ТЕКА, Ф = sys.argv[1], re.compile(sys.argv[2] if len(sys.argv) > 2 else ".")
ВЕЧ_Т, ДЕНЬ_Т = {"pumps", "dress_shoes", "heeled_sandals", "clutch"}, {"loafers", "ballet_flats", "moccasins", "tote", "sneakers", "plimsolls"}
ВЕЧ_Ф = {"satin", "silk", "velvet", "lace", "guipure", "atlas", "patent_leather", "chiffon"}
ДЕНЬ_С, ВЕЧ_С = re.compile(r"овчин|вовнян|солом|шопер|хутр", re.I), re.compile(r"сатин|шовк|оксамит|мереж|атлас|паєт|лак|шпильк|човник", re.I)
for ш in sorted({os.path.dirname(x): x for x in sorted(glob.glob(os.path.join(ТЕКА, "*", "вердикти.txt*")))}.values()):
    if not Ф.search(ш): continue
    d = json.load(gzip.open(ш, "rt") if ш.endswith(".gz") else open(ш))
    п = d["спільне"]["паспорт"]; т = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    цілі = K.Counter(tuple(x) for x in re.findall(r'outfit_level_off_occasion","values":\{[^}]*"target":\[([\d.]+),([\d.]+)\]', т))
    print("==", ш.split("/")[-2], "| смуга", п.get("ошатність"), "| година", п.get("година"), "| намір", п["виміри"].get("intent"),
          "| K-KOH-05 цілі", dict(цілі) or "—")
    for в in d["прогони"][0]["вердикти"]:
        if str(в["рука"]) not in "12": continue
        кр = {c["крок"]: c for c in в["етапи"]["виклики"]}
        а = json.loads(кр["assembly"]["запит"]["текст"]); пул = {р.get("name"): р for р in а["pool"]}
        сук = (а.get("kind_notes", {}).get("dress") or {}).get("statements") or [{}]
        фото = next((x["kind_cut_to_photo_formality"] for x in сук if isinstance(x, dict) and "kind_cut_to_photo_formality" in x), {})
        print("  рука", в["рука"], "| evening_outing" if "evening_outing" in а["style_rules"] else "| — вечора", "| day_outing" if "day_outing" in а["style_rules"] else "",
              "| суконь у пулі", sum(1 for р in а["pool"] if "dress" in str(р.get("type")) and р.get("type") != "dress_shoes"),
              "| сукні фото: смуга", фото.get("band"), "знято", фото.get("removed"), "з них ошатних", фото.get("too_dressy"))
        for р in в.get("речі_образу") or []:
            x = пул.get(р.get("назва"), {}); тк = set(x.get("fabric") if isinstance(x.get("fabric"), list) else [x.get("fabric")])
            мітка = "ВЕЧ" if (x.get("type") in ВЕЧ_Т or тк & ВЕЧ_Ф or x.get("color") in ("golden", "silvery") or ВЕЧ_С.search(р.get("назва") or "")) else ("ДЕНЬ" if (x.get("type") in ДЕНЬ_Т or ДЕНЬ_С.search(р.get("назва") or "")) else "")
            print("     %-4s %-14s %-6s %-22s %s" % (мітка, x.get("type"), x.get("heel", ""), ",".join(sorted(map(str, тк)))[:22], (р.get("назва") or x.get("name") or "?")[:60]))
