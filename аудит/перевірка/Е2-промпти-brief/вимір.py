"""Вимірює обидва формати brief та їхніх викликачів проти заданого коміту без запуску моделі."""
import itertools
import json
from pathlib import Path
import subprocess
import sys
import types

if __name__ == "__main__":
    корінь = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(корінь / "джерела"))
    import brief as після
    import повнота_образу as вибір

    sha = sys.argv[1] if len(sys.argv) > 1 else "6028f963a49c8a9d2c274385fb85699652b393e4"
    текст = subprocess.check_output(["git", "show", sha + ":джерела/brief.py"], cwd=корінь).decode("utf-8")
    до = types.ModuleType("brief_до")
    exec(compile(текст, "brief_до.py", "exec"), до.__dict__)
    результат = {"база": sha, "формати": {}, "виклики": []}
    for ім in ("ФОРМАТ", "ФОРМАТ_ЛИШЕ_ТЕКСТ"):
        старий, новий = getattr(до, ім), getattr(після, ім)
        assert старий.rsplit("\n\n", 1)[0] == новий.rsplit("\n\n", 1)[0]
        assert новий.endswith(після._МЕЖІ_ОПИСУ) and новий.count(після._МЕЖІ_ОПИСУ) == 1
        результат["формати"][ім] = [len(старий), len(новий)]
    образи = [dict(підпис="о1", речі=[], свідомі=[], блокує=[], знахідки=[])]
    for без_фото, вимоги, колір, словник in itertools.product((False, True), ("", "тонкі підбори"), ("", "червоний"), (False, True)):
        блок = dict(текст="умови") if словник else "умови"
        а = до.запит_B("офіс", блок, вимоги, без_фото, колір)
        б = після.запит_B("офіс", блок, вимоги, без_фото, колір)
        assert len(б) < len(а) and а.rsplit("\n\n", 1)[0] == б.rsplit("\n\n", 1)[0]
        результат["виклики"].append(dict(виклик="запит_B", без_фото=без_фото, вимоги=вимоги, колір=колір,
                                           словник=словник, довжини=[len(а), len(б)]))
    for без_фото in (False, True):
        вибір._Б = до
        а = вибір.промпт_вибору(образи, "офіс", без_фото)
        вибір._Б = після
        б = вибір.промпт_вибору(образи, "офіс", без_фото)
        assert len(б) < len(а) and а.rsplit("\n\n", 1)[0] == б.rsplit("\n\n", 1)[0]
        результат["виклики"].append(dict(виклик="промпт_вибору", без_фото=без_фото, довжини=[len(а), len(б)]))
    assert all(б < а for а, б in результат["формати"].values())
    print(json.dumps(результат, ensure_ascii=False, indent=2))
