"""Запис нового виду (`джерела/запис_речі.py`: промпт і розбір з одного визначення міток ядра) для речей одягу складів і
пулів — той самий код і модель, що пройшли мірило кольору #4856: `claude -p --model sonnet --effort high` за підпискою,
без інструментів; слова крамниці й таблиця мірок — `вхід.поля_крамниці` проби 300; фото — уся галерея (до 8 кадрів,
/tmp/пс/фото від `запис_фото.py`). Журнал дописується, готові пропускає.
Запуск з кореня: python3 <цей скрипт> <журнал.jsonl> [паралельно]"""
import base64, glob, gzip, json, os, pickle, subprocess, sys, tempfile, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "аудит/проби/запис-речі-вибірка-300/скрипти"); sys.path.insert(0, "джерела")
from вхід import поля_крамниці, P
import запис_речі
ЖУРНАЛ = sys.argv[1]; ПАР = int(sys.argv[2]) if len(sys.argv) > 2 else 6
МОДЕЛЬ, ЗУСИЛЛЯ = "sonnet", "high"
БІН = "/opt/node22/bin/claude"
ОДЯГ = {"верх", "низ", "сукня", "комплект", "верхній_шар"}
Р = {р["id"]: р for р in pickle.load(open("/tmp/каталог_рядки.pkl", "rb"))}
ІДИ = [і for і in json.load(open("/tmp/пс/речі_запису.json")) if Р[і].get("слот") in ОДЯГ]
ПОТРІБНІ = {і.split("@")[0] for і in ІДИ}
R = {}
for л in gzip.open("каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8"):
    р = json.loads(л)
    if р.get("ід") in ПОТРІБНІ: R[р["ід"]] = р
ТЕКА = tempfile.mkdtemp(prefix="прохід-"); замок = threading.Lock(); готові = set()
if os.path.exists(ЖУРНАЛ):
    for л in open(ЖУРНАЛ, encoding="utf-8"):
        з = json.loads(л)
        if з.get("статус") == "ok": готові.add(з["ід"])
def фото_речі(ід):
    return sorted(glob.glob("/tmp/пс/фото/%s-*.jpg" % ід.split("@")[0]), key=lambda ф: int(ф.rsplit("-", 1)[1][:-4]))
def один(ід):
    р = R[ід.split("@")[0]]
    фото = фото_речі(ід)
    таблиця = P(р, "таблиця_мірок")
    системний, текст = запис_речі.промпт(поля_крамниці(р), len(фото), таблиця[:1400] if таблиця else None)
    бл = [{"type": "text", "text": текст}]
    for ф in фото:
        бл.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(open(ф, "rb").read()).decode()}})
    вхід = json.dumps({"type": "user", "message": {"role": "user", "content": бл}}, ensure_ascii=False) + "\n"
    з = {"ід": ід, "модель": МОДЕЛЬ, "зусилля": ЗУСИЛЛЯ, "фото": len(фото)}
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
                з.update({"статус": "ok", "с": round(ітог["duration_ms"] / 1000, 1), "вхід_нових": u["input_tokens"],
                          "вхід_кеш_запис": u["cache_creation_input_tokens"], "вхід_кеш_читання": u["cache_read_input_tokens"],
                          "вихід": u["output_tokens"], "моделі": list(ітог.get("modelUsage") or {}), "текст": ітог.get("result") or ""})
                break
            з.update({"статус": "збій", "помилка": (str((ітог or {}).get("result")) + " " + п.stderr)[-300:]})
        except Exception as e:
            з.update({"статус": "збій", "помилка": f"{type(e).__name__}: {e}"[:300]})
    with замок, open(ЖУРНАЛ, "a", encoding="utf-8") as ф: ф.write(json.dumps(з, ensure_ascii=False) + "\n")
    return з["статус"]
рядки = [і for і in ІДИ if і not in готові and (фото_речі(і) or os.environ.get("БЕЗ_ФОТО"))]
with ThreadPoolExecutor(ПАР) as п: підсумок = list(п.map(один, рядки))
print("зроблено", підсумок.count("ok"), "збоїв", len(підсумок) - підсумок.count("ok"), "готових раніше", len(готові), "без фото не взято", sum(1 for і in ІДИ if not фото_речі(і)))
