# -*- coding: utf-8 -*-
"""Проба К-4: РЯДОК ОСОБЛИВОСТЕЙ `features` на збережених відповідях прогону розбору (uk) — друкує факт, моделі не кличе. Теці прогону:
рядків і слів (понад 15 — стеля до К-4, понад `СТЕЛЯ_СЛІВ` — стільки зрізав би `_обрізати`); рядків з маркетингом чи оцінкою (`МАРКЕТИНГ`), з брендом
(ім'я латиницею з великої літери з даних крамниці, що не є кодом, або ім'я крамниці), з кодом через «_», з «|», з кирилицею, з самих кодів і кольору;
слів рядка, що повторюють коди чи імена полів ТІЄЇ Ж відповіді (колір — ні: відтінок крамниці рядок несе навмисно); промпт — як його бачила модель
і за чинним правилом (uk, en). «Після» правила — та сама проба на теці перепрогону. Запуск: python3 джерела/проби/каталог_розбір_нюанси.py [тека …]"""
import collections, glob, json, os, re, statistics as st, subprocess, sys, tarfile, types  # noqa: E401
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д)  # noqa: E702
import збирач_промптів as ЗП; КР = types.ModuleType("каталог_розбір_к4"); КР.__file__ = os.path.join(Д, "каталог_розбір.py"); exec(subprocess.run(["git", "-C", Д, "show", "4fedabb:джерела/каталог_розбір.py"], capture_output=True, text=True, check=True).stdout, КР.__dict__)  # noqa: E702 — модуль розбору К-4 (uk/en), яким міряно; РЗ-К лишив одну англійську мову
МАРКЕТИНГ = re.compile(r"\b(?:comfort|elegan|stylish|perfect|beaut|suitab|ideal|trend|fashion|luxur|cozy|cosy|versatil|chic|flatter|feminin|romantic|"
                       r"modern|timeless|everyday|daily|casual|office|holiday|occasion|combin|easy|quality|premium|refined|unique|special|lovely|basic)\w*", re.I)
ВСІ_КОДИ, КОЛІР = {с for к in КР.ПЕРЕЛІКИ.values() for код in к for с in re.split(r"[_\-]", код)}, set(КР.ПЕРЕЛІКИ["color_main"]) | {"color", "colour", "shade", "tone"}
НОСІЇ, СЛУЖБОВІ, є = {"fit", "neck", "silhouette"}, {"and", "with", "the", "for", "from", "into", "its", "has", "are", "that", "this"}, lambda с, мн: bool({с, с[:-1], с[:-2]} & мн)
ПОЗА, EN = ("color_main", "color_extra", "color_why", "color_from", "veto", КР.ОСОБЛИВОСТІ, КР.UNKNOWN, "yes", "no", "none"), dict(zip(
    ("назва", "категорія", "опис", "параметри"), ("name", "category", "description", "params")))
for т in sys.argv[1:] or sorted(glob.glob(os.path.join(Д, "..", "аудит", "розбір_каталогу", "*_uk*"))):
    м, ряд, мк, пр, тар = json.load(open(os.path.join(т, "прогін.json"), encoding="utf-8")), [], collections.Counter(), [], os.path.join(т, "сирі_відповіді.tar.gz")
    сирі = {ч.name: а.extractfile(ч).read().decode("utf-8").replace("\r\n", "\n") for а in ([tarfile.open(тар)] if os.path.exists(тар) else []) for ч in а if ч.isfile()}
    for р in м["речі"]:
        запит, відп = (open(ф, encoding="utf-8").read() if os.path.exists(ф := os.path.join(т, р["файл"])) else сирі[р["файл"]]).split("── ЗАПИТ\n", 1)[1].split("\n\n── ВІДПОВІДЬ", 1)
        з = json.loads(запит); дані = {к: в for к, в in з.items() if к != "завдання"}                                  # noqa: E702
        пр.append([len(запит)] + [len(json.dumps(ЗП.зібрати(КР.РОЗБІР[мв], д), ensure_ascii=False, indent=1)) for мв, д in (("uk", дані), ("en", {
            EN[к]: в for к, в in дані.items()}))] + [[п for п in з["завдання"]["правила"] if "features" in п]])
        поля, об = КР.з_відповіді(відп)[0], КР._ПР.розібрати_json(відп.replace(КР.ВСТАВКА, ""))
        if not поля or поля[КР.ОСОБЛИВОСТІ] == КР.UNKNOWN: continue                                                      # noqa: E701
        f = об[КР.ОСОБЛИВОСТІ] if isinstance(об.get(КР.ОСОБЛИВОСТІ), str) else поля[КР.ОСОБЛИВОСТІ]                   # до обрізання
        кс = НОСІЇ | {с for т_ in re.findall(r'"([^"]+)"', json.dumps({к: в for к, в in поля.items() if к not in ПОЗА})) if т_ not in ПОЗА for с in re.split(r"[_\-]", т_)}
        сл, імена = [с for с in re.findall(r"[a-z]{3,}", f.lower()) if с not in СЛУЖБОВІ], re.findall(r"\b[A-Z][A-Za-z]{2,}(?: [A-Z][A-Za-z]{2,})*", json.dumps(дані, ensure_ascii=False))
        мк.update(с.lower() for с in МАРКЕТИНГ.findall(f)); ряд.append((len(f.split()), bool(МАРКЕТИНГ.search(f)), any(  # noqa: E702
            і in f for і in імена if і.lower() not in ВСІ_КОДИ) or bool(re.search(r"\b%s\b" % re.escape(р["id"].split("@")[-1].split(".")[0]), f.lower())),
            bool(re.search(r"[A-Za-z]_[A-Za-z]", f)), "|" in f, bool(КР._КИРИЛИЦЯ.search(f)), bool(сл) and all(є(с, кс | КОЛІР) for с in сл),
            sum(є(с, кс) for с in сл), len(сл)))
    н, п, сум = len(ряд), sorted(р[0] for р in ряд) or [0], lambda і: sum(р[і] for р in ряд); до, uk, en = (sum(х[і] for х in пр) / len(пр) for і in range(3))  # noqa: E702,E731
    print("%s · відповідей %d · рядків (не unknown) %d · слів: медіана %s, p90 %d, найдовший %d · понад 15 — %d, понад %d — %d\n  рядків: маркетинг чи оцінка "
          "%s · бренд %s · код через «_» %s · «|» %s · кирилиця %s · самі коди й колір %s\n  слова маркетингу: %s\n  слів рядка, що повторюють коди чи імена полів "
          "тієї ж відповіді (без кольору): %d з %d (%d %%)\n  промпт, знаків у середньому: як бачила модель %.0f · за чинним правилом uk %.0f (%+.0f, %+.1f %%), "
          "en %.0f · правил про features: %d (%d знаків) → %d (%d)" % (м["модель"], len(м["речі"]), н, st.median(п), п[int(0.9 * len(п))],
          п[-1], sum(х > 15 for х in п), КР.СТЕЛЯ_СЛІВ, sum(х > КР.СТЕЛЯ_СЛІВ for х in п), *("%d (%d %%)" % (сум(і), round(100.0 * сум(і) / max(н, 1)))
          for і in range(1, 7)), ", ".join("%s×%d" % кч for кч in мк.most_common(10)), сум(7), сум(8), round(100.0 * сум(7) / max(сум(8), 1)), до, uk,
          uk - до, 100.0 * (uk - до) / до, en, len(пр[0][3]), sum(map(len, пр[0][3])), len(КР._ОСОБЛИВОСТІ_UK), sum(map(len, КР._ОСОБЛИВОСТІ_UK))))
