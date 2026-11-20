"""Прилад виміру межі пулу (не код продукту): місцевий «міст», що НЕ кличе моделі, а віддає записані відповіді
справжнього моста з `аудит/проби/Живий-через-міст/стенд/службове/<ситуація>/обміни.jsonl` (той самий прохід).
Запит зіставляється із записаним за видом (роль задачі / перші 150 знаків тексту) і схожістю тексту; кожен записаний
обмін віддається раз, поки є невикористані того ж виду. Запити складання пишуться цілком у <журнал>.jsonl —
з них `межа_пулу.py` бере рядки пулу 43 400, на якому сторінка цього разу збирала.
Запуск: python3 міст_запис.py <порт> <журнал.jsonl>"""
import difflib, json, sys, threading, urllib.parse, pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ПОРТ = int(sys.argv[1]); ЖУРНАЛ = sys.argv[2]
ЗАПИСИ = pathlib.Path(__file__).resolve().parents[2] / "Живий-через-міст" / "стенд" / "службове"
замок = threading.Lock(); кеш = {}; взято = {}


def текст(тіло):
    return "".join(б.get("text", "") for м in тіло.get("messages") or [] for б in (м.get("content") if isinstance(м.get("content"), list) else [{"text": str(м.get("content") or "")}]) if б.get("type", "text") == "text")


def вид(т):
    try:
        р = (json.loads(т).get("task") or {}).get("role")
        if isinstance(р, str):
            return "role:" + р[:150]
    except Exception:
        pass
    return "text:" + т[:150]


def записи(сит, прохід):
    к = (сит, прохід)
    if к not in кеш:
        вих = []
        for р in open(ЗАПИСИ / сит / "обміни.jsonl", encoding="utf-8"):
            д = json.loads(р)
            if str(д.get("прохід")) != str(прохід) or not д.get("відповідь"):
                continue
            т = текст(json.loads(д["запит"]))
            вих.append(dict(вид=вид(т), т=т, статус=д.get("статус") or 200, відповідь=д["відповідь"]))
        кеш[к] = вих
    return кеш[к]


class О(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_POST(self):
        тіло = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        сит, _, прохід = urllib.parse.unquote(self.headers.get("x-prohid") or "").partition(" · ")
        т = текст(тіло); в = вид(т)
        with замок:
            зз = записи(сит.strip(), прохід.strip())
            вж = взято.setdefault((сит, прохід), set())
            кандидати = [і for і, з in enumerate(зз) if з["вид"] == в and і not in вж] or \
                        [і for і, з in enumerate(зз) if з["вид"] == в]
            if кандидати:
                і = max(кандидати, key=lambda і: difflib.SequenceMatcher(None, т[:3000], зз[і]["т"][:3000]).ratio())
                вж.add(і); з = зз[і]
                схож = round(difflib.SequenceMatcher(None, т[:3000], з["т"][:3000]).ratio(), 3)
            else:
                і, з, схож = None, None, 0
            рядок = {"сит": сит, "прохід": прохід, "вид": в[:80], "запис": і, "схожість": схож, "знаків": len(т)}
            if "Build outfits" in в:
                рядок["запит"] = т
            with open(ЖУРНАЛ, "a", encoding="utf-8") as ф:
                ф.write(json.dumps(рядок, ensure_ascii=False) + "\n")
        if з is None:
            б = json.dumps({"error": {"message": "нема записаної відповіді цього виду"}}).encode()
            self.send_response(502)
        else:
            б = з["відповідь"].encode("utf-8")
            self.send_response(int(з["статус"]))
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(б)))
        self.end_headers(); self.wfile.write(б)


ThreadingHTTPServer(("127.0.0.1", ПОРТ), О).serve_forever()
