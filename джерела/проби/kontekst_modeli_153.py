# -*- coding: utf-8 -*-
"""Рядок 153: чому жнива самі готують свою модель. Три потоки шлють 6 справжніх запитів жнив (фото 1024 px, промпт набору) спершу під
контекстом, з яким модель приходить від JIT LM Studio (4096 на 4 слоти), потім під виміряним (16384 на 3). Друкує ок/збій і токени
запиту з `usage` самої відповіді. Наприкінці лишає модель у робочому стані 16384/3 — проба нічого за собою не лишає.
ВИМІРЯНО 24.09.2026: JIT 4096/4 — 0 ок, 6 HTTP 400; 16384/3 — 6 ок, 0 збоїв; один запит важить prompt 1939–1961 + до 600 на відповідь,
тобто ~2 560 токенів, а слот JIT дає 1024. Звідси поріг `жнива_промпти.КОНТЕКСТ_НА_ПОТІК` = 4096 і перевірка на старті прогону. Поодинокий запит JIT переживає — пастка видна лише потоками, і саме тому вона жила непоміченою."""
import json, os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import жнива_v2 as Ж
МОД, LMS = "qwen3-vl-8b-instruct", os.path.join(os.path.expanduser("~"), ".lmstudio", "bin", "lms.exe")
if not os.path.exists(LMS):
    sys.exit("lms.exe не знайдено — проба міряє саме завантаження моделі")
ТЕКА = os.path.join(Ж.ТУТ, "аудит")
речі = [з for з in json.load(open(os.path.join(ТЕКА, "збагачення_v2_вибірка.json"), encoding="utf-8"))["речі"]
        if з.get("фото_показу") and os.path.exists(os.path.join(ТЕКА, з["фото_показу"]))]
шлях = os.path.join(tempfile.gettempdir(), "kontekst153.jpg"); shutil.copyfile(os.path.join(ТЕКА, речі[0]["фото_показу"]), шлях)
b64, текст = Ж._b64(Ж._фото_1024(шлях), сторона=1024), Ж._підставити(Ж.ПРОМПТ_ОДЯГ, "сукня")


def один(_):
    """Один запит жнив без повторів: «ок» або текст збою (HTTP 400 — саме те, що ловимо)."""
    try:
        Ж._запит(МОД, текст, [b64], повтори=0, токенів=600)
        return "ок"
    except Exception as e:
        return type(e).__name__ + ": " + str(e)[:40]


for контекст, слотів in ((4096, 4), (16384, 3)):
    subprocess.call([LMS, "unload", "--all"], timeout=120)
    subprocess.call([LMS, "load", МОД, "--gpu", "max", "-c", str(контекст), "--parallel", str(слотів),
                     "--identifier", МОД, "-y"], timeout=900)
    к, п = Ж._стан_моделі(МОД)
    with ThreadPoolExecutor(3) as пул:
        вихід = list(пул.map(один, range(6)))
    print("контекст %d на %d слот(ів) = %d на потік · 3 потоки, 6 запитів: ок %d, збоїв %d%s"
          % (к, п, к // max(п, 1), вихід.count("ок"), len(вихід) - вихід.count("ок"),
             " · " + sorted(set(в for в in вихід if в != "ок"))[0] if any(в != "ок" for в in вихід) else ""))
print("модель лишено в робочому стані: контекст %d на %d слот(ів)" % Ж._стан_моделі(МОД))
