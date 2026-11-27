#!/usr/bin/env python3
"""Прохід запису нового виду з міткою «колір» (наряд `Запис-речі-колір-мітка`, п.3) над речами вибірки
(`дані/вибірка.json`) через `claude -p` за підпискою — той самий транспорт, що в #4769 (`запис-речі-вибірка-300/скрипти/
прохід_новий.py`). Промпт — `запис_речі.промпт` з одного визначення міток ядра; слова крамниці й таблиця мірок —
`вхід.поля_крамниці` проби 300; фото — уся галерея варіанта (до 8 кадрів, /tmp/колір-с5/модель від `фото.py`).
Запуск з кореня: python3 аудит/проби/запис-речі-колір-с5/скрипти/прохід.py <модель> <журнал.jsonl> [паралельно]
`ЛИШЕ_ОЧИМА=1` — лише 60 речей огляду очима (повтор (а) після поправки визначення за перевіркою: журнали `*_2.jsonl`, після другої поправки — `*_3.jsonl`; `ЗУСИЛЛЯ=high` — зусилля моделі, журнал `sonnet_3_high.jsonl`)."""
import base64, glob, gzip, json, os, subprocess, sys, tempfile, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "аудит/проби/запис-речі-вибірка-300/скрипти"); sys.path.insert(0, "джерела")
from вхід import поля_крамниці, P
import запис_речі
МОДЕЛЬ, ЖУРНАЛ = sys.argv[1:3]; ПАР = int(sys.argv[3]) if len(sys.argv) > 3 else 6
БІН = "/opt/node22/bin/claude"; ТЕКА_Ф = "/tmp/колір-с5/модель"
ВИБ = json.load(open("аудит/проби/запис-речі-колір-с5/дані/вибірка.json", encoding="utf-8"))["речі"]
ПОТРІБНІ = {в["ід"].split("@")[0] for в in ВИБ}
R = {}
for л in gzip.open("каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8"):
    р = json.loads(л)
    if р.get("ід") in ПОТРІБНІ: R[р["ід"]] = р
ТЕКА = tempfile.mkdtemp(prefix="прохід-"); замок = threading.Lock(); готові = set()
if os.path.exists(ЖУРНАЛ):
    for л in open(ЖУРНАЛ, encoding="utf-8"):
        з = json.loads(л)
        if з.get("статус") == "ok": готові.add(з["ід"])
def один(в):
    ід = в["ід"]; р = R[ід.split("@")[0]]
    фото = sorted(glob.glob("%s/%s-*.jpg" % (ТЕКА_Ф, ід.split("@")[0])), key=lambda ф: int(ф.rsplit("-", 1)[1][:-4]))
    таблиця = P(р, "таблиця_мірок")
    системний, текст = запис_речі.промпт(поля_крамниці(р), len(фото), таблиця[:1400] if таблиця else None)
    бл = [{"type": "text", "text": текст}]
    for ф in фото:
        бл.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(open(ф, "rb").read()).decode()}})
    вхід = json.dumps({"type": "user", "message": {"role": "user", "content": бл}}, ensure_ascii=False) + "\n"
    з = {"ід": ід, "модель": МОДЕЛЬ, "фото": len(фото)}
    for спроба in range(3):
        try:
            п = subprocess.run([БІН, "-p", "--model", МОДЕЛЬ, "--effort", os.environ.get("ЗУСИЛЛЯ", "low"), "--tools", "", "--strict-mcp-config", "--no-session-persistence",
                                "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--system-prompt", системний],
                               input=вхід, capture_output=True, text=True, timeout=600, cwd=ТЕКА,
                               env=dict(os.environ, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"))
            ітог = None
            for л in п.stdout.splitlines():
                try: о = json.loads(л)
                except Exception: continue
                if о.get("type") == "result": ітог = о
            if ітог and ітог.get("subtype") == "success" and not ітог.get("is_error"):
                u = ітог["usage"]
                з.update({"статус": "ok", "с": round(ітог["duration_ms"] / 1000, 1), "вхід_нових": u["input_tokens"],
                          "вхід_кеш_запис": u["cache_creation_input_tokens"], "вхід_кеш_читання": u["cache_read_input_tokens"],
                          "вихід": u["output_tokens"], "моделі": list(ітог.get("modelUsage") or {}), "текст": ітог.get("result") or ""})
                break
            з.update({"статус": "збій", "помилка": (str((ітог or {}).get("result")) + " " + п.stderr)[-300:]})
        except Exception as e:
            з.update({"статус": "збій", "помилка": f"{type(e).__name__}: {e}"[:300]})
    with замок, open(ЖУРНАЛ, "a", encoding="utf-8") as ф: ф.write(json.dumps(з, ensure_ascii=False) + "\n")
    return з["статус"]
рядки = [в for в in ВИБ if в["ід"] not in готові and (not os.environ.get("ЛИШЕ_ОЧИМА") or в.get("очима"))][: int(os.environ.get("СКІЛЬКИ") or 10**9)]
with ThreadPoolExecutor(ПАР) as п: підсумок = list(п.map(один, рядки))
print(МОДЕЛЬ, "зроблено", підсумок.count("ok"), "збоїв", len(підсумок) - підсумок.count("ok"), "готових раніше", len(готові))
