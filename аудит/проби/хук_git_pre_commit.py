#!/usr/bin/env python3
"""Стенд хука git `.githooks/pre-commit` (наряд диспетчера 16.11, КОЛО #4013): справжній `git commit` у тимчасовому клоні.

Запуск (з кореня репозиторію): python3 аудит/проби/хук_git_pre_commit.py   (код виходу ≠ 0, якщо є ✗)
Тимчасовий репозиторій: копії приладів, паспортів, дошки й `.githooks` з робочого дерева, `core.hooksPath=.githooks`,
як після SessionStart. Команди виконує `bash -c` — так, як їх пише сесія: це не виклик функції хука, а коміт.
Мірило: кожна форма команди з рядків 15931–15934 (heredoc з апострофом через `cat >` і `git commit -F -`, маркер у лапках,
коментар оболонки перед `git commit` чи після `git add`, `cd <інше дерево>`, `git -C`; незакрита лапка — синтаксична помилка оболонки, коміт не стартує, хукові нічого стерегти) з хибним файлом
дошки — коміт відхилено (код ≠ 0, у stderr названо файл і поле); добрий файл — проходить; без файлів дошки — проходить
і хук мовчить; `--amend`, `-a`, `-- <шляхи>`, `bash -c 'git commit'`, `git merge`, `git commit-tree` — як описано в мітках.
З `--старий <шлях до старого хука>` ті самі форми ганяються крізь старий хук PreToolUse (JSON на stdin): «пропусків A з N».
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
Д = "аудит/дошка/claude/стенд.md"
ДОБРИЙ = ("| 16999 | виконавець · стенд хука: рядок для перевірки <!-- дошка: дата=2026-11-16; рід=процес; "
          "попередник=ні; механізм=неповна-правка; корінь=жоден --> | низька | **ВІДКРИТО** · виявлено: виконавець; "
          "внесено: #1 | вимір | місце | мірило |\n")
ХИБНИЙ = ДОБРИЙ.replace("рід=процес", "рід=нісенітниця")
ТІЛО_ЗІ_СЛОВОМ = "<<'EOF'\n" + ХИБНИЙ.replace("стенд хука", "пам'ять хука") + "EOF"
збої = []


def sh(*а, cwd, вхід=None, env=None):
    return subprocess.run(list(а), cwd=cwd, input=вхід, capture_output=True, text=True, env=env)


def перевір(умова, текст):
    print(("✔ " if умова else "✗ ") + текст)
    if not умова:
        збої.append(текст)


def новий():
    т = tempfile.mkdtemp(prefix="стенд_хук_")
    for шлях in ("джерела/прилади", "аудит/корені", ".githooks"):
        shutil.copytree(os.path.join(КОРІНЬ, шлях), os.path.join(т, шлях), ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(os.path.join(КОРІНЬ, "аудит/БЕКЛОГ.md"), os.path.join(т, "аудит/БЕКЛОГ.md"))
    sh("git", "init", "-q", "-b", "main", cwd=т)
    for к, з in (("user.name", "стенд"), ("user.email", "s@s"), ("core.hooksPath", ".githooks")):
        sh("git", "config", к, з, cwd=т)
    sh("git", "add", "-A", cwd=т)
    sh("git", "commit", "-q", "-m", "початок", cwd=т)
    return т


def пиши(т, вміст, шлях=Д):
    повний = os.path.join(т, шлях)
    os.makedirs(os.path.dirname(повний), exist_ok=True)
    with open(повний, "w", encoding="utf-8") as ф:
        ф.write(вміст)


def біг(т, команда):
    return sh("bash", "-c", команда, cwd=т)


ФОРМИ = [  # (мітка, команда з {Д}, потрібен інший репозиторій А?)
    ("15931 а: cat > файл <<'EOF' з апострофом ⏎ git add -A && git commit", f"cat > {Д} {ТІЛО_ЗІ_СЛОВОМ}\ngit add -A && git commit -m x"),
    ("15931 б: git commit -F - <<'EOF' з апострофом", f"cat > {Д} <<'EOF'\n{ХИБНИЙ}EOF\ngit add -A\ngit commit -F - <<'EOF'\nзапис про пам'ять\nEOF"),
    ("15932: маркер <<EOF у лапках ⏎ git commit ⏎ EOF", f'echo "<<EOF"\ngit add -A\ngit commit -m x\nEOF'),
    ("15933 а: # коментар ⏎ git add <файл> && git commit", f"# крок 3: коміт\ngit add {Д} && git commit -m x"),
    ("15933 б: git add -A  # усе ⏎ git commit", "git add -A  # усе\ngit commit -m x"),
    ("15933 в: # … ⏎ git commit && git push", "# коміт і пуш\ngit add -A\n# ще\ngit commit -m x && git push origin HEAD"),
    ("15934 а: cd <інше дерево> && git commit -F - <<'EOF' з апострофом", "cd {А} && git commit -F - <<'EOF'\nпам'ять\nEOF"),
    ("15934 б: git -C <інше дерево> commit -m \"пам'ять\"", "git -C {А} commit -m \"пам'ять\""),
    ("15917: bash -c 'git commit -m y'", "bash -c 'git commit -m y'"),
]


def старий_хук(хук, т, команда):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=т)
    р = sh(sys.executable, хук, cwd=т, env=env,
           вхід=json.dumps({"tool_name": "Bash", "tool_input": {"command": команда}, "cwd": т}))
    return "deny" in р.stdout


def підготуй(команда):
    """(дерево, де виконати, готова команда): хибний файл дошки — в індексі дерева коміту; форми `{А}` ідуть з чистого Б."""
    А, Б = новий(), новий()
    пиши(А, ХИБНИЙ)
    sh("git", "add", "-A", cwd=А)
    return А, (Б if "{А}" in команда else А), Б, команда.replace("{А}", А).replace("{Д}", Д)


def основне():
    for мітка, команда in ФОРМИ:
        А, де, Б, к = підготуй(команда)
        р = біг(де, к)
        перевір(р.returncode != 0 and Д in р.stderr and "рід" in р.stderr,
                f"{мітка}: відхилено (код {р.returncode}), названо файл і поле")
        n = sh("git", "rev-list", "--count", "HEAD", cwd=А).stdout.strip()
        перевір(n == "1", f"{мітка}: нового коміту нема")
        shutil.rmtree(А)
        shutil.rmtree(Б)


def звичайний():
    т = новий()
    пиши(т, ХИБНИЙ)
    біг(т, f"git add {Д}")
    sh("git", "reset", "-q", cwd=т)
    пиши(т, ДОБРИЙ)
    біг(т, f"git add {Д}")
    р = біг(т, "git commit -m добрий")
    перевір(р.returncode == 0, "добрий файл дошки — коміт проходить")
    пиши(т, "x", "файл.txt")
    біг(т, "git add файл.txt")
    р = біг(т, "git commit -m без_дошки")
    перевір(р.returncode == 0 and not р.stderr and "pre-commit" not in р.stdout, "коміт без файлів дошки — проходить, хук мовчить")
    # --amend: хибне виправлення дошки в уже наявному коміті
    пиши(т, ХИБНИЙ)
    біг(т, f"git add {Д}")
    р = біг(т, "git commit --amend --no-edit")
    перевір(р.returncode != 0 and Д in р.stderr, "git commit --amend з хибним файлом дошки — звіряє, відхилено")
    біг(т, "git reset -q HEAD")
    біг(т, f"git checkout -- {Д}")
    # -a та шляхи
    пиши(т, ХИБНИЙ)
    р = біг(т, "git commit -a -m x")
    перевір(р.returncode != 0 and Д in р.stderr, "git commit -a — звіряє (файл дошки змінено, уже відстежуваний)")
    р = біг(т, f"git commit -m x -- {Д}")
    перевір(р.returncode != 0 and Д in р.stderr, "git commit -- <файл дошки> — звіряє")
    біг(т, f"git checkout -- {Д}")
    # 15918: коміт за шляхом без `--` і без файлу дошки, хибний файл дошки в індексі — індекс у коміт не йде
    пиши(т, ХИБНИЙ)
    біг(т, f"git add {Д}")
    пиши(т, "y", "інший.txt")
    біг(т, "git add інший.txt")
    р = біг(т, "git commit -m y інший.txt")
    перевір(р.returncode == 0 and not р.stderr, "15918: git commit -m y інший.txt (шлях без --) — не звіряє: файл дошки в цей коміт не йде")
    біг(т, "git reset -q HEAD")
    біг(т, f"git checkout -- {Д}")
    біг(т, f"git rm -q --cached {Д}")
    # git merge без конфлікту
    біг(т, "git checkout -q -b гілка")
    пиши(т, ХИБНИЙ, "аудит/дошка/claude/гілка.md")
    біг(т, "git add -A && git commit -q --no-verify -m гілка")
    біг(т, "git checkout -q main")
    пиши(т, "z", "файл2.txt")
    біг(т, "git add -A && git commit -q -m main2")
    р = біг(т, "git merge --no-ff -m злиття гілка")
    перевір(р.returncode == 0, "git merge без конфлікту — не звіряє: pre-commit для злиття git не запускає")
    # commit-tree
    біг(т, f"git checkout -q -b ч main~0 && git rm -q --cached -r аудит/дошка")
    р = біг(т, "SHA=$(git commit-tree 'HEAD^{tree}' -p HEAD -m 'ДИСПЕТЧЕР: лист') && echo $SHA")
    перевір(р.returncode == 0 and len(р.stdout.strip()) == 40, "git commit-tree — не звіряє: інструмент низького рівня, хуків не кличе (листи й позначки)")
    shutil.rmtree(т)


def сесія():
    т = новий()
    sh("git", "config", "--unset", "core.hooksPath", cwd=т)
    with open(os.path.join(КОРІНЬ, ".claude/settings.json"), encoding="utf-8") as ф:
        д = json.load(ф)
    команди = [х["command"] for г in д["hooks"]["SessionStart"] for х in г["hooks"] if "hooksPath" in х["command"]]
    перевір(len(команди) == 1, "settings.json: одна команда SessionStart ставить core.hooksPath")
    shutil.rmtree(os.path.join(т, ".githooks"))
    shutil.copytree(os.path.join(КОРІНЬ, ".githooks"), os.path.join(т, ".githooks"))
    sh("bash", "-c", команди[0], cwd=т, env=dict(os.environ, CLAUDE_PROJECT_DIR=т))
    р = sh("git", "config", "core.hooksPath", cwd=т)
    перевір(р.stdout.strip() == ".githooks", f"після старту сесії: git config core.hooksPath → {р.stdout.strip()}")
    перевір(sorted(os.listdir(os.path.join(т, ".githooks"))) == ["pre-commit"], "у теці хуків лише pre-commit")
    shutil.rmtree(т)


def порівняння(хук):
    """Ті самі форми крізь старий хук PreToolUse: скільки пропущено."""
    пропусків = 0
    for мітка, команда in ФОРМИ:
        А, де, Б, к = підготуй(команда)
        відмова = старий_хук(хук, де, к)
        пропусків += not відмова
        print(("  відмова " if відмова else "  ПРОПУСК ") + мітка)
        shutil.rmtree(А)
        shutil.rmtree(Б)
    print(f"старий хук: пропусків {пропусків} з {len(ФОРМИ)}")


if __name__ == "__main__":
    if "--старий" in sys.argv:
        порівняння(sys.argv[sys.argv.index("--старий") + 1])
        sys.exit(0)
    основне()
    звичайний()
    сесія()
    sys.exit(1 if збої else 0)
