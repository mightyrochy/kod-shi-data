"""Переходи вердикту `колір_тон.сім_ї_кольору` між решіткою бази й робочого дерева на каталозі (крок 20, 13668).

Запуск із кореня репозиторію (розпакований `джерела/каталог_повний.xml`):

    python3 -W ignore аудит/перевірка/річ_колір_межі_сім_ї_20261105/переходи_решітки.py <ревізія бази>

Базовий `колір_тон.py` — `git show <ревізія>:джерела/колір_тон.py`; друкує кожен перехід вердикту, слова крамниці
речей із переходом і зміну сили ахроматичної."""
import collections
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import колір_річ as КР  # noqa: E402
import колір_тон as П  # noqa: E402
import фід_каталог as ФК  # noqa: E402

текст = subprocess.run(["git", "show", f"{sys.argv[1]}:джерела/колір_тон.py"], cwd=КОРІНЬ, check=True,
                       capture_output=True).stdout
with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as ф:
    ф.write(текст)
сп = importlib.util.spec_from_file_location("колір_тон_база", ф.name)
Д = importlib.util.module_from_spec(сп)
сп.loader.exec_module(Д)
каталог = ФК.прочитати_каталог(ФК.каталог_на_диску("каталог_повний.xml"), 0)["каталог"]
переходи, слова, зміна, всього = collections.Counter(), collections.Counter(), [], 0
for річ in каталог:
    lab = КР.точка_кольору(річ)
    if lab is None:
        continue
    lab = [float(x) for x in lab]
    всього += 1
    до = "+".join(к for к, _ in Д.сім_ї_кольору(lab))
    після = "+".join(к for к, _ in П.сім_ї_кольору(lab))
    зміна.append(П.сили_сімей(lab).get("achromatic", 0) - Д.сили_сімей(lab).get("achromatic", 0))
    if до != після:
        переходи[(до, після)] += 1
        слова[річ.get("колір_назва")] += 1
print("речей з виміром:", всього, "вердикт змінився:", sum(переходи.values()))
for (до, після), n in переходи.most_common():
    print(f"  {до} → {після}: {n}")
print("слова:", слова.most_common())
змінені = [x for x in зміна if abs(x) > 1e-9]
print("сила achromatic змінилась у", len(змінені), "речей: зросла", sum(x > 0 for x in змінені), "впала",
      sum(x < 0 for x in змінені), "найбільше +%.3f, найменше %.3f" % (max(змінені, default=0), min(змінені, default=0)))
