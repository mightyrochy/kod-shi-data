"""Рядок 6215: допит під карткою «Оціни мій образ» — промпт оцінки того самого суду + хвіст «now» (`промпт_допиту`).
Replay кодом на записах ж15 (сцени 01–10 `ж1_оціни_образ_6б`): ДО — записаний допит; ПІСЛЯ — записаний промпт оцінки
тієї ж сцени й хвіст `хвіст_допиту` з її питання й «previous» записаного допиту. Друкує символи (і токени Gemma 3 з
GEMMA_TOKENIZER=<tokenizer.json>) допиту поза спільним початком з оцінкою, і всього.
Запуск із `джерела`: [GEMMA_TOKENIZER=…] python3 проби/промпти3_допит_6215.py [гілка живих, типово origin/claude/zhyvi-pachka-15]"""
import sys, os, json, subprocess; sys.path.insert(0, '.')
import оцінка_образу as О
ГІЛКА, ТЕКА = (sys.argv[1:] or ["origin/claude/zhyvi-pachka-15"])[0], "аудит/живі_пачка_15"
git = lambda *а: subprocess.run(["git", "-C", "..", "-c", "core.quotepath=off"] + list(а), capture_output=True, check=True).stdout.decode()
ток = (lambda т: len(_Т.encode(т, add_special_tokens=False).ids)) if os.environ.get("GEMMA_TOKENIZER") else (lambda т: None)
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer
    _Т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"])
промпт = lambda ф: git("show", "%s:%s" % (ГІЛКА, ф)).split("\n", 1)[1].split("\n\n── ВІДПОВІДЬ (")[0]
файли = [ф for ф in git("ls-tree", "-r", "--name-only", ГІЛКА, ТЕКА).splitlines() if "/VIDPOVIDI/" in ф]
Л = dict(до_поза=[0, 0], до_всього=[0, 0], після_поза=[0, 0], після_всього=[0, 0])
def додати(к, т):
    Л[к][0] += len(т); Л[к][1] += ток(т) or 0
сцен = 0
for сц in sorted({ф.split("/")[2] for ф in файли if "ж1_оціни_образ_6б" in ф}):
    оц = [ф for ф in файли if "/%s/" % сц in ф and ф.endswith("_ОЦІНКА_відповідь.txt")]
    доп = [ф for ф in файли if "/%s/" % сц in ф and ф.endswith("_ОЦІНКА_допит.txt")]
    if not оц or not доп:
        continue
    а, д = промпт(оц[0]), промпт(доп[0])
    сп = len(os.path.commonprefix([а, д]))
    додати("до_поза", д[сп:]); додати("до_всього", д)
    дані = json.loads(д[д.index("{"):])
    хвіст = json.dumps(О.хвіст_допиту(дані.get("question"), дані.get("previous")), ensure_ascii=False, default=str)
    після = а.rstrip()[:-1] + ', "now": ' + хвіст + "}"       # той самий вихід, що `json.dumps` промпту з ключем «now»
    assert json.loads(після[після.index("{"):])["now"]["rule"] and після.startswith(а.rstrip()[:-1])
    додати("після_поза", після[len(а.rstrip()) - 1:]); додати("після_всього", після)
    сцен += 1
ф = lambda к: "%d симв. / %s ток." % (Л[к][0], Л[к][1] if os.environ.get("GEMMA_TOKENIZER") else "—")
print("сцен: %d (%s)" % (сцен, ГІЛКА))
print("допит поза спільним початком з оцінкою: ДО %s → ПІСЛЯ %s" % (ф("до_поза"), ф("після_поза")))
print("допит усього в промпті:                ДО %s → ПІСЛЯ %s" % (ф("до_всього"), ф("після_всього")))
