# -*- coding: utf-8 -*-
"""Проба К-5: ЗАБОРОНИ рядка `features` на збережених відповідях прогону — друкує факт, моделі не кличе. Менеджер 27.09
переглянув 20 рядків очима й назвав, що прибрати: маркетинг і оцінки, розмір і обміри, бренд і назву моделі, назву
кольору (колір несе код; виняток — кольори візерунка), країну. СКЛАД ТКАНИНИ ЛИШАЄТЬСЯ — проба міряє його окремо, щоб
було видно, що заборони не з'їли й його. Бренд — тією ж міркою, що `каталог_розбір_нюанси.py` (ім'я з великої літери з
ДАНИХ крамниці, що не є кодом, або ім'я крамниці), інакше «English collar» і «The style» читались би брендом.
«До/після» правила — та сама проба на двох теках поруч. Запуск: python3 джерела/проби/каталог_розбір_заборони.py [тека …]"""
import glob, json, os, re, sys, tarfile  # noqa: E401
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д)  # noqa: E702
import каталог_розбір as КР  # noqa: E402
МАРКЕТИНГ = re.compile(r"\b(?:comfort|elegan|stylish|perfect|beaut|suitab|ideal|trend|fashion|luxur|cozy|cosy|versatil|chic|flatter|feminin|romantic|"
                       r"modern|timeless|everyday|daily|casual|office|holiday|occasion|combin|easy|quality|premium|refined|unique|special|lovely|basic|"
                       r"essential|effortless|aesthetic|relaxed|refresh|statement|must\-have)\w*", re.I)
РОЗМІР = re.compile(r"\b(?:sizes?|measurement\w*|\d+(?:[.,]\d+)?\s*(?:cm|mm|inch\w*)|cm|mm)\b", re.I)
КРАЇНА, ЦІНА = re.compile(r"\b(?:made|manufactured|produced|sewn|handmade)\s+in\b|\bcountry of origin\b", re.I), re.compile(r"\b(?:uah|usd|eur|грн|price)\b|[$€₴]", re.I)
СКЛАД = re.compile(r"\b(?:\d{1,3}\s*%|cotton|viscose|wool|linen|silk|polyester|elastane|cashmere|acrylic|polyamide|leather)\b", re.I)
КОЛІР = re.compile(r"\b(?:%s)\b" % "|".join(sorted(re.escape(с) for с in set(КР.ПЕРЕЛІКИ["color_main"]) - {КР.UNKNOWN} | {"colour", "color", "shade", "tone"})), re.I)
ВСІ_КОДИ = {с for к in КР.ПЕРЕЛІКИ.values() for код in к for с in re.split(r"[_\-]", код)}
ЗАБОРОНИ = (("маркетинг", МАРКЕТИНГ), ("розмір", РОЗМІР), ("бренд", None), ("колір", КОЛІР), ("країна", КРАЇНА), ("ціна", ЦІНА))
for т in sys.argv[1:] or sorted(glob.glob(os.path.join(Д, "..", "аудит", "розбір_каталогу", "*_uk*"))):
    м = json.load(open(os.path.join(т, "прогін.json"), encoding="utf-8")); тар = os.path.join(т, "сирі_відповіді.tar.gz")  # noqa: E702
    сирі = {ч.name: а.extractfile(ч).read().decode("utf-8").replace("\r\n", "\n") for а in ([tarfile.open(тар)] if os.path.exists(тар) else []) for ч in а if ч.isfile()}
    рядків, влип, склад = 0, {і: [] for і, _ in ЗАБОРОНИ}, 0
    for р in м["речі"]:
        ф = os.path.join(т, р["файл"])
        цілий = open(ф, encoding="utf-8").read() if os.path.exists(ф) else сирі.get(р["файл"], "")
        запит, _, відп = цілий.split("── ЗАПИТ\n", 1)[-1].partition("\n\n── ВІДПОВІДЬ")
        поля = КР.з_відповіді(відп)[0]
        if not поля or поля[КР.ОСОБЛИВОСТІ] == КР.UNKNOWN: continue  # noqa: E701
        f = поля[КР.ОСОБЛИВОСТІ]; рядків += 1; склад += bool(СКЛАД.search(f))  # noqa: E702
        дані = {к: в for к, в in json.loads(запит).items() if к != "завдання"}
        імена = [і for і in re.findall(r"\b[A-Z][A-Za-z]{2,}(?: [A-Z][A-Za-z]{2,})*", json.dumps(дані, ensure_ascii=False)) if і.lower() not in ВСІ_КОДИ]
        бренд = next((re.search(re.escape(і), f) for і in імена if і in f), None) or re.search(r"\b%s\b" % re.escape(р["id"].split("@")[-1].split(".")[0]), f, re.I)
        for і, ре in ЗАБОРОНИ:
            влучив = бренд if і == "бренд" else ре.search(f)
            if влучив: влип[і].append("%s: …%s…" % (р["id"], f[max(0, влучив.start() - 18):влучив.end() + 18].strip()))  # noqa: E701
    print("%s · рядків (не unknown) %d · склад тканини в %d (%d %%)" % (os.path.basename(os.path.normpath(т)), рядків, склад, round(100.0 * склад / max(рядків, 1))))
    for і, _ in ЗАБОРОНИ:
        print("  %-10s %3d (%2d %%)%s" % (і, len(влип[і]), round(100.0 * len(влип[і]) / max(рядків, 1)), "".join("\n      " + п for п in влип[і][:3])))
