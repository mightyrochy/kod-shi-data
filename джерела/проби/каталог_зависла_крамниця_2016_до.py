"""Відтворює незавершену SQLite-чергу на голові пачки #2016 тією самою пробою ПІСЛЯ."""
import os, subprocess, sys, tempfile
from pathlib import Path


def main():
    """Виконує історичні модулі в тимчасовій теці без зміни робочої гілки й мережі."""
    корінь = Path(__file__).resolve().parents[2]
    база = "faec4110bf5e104bc160f35524452aaaeb763806"
    with tempfile.TemporaryDirectory(prefix="обхід-2016-до-") as ж:
        тека = Path(ж)
        (тека / "zhnyvarka").mkdir()
        for ім in ("обхід.py", "виконавець.py", "журнал_проходу.py", "json_прохід.py"):
            код = subprocess.check_output(["git", "show", f"{база}:zhnyvarka/{ім}"], cwd=корінь)
            (тека / "zhnyvarka" / ім).write_bytes(код)
        проби = тека / "джерела" / "проби"; проби.mkdir(parents=True)
        for суфікс in ("sqlite", "sqlite_проба"):
            ім = f"каталог_зависла_крамниця_{суфікс}.py"
            (проби / ім).write_bytes(Path(__file__).with_name(ім).read_bytes())
        п = subprocess.run([sys.executable, str(проби / "каталог_зависла_крамниця_sqlite.py")],
                           capture_output=True, text=True, encoding="utf-8", timeout=60,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        print(п.stdout, end="")
        assert п.returncode == 1 and "SQLite-повтор: помилок 16/16" in п.stdout, п.stderr
        assert "OperationalError: no such table:" in п.stdout
    print("5.3-Б ДО #2016: обрив SQLite відтворено, 16/16 сценаріїв помилкові")


if __name__ == "__main__":
    main()
