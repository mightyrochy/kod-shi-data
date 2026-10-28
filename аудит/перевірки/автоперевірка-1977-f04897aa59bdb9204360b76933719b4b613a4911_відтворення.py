"""Відтворює зауваження до PR #1977 без мережі; аргумент — дерево перевіреної голови."""
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "zhnyvarka"))
import обхід

def запуск(журнал, магазини, режим, паралельно=1):
    вивід = io.StringIO()
    with redirect_stdout(вивід):
        обхід.main(["--журнал", журнал, "--магазини", магазини,
                    "--секунд-на-магазин", "1", "--секунд-на-цикл", "3",
                    "--циклів", "2", "--паралельно", str(паралельно), "--заглушка", режим])
    with open(Path(журнал) / "обхід_стан.tsv", encoding="utf-8") as ф:
        return вивід.getvalue().strip(), {р["домен"]: р for р in csv.DictReader(ф, delimiter="\t")}

with tempfile.TemporaryDirectory(prefix="перевірка1977-синхрон-") as ж:
    вивід, ряди = запуск(ж, "hang.com,ok.com", "синхронний_блок")
    print("ВИПАДОК 1: синхронне зависання першої крамниці, паралельно=1")
    print(вивід)
    for р in ряди.values():
        print(json.dumps(р, ensure_ascii=False))
    print("ok.com має сирий журнал:", (Path(ж) / "сирі" / "ok.com.jsonl").exists())
    вивід, ряди = запуск(ж, "hang.com,ok.com", "синхронний_блок")
    print("Повтор того самого порядку:", вивід)
    print("ok.com після повтору:", ряди["ok.com"]["стан_код"], ряди["ok.com"]["причина_код"])

with tempfile.TemporaryDirectory(prefix="перевірка1977-закриття-") as ж:
    print("ВИПАДОК 2: повтор після зависання закриття")
    вивід, ряди = запуск(ж, "hang.com", "закриття")
    print("Перший запуск:", вивід)
    print(json.dumps(ряди["hang.com"], ensure_ascii=False))
    вивід, ряди = запуск(ж, "hang.com", "успіх")
    print("Другий запуск:", вивід or "жодного циклу")
    print(json.dumps(ряди["hang.com"], ensure_ascii=False))

with tempfile.TemporaryDirectory(prefix="перевірка1977-джерело-") as ж:
    import sqlite3
    from unittest.mock import Mock, patch
    база = Path(ж) / "проходи" / "test.com" / "черга.sqlite3"
    база.parent.mkdir(parents=True)
    with sqlite3.connect(база) as з:
        з.executescript("CREATE TABLE черга(url TEXT, стан TEXT); CREATE TABLE мета(ключ TEXT, значення TEXT); INSERT INTO мета VALUES ('відомо','0');")
    з.close()
    ряд = dict(нотатка="sitemap +0;", карток="0", адрес_знайдено="0", відкрито="0")
    print("ВИПАДОК 3: порожня розвідка не доводить завершення")
    зведення = Path(ж) / "зведення_жнив.tsv"
    зведення.write_text("домен\n", encoding="utf-8")
    with patch.object(обхід, "останні_рядки", return_value=({"test.com": ряд}, 1)), patch.object(обхід.subprocess, "Popen", return_value=Mock(wait=Mock(return_value=0))) as процес:
        _, ряди = запуск(ж, "test.com", "успіх")
        print("Перший запуск, процесів:", процес.call_count)
        print(json.dumps(ряди["test.com"], ensure_ascii=False))
        вивід, _ = запуск(ж, "test.com", "успіх")
        print("Повтор, загалом процесів:", процес.call_count, ";", вивід or "жодного циклу")

with tempfile.TemporaryDirectory(prefix="перевірка1977-виняток-") as ж:
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import Mock, patch
    import виконавець
    class Браузер:
        async def new_context(self, **kwargs):
            raise RuntimeError("context creation failed")
    а = SimpleNamespace(журнал=ж, секунд_на_магазин=1, заглушка=None, без_огляду=True)
    в = виконавець.Виконавець(а)
    def завершити(timeout):
        async def крок():
            await в._магазин(Браузер(), dict(домен="test.com", сімейство="woo", транспорт="http"), asyncio.Semaphore(1))
        asyncio.run(крок())
        return 0
    print("ВИПАДОК 4: виняток створення контексту, бойовий _магазин без заглушки")
    with patch.object(обхід.subprocess, "Popen", return_value=Mock(wait=завершити)) as процес:
        _, ряди = запуск(ж, "test.com", "успіх")
        print(json.dumps(ряди["test.com"], ensure_ascii=False))
        вивід, _ = запуск(ж, "test.com", "успіх")
        print("Повтор, загалом процесів:", процес.call_count, ";", вивід or "жодного циклу")
