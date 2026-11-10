"""Темні коричневі каталогу (слово буре, L* ≤ 35): вердикт `колір_тон.сім_ї_кольору` на ревізіях-аргументах і в дереві.
Запуск із кореня: python3 -W ignore <шлях> d3e9540a fe6bb677"""
"""Темні коричневі каталогу: вердикт на базах і в дереві."""
import collections, importlib.util, subprocess, sys, tempfile, re
sys.path.insert(0, "джерела")
import колір_річ as КР, колір_тон as П, фід_каталог as ФК
from колір_простір_перетворення import lch
def база(рев):
    т = subprocess.run(["git", "show", f"{рев}:джерела/колір_тон.py"], check=True, capture_output=True).stdout
    ф = tempfile.NamedTemporaryFile(suffix=".py", delete=False); ф.write(т); ф.close()
    сп = importlib.util.spec_from_file_location("кт_" + рев, ф.name); м = importlib.util.module_from_spec(сп)
    сп.loader.exec_module(м); return м
Б = {р: база(р) for р in sys.argv[1:]}
кат = ФК.прочитати_каталог(ФК.каталог_на_диску("каталог_повний.xml"), 0)["каталог"]
БУРЕ = re.compile(r"коричн|шоколад|кав|мокко|мока|бур|каштан|горіх|капучин|кемел|тауп|какао", re.I)
лічба = collections.Counter(); рядки = []
for р in кат:
    lab = КР.точка_кольору(р)
    if lab is None: continue
    lab = [float(x) for x in lab]; L, C, h = lch(lab)
    сл = (р.get("колір_назва") or "")
    if not БУРЕ.search(сл) or L > 35: continue
    в = ["+".join(к for к, _ in м.сім_ї_кольору(lab)) for м in Б.values()] + ["+".join(к for к, _ in П.сім_ї_кольору(lab))]
    перша = [x.split("+")[0] for x in в]
    лічба[tuple(перша)] += 1
    if len(set(в)) > 1:
        рядки.append((round(L,1), round(C,1), round(h), КР.hex_кольору(р) if hasattr(КР,"hex_кольору") else "", сл, (р.get("назва") or "")[:40], " | ".join(в)))
print("темних бурих (L*≤35, слово буре):", sum(лічба.values()))
for к, н in лічба.most_common(): print("  перша сім'я", " → ".join(к), н)
for r in sorted(рядки): print(r)
