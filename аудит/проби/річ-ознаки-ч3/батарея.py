"""Батарея й релевантні сім'ї послідовно, без пропуску наступних перевірок після збою."""
import json, os, pathlib, shutil, subprocess, sys, time


def main():
    """Записує журнали, коди й тривалість усіх перевірок до кінця."""
    К = pathlib.Path(__file__).resolve().parents[3]
    Д = pathlib.Path(__file__).resolve().parent
    дж = К / "джерела"
    скрипти = ["стенд_знімок.py --дим", "тест_живого_шляху.py", "тест_протоколу.py",
               "прилади/розділи_гейтів.py", "audit_contracts.py"]
    сімʼя = [p for p in sorted((дж / "проби").glob("*.py"))
             if p.stem.startswith(("pal_", "rang_", "bas_", "ознаки_"))
             and p.stem not in ("pal_вердикт", "pal_вимір", "ознаки_межа_5192")]
    скрипти += [str(p.relative_to(дж)) for p in сімʼя]
    скрипти += ["проби/поділ_palette_ast.py", "проби/поділ_суд_ast.py"]
    команди = [[sys.executable, "-W", "ignore", *s.split()] for s in скрипти]
    команди.append([shutil.which("node"), "тест_показу.js"])
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHON=sys.executable,
                       NODE_PATH=str(дж / "node_modules"))
    вих = []
    for н, команда in enumerate(команди, 1):
        поч = time.monotonic()
        try:
            р = subprocess.run(команда, cwd=дж, env=середовище, capture_output=True, timeout=900)
            код, лог = р.returncode, р.stdout + р.stderr
        except subprocess.TimeoutExpired as п:
            код, лог = 124, (п.stdout or b"") + (п.stderr or b"")
        ім = str(н).zfill(2) + "-" + pathlib.Path(команда[-1]).stem + ".log"
        (Д / ім).write_bytes(лог)
        вих.append(dict(команда=команда, код=код, секунд=round(time.monotonic()-поч, 1), журнал=ім))
        print(н, "/", len(команди), код, команда[-1], flush=True)
        (Д / "батарея.json").write_text(json.dumps(вих, ensure_ascii=False, indent=2), "utf8")
    return int(any(x["код"] for x in вих))


if __name__ == "__main__":
    sys.exit(main())
