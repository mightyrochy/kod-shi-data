"""Відтворює хибне завершення JSON-крамниць на голові пачки #1992 без мережі."""
import os, subprocess, sys, tempfile
from pathlib import Path

def main():
    """Запускає ту саму пробу на історичному коді, зберігаючи робочу гілку."""
    корінь = Path(__file__).resolve().parents[2]
    база = "e4a72471c41a3f86619b69dde15b36ed44f1ddad"
    with tempfile.TemporaryDirectory(prefix="обхід-1992-до-") as ж:
        тека = Path(ж)
        (тека / "zhnyvarka").mkdir()
        for ім in ("обхід.py", "виконавець.py", "журнал_проходу.py"):
            код = subprocess.check_output(["git", "show", f"{база}:zhnyvarka/{ім}"], cwd=корінь)
            (тека / "zhnyvarka" / ім).write_bytes(код)
        проби = тека / "джерела" / "проби"
        проби.mkdir(parents=True)
        for суфікс in ("проба", "повтор"):
            ім = f"каталог_зависла_крамниця_json_{суфікс}.py"
            (проби / ім).write_bytes(Path(__file__).with_name(ім).read_bytes())
        п = subprocess.run([sys.executable, str(проби / ім)], capture_output=True, text=True,
                           encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=40)
        for рядок in п.stdout.splitlines():
            if рядок.startswith(("woo/", "shopify/", "JSON-повтор")):
                print(рядок)
        assert п.returncode == 1 and "JSON-повтор: помилок 16/20" in п.stdout, п.stderr or п.stdout
    print("5.3-Б ДО #1992: HTML 502 дає залишок=0 і повтор=0/2 для обох JSON-сімейств")

if __name__ == "__main__":
    main()
