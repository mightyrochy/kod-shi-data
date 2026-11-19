#!/usr/bin/env python3
"""Повтор записаних входів прогону 13.11 на моделі через `claude -p` за підпискою (ключа API нема).
Вхід — тіла моста (`міст_тіло.js`), фото крамниць тягнуться й кладуться base64, як у стенді 13.11.
Журнал: токени з `claude -p` (вхід разом з накладними CLI, вихід і з нього — думки), секунди, текст відповіді.
Запуск: python3 повтор.py <міст.jsonl> <модель> <effort> <журнал.jsonl> [паралельно]"""
import base64, json, os, subprocess, sys, tempfile, threading, urllib.request
from concurrent.futures import ThreadPoolExecutor
ВХІД, МОДЕЛЬ, ЗУСИЛЛЯ, ЖУРНАЛ = sys.argv[1:5]; ПАР = int(sys.argv[5]) if len(sys.argv) > 5 else 8
БІН = "/opt/node22/bin/claude"
СИСТЕМНИЙ = ("You are the model behind a mobile styling app. The user message is the application prompt, "
             "verbatim. Do exactly what it asks and output only the answer it asks for: raw JSON with no code "
             "fence when it asks for JSON, plain prose when it asks for prose. No preamble, no commentary, "
             "no tools, no questions back.")
ТЕКА = tempfile.mkdtemp(prefix="повтор-"); замок = threading.Lock(); КЕШ_ФОТО = {}
ТИПИ = {"image/jpeg", "image/png", "image/webp", "image/gif"}
готові = set()
if os.path.exists(ЖУРНАЛ):
    for л in open(ЖУРНАЛ, encoding="utf-8"):
        з = json.loads(л)
        if з.get("статус") == "ok": готові.add(з["id"])

def кадр(url):
    if url in КЕШ_ФОТО: return КЕШ_ФОТО[url]
    к = None
    try:
        з = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(з, timeout=20) as в:
            тип = (в.headers.get("Content-Type") or "image/jpeg").split(";")[0].strip(); б = в.read()
        if б and len(б) <= 5 * 1024 * 1024:
            if тип not in ТИПИ:
                тип = ("image/png" if б[:4] == b"\x89PNG" else "image/webp" if б[8:12] == b"WEBP"
                       else "image/gif" if б[:3] == b"GIF" else "image/jpeg")
            к = {"type": "image", "source": {"type": "base64", "media_type": тип, "data": base64.b64encode(б).decode()}}
    except Exception:
        pass
    КЕШ_ФОТО[url] = к; return к

def один(рядок):
    з = json.loads(рядок); тіло = з["тіло"]; бл = []; фото = 0; випало = 0
    for м in тіло["messages"]:
        for б in м["content"]:
            if б["type"] == "image":
                фото += 1; д = б["source"]
                к = ({"type": "image", "source": д} if д.get("type") == "base64" else кадр(д.get("url") or ""))
                if к: бл.append(к)
                else: випало += 1; бл.append({"type": "text", "text": "(image not delivered)"})
            else:
                бл.append({"type": "text", "text": б["text"]})
    вхід = json.dumps({"type": "user", "message": {"role": "user", "content": бл}}, ensure_ascii=False) + "\n"
    запис = {"id": з["id"], "модель": МОДЕЛЬ, "effort": ЗУСИЛЛЯ, "фото": фото, "фото_випало": випало}
    for спроба in range(3):
        try:
            р = subprocess.run([БІН, "-p", "--model", МОДЕЛЬ, "--effort", ЗУСИЛЛЯ, "--tools", "", "--strict-mcp-config",
                                "--no-session-persistence", "--input-format", "stream-json", "--output-format", "stream-json",
                                "--verbose", "--system-prompt", СИСТЕМНИЙ], input=вхід, capture_output=True, text=True,
                               timeout=900, cwd=ТЕКА, env=dict(os.environ, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"))
            ітог = None
            for л in р.stdout.splitlines():
                try: о = json.loads(л)
                except Exception: continue
                if о.get("type") == "result": ітог = о
            if ітог and ітог.get("subtype") == "success" and not ітог.get("is_error"):
                u = ітог["usage"]
                запис.update({"статус": "ok", "с": round(ітог["duration_ms"] / 1000, 1), "вхід_нових": u["input_tokens"],
                              "вхід_кеш_запис": u["cache_creation_input_tokens"], "вхід_кеш_читання": u["cache_read_input_tokens"],
                              "вихід": u["output_tokens"], "думки": (u.get("output_tokens_details") or {}).get("thinking_tokens"),
                              "stop": ітог.get("stop_reason"), "usd_cli": ітог.get("total_cost_usd"),
                              "моделі": list(ітог.get("modelUsage") or {}), "текст": ітог.get("result") or ""})
                break
            запис.update({"статус": "збій", "помилка": (str((ітог or {}).get("result")) + " " + р.stderr)[-400:]})
        except Exception as e:
            запис.update({"статус": "збій", "помилка": f"{type(e).__name__}: {e}"[:400]})
    with замок, open(ЖУРНАЛ, "a", encoding="utf-8") as ф:
        ф.write(json.dumps(запис, ensure_ascii=False) + "\n")
    return запис["статус"]

рядки = [л for л in open(ВХІД, encoding="utf-8") if json.loads(л)["id"] not in готові]
with ThreadPoolExecutor(ПАР) as п:
    підсумок = list(п.map(один, рядки))
print(МОДЕЛЬ, ЗУСИЛЛЯ, "зроблено", підсумок.count("ok"), "збоїв", len(підсумок) - підсумок.count("ok"), "пропущено готових", len(готові))
