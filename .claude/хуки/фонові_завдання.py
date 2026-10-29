#!/usr/bin/env python3
"""Хук PreToolUse на `Bash`: фонове завдання, коротше за хід, іде на передньому плані.

`CLAUDE.md`, «Контекст і пам'ять»: фонове завдання (`run_in_background`) будить окремим ходом, що перечитує весь
контекст; фоном — лише довше за хід. В.2 (`аудит/витрати/аналіз_2910.md`, §5 п.3): правило-текст не тримає — дальші
ходи виконавців 27 % → 39,5 % вартості, пробудження task-notification — $252 за тиждень. Тепер його перевіряє механізм
у мить виклику (наряд хук-фонові-завдання; звіт `аудит/перевірка/хук_фонові_завдання.md`).

Що робить з `Bash` з `run_in_background: true`:
- цикл чекання (`sleep N`, `until/while …; do … sleep`) — відмова: завершення фонового завдання й так будить, а чекач
  фоном — ще одне пробудження;
- решта — через `updatedInput` на передній план з `timeout` 600000 (межа переднього плану). Довге не ламається: команда,
  що не встигла за `timeout`, сама переходить у фон (вимір 29.10, звіт) — одне пробудження, як і було; коротше за 10 хв
  — жодного. Явний `timeout` ознакою довгого не є: у В.2 він стоїть у 38 з 55 фонових викликів як страховка, незалежно
  від тривалості.
Решта інструментів — без змін; `Agent` хук не чіпає: платформа ставить субагента у фон і з `run_in_background: false`
(`CLAUDE_AUTO_BACKGROUND_TASKS=true`, звіт).

Хук не падає сесію: будь-яка помилка — виклик як є, попередження в stderr.
"""
import json
import re
import sys

МЕЖА_МС = 600000  # найбільший timeout переднього плану Bash
ЧЕКАННЯ = re.compile(r"^\s*sleep\s+\d|\b(?:until|while)\b.*?\bdo\b.*?\bsleep\b", re.S)
ВІДМОВА = ("хук фонові_завдання: цикл чекання фоном — друге пробудження: фонове завдання само будить, коли скінчиться "
           "(`CLAUDE.md`, «фоном — лише довше за хід, одним скриптом»). Чекати — на передньому плані "
           "(`timeout` до 600000) або кінчити хід без чекача.")


def рішення(дані):
    """«відмова», новий вхід інструмента або None (виклик як є)."""
    if дані.get("tool_name") != "Bash":
        return None
    вхід = дані.get("tool_input") or {}
    if вхід.get("run_in_background") is not True:
        return None
    if ЧЕКАННЯ.search(str(вхід.get("command", ""))):
        return "відмова"
    новий = dict(вхід)
    новий["run_in_background"] = False
    новий["timeout"] = МЕЖА_МС
    return новий


def main():
    новий = рішення(json.load(sys.stdin))
    if новий is None:
        return
    if новий == "відмова":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": ВІДМОВА}}, ensure_ascii=False))
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "updatedInput": новий,
        "additionalContext": ("хук фонові_завдання: фонове завдання йде на передньому плані (`CLAUDE.md`, «фоном — лише "
                              "довше за хід»); не встигне за 10 хв — саме перейде у фон."),
    }}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as п:  # хук не падає сесію
        print(f"хук фонові_завдання: {type(п).__name__}: {п}; виклик як є", file=sys.stderr)
