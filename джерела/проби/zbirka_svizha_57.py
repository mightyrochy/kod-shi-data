# -*- coding: utf-8 -*-
"""Рядок 57 дошки: перший прогін збірки у СВІЖОМУ дереві.

ДО ПРАВКИ (виміряно 19.09.2026): «показ: повний зонд не побачив `composer`» —
фікстури `каталог_brief.xml` на диску нема, `запити` віддають порожній пул; а
з розпакованою фікстурою — «каталог_повний.xml БРУДНИЙ — помилок слота 325,
подвійних екранувань 24». CI обидва кроки робив окремо й був зелений.
ПІСЛЯ: збірка розпаковує обидва каталоги й чистить фід тією самою функцією,
що й CI (`чистка_каталогу.забезпечити_чистим`), і перший прогін зелений."""
import sys, os, re, shutil, pathlib, subprocess, tempfile
_КОРІНЬ = pathlib.Path(__file__).resolve().parent.parent

# СВІЖЕ СЕРЕДОВИЩЕ = КОПІЯ ДЕРЕВА БЕЗ РОЗПАКОВАНИХ КАТАЛОГІВ, А НЕ ВИДАЛЕННЯ З РОБОЧОГО (рядок 2740).
# Доти проба `unlink`-ала `джерела/каталог_повний.xml` і `каталог_brief.xml` прямо в робочому
# дереві й будувала там; паралельна лічба проб (NYTOK=6) у ці хвилини читала зниклий фід —
# шість червоних `FileNotFoundError`, що на NYTOK=2 зеленіли. Тепер збірка йде у власній
# тимчасовій копії (архіви `.gz` — джерело, розпакованих копій у копії нема, як у свіжому
# checkout), а робоче дерево проба не чіпає.
кореневий = pathlib.Path(tempfile.mkdtemp(prefix="svizha_57_"))
тека = кореневий / _КОРІНЬ.name
shutil.copytree(_КОРІНЬ, тека, ignore=shutil.ignore_patterns(
    "node_modules", "__pycache__", "каталог_повний.xml", "каталог_brief.xml", "каталог_збагачення.json"))
shutil.copy(_КОРІНЬ.parent / "каталог_повний.xml.gz", кореневий / "каталог_повний.xml.gz")
print("збірка у власній копії дерева без розпакованих каталогів (робоче дерево не чіпано)")

вихід = os.path.join(tempfile.mkdtemp(), "index_проба.html")
r = subprocess.run([sys.executable, "build_артефакт.py", ".", вихід, "показ-повний"],
                   cwd=тека, capture_output=True, text=True, timeout=1800,
                   env=dict(os.environ, LYUSTERKO_CATALOG="повний"))
вив = r.stdout + r.stderr
чистка = next((s.strip() for s in вив.splitlines() if "каталог почищено" in s), None)
речей = re.search(r"· (\d+) речей", вив)
print("зібрано: %s (код %d)" % ("ТАК" if r.returncode == 0 else "НІ", r.returncode))
print("речей: %s" % (речей.group(1) if речей else "—"))
print("чистка: %s" % (чистка or "рядка про чистку нема"))
if r.returncode:
    print("причина відмови: %s" % вив.strip().splitlines()[-1][:200])
shutil.rmtree(кореневий, ignore_errors=True)
assert r.returncode == 0 and чистка and речей, "перший прогін у свіжому дереві не зелений"
