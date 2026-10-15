"""Рядок 5500 (власник 15.10: «ловити поломки мають тестувальниці»): чи вимкнене правило руки 2 дало ЗЛАМАНЕ МІСЦЕ на картці
(тінь суду руки 2 проти знахідок того самого правила в руці 1; різні речі в слотах правила) і, для людських вердиктів (не «Проба
РВ-6»), чи скаржились на аспект правила (`причини`, reasons/about_items dislike, «замінити» в слоті) у руці 2 і в руці 1 як базі.
Мапа аспект·слоти — тимчасова (кандидат у `правило_руки2.ПЕРЕЛІК`). Запуск: python3 джерела/проби/рука2_зламане_місце.py [--git|файли]"""
import collections, gzip, json, os, re, subprocess, sys
КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(КОРІНЬ, "джерела")); import правило_руки2 as ПР2
def файли():   # як `рука2_повтор_сукні.py`: --git — усі версії файлів вердиктів усіх гілок
    if sys.argv[1:] == ["--git"]:
        git = lambda *а: subprocess.run(("git", "-C", КОРІНЬ) + а, capture_output=True).stdout; рр = git("log", "--all", "--format=", "--raw", "--no-abbrev", "--diff-filter=AM", "--no-renames", "--", ":(glob)**/вердикти*", ":(glob)**/verdykty*").decode().splitlines()
        yield from (git("cat-file", "blob", б) for б in sorted({р.split()[3] for р in рр if р.startswith(":")})); return
    for ш in sys.argv[1:] or [os.path.join(КОРІНЬ, "аудит", "тести")]:
        for к, _, фф in (os.walk(ш) if os.path.isdir(ш) else [("", 0, [ш])]):
            yield from (open(os.path.join(к, ф), "rb").read() for ф in фф if "verdykty" in ф or "вердикти" in ф)
речі = lambda в: {r["id"]: r.get("слот") for r in в.get("речі_образу") or [] if isinstance(r, dict)}; пари, гр = {}, collections.defaultdict(collections.Counter)
for дані in файли():
    try: д = json.loads(gzip.decompress(дані) if дані[:2] == b"\x1f\x8b" else дані)
    except ValueError: continue
    for п in (д.get("прогони") or []) if isinstance(д, dict) else []:
        вв = {str(в.get("рука")): в for в in п.get("вердикти") or []}; сп = dict(д.get("спільне") or {}, **(п.get("спільне") or {}))
        if "1" in вв and "2" in вв: пари[(д.get("пристрій"), п.get("прогін"), вв["1"].get("склад"), вв["2"].get("склад"))] = (вв["1"], вв["2"], "Проба" in str(сп.get("профіль")))
Т = ("верх", "низ", "сукня", "верхній_шар", "комбінезон"); ПРИК = ("сережки", "намисто", "кольє", "браслет", "каблучка")
МАПА = {"R-COL-16": ("colour", Т), "K-BOD-02": ("cut", Т), "K-CRA-01": ("combination", ()), "K-KOH-02": ("occasion", ()), "K-OUT-33": ("weather", ("верхній_шар",)),
        "K-COL-06-M": ("colour", ПРИК), "K-REG-01": ("style", ()), "K-SIL-03": ("cut", Т), "K-FIT-03": ("cut", Т + ("взуття",)), "K-ACC-01": ("combination", ("сумка",)),
        "K-SHO-16": ("comfort", ("взуття",)), "K-PAL-18": ("colour", ()), "R-MUA-02": (None, ()), "K-MAT-03": ("weather", ())}
def скарга(в, аспект, слоти):   # аспект на картці чи «не ця»/dislike на речі слоту правила (без слотів — будь-якої)
    вн, рр = в.get("коментар_внутрішня") or {}, речі(в); слот = lambda і: (рр.get(і) in слоти) if слоти else і in рр
    мін = set(str(в.get("причини") or "").split("+")) | set(вн.get("reasons") or [])
    мін |= {р for і in вн.get("about_items") or [] if і.get("opinion") == "dislike" and слот(і.get("id")) for р in і.get("reasons") or [аспект]}
    return bool(аспект and аспект in мін) or any(слот(і) for і in str(в.get("замінити") or "").split("+") if і)
for в1, в2, стенд in пари.values():
    if в2.get("поломка_руки") != "rule_off": continue   # стенд — вердикти скриптом: лише фізика поломки, без скарг
    ід = в2.get("правило_руки"); аспект, слоти = МАПА.get(ід, (None, ())); коди = set(ПР2.ЗА_ІД.get(ід, {}).get("коди") or [ід]); т2 = len([з for з in в2.get("тінь_знахідки") or [] if з.get("правило") in коди]) if "тінь_знахідки" in в2 else sum(int(x) for x in re.findall(r"judge\W{0,3}(\d+)", json.dumps(в2.get("тінь_правила"))))
    з1 = sum(1 for з in в1.get("знахідки_коду") or [] if з.get("правило") in коди); р1, р2 = речі(в1), речі(в2)
    людина = all(в.get("вердикт_людини") for в in (в1, в2)) and not стенд
    c = гр["%s · %s · %s" % (ід, str(в2.get("пара_руки") or "—").split(" ·")[0], "людина" if людина else "стенд")]
    c["пар"] += 1; c["тінь суду в руці 2"] += т2 > 0; c["те саме правило говорить у руці 1"] += з1 > 0; c["тінь2 > знахідок1"] += т2 > з1
    c["речі слотів правила різні"] += bool(слоти) and {i for i, с in р1.items() if с in слоти} != {i for i, с in р2.items() if с in слоти}
    if людина: c["скарга на %s: рука 2" % аспект] += скарга(в2, аспект, слоти); c["скарга: рука 1"] += скарга(в1, аспект, слоти)
for г, c in sorted(гр.items()): print("%-34s" % г, " · ".join("%s %d" % кв for кв in c.items()))
