"""Повторює мірила журналу на точній голові попередньої доробки."""
import os, subprocess, sys, tempfile
from pathlib import Path


def main():
    """Вивантажує лише потрібні історичні модулі й запускає ті самі нові проби."""
    корінь = Path(__file__).resolve().parents[2]
    база = "4d9184708f0d7c177f69bc2f22c496c23562b8e9"
    with tempfile.TemporaryDirectory() as ж:
        тека = Path(ж); (тека / "zhnyvarka").mkdir()
        for файл in (корінь / "zhnyvarka").glob("*.py"):
            п = subprocess.run(["git", "show", f"{база}:zhnyvarka/{файл.name}"], capture_output=True, cwd=корінь)
            if п.returncode == 0: (тека / "zhnyvarka" / файл.name).write_bytes(п.stdout)
        проби = тека / "джерела/проби"; проби.mkdir(parents=True)
        for назва in ("json_проба", "журнал", "журнал_json"):
            ім = f"каталог_зависла_крамниця_{назва}.py"
            (проби / ім).write_bytes(Path(__file__).with_name(ім).read_bytes())
        for назва in ("журнал", "журнал_json"):
            п = subprocess.run([sys.executable, str(проби / f"каталог_зависла_крамниця_{назва}.py")],
                capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
            print(п.stdout, end=""); assert п.returncode == 1, п.stderr
        доказ = корінь / "аудит/перевірки/доробка-53Б-журнал/відтворення.py"
        п = subprocess.run([sys.executable, str(доказ), ж], capture_output=True, text=True, encoding="utf-8")
        print(п.stdout, end="")
        assert п.returncode == 1 and "ОБРИВ/JSONL: UnicodeDecodeError" in п.stdout and "товар121=False" in п.stdout, п.stderr
    print("ДО 4d918470: обидва мірила падають; ті самі проби ПІСЛЯ мають код 0")


if __name__ == "__main__":
    main()
