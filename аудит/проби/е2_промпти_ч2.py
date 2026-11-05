"""Довжини промптів жнив ДО/ПІСЛЯ на всьому каталозі, без виклику моделі."""
import collections, json, re, subprocess, sys
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import feed, жнива_промпти as після
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "6377cbcf1adc6d443bbbb830ee1af8bf7b07a5d5"
до = type(sys)("жнива_до")
exec(compile(subprocess.check_output(["git", "-C", str(КОРІНЬ), "show", БАЗА + ":джерела/жнива_промпти.py"]).decode("utf-8"), "до.py", "exec"), до.__dict__)
офери = feed.читати_yml(feed.каталог_на_диску(str(КОРІНЬ / "джерела/каталог_повний.xml")))[0]
пари, кількість, порушення, знаків = {}, collections.Counter(), [], [0, 0]
for офер in офери:
    тип, слот = після.тип_речі(офер)
    набір = після.набір_слота(слот)
    тексти = [м._підставити(м.ПРОМПТ_НАБОРУ[набір], тип, слот == "сукня") for м in (до, після)]
    пари[набір + (":сукня" if слот == "сукня" else "")] = [len(т) - len(тип) for т in тексти]
    кількість[набір] += 1
    знаків = [с + len(т) for с, т in zip(знаків, тексти)]
    if len(тексти[1]) >= len(тексти[0]) or re.search(r"\{[а-я_]+\}", тексти[1]):
        порушення.append(офер["id"])
print(json.dumps(dict(база=БАЗА, оферів=len(офери), набори=кількість, довжини_без_типу=пари,
                     знаків=знаків, аркуш=[len(м.ПРОМПТ_АРКУШ) for м in (до, після)],
                     порушень=len(порушення)), ensure_ascii=False, indent=2))
import brief, міст_помічниця, пакет_моделі, вердикт_моделі, збирач_промптів as збирач
пари_оголошень = {}
for модуль, ім, дані in ((міст_помічниця, "ДОВІДКА", dict(question="q", app="app", state={"screen": "case"})),
                         (пакет_моделі, "СКЛАДАННЯ", dict(pool=[{"n": "#1·01"}], outfits_wanted=10)),
                         (вердикт_моделі, "РЕМОНТ", dict(verdict=[{"id": "o1"}], outfits_wanted=5))):
    старий = type(sys)("до_" + модуль.__name__)
    exec(compile(subprocess.check_output(["git", "-C", str(КОРІНЬ), "show", БАЗА + ":джерела/" + модуль.__name__ + ".py"]).decode("utf-8"), "до.py", "exec"), старий.__dict__)
    пари_оголошень[ім] = [len(json.dumps(збирач.зібрати(getattr(м, ім), дані), ensure_ascii=False)) for м in (старий, модуль)]
print(json.dumps(dict(оголошення=пари_оголошень), ensure_ascii=False))
sys.exit(bool(порушення) or not офери or any(б >= а for а, б in пари_оголошень.values()))
