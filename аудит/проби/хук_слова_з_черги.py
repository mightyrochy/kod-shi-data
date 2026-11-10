#!/usr/bin/env python3
"""Проба хука `.claude/хуки/слова_власника.py` (08.11): слово власника, що в транскрипті лише `queue-operation`/`enqueue`.

Формат — з реального транскрипту сесії (`~/.claude/projects/*/*.jsonl`): `{"type":"queue-operation","operation":"enqueue",
"timestamp":…,"content":<текст>}` без `origin`; далі `dequeue` без тексту. Лист сесії в черзі має `content` з
`<cross-session-message …>`. Запуск: python3 аудит/проби/хук_слова_з_черги.py [шлях_до_хука] — код виходу 1 при провалі.
"""
import json
import os
import subprocess
import sys
import tempfile

ХУК = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "хуки", "слова_власника.py")


def черга(час, т):
    return {"type": "queue-operation", "operation": "enqueue", "timestamp": f"2026-11-08T{час}:00.000Z", "content": т}


ЛИСТ = '<cross-session-message from-session="session_X">\nДані\n</cross-session-message>'
РЯДКИ = [
    черга("10:07", "слово лише в черзі"),                              # 1: не доставлено → беремо
    {"type": "queue-operation", "operation": "dequeue", "timestamp": "2026-11-08T10:07:30.000Z"},
    черга("10:08", "слово в черзі й доставлене"),                      # 2: доставлено → один запис
    {"type": "user", "uuid": "a", "timestamp": "2026-11-08T10:09:00.000Z", "origin": {"kind": "human"},
     "message": {"content": "слово в черзі й доставлене"}},
    черга("10:10", ЛИСТ),                                              # 3: лист сесії → ні
    черга("10:11", "ЗАПУСКАЧ: abc"),                                   # 4: мітка → ні
    черга("10:12", "<system-reminder>нагадування</system-reminder>"),  # 5: платформа → ні
    черга("10:13", "/effort medium"),                                  # 6: слеш-команда → ні
]
ОЧІКУЮ = ["10:07 UTC «слово лише в черзі»", "10:08 UTC «слово в черзі й доставлене»"]

with tempfile.TemporaryDirectory() as д:
    т = os.path.join(д, "s.jsonl")
    with open(т, "w", encoding="utf-8") as ф:
        ф.write("\n".join(json.dumps(р, ensure_ascii=False) for р in РЯДКИ))
    вивід = subprocess.run([sys.executable, "-X", "utf8", ХУК], input=json.dumps({"source": "compact", "transcript_path": т}),
                           capture_output=True, text=True, encoding="utf-8", check=True).stdout
print(вивід)
рядки = [р for р in вивід.splitlines() if р.startswith("- ")]
помилки = [о for о in ОЧІКУЮ if not any(о in р for р in рядки)]
if len(рядки) != len(ОЧІКУЮ):
    помилки.append(f"рядків слів {len(рядки)}, має бути {len(ОЧІКУЮ)}")
print("ПРОБА", "ПРОВАЛ: " + "; ".join(помилки) if помилки else "ОК: 2 слова (черга без доставки; черга+доставка — один запис), лист/мітка/тег/слеш — ні")
sys.exit(1 if помилки else 0)
