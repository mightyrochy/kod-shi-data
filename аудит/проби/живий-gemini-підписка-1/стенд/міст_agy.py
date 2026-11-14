#!/usr/bin/env python3
"""Прилад проби «Живий-gemini-підписка-1» (не код продукту): місцевий міст сторінки Люстерка до `agy` за підпискою.
Як `живий-як-людина-1/стенд/міст_claude.py` — сторінка шле тіло Anthropic-моста ({model, max_tokens, messages:[{role,
content:[text|image]}]}), міст віддає його моделі й повертає {content:[{type:text}], usage, stop_reason}. Відмінності
(і в README прогону): (1) `agy` не приймає блок зображення, тому фото речей (адреса крамниці) міст тягне, кладе файлом
`NN.ext` у нову теку виклику, а на місці блоку в тексті ставить `@NN.ext` — модель читає файл інструментом `read_file`;
(2) системного тексту `agy` не замінити (прапора нема), тож перед текстом сторінки — коротке доручення моста, а текст
сторінки — слово в слово між маркерами; (3) вхід — текст у stdin (`--input-format stream-json`), бо промпти сторінки
сягають 140 тис. символів, а рядок команди Windows — 32 тис.
Кожне звернення: `записи/<н>.json.gz` — стандартний вхід, сирий стандартний вивід `agy` (усі події), код повернення.
Запуск: python міст_agy.py <порт> <журнал.jsonl> <тека_записів> [модель]   (модель — і з AGY_MODEL)"""
import base64, gzip, json, os, re, shutil, subprocess, sys, tempfile, threading, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ПОРТ = int(sys.argv[1]); ЖУРНАЛ = sys.argv[2]; ЗАПИСИ = sys.argv[3]
МОДЕЛЬ = (sys.argv[4] if len(sys.argv) > 4 else None) or os.environ.get("AGY_MODEL") or "gemini-3.8-flash-high"
БІН = os.environ.get("AGY_BIN") or shutil.which("agy") or "agy"
СТЕЛЯ_С = int(os.environ.get("AGY_СТЕЛЯ_С") or 660)  # зовнішня стеля одного звернення; `--print-timeout` — на 30 с менше
ДОРУЧЕННЯ = ("You are the model behind a mobile styling app. Between the markers BEGIN APPLICATION PROMPT and END "
             "APPLICATION PROMPT is the application prompt, verbatim. Do exactly what it asks and output only the answer "
             "it asks for: raw JSON with no code fence when it asks for JSON, plain prose when it asks for prose. No "
             "preamble, no commentary, no questions back. Do not run commands, do not write or change files, do not use "
             "the network or other agents. The only tool you may use is read_file, and only on the image files that the "
             "prompt names as @NN.ext (each such file is the shop photo at that place of the prompt; read each one "
             "once, then answer).")
ТЕКА = os.path.join(os.environ.get("TEMP") or tempfile.gettempdir(), "міст-agy-" + str(os.getpid()))
os.makedirs(ТЕКА, exist_ok=True); os.makedirs(ЗАПИСИ, exist_ok=True)
замок = threading.Lock(); у_польоті = 0; макс_одночасно = 0; номер = 0
РОЗШ = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}


def кадр(url):
    """(байти, розширення, статус) — статус відповіді крамниці чи опис помилки."""
    try:
        з = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(з, timeout=20) as в:
            б = в.read(); тип = (в.headers.get("Content-Type") or "").split(";")[0].strip()
            статус = в.status
        if not б or len(б) > 5 * 1024 * 1024:
            return None, None, f"{статус} розмір {len(б)}"
        р = (".png" if б[:4] == b"\x89PNG" else ".webp" if б[8:12] == b"WEBP" else ".gif" if б[:3] == b"GIF"
             else ".jpg" if б[:2] == b"\xff\xd8" else РОЗШ.get(тип, ".jpg"))
        return б, р, статус
    except urllib.error.HTTPError as e:
        return None, None, e.code
    except Exception as e:
        return None, None, f"{type(e).__name__}"


def текст_і_фото(повід, теква):
    """Текст сторінки слово в слово; блок зображення → `@NN.ext` (файл у теці виклику). → (текст, [фото], розібрано)"""
    частини = []; фото = []
    for м in повід:
        if len(повід) > 1:
            частини.append(f"[{'assistant' if м.get('role') == 'assistant' else 'user'}]")
        c = м.get("content")
        if not isinstance(c, list):
            частини.append(str(c or "")); continue
        for б in c:
            if б.get("type") != "image":
                частини.append(б.get("text") or ""); continue
            дж = б.get("source") or {}; н = len(фото) + 1
            if дж.get("type") == "base64":
                дані = base64.b64decode(дж.get("data") or ""); р = РОЗШ.get(дж.get("media_type") or "", ".jpg"); статус = "base64"
                url = None
            else:
                url = дж.get("url") or ""; дані, р, статус = кадр(url)
            if дані:
                ім = f"{н:02d}{р}"
                with open(os.path.join(теква, ім), "wb") as ф: ф.write(дані)
                частини.append("@" + ім)
            else:
                частини.append("(image not delivered)")
            фото.append({"н": н, "url": url, "статус": статус, "дійшло": bool(дані), "байтів": len(дані or b"")})
    return "\n".join(частини), фото


