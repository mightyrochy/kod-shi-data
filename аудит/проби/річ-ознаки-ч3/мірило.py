"""Повний незмінений прилад на незмінному зрізі ДО або робочому дереві ПІСЛЯ."""
import io, json, os, pathlib, subprocess, sys, tarfile, tempfile, time


def main():
    """Зберігає повний UTF-8 вивід і код; зріз ДО містить усе tracked джерела/."""
    К = pathlib.Path(__file__).resolve().parents[3]
    Д = pathlib.Path(__file__).resolve().parent
    режим = sys.argv[1]
    дерево = К
    база = "f932312e77"
    if режим == "до":
        дерево = pathlib.Path(tempfile.gettempdir()) / "ознаки-ч3-до"
        дерево.mkdir(exist_ok=True)
        архів = subprocess.check_output(["git", "archive", база, "джерела"], cwd=К)
        with tarfile.open(fileobj=io.BytesIO(архів)) as т:
            for член in т.getmembers():
                if not (дерево / член.name).resolve().is_relative_to(дерево.resolve()):
                    raise ValueError(член.name)
            т.extractall(дерево, filter="data")
    початок = time.monotonic()
    команда = [sys.executable, "-W", "ignore", str(К / "джерела/прилади/корінь_річ_ознаки_обличчя.py"),
               "--корінь", str(дерево)]
    try:
        р = subprocess.run(команда, cwd=К, capture_output=True, timeout=900,
                           env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"))
        код, вихід, помилка = р.returncode, р.stdout, р.stderr
    except subprocess.TimeoutExpired as п:
        код, вихід, помилка = 124, п.stdout or b"", п.stderr or b""
    (Д / (режим + ".txt")).write_bytes(вихід)
    (Д / (режим + "-помилка.txt")).write_bytes(помилка)
    мета = dict(база=база, команда=команда, код=код, секунд=round(time.monotonic()-початок, 1))
    (Д / (режим + "-мірило.json")).write_text(json.dumps(мета, ensure_ascii=False, indent=2), "utf8")
    print(json.dumps(мета, ensure_ascii=False), flush=True)
    return код


if __name__ == "__main__":
    sys.exit(main())
