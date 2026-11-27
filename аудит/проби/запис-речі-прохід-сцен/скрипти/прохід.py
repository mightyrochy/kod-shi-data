#!/usr/bin/env python3
"""Прохід запису нового виду над перелічними речами (наряд `Запис-речі-прохід-сцен`, п.2–3): галерея речі (до 8 кадрів,
640 px, /tmp/прохід-сцен/кадри) + слова крамниці + таблиця мірок → `claude -p` за підпискою (той самий транспорт, що
`запис-речі-колір-с5/скрипти/прохід.py`), промпт — `запис_речі.промпт` з визначення міток. Один запис на рядок журналу:
модель, зусилля, дата, версія визначення (sha1 `мітки_речі.json`), токени, секунди, сира відповідь. Відновлюється з журналу.
Запуск з кореня: ЗУСИЛЛЯ=high python3 <цей файл> sonnet /tmp/прохід-сцен/журнал.jsonl [паралельно] ; СКІЛЬКИ=N — обмежити."""
import base64, datetime, gzip, hashlib, io, json, os, subprocess, sys, tempfile, threading, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
sys.path.insert(0, "аудит/проби/запис-речі-вибірка-300/скрипти"); sys.path.insert(0, "джерела")
from вхід import поля_крамниці, P
import запис_речі
МОДЕЛЬ, ЖУРНАЛ = sys.argv[1:3]; ПАР = int(sys.argv[3]) if len(sys.argv) > 3 else 6
ЗУСИЛЛЯ = os.environ.get("ЗУСИЛЛЯ", "high"); БІН = "/opt/node22/bin/claude"; ТЕКА_Ф = "/tmp/прохід-сцен/кадри"
ВЕРСІЯ = hashlib.sha1(open("джерела/ядро/дані/мітки_речі.json", "rb").read()).hexdigest()[:12]
os.makedirs(ТЕКА_Ф, exist_ok=True)
ПЕРЕЛІК = [р["ід"] for р in json.load(open("аудит/проби/запис-речі-прохід-сцен/дані/перелік.json", encoding="utf-8"))["речі"]]
if os.environ.get("ІД"): ПЕРЕЛІК = [і for і in ПЕРЕЛІК if і in set(open(os.environ["ІД"]).read().split())]
R = {}
for л in gzip.open("каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8"):
    р = json.loads(л)
    if р.get("ід") in set(ПЕРЕЛІК): R[р["ід"]] = р
замок = threading.Lock(); готові = set()
if os.path.exists(ЖУРНАЛ):
    for л in open(ЖУРНАЛ, encoding="utf-8"):
        з = json.loads(л)
        if з.get("статус") in ("ok", "нема"): готові.add(з["ід"])
def кадри(ід, р):
    шлях = lambda н: f"{ТЕКА_Ф}/{ід}-{н}.jpg"
    if os.path.exists(f"{ТЕКА_Ф}/{ід}.готово"): return sorted(f for f in (шлях(н) for н in range(1, 9)) if os.path.exists(f))
    н = 0
    for к in [к for к in р["кадри"] if к.startswith("http")][:8]:
        try:
            з = urllib.request.Request(к, headers={"User-Agent": "Mozilla/5.0"})
            І = Image.open(io.BytesIO(urllib.request.urlopen(з, timeout=25).read())); І.load(); І = І.convert("RGB")
        except Exception: continue
        if min(І.size) < 120: continue
        І.thumbnail((640, 640)); н += 1; І.save(шлях(н), quality=82)
    open(f"{ТЕКА_Ф}/{ід}.готово", "w").close()
    return [шлях(і) for і in range(1, н + 1)]
def один(ід):
    р = R.get(ід)
    з = {"ід": ід, "модель": МОДЕЛЬ, "зусилля": ЗУСИЛЛЯ, "версія_міток": ВЕРСІЯ, "дата": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if not р:
        з["статус"] = "нема"
    else:
        фото = кадри(ід, р); з["фото"] = len(фото)
        таблиця = P(р, "таблиця_мірок")
        системний, текст = запис_речі.промпт(поля_крамниці(р), len(фото), таблиця[:1400] if таблиця else None)
        бл = [{"type": "text", "text": текст}] + [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(open(ф, "rb").read()).decode()}} for ф in фото]
        вхід = json.dumps({"type": "user", "message": {"role": "user", "content": бл}}, ensure_ascii=False) + "\n"
        ТЕКА = tempfile.mkdtemp(prefix="прохід-")
        for спроба in range(3):
            try:
                п = subprocess.run([БІН, "-p", "--model", МОДЕЛЬ, "--effort", ЗУСИЛЛЯ, "--tools", "", "--strict-mcp-config", "--no-session-persistence",
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
                    з.update({"статус": "ok", "с": round(ітог["duration_ms"] / 1000, 1), "вхід_нових": u["input_tokens"], "вхід_кеш_запис": u["cache_creation_input_tokens"],
                              "вхід_кеш_читання": u["cache_read_input_tokens"], "вихід": u["output_tokens"], "моделі": list(ітог.get("modelUsage") or {}), "текст": ітог.get("result") or ""})
                    break
                з.update({"статус": "збій", "помилка": (str((ітог or {}).get("result")) + " " + п.stderr)[-300:]})
            except Exception as e:
                з.update({"статус": "збій", "помилка": f"{type(e).__name__}: {e}"[:300]})
    with замок, open(ЖУРНАЛ, "a", encoding="utf-8") as ф: ф.write(json.dumps(з, ensure_ascii=False) + "\n")
    return з["статус"]
рядки = [і for і in ПЕРЕЛІК if і not in готові][: int(os.environ.get("СКІЛЬКИ") or 10**9)]
with ThreadPoolExecutor(ПАР) as п: підсумок = list(п.map(один, рядки))
print(МОДЕЛЬ, ЗУСИЛЛЯ, "ok", підсумок.count("ok"), "нема", підсумок.count("нема"), "збоїв", len(підсумок) - підсумок.count("ok") - підсумок.count("нема"), "раніше", len(готові))
