"""Сили сімей точок регресій #3196 (LCh) на d3e9540a (крок 18), fe6bb677 (крок 19) і в дереві. Запуск із кореня."""
import importlib.util, subprocess, sys, tempfile, math
sys.path.insert(0, "джерела")
import колір_тон as П
from колір_простір_перетворення import lab_з_lch, hex_з_lab, lch
def база(рев):
    т = subprocess.run(["git", "show", f"{рев}:джерела/колір_тон.py"], check=True, capture_output=True).stdout
    ф = tempfile.NamedTemporaryFile(suffix=".py", delete=False); ф.write(т); ф.close()
    сп = importlib.util.spec_from_file_location("кт_" + рев, ф.name); м = importlib.util.module_from_spec(сп)
    сп.loader.exec_module(м); return м
Б = [(р, база(р)) for р in ("d3e9540a", "fe6bb677")] + [("дерево", П)]
for L, C, h, ім in [(11.1, 3.6, 73, "жилет"), (16.8, 6.7, 3, "сумка тоут"), (12.5, 6.3, 41, "спідниця"), (16.3, 5.0, 21, "туфлі"),
                    (13.43, 4.37, 31.8, "№5 #231716"), (14.65, 3.9, 30, "#2a1a18?")]:
    lab = lab_з_lch(L, C, h)
    print(ім, (L, C, h), hex_з_lab(lab))
    for р, м in Б:
        print("   ", р, {к: round(с, 3) for к, с in list(м.сили_сімей(lab).items())[:4]})
