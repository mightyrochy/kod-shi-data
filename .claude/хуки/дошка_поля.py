#!/usr/bin/env python3
"""Хук PreToolUse на `Bash`: коміт файлу дошки `аудит/дошка/**` не йде, доки поля не пройшли ту саму перевірку, що в CI.

Чому: файл дошки сесія пише за шапкою `джерела/прилади/дошка_поля.py`, а поля звіряв лише CI на голові PR — після листа
«ГОТОВО». За 15–16.11 це тричі дало червоний CI (#3963, звіти перевірки #3997 і #3998) і окрему сесію доробки.
Тепер звірка — у мить коміту (наряд диспетчера 16.11 за листом менеджера 03:18).

Що робить з `Bash`-командою, де є `git commit`:
- дерево коміту — `git -C <тека>`, `cd <тека> &&` у команді чи початкова тека виклику, а не лише `CLAUDE_PROJECT_DIR`;
  префікс змінних (`A=1 git commit`) пропускається, `git commit-tree` — не коміт, коміт `-- <шляхи>` — лише їхні файли;
- серед файлів коміту нема `аудит/дошка/**` — нічого, прилад не запускається;
- є — запускає `python3 джерела/прилади/згорнути_дошку.py --лише-перевірити`, те саме, що крок CI «файли дошки згортаються»
  (той самий код приладу, правил тут нема), і при коді виходу ≠ 0 відмовляє, показуючи його рядки «ПОМИЛКА <файл>:<рядок>: …».
Розбір команди: тіла heredoc (`<<'EOF' … EOF`) перед розбором прибираються — це дані, не код; збій розбору (незакрита
лапка) — не пропуск: кожен `git … commit` команди рахується комітом у початковому дереві без обмеження шляхів.
Файли коміту: індекс; коли команда сама робить `git add` чи `commit -a`, ще й змінені та нові файли дошки робочого дерева.

Хук не падає сесію й не спиняє її за власний збій (нема python, приладу, git, команду не розібрано, прилад завис):
виклик іде як є, рядок попередження.
Не покриває: Codex і `agy` на ноутбуці комітять не через Claude Code.
"""
import json
import os
import re
import shlex
import subprocess
import sys

ТЕКА = "аудит/дошка/"
ПРИЛАД = os.path.join("джерела", "прилади", "згорнути_дошку.py")
САМ_ДОДАЄ = re.compile(r"\bgit(?:\s+(?:-[cC]\s+\S+|--\S+))*\s+add\b|\bcommit(?![-\w])[^;&|\n]*?(?:\s-[a-zA-Z]*a|\s--all\b)")
ЗМІННА = re.compile(r"^[A-Za-z_]\w*=")
HEREDOC = re.compile(r"<<(-?)[ \t]*(?:'([^'\n]+)'|\"([^\"\n]+)\"|\\?([A-Za-z_][\w.-]*))")
КОМІТ = re.compile(r"\bgit\b[^\n;&|]*?\bcommit(?![-\w])")
МЕЖА_С = 60
МАКС_РЯДКІВ = 40


def без_heredoc(команда):
    """Команда без тіл heredoc (`<<'EOF' … EOF`, `<<-EOF`): тіло — дані для `cat`/`git commit -F -`, не код оболонки, і
    його апостроф чи лапка не мають відкривати лапку розбору. Рядок з маркером лишається, рядки тіла й кінцевий
    рядок-обмежник — зникають. Маркер без обмежника далі в команді — не heredoc, нічого не прибирається."""
    рядки, вихід, i = команда.split("\n"), [], 0
    while i < len(рядки):
        р = рядки[i]
        вихід.append(р)
        i += 1
        черга = [(м.group(1) == "-", м.group(2) or м.group(3) or м.group(4)) for м in HEREDOC.finditer(р)
                 if not р[:м.start()].endswith("<")]
        for тире, межа in черга:
            кінець = next((j for j in range(i, len(рядки))
                           if (рядки[j].lstrip("\t") if тире else рядки[j]) == межа), None)
            if кінець is None:
                break
            i = кінець + 1
    return "\n".join(вихід)


