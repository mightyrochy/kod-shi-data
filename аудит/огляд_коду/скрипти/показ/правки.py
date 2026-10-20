"""Скільки комітів за період правили кожну верхню функцію `показ.html` — за заголовком ханка git
(найближчий рядок з колонки 0 перед ханком: `function ім(` / `async function ім(`). Плюс: скільки злиттів PR\nправили показ і скільки з них — ще й стенд. Потрібна повна історія (`git fetch --unshallow`).
Запуск з кореня: python3 аудит/огляд_коду/скрипти/показ/правки.py [з дати, типово 2026-09-18]"""
import re, subprocess, sys
from collections import Counter, defaultdict
З = sys.argv[1] if len(sys.argv) > 1 else "2026-09-18"
вивід = subprocess.run(["git", "log", "--since=" + З, "--no-merges", "--format=@@К %h", "-p", "--unified=0", "--",
                        "джерела/показ.html"], capture_output=True, text=True, errors="replace").stdout
коміти, на_функцію, рядків = 0, defaultdict(set), Counter()
к = None
for р in вивід.split("\n"):
    if р.startswith("@@К "):
        к = р[4:]; коміти += 1
    elif р.startswith("@@ "):
        м = re.search(r"@@ [^@]* @@ (?:async )?function\s+([^\s(]+)", р)
        if м:
            на_функцію[м.group(1)].add(к)
    elif р.startswith(("+", "-")) and not р.startswith(("+++", "---")):
        рядків[к] += 1
print("комітів (без злиттів) з %s: %d; змінених рядків %d" % (З, коміти, sum(рядків.values())))
for ім, кк in sorted(на_функцію.items(), key=lambda x: -len(x[1]))[:15]:
    print("  %s\t%d" % (ім, len(кк)))
# злиття PR у main з тієї ж дати: скільки правили показ і скільки з них — ще й стенд
злиття = subprocess.run(["git", "log", "--first-parent", "--merges", "--since=" + З, "--format=%H", "origin/main"],
                        capture_output=True, text=True).stdout.split()
разом = показ = 0
for h in злиття:
    ф = subprocess.run(["git", "-c", "core.quotePath=false", "diff", "--name-only", h + "^1", h], capture_output=True, text=True).stdout.split("\n")
    п, с = "джерела/показ.html" in ф, "аудит/проби/рв6_стенд.js" in ф
    показ += п; разом += п and с
print("злиттів у main з %s: %d; правили показ %d, з них і стенд %d" % (З, len(злиття), показ, разом))
