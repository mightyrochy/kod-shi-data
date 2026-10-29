#!/usr/bin/env python3
"""Проба «СЛОВО ВЛАСНИКА» у `.claude/хуки/листи_менеджерові.py` (наряд хук-час-слова-власника): транскрипт-зразок і вхід
хука з файлу → рішення.

Запуск: python3 аудит/проби/хук_час_слова_власника.py [шлях_до_хука]   (без аргументу — хук з робочого дерева).
ДО на `main`: git show origin/main:.claude/хуки/листи_менеджерові.py > /tmp/хук_до.py; ... /tmp/хук_до.py — лист із
«~09:35» на слово о 09:26 пропущено. Мірило: «~09:35» — відмова з «09:26»; «09:26» — пропущено; слова нема в
транскрипті — відмова; транскрипта нема — пропущено з попередженням.
"""
import json
import os
import subprocess
import sys
import tempfile

КОРІНЬ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ХУК = sys.argv[1] if len(sys.argv) > 1 else os.path.join(КОРІНЬ, ".claude", "хуки", "листи_менеджерові.py")
МЕНЕДЖЕР, ДИСПЕТЧЕР = "session_MGR1", "session_DSP1"
СТАН = f"| диспетчер | {ДИСПЕТЧЕР} | x |\n| менеджер | {МЕНЕДЖЕР} | x |\n"
СЛОВО_1 = "я не маю тобі нагадувати правила. Вони існують щоб їх виконувати."
СЛОВО_2 = "хук має перевіряти час слова за транскриптом"


def подія(i, текст, час, origin=None):
    е = {"type": "user", "uuid": f"u{i}", "timestamp": час, "message": {"role": "user", "content": текст}}
    if origin:
        е["origin"] = origin
    return е


def запуск(лист, транскрипт=True):
    with tempfile.TemporaryDirectory() as т:
        os.makedirs(os.path.join(т, "аудит"))
        with open(os.path.join(т, "аудит", "СТАН.md"), "w", encoding="utf-8") as ф:
            ф.write(СТАН)
        шлях = os.path.join(т, "s.jsonl") if транскрипт else os.path.join(т, "нема.jsonl")
        if транскрипт:
            with open(шлях, "w", encoding="utf-8") as ф:
                for е in (подія(0, СЛОВО_1, "2026-10-29T09:26:41Z", {"kind": "human"}),
                          подія(1, СЛОВО_2, "2026-10-29T10:02:10Z", {"kind": "human"}),
                          подія(2, "ЗАПУСКАЧ: abc", "2026-10-29T10:30:00Z", {"kind": "human"})):
                    ф.write(json.dumps(е, ensure_ascii=False) + "\n")
        вхід = {"tool_name": "mcp__claude-code-remote__send_message", "transcript_path": шлях,
                "tool_input": {"session_id": МЕНЕДЖЕР, "message": лист}}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=т, ЛИСТИ_СТАН_ФАЙЛ=os.path.join(т, "з"),
                   CLAUDE_CODE_REMOTE_SDK_URL=f"https://x/sessions/cse_{ДИСПЕТЧЕР[len('session_'):]}")
        р = subprocess.run([sys.executable, ХУК], input=json.dumps(вхід), capture_output=True, text=True, env=env)
    рішення = "відмова" if "deny" in р.stdout else "пропущено"
    return рішення + (" +stderr" if р.stderr.strip() else ""), р.stdout


ВИПАДКИ = [
    (f"СЛОВО ВЛАСНИКА ~09:35 UTC: «{СЛОВО_1}»", True, "відмова", "09:26"),
    (f"СЛОВО ВЛАСНИКА 09:26 UTC: «{СЛОВО_1}»", True, "пропущено", ""),
    (f"СЛОВО ВЛАСНИКА 10:02 UTC\n{СЛОВО_2}\nрішення: записати", True, "пропущено", ""),
    (f"СЛОВО ВЛАСНИКА: «{СЛОВО_1}»", True, "відмова", "09:26"),
    ("СЛОВО ВЛАСНИКА 09:26 UTC: «слова, якого власник не казав»", True, "відмова", "09:26"),
    (f"СЛОВО ВЛАСНИКА 09:26 UTC: «{СЛОВО_1}»", False, "пропущено +stderr", ""),
    ("КОЛО", True, "пропущено", ""),
]

збої = 0
for лист, є, чекано, у_причині in ВИПАДКИ:
    факт, вивід = запуск(лист, є)
    ок = факт == чекано and у_причині in вивід
    збої += not ок
    print(f"{'ок ' if ок else 'ЗБІЙ'} {лист.splitlines()[0][:48]!r} транскрипт={'є' if є else 'нема'} → {факт} (чекано {чекано})")
print("збоїв:", збої)
sys.exit(1 if збої else 0)
