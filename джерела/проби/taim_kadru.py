# -*- coding: utf-8 -*-
"""ПРОБА: `--тайм-кадру` не дає ОДНОМУ кадру тримати річ (наряд Н-6, 27.09.2026).
ФАКТ, який перевіряється: жодна річ не коштує більше за стелю. До патча вихід із
`with ThreadPoolExecutor(...)` чекав КОЖЕН потік, тому річ коштувала стільки, скільки її
найповільніший кадр (виміряно 27.09: кадр у TimeoutError на 85.8 с, кадр на 128.4 с).
ДРУКУЄ час кожної речі проти стелі, скільки кадрів не встигло і скільки речей пішло в
чергу повтору. Прогін `--сухо`: карту не займає, тож можна пускати поряд із виміром.
ЗАПУСК (тека `джерела`): python проби/taim_kadru.py [стеля_с] [речей]"""
import gzip, json, os, re, subprocess, sys, tempfile

стеля = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
речей = int(sys.argv[2]) if len(sys.argv) > 2 else 3
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
тимч = tempfile.gettempdir()
вих = os.path.join(тимч, "proba_taim_kadru.json.gz")
наказ = [sys.executable, "-u", "жнива_кадри.py", "--сухо", "--кеш", "--заново",
         "--тайм-кадру", str(стеля), "--ліміт", str(речей), "--крамниці", "sunwin-store.com",
         "--кеш-індекс", os.path.join(тимч, "zhnyva_v2_cache", "кадри_індекс_proba.json"),
         "--вихід", вих]
п = subprocess.run(наказ, cwd=ТУТ, capture_output=True, text=True, encoding="utf-8", errors="replace")
часи = [float(м) for м in re.findall(r"з кешу \d+, ([\d.]+) с", п.stdout)]
повторів = len(re.findall(r"^повтор \[", п.stdout, re.M))
if not часи:
    print("проба не побачила жодної речі; код %d; хвіст: %s" % (п.returncode, (п.stdout + п.stderr)[-300:]))
    sys.exit(1)
ЗАПАС = 1.5                                  # накладні на запуск потоків і запис кадру на диск
for н, с in enumerate(часи, 1):
    print("річ %d: %.1f с%s" % (н, с, "  ← ПОНАД СТЕЛЮ" if с > стеля + ЗАПАС else ""))
зп = json.load(gzip.open(вих, "rt", encoding="utf-8"))["записи"]
не_встигло = sum(1 for р in зп.values() for в in р if в.get("не_встиг"))
print("стеля %.0f с; найдовша річ %.1f с; кадрів не встигло %d; речей у черзі повтору %d"
      % (стеля, max(часи), не_встигло, повторів))
print("ФАКТ: %s" % ("жодна річ не перевищила стелю" if max(часи) <= стеля + ЗАПАС
                    else "Є РІЧ ПОНАД СТЕЛЮ — стеля не діє"))
