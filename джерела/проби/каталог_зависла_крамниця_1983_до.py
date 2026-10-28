"""Відтворює обидві P1 на голові пачки #1983 тими самими пробами, що міряють виправлення."""
import os, subprocess, sys, tempfile
from pathlib import Path


def main():
    """Запускає проби на ізольованих історичних модулях без мережі й змін робочої гілки."""
    корінь = Path(__file__).resolve().parents[2]
    база = "16f0e7d994ddc6884cbce3d78bcc91527d4333b2"
    with tempfile.TemporaryDirectory(prefix="обхід-1983-до-") as ж:
        тека = Path(ж)
        (тека / "zhnyvarka").mkdir()
        for ім in ("обхід.py", "виконавець.py", "журнал_проходу.py"):
            код = subprocess.check_output(["git", "show", f"{база}:zhnyvarka/{ім}"], cwd=корінь)
            (тека / "zhnyvarka" / ім).write_bytes(код)
        проби = тека / "джерела" / "проби"
        проби.mkdir(parents=True)
        for назва in ("перелік", "черговість"):
            ім = f"каталог_зависла_крамниця_{назва}.py"
            (проби / ім).write_bytes(Path(__file__).with_name(ім).read_bytes())
            п = subprocess.run([sys.executable, str(проби / ім)], capture_output=True, text=True,
                               encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=40)
            print(п.stdout, end="")
            assert п.returncode == 1, п.stderr or f"{назва}: очікується відтворення вади"
            if назва == "перелік":
                assert п.stdout.count("запусків=1/2") == 4 and п.stdout.count("запусків=0/2") == 1
            else:
                assert п.stdout.count("CATALOG=0/2") == 2
    print("5.3-Б ДО #1983: перелік — 5/6 помилкових, черговість — 2/6; обидві P1 відтворено")


if __name__ == "__main__":
    main()
