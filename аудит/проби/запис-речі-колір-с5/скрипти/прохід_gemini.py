#!/usr/bin/env python3
"""Прохід запису нового виду з міткою «колір» над речами вибірки (`дані/вибірка.json`)
через неінтерактивний `agy -p` на моделях Gemini (наряд `Запис-речі-колір-рушій-gemini`).
Промпт — `запис_речі.промпт`; слова крамниці й таблиця мірок — `вхід.поля_крамниці` проби 300;
фото — галерея варіанта (до 8 кадрів, з ТЕКА_КОЛІР/модель від `фото.py`).
Запуск з кореня: python3 аудит/проби/запис-речі-колір-с5/скрипти/прохід_gemini.py <модель> <журнал.jsonl> [паралельно]
`ЛИШЕ_ОЧИМА=1` — лише 60 речей огляду очима."""
import glob, gzip, json, os, subprocess, sys, tempfile, threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "аудит/проби/запис-речі-вибірка-300/скрипти")
sys.path.insert(0, "джерела")
from вхід import поля_крамниці, P
import запис_речі

МОДЕЛЬ, ЖУРНАЛ = sys.argv[1:3]
ПАР = int(sys.argv[3]) if len(sys.argv) > 3 else 4
БІН = os.environ.get("AGY_BIN", "agy")
ТЕКА_Б = os.environ.get("ТЕКА_КОЛІР", "/tmp/колір-с5")
ТЕКА_Ф = f"{ТЕКА_Б}/модель"

ВИБ = json.load(open("аудит/проби/запис-речі-колір-с5/дані/вибірка.json", encoding="utf-8"))["речі"]
ПОТРІБНІ = {в["ід"].split("@")[0] for в in ВИБ}
R = {}
for л in gzip.open("каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8"):
    р = json.loads(л)
    if р.get("ід") in ПОТРІБНІ:
        R[р["ід"]] = р

замок = threading.Lock()
готові = set()
if os.path.exists(ЖУРНАЛ):
    for л in open(ЖУРНАЛ, encoding="utf-8"):
        try:
            з = json.loads(л)
            if з.get("статус") == "ok":
                готові.add(з["ід"])
        except Exception:
            continue


def один(в):
    ід = в["ід"]
    р = R[ід.split("@")[0]]
    фото = sorted(glob.glob("%s/%s-*.jpg" % (ТЕКА_Ф, ід.split("@")[0])), key=lambda ф: int(ф.rsplit("-", 1)[1][:-4]))[:8]
    таблиця = P(р, "таблиця_мірок")
    системний, текст = запис_речі.промпт(поля_крамниці(р), len(фото), таблиця[:1400] if таблиця else None)

    фото_перелік = "\n".join(f"- {os.path.abspath(ф)}" for ф in фото)
    повний_промпт = f"""{системний}

=== PHOTOS OF THE ITEM ===
Please inspect all {len(фото)} photo(s) of the item using read_file in parallel:
{фото_перелік}
Do not use run_command or any terminal tools. Only use read_file to inspect the photos, then output the requested JSON.

{текст}
"""
    з = {"ід": ід, "модель": МОДЕЛЬ, "фото": len(фото)}
    for спроба in range(3):
        try:
            cwd_dir = tempfile.mkdtemp(prefix="прохід-gemini-")
            п = subprocess.run([БІН, "--model", МОДЕЛЬ, "--output-format", "json", f"-p={повний_промпт}"],
                               capture_output=True, text=True, timeout=300, cwd=cwd_dir)
            if п.returncode == 0:
                ітог = json.loads(п.stdout)
                if ітог.get("status") == "SUCCESS":
                    u = ітог.get("usage") or {}
                    з.update({
                        "статус": "ok",
                        "с": round(float(ітог.get("duration_seconds", 0)), 1),
                        "вхід_нових": u.get("input_tokens", 0),
                        "вхід_кеш_запис": 0,
                        "вхід_кеш_читання": u.get("cache_read_tokens", 0),
                        "вихід": u.get("output_tokens", 0),
                        "моделі": [МОДЕЛЬ],
                        "текст": ітог.get("response") or ""
                    })
                    break
            з.update({"статус": "збій", "помилка": (п.stdout + " " + п.stderr)[-300:]})
        except Exception as e:
            з.update({"статус": "збій", "помилка": f"{type(e).__name__}: {e}"[:300]})

    with замок, open(ЖУРНАЛ, "a", encoding="utf-8") as ф:
        ф.write(json.dumps(з, ensure_ascii=False) + "\n")
    return з["статус"]


рядки = [в for в in ВИБ if в["ід"] not in готові and (not os.environ.get("ЛИШЕ_ОЧИМА") or в.get("очима"))][: int(os.environ.get("СКІЛЬКИ") or 10**9)]
with ThreadPoolExecutor(ПАР) as п:
    підсумок = list(п.map(один, рядки))

print(МОДЕЛЬ, "зроблено", підсумок.count("ok"), "збоїв", len(підсумок) - підсумок.count("ok"), "готових раніше", len(готові))
