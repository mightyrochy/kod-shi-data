#!/usr/bin/env python3
"""Хук PreToolUse на `Bash`: коміт файлу дошки `аудит/дошка/**` не йде, доки поля не пройшли ту саму перевірку, що в CI.

Чому: файл дошки сесія пише за шапкою `джерела/прилади/дошка_поля.py`, а поля звіряв лише CI на голові PR — після листа
«ГОТОВО». За 15–16.11 це тричі дало червоний CI (#3963, звіти перевірки #3997 і #3998) і окрему сесію доробки.
Тепер звірка — у мить коміту (наряд диспетчера 16.11 за листом менеджера 03:18).

Що робить з `Bash`-командою, де є `git commit`:
- серед файлів коміту нема `аудит/дошка/**` — нічого, прилад не запускається;
- є — запускає `python3 джерела/прилади/згорнути_дошку.py --лише-перевірити`, те саме, що крок CI «файли дошки згортаються»
  (той самий код приладу, правил тут нема), і при коді виходу ≠ 0 відмовляє, показуючи його рядки «ПОМИЛКА <файл>:<рядок>: …».
Файли коміту: індекс; коли команда сама робить `git add` чи `commit -a`, ще й змінені та нові файли дошки робочого дерева.

Хук не падає сесію й не спиняє її за власний збій (нема python, приладу, git, команду не розібрано, прилад завис):
виклик іде як є, рядок попередження.
Не покриває: Codex і `agy` на ноутбуці комітять не через Claude Code.
"""
import json
import os
import re
import subprocess
import sys

ТЕКА = "аудит/дошка/"
ПРИЛАД = os.path.join("джерела", "прилади", "згорнути_дошку.py")
КОМІТ = re.compile(r"(?:^|[;&|(\n]|&&|\|\|)\s*git(?:\s+(?:-[cC]\s+\S+|--\S+))*\s+commit\b")
САМ_ДОДАЄ = re.compile(r"\bgit(?:\s+(?:-[cC]\s+\S+|--\S+))*\s+add\b|\bcommit\b[^;&|\n]*?(?:\s-[a-zA-Z]*a|\s--all\b)")
МЕЖА_С = 60
МАКС_РЯДКІВ = 40


def файли_дошки(корінь, команда):
    """Файли `аудит/дошка/**` коміту: індекс, а коли команда сама додає чи комітить `-a` — ще й робоче дерево."""
    р = subprocess.run(["git", "-c", "core.quotepath=off", "status", "--porcelain=v1", "-z", "--", ТЕКА],
                       cwd=корінь, capture_output=True, text=True, timeout=МЕЖА_С)
    if р.returncode != 0:
        raise RuntimeError("git status: " + р.stderr.strip()[:200])
    сам = bool(САМ_ДОДАЄ.search(команда))
    знайдені = []
    for запис in [з for з in р.stdout.split("\0") if з]:
        індекс, дерево, шлях = запис[0], запис[1], запис[3:]
        if шлях.startswith(ТЕКА) and (індекс not in " ?" or (сам and дерево != " ") or (сам and індекс == "?")):
            знайдені.append(шлях)
    return знайдені


def рішення(дані):
    """None — коміт іде; (ТЕКСТ, відмова?) — інакше."""
    if дані.get("tool_name") != "Bash":
        return None
    команда = str((дані.get("tool_input") or {}).get("command", ""))
    if not КОМІТ.search(команда):
        return None
    корінь = os.environ.get("CLAUDE_PROJECT_DIR") or дані.get("cwd") or os.getcwd()
    файли = файли_дошки(корінь, команда)
    if not файли:
        return None
    прилад = os.path.join(корінь, ПРИЛАД)
    if not os.path.isfile(прилад):
        raise RuntimeError("нема приладу " + ПРИЛАД)
    р = subprocess.run([sys.executable, "-I", прилад, "--лише-перевірити"], cwd=корінь, capture_output=True,
                       text=True, timeout=МЕЖА_С)
    if р.returncode == 0:
        return None
    рядки = [л for л in (р.stderr + "\n" + р.stdout).splitlines() if л.startswith("ПОМИЛКА")]
    if not рядки:
        raise RuntimeError("прилад вийшов з кодом %d без рядків «ПОМИЛКА»: %s" % (р.returncode, р.stderr.strip()[:200]))
    показ = рядки[:МАКС_РЯДКІВ] + (["… ще %d" % (len(рядки) - МАКС_РЯДКІВ)] if len(рядки) > МАКС_РЯДКІВ else [])
    return ("хук дошка_поля: коміт файлів дошки (%s) відхилено — поля не проходять перевірку CI "
            "(`python3 джерела/прилади/згорнути_дошку.py --лише-перевірити`; шапка `джерела/прилади/дошка_поля.py`). "
            "Виправ файл і коміть знову:\n%s" % (", ".join(файли), "\n".join(показ)))


def main():
    try:
        відмова = рішення(json.load(sys.stdin))
    except Exception as е:  # зламаний хук не спиняє сесії
        застереження = "хук дошка_поля: збій хука, коміт іде без звірки полів: %s: %s" % (type(е).__name__, е)
        print(застереження, file=sys.stderr)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": застереження}},
                         ensure_ascii=False))
        return
    if відмова:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": відмова}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
