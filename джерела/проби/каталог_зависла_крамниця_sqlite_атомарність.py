"""Перериває справжній процес під час створення SQLite-схеми й перевіряє відновлення."""
import os, sqlite3, subprocess, sys, tempfile
from contextlib import closing
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
from журнал_проходу import ЖурналПроходу, прочитати_чергу


def main():
    """Доводить відсутність часткової схеми після примусової зупинки на кожній межі DDL."""
    if len(sys.argv) > 1:
        підключити, межа = sqlite3.connect, int(sys.argv[2])
        def підключення(*арг, **поля):
            """Зупиняє процес перед черговим CREATE через трасування SQLite."""
            база, лічба = підключити(*арг, **поля), [0]
            def трасувати(sql):
                """Обриває створення після появи файла й перед завершенням схеми."""
                if sql.startswith("CREATE TABLE"):
                    лічба[0] += 1
                    if лічба[0] == межа:
                        os._exit(7)
            база.set_trace_callback(трасувати)
            return база
        sqlite3.connect = підключення
        ЖурналПроходу(sys.argv[1], "hang.com", "проба")
        raise AssertionError("процес не перервано")
    for межа in (1, 2, 3):
        with tempfile.TemporaryDirectory(prefix="обхід-sqlite-ddl-") as ж:
            п = subprocess.run([sys.executable, __file__, ж, str(межа)], timeout=10)
            база = Path(ж) / "hang.com" / "черга.sqlite3"
            assert п.returncode == 7 and база.is_file() and прочитати_чергу(база) is None
            with closing(sqlite3.connect(база)) as з:
                assert not з.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            журнал = ЖурналПроходу(ж, "hang.com", "проба")
            журнал.перелік(["/p1"]); журнал.закрити()
            assert прочитати_чергу(база) == (1, 0, True)
            print(f"DDL {межа}/3: обрив=7, часткових таблиць=0, відновлено pending=1")

if __name__ == "__main__":
    main()
