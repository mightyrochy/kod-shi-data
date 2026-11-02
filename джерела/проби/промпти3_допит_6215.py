"""Рядки 6215, 6450: збирання оцінки й допиту справжніми функціями на входах записаних сцен `ж1_оціни_образ_6б`.
Підмінено лише підготовку даних суду: промпт, правила, схема й хвіст — продуктові. Друкує сцени, де схема допиту має
ключі картки, і символи (токени Gemma 3 з
GEMMA_TOKENIZER=<tokenizer.json>) допиту поза спільним початком з оцінкою.
Запуск із `джерела`: [GEMMA_TOKENIZER=…] python3 проби/промпти3_допит_6215.py [гілка живих] [тека]"""
import sys, os, json, subprocess; sys.path.insert(0, '.')
from unittest.mock import patch
import оцінка_образу as О
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
def тепер(о, хвіст=None):
    """Збирає справжній промпт на записаних даних суду, без повторного судження каталогу."""
    дані = {п.шлях: о[п.шлях] for п in О.ОЦІНКА.вхід if п.шлях in о}
    мова = о.get("task", {}).get("language") or о.get("language")
    with patch.object(О, "дані_оцінки", return_value=дані):
        return (О.промпт_допиту({}, хвіст["question"], хвіст["previous"], мова_тексту=мова) if хвіст else
                О.промпт_оцінки({}, мова_тексту=мова))
файли = [ф for ф in git("ls-tree", "-r", "--name-only", ГІЛКА, ТЕКА).splitlines() if "/VIDPOVIDI/" in ф]
Л = dict(до_картка=0, після_картка=0, до_поза=[0, 0], після_поза=[0, 0], сцен=0)
for сц in sorted({ф.split("/")[2] for ф in файли if "ж1_оціни_образ_6б" in ф}):
    оц = sorted(ф for ф in файли if "/%s/" % сц in ф and ф.endswith("_ОЦІНКА_відповідь.txt"))
    доп = [ф for ф in файли if "/%s/" % сц in ф and ф.endswith("_ОЦІНКА_допит.txt")]
    if not оц or not доп:
        continue
    а, д = обʼєкт([ф for ф in оц if крок(ф) < крок(доп[0])][-1]), обʼєкт(доп[0])     # оцінка перед допитом
    Л["до_картка"] += bool(КАРТКА & set(д["task"].get("answer_schema") or д.get("answer_schema") or {}))
    п_а = тепер(а)
    п_д = json.loads(тепер(д, д["now"]))
    assert list(п_д)[-2:] == ["answer_schema", "now"]
    assert not any('"%s"' % к in р for к in КАРТКА for р in п_д["task"]["rules"])
    Л["після_картка"] += bool(КАРТКА & set(п_д["answer_schema"]))
    for к, (х, у) in (("до_поза", (дамп(а), дамп(д))), ("після_поза", (п_а, дамп(п_д)))):
        сп = len(os.path.commonprefix([х, у])); Л[к][0] += len(у) - сп; Л[к][1] += ток(у[сп:])
    Л["сцен"] += 1
print("сцен: %d (%s:%s)" % (Л["сцен"], ГІЛКА, ТЕКА))
print("схема допиту з ключами картки (verdict/works/change): ДО %d → ПІСЛЯ %d" % (Л["до_картка"], Л["після_картка"]))
print("допит поза спільним початком з оцінкою: ДО %d симв./%d ток. → ПІСЛЯ %d симв./%d ток." % (*Л["до_поза"], *Л["після_поза"]))
