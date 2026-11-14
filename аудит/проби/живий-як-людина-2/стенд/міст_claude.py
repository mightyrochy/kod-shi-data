#!/usr/bin/env python3
"""Прилад проби «Живий-як-людина-2» (не код продукту): місцевий міст для сторінки Люстерка.
Сторінка шле тіло Anthropic-моста ({model, max_tokens, messages:[{role, content:[text|image]}]});
цей сервер віддає його `claude -p --input-format stream-json` за підпискою сесії (без ключів API) —
текст слово в слово, фото речей (адреса крамниці) тягне й кладе base64, як справжній воркер, а скільки
не дістав — заголовком `x-images-dropped`. Назад — {content:[{type:text}], usage, stop_reason}.
Журнал (JSONL): секунди, токени й долари з `claude -p`. Стеля — сума total_cost_usd; після неї 503.
Відмінність від `хмара-б1-1211/сервер_claude.py`: там форма OpenAI й фото речей відкидались; тут фото доходять.
Запуск: python3 міст_claude.py <порт> <журнал.jsonl> [стеля_доларів]"""
import base64, json, os, re, subprocess, sys, tempfile, threading, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ПОРТ = int(sys.argv[1]); ЖУРНАЛ = sys.argv[2]
СТЕЛЯ = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
МОДЕЛЬ = os.environ.get("CLAUDE_MODEL") or "claude-sonnet-5-5"
БІН = os.environ.get("ZHYVA_BIN") or "/opt/node22/bin/claude"
СИСТЕМНИЙ = ("You are the model behind a mobile styling app. The user message is the application prompt, "
             "verbatim. Do exactly what it asks and output only the answer it asks for: raw JSON with no code "
             "fence when it asks for JSON, plain prose when it asks for prose. No preamble, no commentary, "
             "no tools, no questions back.")
ТЕКА = tempfile.mkdtemp(prefix="міст-людина-")
замок = threading.Lock(); у_польоті = 0; макс_одночасно = 0; сума = 0.0; номер = 0
ТИПИ = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def кадр(url):
    try:
        з = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(з, timeout=20) as в:
            тип = (в.headers.get("Content-Type") or "image/jpeg").split(";")[0].strip()
            б = в.read()
        if not б or len(б) > 5 * 1024 * 1024:
            return None
        if тип not in ТИПИ:
            тип = ("image/png" if б[:4] == b"\x89PNG" else "image/webp" if б[8:12] == b"WEBP"
                   else "image/gif" if б[:3] == b"GIF" else "image/jpeg")
        return {"type": "image", "source": {"type": "base64", "media_type": тип,
                                            "data": base64.b64encode(б).decode()}}
    except Exception:
        return None


def блоки(повід):
    вих = []; дропи = 0; фото = 0
    for м in повід:
        if len(повід) > 1:
            вих.append({"type": "text", "text": f"[{'assistant' if м.get('role') == 'assistant' else 'user'}]"})
        c = м.get("content")
        if not isinstance(c, list):
            вих.append({"type": "text", "text": str(c or "")}); continue
        for б in c:
            if б.get("type") != "image":
                вих.append({"type": "text", "text": б.get("text") or ""}); continue
            фото += 1; дж = б.get("source") or {}
            if дж.get("type") == "base64":
                вих.append({"type": "image", "source": {"type": "base64", "media_type": дж.get("media_type") or "image/jpeg",
                                                        "data": дж.get("data")}}); continue
            к = кадр(дж.get("url") or "")
            if к: вих.append(к)
            else: дропи += 1; вих.append({"type": "text", "text": "(image not delivered)"})
    return вих, дропи, фото


