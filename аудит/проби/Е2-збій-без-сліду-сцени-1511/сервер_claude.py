#!/usr/bin/env python3
"""Прилад проби «Хмара-тестовий-прогін-проба» (не код продукту): місцевий сервер форми OpenAI
(`/v1/chat/completions`), що кожен виклик стенда передає в `claude -p` за підпискою сесії і пише
журнал викликів (JSONL): секунди, токени й долари з JSON-виводу `claude -p`, скільки викликів було одночасно.
Запуск: python3 сервер_claude.py <порт> <журнал.jsonl> [стеля_доларів]
Стеля — сума total_cost_usd; після неї нові виклики дістають 503 (стоп проби). Ключів нема: CLI бере підписку сесії.
Корені-нуль-живе-мірило-1511: копія сервера `автоживий-eebb37ae…`, плюс зображення — частини `image_url` (data URL)
ідуть у `claude -p` блоками image через `--input-format stream-json` (доти сервер передавав лише текст, і фото речі
й «Оціни мій образ» модель не бачила)."""
import json, os, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ПОРТ = int(sys.argv[1]); ЖУРНАЛ = sys.argv[2]
СТЕЛЯ = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
МОДЕЛЬ = os.environ.get("CLAUDE_MODEL") or "claude-sonnet-5-5"
БІН = os.environ.get("ZHYVA_BIN") or "/opt/node22/bin/claude"
СИСТЕМНИЙ = ("You are the model behind a mobile styling app. The user message is the application prompt, "
             "verbatim. Do exactly what it asks and output only the answer it asks for: raw JSON with no code "
             "fence when it asks for JSON, plain prose when it asks for prose. No preamble, no commentary, "
             "no tools, no questions back.")
ТЕКА = tempfile.mkdtemp(prefix="клод-проба-")  # нейтральна тека: CLAUDE.md репозиторію не підхоплюється
замок = threading.Lock(); у_польоті = 0; макс_одночасно = 0; сума = 0.0; номер = 0


def блоки_повідомлень(повід):
    """Блоки Anthropic з тексту й зображень у порядку повідомлень; None — коли зображень нема."""
    бл = []; є_фото = False; кілька = len(повід) > 1
    for м in повід:
        c = м.get("content"); ч = c if isinstance(c, list) else [{"type": "text", "text": c or ""}]
        if кілька: бл.append({"type": "text", "text": f"[{м.get('role')}]"})
        for б in ч:
            if not isinstance(б, dict): continue
            if б.get("type") == "text": бл.append({"type": "text", "text": б.get("text") or " "})
            elif б.get("type") == "image_url":
                url = (б.get("image_url") or {}).get("url") or ""
                if url.startswith("data:") and ";base64," in url:
                    тип, дані = url[5:].split(";base64,", 1)
                    бл.append({"type": "image", "source": {"type": "base64", "media_type": тип or "image/jpeg", "data": дані}}); є_фото = True
    return бл if є_фото else None


def текст_повідомлень(повід):
    ч = []
    for м in повід:
        c = м.get("content")
        if isinstance(c, list):
            c = "\n".join(б.get("text", "") for б in c if isinstance(б, dict) and б.get("type") == "text")
        ч.append(c or "")
    return ч[0] if len(ч) == 1 else "\n\n".join(f"[{м.get('role')}]\n{т}" for м, т in zip(повід, ч))


