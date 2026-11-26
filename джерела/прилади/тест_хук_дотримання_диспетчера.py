# -*- coding: utf-8 -*-
"""Тест хука `.claude/хуки/дотримання_диспетчера.py` (наряд Хук-дотримання-диспетчера-цитати).

python3 джерела/прилади/тест_хук_дотримання_диспетчера.py [-v]      # з кореня репозиторію

(а) кожна цитата хука (`ЦИТАТИ`) — підрядок названого розділу чинного файла договору на поточному дереві;
(б) стенд: транскрипт старший за добу без листа «ДИСПЕТЧЕР ПЕРЕДАЧА» — нагадування на кожному Stop, не частіше за раз
    на годину, а не раз на транскрипт;
(в) лист `send_message` на адресу «попередній — <id>» чи «передає: <id>» з рядка «диспетчер» хук не відхиляє.
"""
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ТУТ = os.path.dirname(os.path.abspath(__file__))
КОРІНЬ = os.path.normpath(os.path.join(ТУТ, "..", ".."))
ХУК = os.path.join(КОРІНЬ, ".claude", "хуки")
sys.path.insert(0, ХУК)
хук = importlib.import_module("дотримання_диспетчера")

Я, ПОПЕРЕДНІЙ, ПЕРЕДАЄ, МЕНЕДЖЕР, ЧУЖА = "session_AAA1", "session_BBB2", "session_CCC3", "session_MMM4", "session_ZZZ9"
СТАН = (f"| роль | адреса | коли | кому |\n|---|---|---|---|\n"
        f"| диспетчер | {Я} (ДИСПЕТЧЕР-32; попередній — {ПОПЕРЕДНІЙ}; передає: {ПЕРЕДАЄ}) | 2026-11-26 | усі |\n"
        f"| менеджер | {МЕНЕДЖЕР} (Fable) | 2026-11-26 | диспетчер |\n")


def пробіли(т):
    return re.sub(r"\s+", " ", т)


def розділ(файл, назва):
    """Текст розділу `## <назва>` до наступного `## ` (None — розділу нема)."""
    with open(os.path.join(КОРІНЬ, файл), encoding="utf-8") as ф:
        частини = re.split(r"(?m)^## ", ф.read())
    for ч in частини[1:]:
        if ч.splitlines()[0].strip() == назва:
            return пробіли(ч)
    return None


class Цитати(unittest.TestCase):
    def test_кожна_цитата_є_в_розділі_договору(self):
        впали = []
        for ключ, (файл, назва, текст) in хук.ЦИТАТИ.items():
            тіло = розділ(файл, назва)
            if тіло is None:
                впали.append(f"{ключ}: у {файл} нема розділу «{назва}»")
            elif пробіли(текст) not in тіло:
                впали.append(f"{ключ}: текст не є підрядком «{назва}» у {файл}")
        self.assertEqual(впали, [], "\n" + "\n".join(впали))


class Стенд(unittest.TestCase):
    def setUp(self):
        self.тека = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.тека, "аудит"))
        with open(os.path.join(self.тека, "аудит", "СТАН.md"), "w", encoding="utf-8") as ф:
            ф.write(СТАН)
        self.стан = os.path.join(self.тека, "стан")

    def транскрипт(self, початок, листи=()):
        шлях = os.path.join(self.тека, "т.jsonl")
        записи = [{"type": "assistant", "timestamp": початок, "message": {"content": [], "stop_reason": "end_turn"}}]
        for кому, текст in листи:
            записи.append({"type": "assistant", "timestamp": початок, "message": {"content": [
                {"type": "tool_use", "name": хук.ІМ_ЛИСТ, "input": {"session_id": кому, "message": текст}}]}})
        with open(шлях, "w", encoding="utf-8") as ф:
            ф.write("\n".join(json.dumps(з, ensure_ascii=False) for з in записи) + "\n")
        return шлях

    def запуск(self, вхід, зараз):
        середовище = dict(os.environ, CLAUDE_PROJECT_DIR=self.тека, ДОТРИМАННЯ_ТЕКА=self.стан,
                          ДОТРИМАННЯ_ЗАРАЗ=зараз, CLAUDE_CODE_REMOTE_SDK_URL=f"https://x/sessions/cse_{Я[8:]}")
        р = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ХУК, "дотримання_диспетчера.py")],
                           input=json.dumps(вхід), capture_output=True, text=True, env=середовище, timeout=60)
        return json.loads(р.stdout) if р.stdout.strip() else None

    def stop(self, шлях, зараз):
        return self.запуск({"transcript_path": шлях, "cwd": self.тека}, зараз)

    def test_нагадування_про_передачу_щогодини_а_не_раз(self):
        т = self.транскрипт("2026-11-20T00:00:00Z")
        перший = self.stop(т, "2026-11-26T10:00:00Z")
        self.assertIsNotNone(перший)
        self.assertIn("«ДИСПЕТЧЕР ПЕРЕДАЧА»", перший["reason"])
        self.assertIsNone(self.stop(т, "2026-11-26T10:20:00Z"), "у межах години — одне")
        self.assertIsNone(self.stop(т, "2026-11-26T10:59:00Z"), "у межах години — одне")
        self.assertIsNotNone(self.stop(т, "2026-11-26T11:01:00Z"), "понад годину — знову")
        self.assertIsNotNone(self.stop(т, "2026-11-26T12:30:00Z"), "понад годину — знову")

    def test_до_доби_й_після_листа_нагадування_нема(self):
        self.assertIsNone(self.stop(self.транскрипт("2026-11-26T01:00:00Z"), "2026-11-26T10:00:00Z"))
        т = self.транскрипт("2026-11-20T00:00:00Z", [(МЕНЕДЖЕР, "ДИСПЕТЧЕР ПЕРЕДАЧА #1 гілка")])
        self.assertIsNone(self.stop(т, "2026-11-26T10:00:00Z"))

    def test_лист_попередникові_й_наступникові_без_відмови(self):
        for кому in (ПОПЕРЕДНІЙ, ПЕРЕДАЄ):
            вхід = {"tool_name": хук.ІМ_ЛИСТ, "tool_input": {"session_id": кому, "message": f"НОВИЙ ДИСПЕТЧЕР: {Я}"}}
            self.assertIsNone(self.запуск(вхід, "2026-11-26T10:00:00Z"), кому)

    def test_лист_чужій_сесії_відхиляється(self):
        вхід = {"tool_name": хук.ІМ_ЛИСТ, "tool_input": {"session_id": ЧУЖА, "message": "привіт"}}
        р = self.запуск(вхід, "2026-11-26T10:00:00Z")
        self.assertEqual(р["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
