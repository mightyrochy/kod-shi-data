"""Батарея читачів ознак до кінця, з окремими журналами та кодами виходу."""
import json
import os
import pathlib
import subprocess
import sys
import time


def main():
    """Виконує стандартні команди й релевантні сім'ї без зупинки на першій невдачі."""
    тека = pathlib.Path(__file__).resolve().parent
    дж = тека.parents[2] / "джерела"
    середовище = dict(os.environ, PYTHONUTF8="1", NODE_PATH=str(дж / "node_modules"))
    py = [sys.executable, "-W", "ignore"]
    команди = [py + [ім] for ім in ("стенд_знімок.py", "тест_живого_шляху.py", "тест_протоколу.py",
                                   "прилади/розділи_гейтів.py", "audit_contracts.py")]
    команди[0].append("--дим")
    команди.append(["node", "тест_показу.js"])
    імена = ("ознаки_обличчя_10704.py", "ознаки_підтон.py", "ознаки_підтон_палітра.py",
             "ознаки_походження.py", "помада_від_шкіри_1840.py", "очі_контраст_2330.py",
             "поділ_bridge_ast.py", "поділ_colorspace_ast.py", "поділ_суд_ast.py",
             "поділ_колір_образу_ast.py", "поділ_pipeline_ast.py", "поділ_palette_ast.py")
    команди += [py + ["проби/" + ім] for ім in імена]
    команди += [py + [str(ш.relative_to(дж))] for ш in sorted((дж / "проби").glob("pal_*.py"))
                if ш.name not in ("pal_вердикт.py", "pal_вимір.py")]
    результати = []
    for і, команда in enumerate(команди):
        журнал = "%02d-%s.txt" % (і + 1, pathlib.Path(команда[-1] if команда[-1] != "--дим" else команда[-2]).stem)
        початок = time.monotonic()
        with (тека / журнал).open("wb") as ф:
            вих = subprocess.run(команда, cwd=дж, env=середовище, stdout=ф, stderr=subprocess.STDOUT)
        запис = dict(команда=команда, код=вих.returncode, секунд=round(time.monotonic() - початок, 2), журнал=журнал)
        результати.append(запис)
        (тека / "батарея.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), "utf-8")
        print("%d/%d код %d · %s" % (і + 1, len(команди), вих.returncode, журнал), flush=True)
    return int(any(р["код"] for р in результати))


if __name__ == "__main__":
    sys.exit(main())