class О(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _відп(self, код, об):
        б = json.dumps(об, ensure_ascii=False).encode("utf-8")
        self.send_response(код); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(б))); self.end_headers(); self.wfile.write(б)

    def do_GET(self):
        self._відп(200, {"data": [{"id": МОДЕЛЬ}]})

    def do_POST(self):
        global у_польоті, макс_одночасно, сума, номер
        тіло = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        промпт = текст_повідомлень(тіло.get("messages") or [])
        фото = блоки_повідомлень(тіло.get("messages") or [])
        with замок:
            if сума >= СТЕЛЯ:
                return self._відп(503, {"error": f"стеля проби {СТЕЛЯ} $ вичерпана (сума {сума:.4f})"})
            у_польоті += 1; макс_одночасно = max(макс_одночасно, у_польоті); номер += 1
            н = номер; одночасно = у_польоті
        т0 = time.time(); запис = {"н": н, "початок_utc": time.strftime("%H:%M:%S", time.gmtime(т0)),
                                   "промпт_симв": len(промпт), "одночасно_на_старті": одночасно,
                                   "стеля_сторінки": тіло.get("max_tokens")}
        р = None; помилка = None
        try:
            формат = ["--input-format", "stream-json", "--output-format", "stream-json", "--verbose"] if фото else ["--output-format", "json"]
            вхід = (json.dumps({"type": "user", "message": {"role": "user", "content": фото}}) + "\n") if фото else промпт
            р = subprocess.run([БІН, "-p", "--model", МОДЕЛЬ, "--tools", "", "--strict-mcp-config",
                                "--no-session-persistence", *формат,
                                "--system-prompt", СИСТЕМНИЙ], input=вхід, capture_output=True, text=True,
                               timeout=900, cwd=ТЕКА,
                               env=dict(os.environ, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"))
            if фото:
                ітог = [json.loads(л) for л in р.stdout.splitlines() if л.strip().startswith("{")]
                ітог = next(д for д in ітог if д.get("type") == "result")
                запис["фото"] = sum(1 for б in фото if б["type"] == "image")
            else:
                ітог = json.loads(р.stdout)
        except Exception as e:
            ітог = None; помилка = f"{type(e).__name__}: {e}"[:300] + (" · " + (р.stderr or р.stdout)[:300] if р else "")
        с = time.time() - т0
        with замок:
            у_польоті -= 1
        текст = ""; u = {}; вартість = 0.0; стоп = "stop"; статус = 200
        if ітог is None or ітог.get("is_error") or ітог.get("subtype") != "success":
            статус = 429 if ітог and re_ліміт(ітог) else 599
            помилка = помилка or str(ітог.get("result") or ітог.get("api_error_status"))[:300]
        else:
            текст = ітог.get("result") or ""; u = ітог.get("usage") or {}; вартість = ітог.get("total_cost_usd") or 0.0
            if ітог.get("stop_reason") == "max_tokens": стоп = "length"
        if ітог: вартість = ітог.get("total_cost_usd") or 0.0
        with замок:
            сума += вартість; сума_зараз = сума
        вх = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        запис.update({"с": round(с, 1), "статус": статус, "usd": вартість, "вхід_нових": u.get("input_tokens"),
                      "вхід_кеш_читання": u.get("cache_read_input_tokens"),
                      "вхід_кеш_запис": u.get("cache_creation_input_tokens"), "вихід": u.get("output_tokens"),
                      "думка": (u.get("output_tokens_details") or {}).get("thinking_tokens"),
                      "стоп": ітог.get("stop_reason") if ітог else None, "симв_відповіді": len(текст),
                      "модель": list((ітог or {}).get("modelUsage") or {}), "помилка": помилка,
                      "сума_usd": round(сума_зараз, 4), "макс_одночасно_досі": макс_одночасно})
        with замок, open(ЖУРНАЛ, "a", encoding="utf-8") as ф:
            ф.write(json.dumps(запис, ensure_ascii=False) + "\n")
        if статус != 200:
            return self._відп(статус if статус != 599 else 502, {"error": помилка})
        self._відп(200, {"id": f"cl{н}", "object": "chat.completion", "model": МОДЕЛЬ,
                         "choices": [{"index": 0, "message": {"role": "assistant", "content": текст},
                                      "finish_reason": стоп}],
                         "usage": {"prompt_tokens": вх, "completion_tokens": u.get("output_tokens") or 0}})


def re_ліміт(ітог):
    import re
    return bool(re.search(r"rate|limit|quota|429", str(ітог.get("result")) + str(ітог.get("api_error_status")), re.I))


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", ПОРТ), О).serve_forever()
