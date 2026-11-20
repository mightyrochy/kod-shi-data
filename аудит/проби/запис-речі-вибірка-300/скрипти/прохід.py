#!/usr/bin/env python3
"""Прохід моделі над 300 речами вибірки через `claude -p` за підпискою (як `модель-текст-claude/скрипти/повтор.py`).
Запуск з кореня репозиторію: python3 .../прохід.py <модель> <журнал.jsonl> [паралельно] [скільки]"""
import base64, glob, gzip, json, os, subprocess, sys, tempfile, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from вхід import промпт, СИСТЕМНИЙ
МОДЕЛЬ, ЖУРНАЛ = sys.argv[1:3]; ПАР = int(sys.argv[3]) if len(sys.argv) > 3 else 6; МАКС = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
БІН = "/opt/node22/bin/claude"; ТЕКА_Ф = "/tmp/запис300/модель"
ВИБ = json.load(open("аудит/проби/запис-речі-вибірка-300/дані/вибірка.json", encoding="utf-8"))[:МАКС]
R = {}
for л in gzip.open("каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8"):
    р = json.loads(л)
    if "ід" in р: R[р["ід"]] = р
ТЕКА = tempfile.mkdtemp(prefix="прохід-"); замок = threading.Lock()
готові = set()
if os.path.exists(ЖУРНАЛ):
    for л in open(ЖУРНАЛ, encoding="utf-8"):
        з = json.loads(л)
        if з.get("статус") == "ok": готові.add(з["ід"])
def один(в):
    ід = в["ід"]; р = R[ід]; фото = sorted(glob.glob("%s/%s-[12].jpg" % (ТЕКА_Ф, ід)))
    бл = [{"type": "text", "text": промпт(р, len(фото))}]
    for ф in фото:
        бл.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(open(ф, "rb").read()).decode()}})
    вхід = json.dumps({"type": "user", "message": {"role": "user", "content": бл}}, ensure_ascii=False) + "\n"
    з = {"ід": ід, "модель": МОДЕЛЬ, "фото": len(фото)}
    for спроба in range(3):
        try:
            п = subprocess.run([БІН, "-p", "--model", МОДЕЛЬ, "--effort", "low", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
                                "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--system-prompt", СИСТЕМНИЙ],
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
                          "вихід": u["output_tokens"], "думки": (u.get("output_tokens_details") or {}).get("thinking_tokens"),
                          "моделі": list(ітог.get("modelUsage") or {}), "текст": ітог.get("result") or ""})
                break
            з.update({"статус": "збій", "помилка": (str((ітог or {}).get("result")) + " " + п.stderr)[-300:]})
        except Exception as e:
            з.update({"статус": "збій", "помилка": f"{type(e).__name__}: {e}"[:300]})
    with замок, open(ЖУРНАЛ, "a", encoding="utf-8") as ф: ф.write(json.dumps(з, ensure_ascii=False) + "\n")
    return з["статус"]
рядки = [в for в in ВИБ if в["ід"] not in готові]
with ThreadPoolExecutor(ПАР) as п: підсумок = list(п.map(один, рядки))
print(МОДЕЛЬ, "зроблено", підсумок.count("ok"), "збоїв", len(підсумок) - підсумок.count("ok"), "готових раніше", len(готові))
