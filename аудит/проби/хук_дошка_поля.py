#!/usr/bin/env python3
"""Стенд хука `.claude/хуки/дошка_поля.py` (наряд диспетчера 16.11): коміт файлу дошки з хибними полями — відмова.

Запуск (з кореня репозиторію, потрібні голови в клоні): python3 аудит/проби/хук_дошка_поля.py
Мірило: записані файли дошки з голів #3997 (bc62011c…) і #3998 (e5b7023e…) — відмова з тими самими рядками «ПОМИЛКА»,
що дає прилад CI (`згорнути_дошку.py --лише-перевірити`); виправлені з голів ebd61f5f… і 16451b20… — коміт іде;
коміт без файлів дошки — прилад не запускається; збій хука (нема приладу) — коміт іде з попередженням.
Наряд 16.11 (рядки 15899–15901): коміт файлу дошки з хибними полями в ІНШОМУ дереві, ніж `CLAUDE_PROJECT_DIR`
(`cd <дерево> && git commit`, `git -C <дерево> commit`), з префіксом змінної середовища — відмова; `git commit-tree` і
коміт за шляхом без файлу дошки — без відмови; нема голови в клоні — стенд червоний з назвою голови.
Тимчасовий репозиторій: копії приладів і дошки з робочого дерева, файл дошки — в індексі.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ХУК = os.path.join(КОРІНЬ, ".claude", "хуки", "дошка_поля.py")
Д1 = "аудит/дошка/claude/перевірка-пачка-1611-0150-А.md"
Д2 = "аудит/дошка/claude/перевірка-пачка-1611-0142.md"
ВИПАДКИ = [  # (мітка, голова, файл, чекаємо відмову, помилок у файлі)
    ("#3997 до", "bc62011c6fc5d823e93d0e049c587a85a8e986dd", Д1, True),
    ("#3998 до", "e5b7023e279b598965605f3fda0453cf17156ca4", Д2, True),
    ("#3997 після", "ebd61f5f274520236c7f4ca4724d945c671fc87e", Д1, False),
    ("#3998 після", "16451b20ad01a2e43f5d08cf503ebc9e24ccae25", Д2, False),
]


def sh(*а, cwd, вхід=None, env=None):
    return subprocess.run(а, cwd=cwd, input=вхід, capture_output=True, text=True, env=env)


def новий_репозиторій():
    т = tempfile.mkdtemp(prefix="хук_дошка_")
    os.makedirs(os.path.join(т, "джерела"))
    shutil.copytree(os.path.join(КОРІНЬ, "джерела", "прилади"), os.path.join(т, "джерела", "прилади"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    os.makedirs(os.path.join(т, "аудит", "дошка", "claude"))
    shutil.copy(os.path.join(КОРІНЬ, "аудит", "БЕКЛОГ.md"), os.path.join(т, "аудит"))
    shutil.copytree(os.path.join(КОРІНЬ, "аудит", "корені"), os.path.join(т, "аудит", "корені"))
    sh("git", "init", "-q", cwd=т)
    sh("git", "add", "-A", cwd=т)
    sh("git", "-c", "user.email=a@b", "-c", "user.name=x", "commit", "-qm", "база", cwd=т)
    return т


def хук(т, команда="git commit -m x", проєкт=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=проєкт or т)
    п = time.perf_counter()
    р = sh(sys.executable, ХУК, cwd=т, вхід=json.dumps({"tool_name": "Bash", "tool_input": {"command": команда}}),
           env=env)
    мс = (time.perf_counter() - п) * 1000
    вихід = json.loads(р.stdout) if р.stdout.strip() else {}
    ш = вихід.get("hookSpecificOutput", {})
    return ш.get("permissionDecision") == "deny", ш.get("permissionDecisionReason", ""), ш.get("additionalContext", ""), \
        р.stderr, мс


def вміст_голови(голова, файл):
    """Файл з голови; нема голови в клоні чи порожній — None (стенд червоний з назвою голови, а не ✔ на порожньому)."""
    р = sh("git", "show", f"{голова}:{файл}", cwd=КОРІНЬ)
    return р.stdout if р.returncode == 0 and р.stdout.strip() else None


def помилки_приладу(т):
    р = sh(sys.executable, "-I", "джерела/прилади/згорнути_дошку.py", "--лише-перевірити", cwd=т)
    return [л for л in р.stderr.splitlines() if л.startswith("ПОМИЛКА")]


def main():
    збої = 0

    def перевір(умова, текст):
        nonlocal збої
        print(("✔ " if умова else "✗ ") + текст)
        збої += 0 if умова else 1

    for мітка, голова, файл, чекаємо in ВИПАДКИ:
        т = новий_репозиторій()
        вміст = вміст_голови(голова, файл)
        if вміст is None:
            перевір(False, f"{мітка}: нема голови {голова} у клоні (git fetch origin {голова}) — випадок не виміряно")
            shutil.rmtree(т)
            continue
        with open(os.path.join(т, файл), "w", encoding="utf-8") as ф:
            ф.write(вміст)
        sh("git", "add", "-A", cwd=т)
        відмова, причина, _, _, мс = хук(т)
        прилад = помилки_приладу(т)
        показані = [л for л in причина.splitlines() if л.startswith("ПОМИЛКА")]
        if чекаємо:
            перевір(відмова and показані == прилад and len(прилад) > 0,
                    f"{мітка} ({голова[:8]}): коміт відхилено, помилок {len(показані)} = рядки приладу CI ({мс:.0f} мс)")
        else:
            перевір(not відмова and not прилад, f"{мітка} ({голова[:8]}): коміт пройшов, помилок 0 ({мс:.0f} мс)")
        shutil.rmtree(т)

    # 15899–15900: хибний файл дошки в індексі дерева А, проєкт (CLAUDE_PROJECT_DIR) — чисте дерево П
    вміст = вміст_голови(ВИПАДКИ[0][1], Д1)
    if вміст is not None:
        А, П = новий_репозиторій(), новий_репозиторій()
        with open(os.path.join(А, Д1), "w", encoding="utf-8") as ф:
            ф.write(вміст)
        sh("git", "add", "-A", cwd=А)
        for мітка, команда, проєкт, чекаємо in [
            ("cd <інше дерево> && git commit", f"cd {А} && git commit -m y", П, True),
            ("git -C <інше дерево> commit", f"git -C {А} commit -m y", П, True),
            ("префікс змінної GIT_AUTHOR_NAME=x git commit", "GIT_AUTHOR_NAME=x git commit -m y", А, True),
            ("два префікси + cd", f"cd {А} && A=1 B='2 3' git commit -m y", П, True),
            ("git commit-tree", "SHA=$(git commit-tree 'HEAD^{tree}' -p HEAD -m \"ДИСПЕТЧЕР: x\")", А, False),
            ("git commit -m y -- інший.txt", "git commit -m y -- інший.txt", А, False),
            ("git commit -m y -- файл дошки", f"git commit -m y -- {Д1}", А, True),
        ]:
            відмова, причина, застереження, _, мс = хук(А, команда, проєкт)
            перевір(відмова == чекаємо and not застереження and (not чекаємо or "ПОМИЛКА" in причина),
                    f"{мітка}: {'відмова' if відмова else 'пропуск'}, очікували {'відмову' if чекаємо else 'пропуск'} ({мс:.0f} мс)")
        shutil.rmtree(А)
        shutil.rmtree(П)
        # 15931: тіло heredoc — не код оболонки; збій розбору — не пропуск
        Б = новий_репозиторій()  # файл дошки з хибними полями — у робочому дереві, не в індексі
        with open(os.path.join(Б, Д1), "w", encoding="utf-8") as ф:
            ф.write(вміст)
        В = новий_репозиторій()  # той самий файл — в індексі
        with open(os.path.join(В, Д1), "w", encoding="utf-8") as ф:
            ф.write(вміст)
        sh("git", "add", "-A", cwd=В)
        тіло = "<<'EOF'\nзапис про пам'ять і її стан\nEOF"
        for мітка, дерево, команда, чекаємо in [
            ("15931 а: cat > файл дошки <<'EOF' з апострофом + git add -A && git commit", Б,
             f"cat > {Д1} {тіло}\ngit add -A && git commit -m x", True),
            ("15931 б: git commit -F - <<'EOF' з апострофом", В, f"git commit -F - {тіло}", True),
            ("15931 в: git commit -m \"$(cat <<'EOF' … пам'ять … EOF)\"", В,
             "git commit -m \"$(cat <<'EOF'\nпідсумок: пам'ять\nEOF\n)\"", True),
            ("15931 г: незакрита лапка у git commit — збій розбору не пропуск", В, "git commit -m 'зламана", True),
            ("15931 д: «git commit» лише в тілі heredoc — не коміт", В, "cat <<'EOF'\ngit commit -m x\nEOF", False),
        ]:
            відмова, причина, застереження, _, мс = хук(дерево, команда)
            перевір(відмова == чекаємо and not застереження and (not чекаємо or "ПОМИЛКА" in причина),
                    f"{мітка}: {'відмова' if відмова else 'пропуск'}{' ' + застереження[:60] if застереження else ''}, "
                    f"очікували {'відмову' if чекаємо else 'пропуск'} ({мс:.0f} мс)")
        shutil.rmtree(Б)
        shutil.rmtree(В)
    else:
        перевір(False, f"нема голови {ВИПАДКИ[0][1]} у клоні — випадки 15899–15900 не виміряно")

    т = новий_репозиторій()  # без дошки: прилад не викликано
    with open(os.path.join(т, "файл.txt"), "w") as ф:
        ф.write("x")
    sh("git", "add", "-A", cwd=т)
    os.remove(os.path.join(т, "джерела", "прилади", "згорнути_дошку.py"))  # якби прилад викликали — збій-попередження
    відмова, _, застереження, _, мс = хук(т)
    перевір(not відмова and not застереження, f"коміт без файлів дошки: пройшов, прилад не викликано ({мс:.0f} мс)")
    перевір(not хук(т, "git status")[0], "не коміт — хук мовчить")

    sh("git", "reset", "-q", cwd=т)
    shutil.copy(os.path.join(КОРІНЬ, "аудит", "БЕКЛОГ.md"), os.path.join(т, Д1))
    sh("git", "add", "-A", cwd=т)  # файл дошки в індексі, приладу нема → збій хука не блокує
    відмова, _, застереження, ст, _ = хук(т)
    перевір(not відмова and "збій хука" in застереження and "збій хука" in ст, "нема приладу: коміт іде, попередження")
    відмова, _, застереження, _, _ = хук(т, "git commit -m 'зламана")
    перевір(not відмова, "команда не розібрана, файлів дошки й приладу нема: коміт іде")
    shutil.rmtree(т)
    sys.exit(1 if збої else 0)


if __name__ == "__main__":
    main()
