"""Черга одного проходу карток; відповіді й стан живуть поза репозиторієм."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3

ЗАВЕРШЕНІ = {"картка", "нижче_порогу", "російська_назва", "не_картка"}


class ЖурналПроходу:
    """Зберігає адреси до запиту, результат після fsync журналу карток."""

    def __init__(self, корінь, домен, відбиток, оновити=False, картки=None):
        self.корінь = Path(корінь).expanduser().resolve()
        if self.корінь.is_relative_to(Path(__file__).resolve().parents[1]) or any(
                (предок / ".git").exists() for предок in (self.корінь, *self.корінь.parents)):
            raise ValueError("JOURNAL_INSIDE_REPOSITORY")
        if not re.fullmatch(r"[a-z0-9.-]+", домен):
            raise ValueError("INVALID_STORE")
        self.тека = self.корінь / домен
        self.тека.mkdir(parents=True, exist_ok=True)
        self.база = sqlite3.connect(self.тека / "черга.sqlite3")
        self.база.executescript('''
            CREATE TABLE IF NOT EXISTS мета (ключ TEXT PRIMARY KEY, значення TEXT);
            CREATE TABLE IF NOT EXISTS черга (url TEXT PRIMARY KEY, стан TEXT, відповідь INTEGER);
            CREATE TABLE IF NOT EXISTS відповіді (
                ід INTEGER PRIMARY KEY, url TEXT, час TEXT, код INTEGER, sha256 TEXT,
                файл TEXT, тип TEXT, кінцева TEXT);
        ''')
        попередній = self.база.execute("SELECT значення FROM мета WHERE ключ='відбиток'").fetchone()
        with self.база:
            self.база.execute("UPDATE черга SET стан='PENDING' WHERE стан='INFLIGHT'")
            if оновити or not попередній or попередній[0] != відбиток:
                self.база.execute("UPDATE черга SET стан='PENDING'")
                self.база.execute("INSERT OR REPLACE INTO мета VALUES ('відомо','0')")
                self.база.execute("INSERT OR REPLACE INTO мета VALUES ('відбиток',?)", (відбиток,))
        for url, ід in self.база.execute("SELECT url, відповідь FROM черга WHERE стан='DONE'").fetchall():
            if not self.придатна(ід, url):
                with self.база:
                    self.база.execute("UPDATE черга SET стан='PENDING' WHERE url=?", (url,))
        if картки is not None:
            завершені = set()
            if Path(картки).exists():
                for рядок in Path(картки).read_text(encoding="utf-8").splitlines():
                    try:
                        запис = json.loads(рядок)
                        if запис.get("стан") in ЗАВЕРШЕНІ:
                            завершені.add((запис.get("url"), запис.get("відповідь")))
                    except json.JSONDecodeError:
                        continue  # Обірваний останній рядок не доводить завершення.
            for url, ід in self.база.execute("SELECT url, відповідь FROM черга WHERE стан='DONE'").fetchall():
                if (url, ід) not in завершені:
                    with self.база:
                        self.база.execute("UPDATE черга SET стан='PENDING' WHERE url=?", (url,))

    def продовження(self):
        """Не повторює пошук адрес відомого незавершеного проходу."""
        відомо = self.база.execute("SELECT значення FROM мета WHERE ключ='відомо'").fetchone()
        return bool(відомо and відомо[0] == '1' and self.звіт()["pending"])

    def перелік(self, адреси):
        """Починає новий прохід; відсутність адреси не видаляє давніх результатів."""
        with self.база:
            self.база.execute("UPDATE черга SET стан='PENDING'")
            for url in dict.fromkeys(адреси):
                self.база.execute("INSERT OR IGNORE INTO черга VALUES (?,'PENDING',NULL)", (url,))
            # Порожня розвідка не доводить вичерпання асортименту.
            self.база.execute("INSERT OR REPLACE INTO мета VALUES ('відомо',?)", ('1' if адреси else '0',))

    def очікують(self):
        """Повертає кожну незавершену адресу рівно раз у цьому запуску."""
        return [р[0] for р in self.база.execute("SELECT url FROM черга WHERE стан!='DONE' ORDER BY rowid")]

    def почати(self, url):
        """Фіксує in-flight до мережевого запиту."""
        with self.база:
            self.база.execute("UPDATE черга SET стан='INFLIGHT' WHERE url=?", (url,))

    def відповідь(self, url, код, тіло, тип="", кінцева=""):
        """Пише незмінне тіло та обмежені метадані без cookies й авторизації."""
        відбиток = hashlib.sha256(тіло).hexdigest()
        файл = self.тека / (відбиток + ".body")
        if not файл.exists() or hashlib.sha256(файл.read_bytes()).hexdigest() != відбиток:
            тимчасовий = файл.with_suffix(".tmp")
            with open(тимчасовий, "wb") as потік:
                потік.write(тіло)
                потік.flush()
                os.fsync(потік.fileno())
            os.replace(тимчасовий, файл)
        with self.база:
            запис = self.база.execute("INSERT INTO відповіді VALUES (NULL,?,?,?,?,?,?,?)", (
                url, datetime.datetime.now(datetime.timezone.utc).isoformat(), код,
                відбиток, файл.name, тип, кінцева or url))
        return запис.lastrowid

    def придатна(self, ід, url):
        """Кеш не є успіхом без цілого тіла й явного HTTP 200."""
        рядок = self.база.execute("SELECT код, sha256, файл, url FROM відповіді WHERE ід=?", (ід,)).fetchone()
        if not рядок or рядок[0] != 200 or рядок[3] != url:
            return False
        if рядок[2] != рядок[1] + ".body":
            return False
        try:
            тіло = (self.тека / рядок[2]).read_bytes()
        except FileNotFoundError:
            return False
        return bool(тіло and hashlib.sha256(тіло).hexdigest() == рядок[1])

    def завершити(self, запис):
        """Невідоме, заслон, збій і неповний розбір лишає до наступної спроби."""
        ід = запис.get("відповідь")
        стан = 'DONE' if запис.get("стан") in ЗАВЕРШЕНІ and self.придатна(ід, запис["url"]) else 'PENDING'
        with self.база:
            self.база.execute("UPDATE черга SET стан=?, відповідь=? WHERE url=?", (стан, ід, запис["url"]))

    def звіт(self):
        """Рахує URL, а не кількість повторних спроб чи карток."""
        загалом, готово = self.база.execute("SELECT count(*), coalesce(sum(стан='DONE'),0) FROM черга").fetchone()
        відомо = self.база.execute("SELECT значення FROM мета WHERE ключ='відомо'").fetchone()
        return {"total": загалом, "done": готово, "pending": загалом - готово,
                "queue_complete": bool(відомо and відомо[0] == '1' and загалом and загалом == готово), "source_complete": None}

    def закрити(self):
        """Закриває власне з'єднання після завершення крамниці."""
        self.база.close()


def відбиток_рецепта(рецепт):
    """Зміна рецепта чи коду вимагає нових відповідей замість давнього успіху."""
    дані = json.dumps(рецепт, sort_keys=True, ensure_ascii=False).encode()
    for назва in ("виконавець.py", "журнал_проходу.py"):
        дані += Path(__file__).with_name(назва).read_bytes()
    return hashlib.sha256(дані).hexdigest()
