#!/usr/bin/env python3
"""Проба П13: К1 Stop-хука `.claude/хуки/обіцянка_без_дії.py` — текст у чаті ходу, який почав не власник.

Запуск: python3 аудит/проби/хук_текст_у_чаті.py [шлях_до_хука]   (без аргументу — хук з робочого дерева).
Транскрипти штучні; справжні ходи менеджера 05–06.11 — `аудит/проби/хук_точки_дії_справжні.py`. Мірило: рядок посеред
ходу листа чи рядка обгортки — повертається (з нагадуванням CLI — ще й з правилом `CLAUDE.md`); хід, що кінчається «—»
чи «ЗАБЛОКОВАНО: …», хід власника, слово власника посеред ходу (і відповідь у наступному), повтор після повернення,
субагент — пропускаються; транскрипту нема — пропуск з попередженням.
"""
import json
import os
import subprocess
import sys
import tempfile

КОРІНЬ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ХУК = sys.argv[1] if len(sys.argv) > 1 else os.path.join(КОРІНЬ, ".claude", "хуки", "обіцянка_без_дії.py")
ЛИСТ = {"type": "user", "origin": {"kind": "task-notification"},
        "message": {"role": "user", "content": "<task-notification>\n<task-type>queued-remote-notifications</task-type>"}}
ВЛАСНИК = {"type": "user", "origin": {"kind": "human"}, "message": {"role": "user", "content": "Як справи з нарядом?"}}
ОБГОРТКА = {"type": "user", "origin": {"kind": "human"},
            "message": {"role": "user", "content": "GEMINI ОБГОРТКА: ГОТОВО gemini/наряд-1 abc"}}
ПОСЕРЕД = {"type": "attachment", "attachment": {"type": "queued_command", "prompt": "А що з ноутбуком?",
                                                "origin": {"kind": "human"}}}
НАГАДУВАННЯ = {"type": "attachment", "attachment": {"type": "silent_turn_reminder",
                                                    "text": "The user hasn't heard from you in a while"}}
# локальна команда (`/effort`) перед листом: відповіді не має, хід почав лист (свій транскрипт виконавця 06.11)
КОМАНДА = {"type": "user", "isMeta": True, "origin": {"kind": "task-notification"},
           "message": {"role": "user", "content": "<local-command-caveat>The command below was run directly</local-command-caveat>"}}
БЕЗ_ДЖЕРЕЛА = {"type": "user", "message": {"role": "user", "content": "Глянь, будь ласка, журнал."}}
ДІЯ = {"type": "assistant", "message": {"role": "assistant", "content": [
    {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "git status"}}]}}
РЕЗУЛЬТАТ = {"type": "user", "message": {"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "t1", "content": "чисто"}]}}


def т(текст, кінець=False):
    з = {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": текст}]}}
    if кінець:
        з["message"]["stop_reason"] = "end_turn"
    return з


ВИПАДКИ = [
    ("лист → рядок посеред ходу, кінець «—»", [ЛИСТ, т("Дивлюсь гілку й злиття."), ДІЯ, РЕЗУЛЬТАТ, т("—", True)], {},
     "К1"),
    ("лист → рядок наприкінці", [ЛИСТ, ДІЯ, РЕЗУЛЬТАТ, т("Злив #12, CI зелений.", True)], {}, "К1"),
    ("лист → нагадування CLI → рядок", [ЛИСТ, ДІЯ, РЕЗУЛЬТАТ, НАГАДУВАННЯ, т("Працюю над нарядом."), ДІЯ, РЕЗУЛЬТАТ,
                                        т("—", True)], {}, "К1+CLAUDE.md"),
    ("команда → лист → рядок: початок — лист", [КОМАНДА, ЛИСТ, ДІЯ, РЕЗУЛЬТАТ, т("Дивлюсь сторінки.", True)], {}, "К1"),
    ("рядок обгортки → рядок", [ОБГОРТКА, т("Позначку прийнято.", True)], {}, "К1"),
    ("лист → лише «—»", [ЛИСТ, ДІЯ, РЕЗУЛЬТАТ, т("—", True)], {}, "пропуск"),
    ("лист → «ЗАБЛОКОВАНО: …»", [ЛИСТ, ДІЯ, РЕЗУЛЬТАТ,
                                 т("ЗАБЛОКОВАНО: пуш відхилено, чекаю дозволу від власника", True)], {}, "пропуск"),
    ("хід власника → відповідь", [ВЛАСНИК, т("Наряд у роботі."), ДІЯ, РЕЗУЛЬТАТ, т("PR #5 відкрито.", True)], {},
     "пропуск"),
    ("лист → слово власника посеред → відповідь", [ЛИСТ, ДІЯ, РЕЗУЛЬТАТ, ПОСЕРЕД, т("Ноутбук вільний.", True)], {},
     "пропуск"),
    ("слово посеред попереднього ходу → відповідь у наступному", [
        ЛИСТ, ДІЯ, ПОСЕРЕД, РЕЗУЛЬТАТ, т("—", True), ЛИСТ, т("Ноутбук вільний.", True)], {}, "пропуск"),
    ("запис без джерела з простим текстом", [БЕЗ_ДЖЕРЕЛА, т("Журнал чистий.", True)], {}, "пропуск"),
    ("повтор після повернення", [ЛИСТ, т("Злив #12.", True)], {"stop_hook_active": True}, "пропуск"),
    ("субагент", [ЛИСТ, т("Знайшов три файли.", True)], {"agent_id": "a1"}, "пропуск"),
]


def запуск(записи, додатково, т_):
    шлях = os.path.join(т_, "т.jsonl")
    with open(шлях, "w", encoding="utf-8") as ф:
        for з in записи:
            ф.write(json.dumps(з, ensure_ascii=False) + "\n")
    вхід = dict({"transcript_path": шлях, "stop_hook_active": False}, **додатково)
    р = subprocess.run([sys.executable, ХУК], input=json.dumps(вхід, ensure_ascii=False), capture_output=True,
                       text=True, encoding="utf-8")
    причина = json.loads(р.stdout).get("reason", "") if р.stdout.strip() else ""
    факт = "К1" if "Текст у чаті читає власник" in причина else ("інше" if причина else "пропуск")
    if "local-command-caveat" in причина:
        факт += " з початком-командою"
    if факт == "К1" and "The user hasn't heard from you" in причина:
        факт += "+CLAUDE.md"
    return факт + (" +stderr" if р.stderr.strip() else "")


def main():
    збої = 0
    with tempfile.TemporaryDirectory() as т_:
        for назва, записи, додатково, чекано in ВИПАДКИ:
            факт = запуск(записи, додатково, т_)
            збої += факт != чекано
            print(f"{'ок ' if факт == чекано else 'ЗБІЙ'} {назва} → {факт} (чекано {чекано})")
        р = subprocess.run([sys.executable, ХУК], input=json.dumps({"transcript_path": os.path.join(т_, "нема.jsonl")}),
                           capture_output=True, text=True, encoding="utf-8")
        факт = ("повертає" if р.stdout.strip() else "пропуск") + (" +stderr" if р.stderr.strip() else "")
        збої += факт != "пропуск +stderr"
        print(f"{'ок ' if факт == 'пропуск +stderr' else 'ЗБІЙ'} транскрипту нема → {факт} (чекано пропуск +stderr)")
    print("збоїв:", збої)
    sys.exit(1 if збої else 0)


main()
