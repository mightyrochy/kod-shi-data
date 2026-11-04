"""Батарея до кінця зі збереженням результатів та очікуванням усіх дочірніх процесів."""
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    файл = Д / "батарея.json"
    попередні = json.loads(файл.read_text("utf8")) if "--продовжити" in sys.argv else []
    вих = {tuple(x["команда"]): x for x in попередні}
    місць = int(sys.argv[sys.argv.index("--паралельно") + 1]) if "--паралельно" in sys.argv else 1

    def виконати(н, команда):
        """Очікує один процес і зберігає його повний журнал."""
        поч = time.monotonic()
        try:
            р = subprocess.run(команда, cwd=дж, env=середовище, capture_output=True, timeout=900)
            код, лог = р.returncode, р.stdout + р.stderr
        except subprocess.TimeoutExpired as п:
            код, лог = 124, (п.stdout or b"") + (п.stderr or b"")
        ім = str(н).zfill(2) + "-" + pathlib.Path(команда[-1]).stem + ".log"
        (Д / ім).write_bytes(лог)
        return dict(команда=команда, код=код, секунд=round(time.monotonic()-поч, 1), журнал=ім)

    def зберегти(результат):
        """Записує зведення лише в головному потоці."""
        вих[tuple(результат["команда"])] = результат
        зведення = [вих[tuple(c)] for c in команди if tuple(c) in вих]
        файл.write_text(json.dumps(зведення, ensure_ascii=False, indent=2), "utf8")
        print(len(вих), "/", len(команди), результат["код"], результат["команда"][-1], flush=True)

    with ThreadPoolExecutor(max_workers=місць) as пул:
        задачі = [пул.submit(виконати, н, c) for н, c in enumerate(команди[:-1], 1) if tuple(c) not in вих]
        for задача in as_completed(задачі):
            зберегти(задача.result())
    if tuple(команди[-1]) not in вих:
        зберегти(виконати(len(команди), команди[-1]))
    return int(any(x["код"] for x in вих.values()))


if __name__ == "__main__":
    sys.exit(main())
