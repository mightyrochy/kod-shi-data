"""Рядки 6215, 6450: допит під карткою «Оціни мій образ» — промпт оцінки того самого суду, на місці схеми картки — схема
лише «answer» (`_ДОПИТ_СХЕМА`), хвіст «now» останнім (`промпт_допиту`). Replay кодом на записах сцен `ж1_оціни_образ_6б`:
ДО — записані оцінка й допит; ПІСЛЯ — ті самі записи в теперішньому порядку (схема останнім ключем після даних) з
хвостом `хвіст_допиту`. Друкує сцени, де схема допиту має ключі картки, і символи (токени Gemma 3 з
GEMMA_TOKENIZER=<tokenizer.json>) допиту поза спільним початком з оцінкою.
Запуск із `джерела`: [GEMMA_TOKENIZER=…] python3 проби/промпти3_допит_6215.py [гілка живих] [тека]"""
import sys, os, json, subprocess; sys.path.insert(0, '.')
import оцінка_образу as О, збирач_промптів as ЗП
ГІЛКА, ТЕКА = (sys.argv[1:] + ["origin/claude/zhyvi-1016-1", "аудит/живі_1016_1"][len(sys.argv[1:]):])[:2]
git = lambda *а: subprocess.run(["git", "-C", "..", "-c", "core.quotepath=off"] + list(а), capture_output=True, check=True).stdout.decode()
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer
    _Т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"])
ток = lambda т: len(_Т.encode(т, add_special_tokens=False).ids) if os.environ.get("GEMMA_TOKENIZER") else 0
обʼєкт = lambda ф: json.loads((п := git("show", "%s:%s" % (ГІЛКА, ф)).split("\n", 1)[1].split("\n\n── ВІДПОВІДЬ (")[0])[п.index("{"):])
дамп = lambda о: json.dumps(о, ensure_ascii=False, default=str)
КАРТКА = {"verdict", "works", "change"}
крок = lambda ф: int(ф.rsplit("/", 1)[1].split("_")[1])
def тепер(о, схема, хвіст=None):                # теперішній порядок: «task» без схеми, дані, схема, «now»
    о = dict(о, task={к: в for к, в in о["task"].items() if к not in ("answer", "answer_schema")}); о.pop("now", None)
    return дамп(dict(о, answer_schema=схема, **({"now": хвіст} if хвіст else {})))
файли = [ф for ф in git("ls-tree", "-r", "--name-only", ГІЛКА, ТЕКА).splitlines() if "/VIDPOVIDI/" in ф]
Л = dict(до_картка=0, після_картка=0, до_поза=[0, 0], після_поза=[0, 0], сцен=0)
for сц in sorted({ф.split("/")[2] for ф in файли if "ж1_оціни_образ_6б" in ф}):
    оц = sorted(ф for ф in файли if "/%s/" % сц in ф and ф.endswith("_ОЦІНКА_відповідь.txt"))
    доп = [ф for ф in файли if "/%s/" % сц in ф and ф.endswith("_ОЦІНКА_допит.txt")]
    if not оц or not доп:
        continue
    а, д = обʼєкт([ф for ф in оц if крок(ф) < крок(доп[0])][-1]), обʼєкт(доп[0])     # оцінка перед допитом
    Л["до_картка"] += bool(КАРТКА & set(д["task"].get("answer_schema") or д.get("answer_schema") or {}))
    п_а = тепер(а, ЗП.скелет(О.ОЦІНКА))
    п_д = json.loads(тепер(д, О._ДОПИТ_СХЕМА, О.хвіст_допиту(д["now"]["question"], д["now"]["previous"])))
    assert list(п_д)[-2:] == ["answer_schema", "now"] and дамп(п_д).startswith(п_а[:п_а.rindex(", \"answer_schema\"")])
    Л["після_картка"] += bool(КАРТКА & set(п_д["answer_schema"]))
    for к, (х, у) in (("до_поза", (дамп(а), дамп(д))), ("після_поза", (п_а, дамп(п_д)))):
        сп = len(os.path.commonprefix([х, у])); Л[к][0] += len(у) - сп; Л[к][1] += ток(у[сп:])
    Л["сцен"] += 1
print("сцен: %d (%s:%s)" % (Л["сцен"], ГІЛКА, ТЕКА))
print("схема допиту з ключами картки (verdict/works/change): ДО %d → ПІСЛЯ %d" % (Л["до_картка"], Л["після_картка"]))
print("допит поза спільним початком з оцінкою: ДО %d симв./%d ток. → ПІСЛЯ %d симв./%d ток." % (*Л["до_поза"], *Л["після_поза"]))
