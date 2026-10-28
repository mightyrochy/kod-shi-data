"""Міряє невідому SQLite-чергу після обриву та її відновлення наступним обходом."""
import sqlite3, sys, tempfile
from pathlib import Path
from каталог_зависла_крамниця_sqlite_проба import обхід, прогін


def main():
    """Перевіряє перервану схему до запуску, при зведенні та після таймауту без нього."""
    помилок = 0
    for таблиць in range(4):
        for давній in (False, True):
            for зведення in (False, True):
                with tempfile.TemporaryDirectory(prefix="обхід-sqlite-") as ж:
                    тека = Path(ж) / "проходи" / "hang.com"; тека.mkdir(parents=True)
                    база = тека / "черга.sqlite3"
                    з = sqlite3.connect(база)
                    for sql in ("CREATE TABLE мета (ключ TEXT PRIMARY KEY, значення TEXT)",
                                "CREATE TABLE черга (url TEXT PRIMARY KEY, стан TEXT, відповідь INTEGER)",
                                "INSERT INTO черга VALUES ('https://hang.com/p1','INFLIGHT',NULL)")[:таблиць]:
                        з.execute(sql)
                    з.commit(); з.close()
                    if давній:
                        обхід.записати(ж, {"hang.com": dict(домен="hang.com", стан_код="WAIT", причина_код="TIMEOUT",
                            адрес=0, готово=0, лишилось=0, цикл=1, підстава="обрив")})
                    try:
                        до, _ = прогін(ж, обрив=True, зі_зведенням=зведення)
                        невідома = обхід.черга(ж, "hang.com") is None
                        після, запуски = прогін(ж)
                        добре = невідома and int(до["hang.com"]["лишилось"]) > 0 and до["ok.com"]["стан_код"] == "CATALOG"
                        добре &= запуски == ["hang.com"] and після["hang.com"]["стан_код"] == "CATALOG"
                        добре &= після["hang.com"]["лишилось"] == "0" and обхід.черга(ж, "hang.com") == (1, 1)
                        факт = f"невідома={невідома}, залишок={до['hang.com']['лишилось']}, ok=CATALOG, повтор={запуски}, готово={після['hang.com']['готово']}"
                    except Exception as збій:
                        добре, факт = False, f"{type(збій).__name__}: {збій}"
                    print(f"крок={таблиць}, давній={давній}, зведення={зведення}: {факт}; {'так' if добре else 'ПОМИЛКА'}")
                    помилок += not добре
    print(f"SQLite-повтор: помилок {помилок}/16")
    return int(bool(помилок))
if __name__ == "__main__":
    sys.exit(main())