class О(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _відп(self, код, об, заг=None):
        б = json.dumps(об, ensure_ascii=False).encode("utf-8")
        self.send_response(код); self.send_header("Content-Type", "application/json")
        for к, з in (заг or {}).items(): self.send_header(к, з)
        self.send_header("Content-Length", str(len(б))); self.end_headers(); self.wfile.write(б)

    def do_POST(self):
        global у_польоті, макс_одночасно, сума, номер
        тіло = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        прохід = urllib.parse.unquote(self.headers.get("x-prohid") or "")
        with замок:
            if сума >= СТЕЛЯ:
                return self._відп(503, {"error": {"message": f"стеля проби {СТЕЛЯ} $ вичерпана"}})
            у_польоті += 1; макс_одночасно = max(макс_одночасно, у_польоті); номер += 1; н = номер
        т0 = time.time()
        бл, дропи, фото = блоки(тіло.get("messages") or [])
        рядок = json.dumps({"type": "user", "message": {"role": "user", "content": бл}}, ensure_ascii=False) + "\n"
        запис = {"н": н, "прохід": прохід, "початок_utc": time.strftime("%H:%M:%S", time.gmtime(т0)),
                 "промпт_симв": sum(len(б.get("text") or "") for б in бл if б["type"] == "text"),
                 "фото": фото, "фото_не_дійшло": дропи, "стеля_сторінки": тіло.get("max_tokens")}
        ітог = None; помилка = None
        try:
            р = subprocess.run([БІН, "-p", "--model", МОДЕЛЬ, "--tools", "", "--strict-mcp-config",
                                "--no-session-persistence", "--input-format", "stream-json",
                                "--output-format", "stream-json", "--verbose", "--system-prompt", СИСТЕМНИЙ],
                               input=рядок, capture_output=True, text=True, timeout=900, cwd=ТЕКА,
                               env=dict(os.environ, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"))
            for л in р.stdout.splitlines():
                try: о = json.loads(л)
                except Exception: continue
                if о.get("type") == "result": ітог = о
            if not ітог: помилка = f"rc {р.returncode}: " + (р.stderr or р.stdout)[-300:]
        except Exception as e:
            помилка = f"{type(e).__name__}: {e}"[:300]
        с = time.time() - т0
        with замок: у_польоті -= 1
        текст = ""; u = {}; вартість = 0.0; стоп = "end_turn"; статус = 200
        if ітог: вартість = ітог.get("total_cost_usd") or 0.0
        if ітог is None or ітог.get("is_error") or ітог.get("subtype") != "success":
            статус = 429 if ітог and re.search(r"rate|limit|quota|429", str(ітог.get("result")), re.I) else 502
            помилка = помилка or str((ітог or {}).get("result") or (ітог or {}).get("api_error_status"))[:300]
        else:
            текст = ітог.get("result") or ""; u = ітог.get("usage") or {}
            if ітог.get("stop_reason") == "max_tokens": стоп = "max_tokens"
        with замок:
            сума += вартість; сума_зараз = сума
        запис.update({"с": round(с, 1), "статус": статус, "usd": вартість, "вхід_нових": u.get("input_tokens"),
                      "вхід_кеш_читання": u.get("cache_read_input_tokens"), "вхід_кеш_запис": u.get("cache_creation_input_tokens"),
                      "вихід": u.get("output_tokens"), "симв_відповіді": len(текст),
                      "модель": list((ітог or {}).get("modelUsage") or {}), "помилка": помилка,
                      "сума_usd": round(сума_зараз, 4), "макс_одночасно_досі": макс_одночасно})
        with замок, open(ЖУРНАЛ, "a", encoding="utf-8") as ф:
            ф.write(json.dumps(запис, ensure_ascii=False) + "\n")
        заг = {"x-model": МОДЕЛЬ}
        if фото: заг["x-images-dropped"] = str(дропи)
        if статус != 200:
            return self._відп(статус, {"error": {"message": помилка or "модель не відповіла"}}, заг)
        вх = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        self._відп(200, {"content": [{"type": "text", "text": текст}],
                         "usage": {"input_tokens": вх, "output_tokens": u.get("output_tokens") or 0},
                         "stop_reason": стоп}, заг)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", ПОРТ), О).serve_forever()
