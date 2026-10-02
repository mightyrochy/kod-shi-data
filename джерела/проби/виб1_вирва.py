"""ВИБ-1: вирва сміливих ідей рук 1–2 на живих файлах — раунд 1 → фінальні 5 → обраний — і чи спирається
«чому» вибору на лічбу зауважень. Аргумент — теки прогонів (типово per_492 і zhp_a). Друкує факт."""
import gzip, glob, json, re, sys
ЛІЧБА = re.compile(r"fewest|fewer|milde?st|milder|light(er|est)? remarks|only light|lowest|heavier|"
                   r"no (structural )?blockers|without blockers|passes every|no failed|clears? the", re.I)
СМІЛИВІ = {"free", "break"}
def js(t):
    try: return json.loads(t[t.index("{"):t.rindex("}") + 1])
    except ValueError: return {}
def кроки_файлу(f):          # per_492: файл вердиктів показу → [(рука, {крок: (запит, відповідь)})]
    for п in json.load(gzip.open(f))["прогони"]:
        for в in п["вердикти"]:
            if в["рука"] in "12":
                yield в["рука"], {c["крок"]: (c["запит"].get("текст", ""), c.get("відповідь_сира") or "")
                                 for c in в["етапи"]["виклики"]}
def кроки_вікл(д):           # сирі виклики стенда (zhp_a): складання, ремонт, вибір — парами в порядку номерів файлів
    ф = lambda шлях: (lambda т: tuple(т.split("── ВІДПОВІДЬ", 1)) if "── ВІДПОВІДЬ" in т else (т, ""))(
        gzip.open(шлях, "rt").read())
    кл = lambda н: [ф(x) for x in sorted(glob.glob(д + "вікл/*_%s*" % н))]
    for р, к in enumerate(zip(кл("ПАКЕТ_V1_ОБРАЗИ"), кл("ВЕРДИКТ_V1_ОБРАЗИ"), кл("ВЕРДИКТ_V1_ВИБІР")), 1):
        yield str(р), dict(zip(("assembly", "repair", "choice"), к))
підсумок = {"1": [0, 0, 0, 0, 0], "2": [0, 0, 0, 0, 0]}   # рук, сміливих у р1, у фіналі, обрано, «лічба» в чому
for тека in sys.argv[1:] or ["аудит/перевірки/per_492", "аудит/перевірки/zhp_a"]:
    for д in sorted(glob.glob(тека + "/*/")):
        дж = glob.glob(д + "вердикти.txt.gz")
        for р, к in (кроки_файлу(дж[0]) if дж else кроки_вікл(д) if glob.glob(д + "вікл") else ()):
            if "choice" not in к: continue
            р1 = js(к["assembly"][1]).get("outfits", []); ф5 = js(к["repair"][1]).get("outfits", [])
            вб = js(к["choice"][1]); за = {o["your_outfit"].get("id"): o["your_outfit"].get("caption")
                                          for o in js(к["choice"][0]).get("verdict", [])}
            підп = за.get(вб.get("chosen")); полюс = next((o.get("pole") for o in ф5 if o.get("caption") == підп), "?")
            сміл = lambda оо: sum(o.get("pole") in СМІЛИВІ for o in оо); ліч = bool(ЛІЧБА.search(вб.get("why", "")))
            for i, x in enumerate((1, сміл(р1), сміл(ф5), полюс in СМІЛИВІ, ліч)): підсумок[р][i] += x
            print("%-28s р%s  р1 %2d (сміл %d) → фінал %d (сміл %d) → обрано %-14s «%s»%s" % (
                д.split("/")[-2], р, len(р1), сміл(р1), len(ф5), сміл(ф5), полюс, (підп or "?")[:28],
                "  ЛІЧБА: " + ЛІЧБА.search(вб["why"]).group(0) if ліч else ""))
for р, (н, а, б, в, г) in підсумок.items():
    print("рука %s: прогонів %d · сміливих ідей р1 %d → у фіналі %d → обрано %d · «чому» на лічбі зауважень %d/%d"
          % (р, н, а, б, в, г, н))
