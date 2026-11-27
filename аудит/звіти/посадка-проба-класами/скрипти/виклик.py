"""Транспорт живого Sonnet за підпискою тим самим швом, що хмарний тестовий прогін 27.11 (`ZHYVA=sonnet`,
`аудит/проби/рв6_н3.js`): `claude -p --model sonnet --tools '' --input-format stream-json`, нейтральний системний рядок
стенда (`КЛОД_СИСТЕМНИЙ`), без `--effort`; фото речі — адресою крамниці, адаптер тягне й кладе base64 (до 1200 px), підпис
«Catalogue photo for item <n>:» перед кадром, як `відповідьМоделіЯдруП` показу.
Вхід — jsonl завдань {ключ, текст, фото: [{n, url}]}; вихід — jsonl {ключ, статус, текст, usage, с}; готові пропускає.
Запуск: python3 виклик.py <завдання.jsonl> <вихід.jsonl> [паралельно]"""
import base64, hashlib, io, json, os, subprocess, sys, tempfile, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
ВХІД, ВИХІД = sys.argv[1:3]; ПАР = int(sys.argv[3]) if len(sys.argv) > 3 else 4
БІН = "/opt/node22/bin/claude"; КЕШ = "/tmp/пс/кадри_викликів"; os.makedirs(КЕШ, exist_ok=True)
СИСТЕМНИЙ = ("You are the model behind a mobile styling app. The user message is the application prompt, verbatim. "
             "Do exactly what it asks and output only the answer it asks for: raw JSON with no code fence when it asks "
             "for JSON, plain prose when it asks for prose. No preamble, no commentary, no tools, no questions back.")
ТЕКА = tempfile.mkdtemp(prefix="виклик-"); замок = threading.Lock()
def кадр(url):
    ф = f"{КЕШ}/{hashlib.sha1(url.encode()).hexdigest()}.jpg"
    if not os.path.exists(ф):
        for спроба in range(5):
            try:
                з = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(з, timeout=30) as в:
                    І = Image.open(io.BytesIO(в.read())); І.load()
                І = І.convert("RGB"); І.thumbnail((1200, 1200)); І.save(ф, quality=85); break
            except Exception as e:
                time.sleep(4 * (спроба + 1))
        else:
            return None
    return base64.b64encode(open(ф, "rb").read()).decode()
готові = set()
if os.path.exists(ВИХІД):
    for л in open(ВИХІД, encoding="utf-8"):
        з = json.loads(л)
        if з.get("статус") == "ok": готові.add(з["ключ"])
def один(завд):
    бл, не_дійшло = [], 0
    for ф in завд.get("фото", []):
        дані = кадр(ф["url"])
        бл.append({"type": "text", "text": "Catalogue photo for item " + ф["n"] + ":"})
        if дані: бл.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": дані}})
        else: не_дійшло += 1; бл.append({"type": "text", "text": "(image not delivered)"})
    бл.append({"type": "text", "text": завд["текст"]})
    вхід = json.dumps({"type": "user", "message": {"role": "user", "content": бл}}, ensure_ascii=False) + "\n"
    з = {"ключ": завд["ключ"], "фото": len(завд.get("фото", [])), "фото_не_дійшло": не_дійшло}
    for спроба in range(3):
        try:
            п = subprocess.run([БІН, "-p", "--model", "sonnet", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
                                "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--system-prompt", СИСТЕМНИЙ],
                               input=вхід, capture_output=True, text=True, timeout=900, cwd=ТЕКА,
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
    with замок, open(ВИХІД, "a", encoding="utf-8") as ф: ф.write(json.dumps(з, ensure_ascii=False) + "\n")
    return з["статус"]
завдання = [json.loads(л) for л in open(ВХІД, encoding="utf-8")]
завдання = [з for з in завдання if з["ключ"] not in готові]
with ThreadPoolExecutor(ПАР) as п: підсумок = list(п.map(один, завдання))
print("зроблено", підсумок.count("ok"), "збоїв", len(підсумок) - підсумок.count("ok"), "готових раніше", len(готові))
