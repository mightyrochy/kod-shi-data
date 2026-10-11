"""REPLAY ЖИВОЇ СЦЕНИ В ХМАРІ (НЕ-ЦЯ-36): записані відповіді моделей сцени (`VIDPOVIDI/` теки `аудит/живі_N/…`) віддаються
стенду замість LM Studio — той самий `рв6_стенд.js` із `MODEL`/`MODEL_MOVA`, лише `MODEL_URL` дивиться сюди. Виклик зіставляється
з записом свого класу (початок промпту без підписів кадрів), серед них — найсхожіший невзятий; коли записи класу скінчились,
бере найсхожіший уже взятий. Друкує кожне зіставлення зі схожістю: нижче ~0.9 — код ДО запису й код прогону дали різні промпти
(мовний шар карток із кадрами, що не дійшли в хмарі), і перевірки, що на них стоять, — не про правку.
Запуск (сцена 07 ЖИВІ-24; тека записів — з гілки `claude/zhyvi-24`, збірка — як у job `stend` `zbirka.yml`):
  python3 аудит/проби/replay_сцени.py <тека сцени> 1236 &
  CHROMIUM=/opt/pw-browsers/chromium-1194/chrome-linux/chrome MODEL_URL=http://127.0.0.1:1236/v1 MODEL=qwen/qwen3.5-9b \
  MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 FOTO=1 ZHINKA=аудит/проби/жінки/ж2.json CHAT_TEXT='…' OTSINKA=0 NE_TSIA=1 \
  NODE_PATH=джерела/node_modules node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 <тека збірки> <тека pyodide> 3"""
import sys, os, re, json, difflib, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

ТЕКА, ПОРТ = sys.argv[1], int(sys.argv[2])
ЗАПИСИ = []
for ф in sorted(os.listdir(os.path.join(ТЕКА, "VIDPOVIDI"))):
    м = re.match(r"seed\d+_(\d+)_(.*)\.txt$", ф)
    if not м:
        continue
    т = open(os.path.join(ТЕКА, "VIDPOVIDI", ф), encoding="utf8", errors="replace").read()
    г = re.match(r"── ПРОМПТ \(\d+ симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \(([^\n]*)\) ──\n(.*)\n$", т, re.S)
    if not г:
        continue
    статус = int((re.search(r"HTTP (\d+)", г.group(2)) or [0, 200])[1])
    ЗАПИСИ.append(dict(н=int(м.group(1)), тип=м.group(2), промпт=г.group(1), відп=г.group(3), статус=статус))
СТЕЛЯ = {int(x) for x in re.findall(r"↔ модель #(\d+) [^\n]*УПЕРЛОСЬ У СТЕЛЮ ВИВОДУ",
                                    open(os.path.join(ТЕКА, "лог.txt"), encoding="utf8", errors="replace").read())}
ВЗЯТО, ЗАМОК = set(), threading.Lock()
print("записів", len(ЗАПИСИ), "· у стелю", sorted(СТЕЛЯ), flush=True)


def клас(т):
    рядки = [р for р in т.split("\n") if р.strip() and not re.match(r"Photo \d+|\(image not delivered\)", р)]
    return re.sub(r"\d+", "#", (рядки or [""])[0][:140])


for з in ЗАПИСИ:
    з["клас"] = клас(з["промпт"])


def схожість(а, б):
    к = lambda x: x[:600] + "\n…\n" + x[-2500:]
    return difflib.SequenceMatcher(None, к(а), к(б), autojunk=False).quick_ratio() \
        if abs(len(а) - len(б)) > 0.5 * max(len(а), len(б), 1) else \
        difflib.SequenceMatcher(None, к(а), к(б), autojunk=False).ratio()


class Р(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        тіло = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        ост = (тіло.get("messages") or [{}])[-1].get("content")
        if isinstance(ост, list):
            текст = "\n".join(б.get("text", "") if б.get("type") == "text" else "" for б in ост
                              if б.get("text") != "(image not delivered)")
        else:
            текст = str(ост or "")
        with ЗАМОК:
            свої = [з for з in ЗАПИСИ if з["клас"] == клас(текст)]
            кандидати = [з for з in свої if з["н"] not in ВЗЯТО] or свої
            найкращий = max(кандидати, key=lambda з: (round(схожість(текст, з["промпт"]), 3), -з["н"]), default=None)
            if найкращий:
                ВЗЯТО.add(найкращий["н"])
        if not найкращий:
            print("  ✗ записи скінчились", текст[:80].replace("\n", " "), flush=True)
            self.send_response(500); self.end_headers(); self.wfile.write(b'{"error":"no record"}'); return
        с = схожість(текст, найкращий["промпт"])
        print("  #%02d %s · схожість %.3f%s" % (найкращий["н"], найкращий["тип"], с,
              "" if найкращий["клас"] == клас(текст) else " · ЧУЖИЙ КЛАС"), flush=True)
        if найкращий["статус"] != 200:
            self.send_response(найкращий["статус"]); self.end_headers()
            self.wfile.write(json.dumps({"error": найкращий["відп"][:300]}).encode()); return
        відп = {"choices": [{"message": {"content": найкращий["відп"]},
                             "finish_reason": "length" if найкращий["н"] in СТЕЛЯ else "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0}}
        дані = json.dumps(відп, ensure_ascii=False).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(дані))); self.end_headers(); self.wfile.write(дані)


ThreadingHTTPServer(("127.0.0.1", ПОРТ), Р).serve_forever()