def коміти(команда, корінь):
    """[(дерево, шляхи після `--` чи None)] для кожного `git commit` команди.

    Дерево — `-C <тека>` git або `cd <тека>` раніше в команді (відносно попереднього), інакше `корінь`.
    Префікси змінних середовища пропускаються; `git commit-tree` — не коміт."""
    команда = без_heredoc(команда)
    л = shlex.shlex(команда.replace("\n", " ; "), posix=True, punctuation_chars=True)
    л.whitespace_split = True
    try:
        слова = list(л)
    except ValueError:
        # Збій розбору — не пропуск: команду не розібрано, тож лічимо кожен `git … commit` у ній комітом у початковому
        # дереві й без обмеження шляхів (звірка індексу й, коли є `git add`/`-a`, робочого дерева).
        return [(корінь, None)] if КОМІТ.search(команда) else []
    сегменти, поточний = [], []
    for с in слова:
        if с and set(с) <= set(";&|()"):
            сегменти.append(поточний)
            поточний = []
        else:
            поточний.append(с)
    сегменти.append(поточний)
    дерево, результат = корінь, []
    for сег in сегменти:
        while сег and ЗМІННА.match(сег[0]):
            сег = сег[1:]
        if not сег:
            continue
        if сег[0] == "cd" and len(сег) > 1:
            дерево = os.path.normpath(os.path.join(дерево, os.path.expanduser(сег[1])))
            continue
        if сег[0] != "git":
            continue
        з, тека, i = сег, дерево, 1
        while i < len(з) and з[i].startswith("-"):
            if з[i] == "-C" and i + 1 < len(з):
                тека = os.path.normpath(os.path.join(тека, з[i + 1]))
                i += 2
            elif з[i] == "-c" and i + 1 < len(з):
                i += 2
            else:
                i += 1
        if i < len(з) and з[i] == "commit":
            шляхи = з[з.index("--") + 1:] if "--" in з[i:] else None
            результат.append((тека, шляхи))
    return результат


def файли_дошки(корінь, команда, шляхи=None):
    """Файли `аудит/дошка/**` коміту в дереві `корінь`: індекс, а коли команда сама додає чи комітить `-a` — ще й
    робоче дерево; коміт за шляхами (`-- <шляхи>`) — лише ті з них, що під текою дошки."""
    р = subprocess.run(["git", "-c", "core.quotepath=off", "status", "--porcelain=v1", "-z", "--", ТЕКА],
                       cwd=корінь, capture_output=True, text=True, timeout=МЕЖА_С)
    if р.returncode != 0:
        raise RuntimeError("git status: " + р.stderr.strip()[:200])
    сам = bool(САМ_ДОДАЄ.search(команда))
    знайдені = []
    for запис in [з for з in р.stdout.split("\0") if з]:
        індекс, дерево, шлях = запис[0], запис[1], запис[3:]
        if шляхи is not None:
            if any(шлях == ш.rstrip("/") or шлях.startswith(ш.rstrip("/") + "/") for ш in шляхи):
                знайдені.append(шлях)
        elif шлях.startswith(ТЕКА) and (індекс not in " ?" or (сам and дерево != " ") or (сам and індекс == "?")):
            знайдені.append(шлях)
    return знайдені


def перевірка(корінь, запасний):
    """Рядки «ПОМИЛКА» приладу дерева `корінь` (прилад дерева, а як нема — проєкту); [] — поля чисті."""
    прилад = os.path.join(корінь, ПРИЛАД)
    if not os.path.isfile(прилад):
        прилад = os.path.join(запасний, ПРИЛАД)
    if not os.path.isfile(прилад):
        raise RuntimeError("нема приладу " + ПРИЛАД)
    р = subprocess.run([sys.executable, "-I", прилад, "--лише-перевірити"], cwd=корінь, capture_output=True,
                       text=True, timeout=МЕЖА_С)
    if р.returncode == 0:
        return []
    рядки = [л for л in (р.stderr + "\n" + р.stdout).splitlines() if л.startswith("ПОМИЛКА")]
    if not рядки:
        raise RuntimeError("прилад вийшов з кодом %d без рядків «ПОМИЛКА»: %s" % (р.returncode, р.stderr.strip()[:200]))
    return рядки


def рішення(дані):
    """None — коміт іде; текст відмови — інакше."""
    if дані.get("tool_name") != "Bash":
        return None
    команда = str((дані.get("tool_input") or {}).get("command", ""))
    if "commit" not in команда:
        return None
    проєкт = os.environ.get("CLAUDE_PROJECT_DIR") or дані.get("cwd") or os.getcwd()
    початок = дані.get("cwd") or os.getcwd()
    for дерево, шляхи in коміти(команда, початок):
        if not os.path.isdir(дерево):
            continue
        файли = файли_дошки(дерево, команда, шляхи)
        if not файли:
            continue
        рядки = перевірка(дерево, проєкт)
        if not рядки:
            continue
        показ = рядки[:МАКС_РЯДКІВ] + (["… ще %d" % (len(рядки) - МАКС_РЯДКІВ)] if len(рядки) > МАКС_РЯДКІВ else [])
        return ("хук дошка_поля: коміт файлів дошки (%s) відхилено — поля не проходять перевірку CI "
                "(`python3 джерела/прилади/згорнути_дошку.py --лише-перевірити`; шапка `джерела/прилади/дошка_поля.py`). "
                "Виправ файл і коміть знову:\n%s" % (", ".join(файли), "\n".join(показ)))
    return None


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
