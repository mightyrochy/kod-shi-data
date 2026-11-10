#!/usr/bin/env python3
"""Проба П14: `.claude/хуки/прийом_менеджера.py` — правило «Що доходить» на вході ходу менеджера, який почав лист.

Запуск: python3 аудит/проби/хук_прийом_менеджера.py [шлях_до_хука]   (без аргументу — хук з робочого дерева).
Мірило: менеджер — сповіщення на вході й лист у результаті `ReadNotifications` нагадують, рядок з міткою обгортки теж;
слово власника, результат без листа, інший інструмент, інша сесія, адреса невідома, субагент — мовчить; СТАН нема —
мовчить з попередженням. Справжні входи 05–06.11 — `аудит/проби/хук_точки_дії_справжні.py`.
"""
import json
import os
import subprocess
import sys
import tempfile

КОРІНЬ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ХУК = sys.argv[1] if len(sys.argv) > 1 else os.path.join(КОРІНЬ, ".claude", "хуки", "прийом_менеджера.py")
МЕНЕДЖЕР = "session_MGR1"
СТАН = f"| роль | сесія |\n|---|---|\n| диспетчер | session_DSP1 |\n| менеджер | {МЕНЕДЖЕР} |\n"
ЛИСТ = ('<cross-session-message from-session="session_DSP1">\nThe following was sent by another Claude Code session '
        'via the send_message tool.\nСЛОВО ВЛАСНИКА 09:10 UTC: «чому чекаєш?»\n</cross-session-message>')
СПОВІЩЕННЯ = "<task-notification>\n<task-type>queued-remote-notifications</task-type>\n<status>pending</status>"


def запуск(вхід, я=МЕНЕДЖЕР, стан=СТАН):
    with tempfile.TemporaryDirectory() as т:
        if стан is not None:
            os.makedirs(os.path.join(т, "аудит"))
            with open(os.path.join(т, "аудит", "СТАН.md"), "w", encoding="utf-8") as ф:
                ф.write(стан)
        env = dict(os.environ, CLAUDE_PROJECT_DIR=т)
        env.pop("CLAUDE_CODE_REMOTE_SDK_URL", None)
        if я:
            env["CLAUDE_CODE_REMOTE_SDK_URL"] = f"https://x/v1/sessions/cse_{я[len('session_'):]}"
        р = subprocess.run([sys.executable, ХУК], input=json.dumps(вхід, ensure_ascii=False), capture_output=True,
                           text=True, encoding="utf-8", env=env)
    нагадав = "Що доходить" in р.stdout and "additionalContext" in р.stdout
    return ("нагадує" if нагадав else "мовчить") + (" +stderr" if р.stderr.strip() else "")


def main():
    вхід_листа = {"hook_event_name": "PostToolUse", "tool_name": "ReadNotifications",
                  "tool_response": {"notifications": [{"content": ЛИСТ}], "remaining": 0}}
    випадки = [
        ("сповіщення на вході", {"hook_event_name": "UserPromptSubmit", "prompt": СПОВІЩЕННЯ}, {}, "нагадує"),
        ("лист у результаті ReadNotifications", вхід_листа, {}, "нагадує"),
        ("рядок обгортки на вході", {"hook_event_name": "UserPromptSubmit", "prompt": "GEMINI ОБГОРТКА: ГОТОВО x"}, {},
         "нагадує"),
        ("слово власника", {"hook_event_name": "UserPromptSubmit", "prompt": "Що робиш?"}, {}, "мовчить"),
        ("ReadNotifications без листа", {"hook_event_name": "PostToolUse", "tool_name": "ReadNotifications",
                                         "tool_response": {"notifications": [], "remaining": 0}}, {}, "мовчить"),
        ("інший інструмент", {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_response": ЛИСТ}, {},
         "мовчить"),
        ("лист у сесії диспетчера", вхід_листа, {"я": "session_DSP1"}, "мовчить"),
        ("адреса невідома", вхід_листа, {"я": None}, "мовчить"),
        ("субагент", dict(вхід_листа, agent_id="a1"), {}, "мовчить"),
        ("СТАН нема", вхід_листа, {"стан": None}, "мовчить +stderr"),
    ]
    збої = 0
    for назва, вхід, додатково, чекано in випадки:
        факт = запуск(вхід, **додатково)
        збої += факт != чекано
        print(f"{'ок ' if факт == чекано else 'ЗБІЙ'} {назва} → {факт} (чекано {чекано})")
    print("збоїв:", збої)
    sys.exit(1 if збої else 0)


main()