class О(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _відп(self, код, об, заг=None):
        б = json.dumps(об, ensure_ascii=False).encode("utf-8")
        self.send_response(код); self.send_header("Content-Type", "application/json")
        for к, з in (заг or {}).items(): self.send_header(к, з)
        self.send_header("Content-Length", str(len(б))); self.end_headers(); self.wfile.write(б)

    def do_POST(self):
        global у_польоті, макс_одночасно, номер
        тіло = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        прохід = urllib.parse.unquote(self.headers.get("x-prohid") or "")
        with замок:
            у_польоті += 1; макс_одночасно = max(макс_одночасно, у_польоті); номер += 1; н = номер
        т0 = time.time(); теква = tempfile.mkdtemp(prefix=f"в{н}-", dir=ТЕКА)
        текст, фото = текст_і_фото(тіло.get("messages") or [], теква)
        вхід = (ДОРУЧЕННЯ + "\n\n===== BEGIN APPLICATION PROMPT =====\n" + текст + "\n===== END APPLICATION PROMPT =====")
        рядок = json.dumps({"event": "user", "message": {"content": [{"type": "text", "text": вхід}]}}, ensure_ascii=False) + "\n"
        запис = {"н": н, "прохід": прохід, "початок_utc": time.strftime("%H:%M:%S", time.gmtime(т0)), "модель": МОДЕЛЬ,
                 "промпт_симв": len(текст), "фото": len(фото), "фото_не_дійшло": sum(1 for ф in фото if not ф["дійшло"]),
                 "стеля_сторінки": тіло.get("max_tokens")}
        вивід = ""; помилка = None; код = None; ітог = None; читань = 0; читань_помилок = 0
        try:
            р = subprocess.run([БІН, "--model", МОДЕЛЬ, "--input-format", "stream-json", "--output-format", "stream-json",
                                "--disable-slash-commands", "--print-timeout", f"{СТЕЛЯ_С - 30}s"],
                               input=рядок.encode("utf-8"), capture_output=True, timeout=СТЕЛЯ_С, cwd=теква,
                               env=dict(os.environ, PYTHONUTF8="1"))
            код = р.returncode; вивід = р.stdout.decode("utf-8", "replace")
            for л in вивід.splitlines():
                try: о = json.loads(л)
                except Exception: continue
                if о.get("event") == "result": ітог = о.get("result") or {}
                с = о.get("step_update") or {}
                if с.get("step_type") == "tool" and с.get("state") in ("DONE", "ERROR"):
                    читань += 1; читань_помилок += с.get("state") == "ERROR"
            if ітог is None: помилка = f"rc {код}: " + (р.stderr.decode('utf-8', 'replace') or вивід)[-300:]
            err_stderr = р.stderr.decode("utf-8", "replace")
        except Exception as e:
            помилка = f"{type(e).__name__}: {e}"[:300]; err_stderr = ""
        с = time.time() - т0
        with замок: у_польоті -= 1
        відповідь = ""; u = {}; статус = 200
        if ітог is None or ітог.get("status") != "SUCCESS":
            статус = 429 if re.search(r"quota|rate|limit|429|exhaust", f"{помилка} {json.dumps(ітог or {}, ensure_ascii=False)} {err_stderr}", re.I) else 502
            помилка = помилка or str((ітог or {}).get("error") or (ітог or {}).get("status"))[:300]
        else:
            відповідь = (ітог.get("response") or "").strip(); u = ітог.get("usage") or {}
            if not відповідь: статус = 502; помилка = "порожня відповідь"
        with gzip.open(os.path.join(ЗАПИСИ, f"{н:04d}.json.gz"), "wt", encoding="utf-8") as ф:
            json.dump({"н": н, "прохід": прохід, "модель": МОДЕЛЬ, "фото": фото, "stdin": рядок, "stdout": вивід,
                       "stderr": err_stderr[-2000:], "код": код}, ф, ensure_ascii=False)
        запис.update({"с": round(с, 1), "статус": статус, "вхід": u.get("input_tokens"), "кеш_читання": u.get("cache_read_tokens"),
                      "вихід": u.get("output_tokens"), "роздуми": u.get("thinking_tokens"), "усього": u.get("total_tokens"),
                      "кроків": (ітог or {}).get("num_turns"), "читань_фото": читань, "читань_помилок": читань_помилок,
                      "симв_відповіді": len(відповідь), "помилка": помилка, "макс_одночасно_досі": макс_одночасно})
        with замок, open(ЖУРНАЛ, "a", encoding="utf-8") as ф:
            ф.write(json.dumps(запис, ensure_ascii=False) + "\n")
        shutil.rmtree(теква, ignore_errors=True)
        заг = {"x-model": МОДЕЛЬ}
        if фото: заг["x-images-dropped"] = str(запис["фото_не_дійшло"])
        if статус != 200:
            return self._відп(статус, {"error": {"message": помилка or "модель не відповіла"}}, заг)
        self._відп(200, {"content": [{"type": "text", "text": відповідь}],
                         "usage": {"input_tokens": (u.get("input_tokens") or 0) + (u.get("cache_read_tokens") or 0),
                                   "output_tokens": u.get("output_tokens") or 0},
                         "stop_reason": "end_turn"}, заг)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ThreadingHTTPServer(("127.0.0.1", ПОРТ), О).serve_forever()
