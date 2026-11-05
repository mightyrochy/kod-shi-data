"""Перевіряє межі UTC, накопичувальні usage та побайтове відтворення результатів."""

import csv
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def записати(шлях, записи):
    """Пише малий штучний журнал без приватних даних."""
    шлях.parent.mkdir(parents=True, exist_ok=True)
    шлях.write_text("".join(json.dumps(з) + "\n" for з in записи), encoding="utf-8")


def головна():
    """Виконує перевірки на штучних подіях та на збереженому результаті."""
    тека = Path(__file__).resolve().parent
    специфікація = importlib.util.spec_from_file_location("вивантаження", тека / "вивантажити.py")
    модуль = importlib.util.module_from_spec(специфікація)
    специфікація.loader.exec_module(модуль)
    with tempfile.TemporaryDirectory(dir=os.environ.get("TEMP")) as тимчасова:
        корінь = Path(тимчасова)
        журнал = корінь / "сесії/сесія.jsonl"
        записи = [{"timestamp": "2026-10-28T23:59:00Z", "type": "session_meta", "payload": {
            "id": "сесія", "timestamp": "2026-10-28T23:59:00Z", "cwd": "w/20261029-015900-aaaaaaaaaaaa/repo"}}]
        for дата, вхід, вихід in [("2026-10-28T23:59:59Z", 90, 10), ("2026-10-29T00:00:00Z", 90, 10),
                                  ("2026-10-29T00:00:01Z", 120, 20), ("2026-11-05T00:00:00Z", 140, 25)]:
            записи.append({"timestamp": дата, "type": "event_msg", "payload": {"type": "token_count", "info": {
                "total_token_usage": {"input_tokens": вхід, "cached_input_tokens": 20, "output_tokens": вихід,
                                      "reasoning_output_tokens": 5, "total_tokens": вхід + вихід}}}})
        записати(журнал, записи)
        сесії, _ = модуль.зібрати_сесії(журнал.parent)
        assert сесії[0]["токени"][4] == 165
        assert сесії[0]["токени_вікна"][4] == 40, "повтор лічильника та кінцева межа не мають витрат"
        # Догонка належить старому запуску, але почалася після кінця вікна.
        записати(журнал.parent / "догонка.jsonl", [
            {"timestamp": "2026-11-05T00:01:00Z", "type": "session_meta", "payload": {
                "id": "догонка", "timestamp": "2026-11-05T00:01:00Z", "cwd": "w/20261105-015900-bbbbbbbbbbbb/repo"}},
            {"timestamp": "2026-11-05T00:02:00Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
                "total_token_usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}}}}])
        сесії, _ = модуль.зібрати_сесії(журнал.parent)
        догонка = next(с for с in сесії if с["ід"] == "догонка")
        assert догонка["токени"][4] == 15 and догонка["токени_вікна"][4] == 0
        потік = корінь / "agy.jsonl"
        def usage(разом):
            """Формує незалежний підсумок для контрольного прикладу."""
            return {"input_tokens": разом - 2, "output_tokens": 2, "cache_read_tokens": 1000, "total_tokens": разом}
        записати(потік, [
            {"event": "init", "conversation_id": "розмова"},
            {"event": "step_update", "step_update": {"step_index": 1, "usage": usage(17)}},
            {"event": "result", "result": {"conversation_id": "розмова", "num_turns": 1, "usage": usage(17)}},
            {"event": "step_update", "step_update": {"step_index": 2, "usage": usage(8)}},
            {"event": "result", "result": {"conversation_id": "розмова", "num_turns": 2, "usage": usage(25)}},
            {"event": "step_update", "step_update": {"step_index": 3, "usage": usage(5)}}])
        _, токени, _, _ = модуль.зібрати_потік(потік, "agy")
        assert токени[4] == 30, "17 + 25 — подвійний облік; правильне 25 + 5"
        assert модуль.мітка(модуль.час_теки("20261029-020000-aaaaaaaaaaaa")) == "2026-10-29T00:00:00.000000Z"
        assert not модуль.у_вікні(модуль.час("2026-11-05T00:00:00Z"))
        # Повтор читання незмінних журналів, а не лише повтор форматування готового знімка.
        запуск = корінь / "запуски/20261029-020000-aaaaaaaaaaaa"
        запуск.mkdir(parents=True)
        (запуск / "worker.json").write_text(json.dumps({"lane": "codex", "name": "gemini-queue/проба/gpt-6.1-sol/1",
            "slug": "проба", "model": "gpt-6.1-sol", "sel": {"emodel": "gpt-6.1-sol"}}), encoding="utf-8")
        (запуск.parent / "wrapper.log").write_text("", encoding="utf-8")
        for назва in ("usage.json", "quota-codex.json"):
            (запуск.parent / назва).write_text("{}", encoding="utf-8")
        обмін = корінь / "обмін"
        обмін.mkdir()
        for назва in ("pools.json", "heartbeat.json"):
            (обмін / назва).write_text("{}", encoding="utf-8")
        журнали = корінь / "cli"
        журнали.mkdir()
        (журнали / "cli-20261029_020001.log").write_text(
            "I1029 02:00:02.000000 1 printmode.go:329] Print mode: running slash command /usage\n", encoding="utf-8")
        історія = корінь / "історія.json"
        історія.write_text(json.dumps({"доступно_правок": 2, "правки": [
            {"час_редагування": "2026-10-29T00:00:00Z", "квота": [], "позначки": []},
            {"час_редагування": "2026-10-30T00:00:00Z", "квота": [], "позначки": []}]}), encoding="utf-8")
        for номер in (1, 2):
            subprocess.run([sys.executable, str(тека / "вивантажити.py"), "--зібрати", "--сесії", str(журнал.parent),
                            "--запуски", str(запуск.parent), "--обмін", str(обмін), "--журнали-agy", str(журнали),
                            "--історія", str(історія), "--вихід", str(корінь / str(номер))], check=True)
        for назва in ("джерела.json", "запуски.csv", "квота.csv", "agy_cli.csv", "звірка.md"):
            assert (корінь / "1" / назва).read_bytes() == (корінь / "2" / назва).read_bytes(), назва
        subprocess.run([sys.executable, str(тека / "вивантажити.py"), "--знімок", str(тека / "джерела.json"),
                        "--вихід", str(корінь / "повтор")], check=True)
        for назва in ("запуски.csv", "квота.csv", "agy_cli.csv", "звірка.md"):
            assert (тека / назва).read_bytes() == (корінь / "повтор" / назва).read_bytes(), назва
    with (тека / "запуски.csv").open(encoding="utf-8", newline="") as потік:
        рядки = list(csv.DictReader(потік))
    for рядок in рядки:
        for суфікс in ("", "_вікна"):
            if рядок["разом" + суфікс] == "":
                continue
            вхід, кеш, вихід, міркування, разом = [int(рядок[п + суфікс]) for п in модуль.ПОЛЯ]
            assert разом == вхід + вихід and кеш >= 0 and 0 <= міркування <= вихід, рядок["ід"]
            if рядок["рушій"] == "codex":
                assert кеш <= вхід, рядок["ід"]
        if рядок["разом_вікна"]:
            assert int(рядок["разом_вікна"]) <= int(рядок["разом"]), рядок["ід"]
        assert рядок["відкати"] == "0", "невідомий відкат потребує окремого розбору"
    дані = json.loads((тека / "джерела.json").read_text(encoding="utf-8"))
    звірка = (тека / "звірка.md").read_text(encoding="utf-8")
    наявні = {р["позначка"] for р in рядки}
    assert all(п in наявні or п in звірка for п in дані["позначки"])
    for назва in ("запуски.csv", "квота.csv", "agy_cli.csv", "джерела.json", "історія_1856.json", "звірка.md"):
        текст = (тека / назва).read_text(encoding="utf-8")
        assert not re.search(r"(?i)C:[/\\]+Users[/\\]+(?!Public(?:[/\\]|\b))", текст), назва
        assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", текст), назва
        assert not re.search(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|sk-[A-Za-z0-9]{20,})", текст), назва
    print(f"ПРОЙШЛО: межі UTC, повтори лічильників, догонка після межі, usage agy, арифметика {len(рядки)} рядків, покриття позначок, повтор збору з тих самих журналів, відтворення 4 файлів, перевірка приватних даних")


if __name__ == "__main__":
    головна()
