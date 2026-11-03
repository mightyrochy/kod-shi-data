#!/usr/bin/env python3
"""Проба хука `.claude/хуки/слова_власника.py` (наряд П.4-А): штучний транскрипт → що хук вкладає після стиснення.

Запуск: python3 аудит/проби/хук_слова_власника.py [шлях_до_хука]   (без аргументу — хук з робочого дерева).
ДО на `main`: git show origin/main:.claude/хуки/слова_власника.py > /tmp/хук_до.py; ... /tmp/хук_до.py
Мірило: вкладено рівно слова власника (3), листи й модельний останній запис — не впливають; субагент — тиша.
"""
import json
import os
import subprocess
import sys
import tempfile

ХУК = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "хуки", "слова_власника.py")
ЛЮДИНА = {"kind": "human"}
ПОВІДОМЛЕННЯ = [  # (текст, origin, ключі події) — слова власника позначено ВЛАСНИК
    ("СТОП: не зливай PR", ЛЮДИНА, {}),
    ("ВАЖЛИВО: п.19 — слова в файли", ЛЮДИНА, {}),
    ("звичайне слово власника", ЛЮДИНА, {}),
    ("ЗАПУСКАЧ: abc123", ЛЮДИНА, {}),
    ("НОУТБУК ГОТОВО гілка deadbeef", ЛЮДИНА, {}),
    ("GEMINI ОБГОРТКА: ГОТОВО gemini/x", ЛЮДИНА, {}),
    ("СПОСТЕРІГАЧ CI #1 червоний", ЛЮДИНА, {}),
    ("<cross-session-message from-session=\"session_X\">\nДані\n    Почни\n</cross-session-message>", None,
     {"isMeta": True, "promptSource": "system", "turnOrigin": "system"}),
    ("<cross-session-message from-session=\"session_Y\">\nЛист тригером\n</cross-session-message>", ЛЮДИНА,
     {"isMeta": True}),
]


def подія(т, origin, дод, i):
    е = {"type": "user", "uuid": f"u{i}", "timestamp": f"2026-10-26T10:{i:02d}:00Z", "message": {"role": "user", "content": т}}
    if origin:
        е["origin"] = origin
    е.update(дод)
    return е


def запуск(теку, імя, останній, джерело="compact"):
    підтека = os.path.join(теку, імя)
    os.makedirs(os.path.dirname(підтека), exist_ok=True)
    with open(підтека, "w", encoding="utf-8") as ф:
        for i, (т, o, д) in enumerate(ПОВІДОМЛЕННЯ):
            ф.write(json.dumps(подія(т, o, д, i), ensure_ascii=False) + "\n")
        ф.write(json.dumps({"type": останній, "uuid": "z", "message": {"role": останній, "content": "x"}}) + "\n")
    вхід = json.dumps({"source": джерело, "transcript_path": підтека})
    return subprocess.run([sys.executable, ХУК], input=вхід, capture_output=True, text=True, check=True).stdout


with tempfile.TemporaryDirectory() as т:
    for назва, імя, останній in (("СЕСІЯ, останній запис — користувача", "s.jsonl", "user"),
                                  ("СЕСІЯ, останній запис — модельний (ручний /compact між ходами)", "s.jsonl", "assistant"),
                                  ("СУБАГЕНТ (subagents/agent-*.jsonl)", "s/subagents/agent-a1.jsonl", "user")):
        print(f"=== {назва}")
        print(запуск(т, імя, останній) or "(порожньо)")

with tempfile.TemporaryDirectory() as т:
    шлях = os.path.join(т, "черга.jsonl")
    записи = [
        {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-10-26T11:01:00Z", "content": "слово лише в черзі"},
        {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-10-26T11:02:00Z", "content": "GEMINI ОБГОРТКА: лист"},
        {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-10-26T11:03:00Z", "content": "доставлене слово"},
        подія("доставлене слово", ЛЮДИНА, {}, 4),
        {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-10-26T11:05:00Z", "content": "видалене слово"},
        {"type": "queue-operation", "operation": "remove", "content": "видалене слово"},
        {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-10-26T11:07:00Z", "content": "слово субагента", "isSidechain": True},
    ]
    with open(шлях, "w", encoding="utf-8") as ф:
        for запис in записи:
            ф.write(json.dumps(запис, ensure_ascii=False) + "\n")
    р = subprocess.run([sys.executable, ХУК], input=json.dumps({"source": "compact", "transcript_path": шлях}),
                       capture_output=True, text=True, check=True).stdout
    assert "2026-10-26 11:01 UTC «слово лише в черзі»" in р and "не дійшло до сесії — лише в черзі" in р, р
    assert р.count("доставлене слово") == 1 and "2026-10-26 11:03" in р, р
    assert all(т not in р for т in ("GEMINI ОБГОРТКА: лист", "видалене слово", "слово субагента")), р
    print("черга: ок")
