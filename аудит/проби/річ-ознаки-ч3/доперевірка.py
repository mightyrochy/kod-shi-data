"""Окремо повторює невдалі перевірки середовища без зміни їхніх меж."""
import json, os, pathlib, subprocess, sys, tempfile, time


def main():
    """Зберігає точні коди, час і стан після імпорту трьох приладів."""
    К = pathlib.Path(__file__).resolve().parents[3]
    Д = pathlib.Path(__file__).resolve().parent
    дж = К / "джерела"
    вих = []
    середа = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONPATH=str(дж))
    def вміст(тека):
        return {p.name for p in тека.iterdir() if p.name != "__pycache__" and p.suffix != ".pyc"}
    до = вміст(дж)
    with tempfile.TemporaryDirectory(prefix="ч3-імпорт117-") as т:
        for ім in ("траса_петлі", "гейти_нові", "measure_person_axis"):
            поч = time.time()
            р = subprocess.run([sys.executable, "-c", "import " + ім], cwd=т, env=середа,
                               capture_output=True, timeout=10)
            час = round(time.time() - поч, 2)
            вих.append(dict(імпорт=ім, код=р.returncode, секунд=час, межа=2,
                            stderr=р.stderr.decode("utf8"), пройшло=р.returncode == 0 and час < 2))
        сміття = sorted(вміст(pathlib.Path(т)))
    assert not сміття and вміст(дж) == до
    середа["PATH"] = r"C:\Program Files\Git\usr\bin" + os.pathsep + середа["PATH"]
    for назва, команда in (
        ("rang-радимо-повтор", [sys.executable, "-W", "ignore", "проби/rang_радимо.py"]),
        ("читачі-фінал", [sys.executable, "-W", "ignore", str(Д / "порівняти.py")]),
        ("самозвіти-фінал", [sys.executable, "-W", "ignore", str(Д / "самозвіти.py")]),
        ("колір-фінал", [sys.executable, "-W", "ignore", str(Д / "читач_кольору.py"), "--перевірити"]),
        ("повтор-фінал", [sys.executable, "-W", "ignore", str(Д / "повтор.py"), "після"]),
    ):
        поч = time.monotonic()
        р = subprocess.run(команда, cwd=дж, env=середа, capture_output=True)
        (Д / (назва + ".log")).write_bytes(р.stdout + р.stderr)
        вих.append(dict(проба=назва, команда=команда, код=р.returncode,
                        секунд=round(time.monotonic()-поч, 1), пройшло=р.returncode == 0))
        print(назва, р.returncode, flush=True)
    (Д / "доперевірка.json").write_text(json.dumps(вих, ensure_ascii=False, indent=2), "utf8")
    return int(not all(x["пройшло"] for x in вих))


if __name__ == "__main__":
    sys.exit(main())
