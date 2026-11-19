# -*- coding: utf-8 -*-
"""Тест `сайт_pages.py` (рядки дошки 16652–16654): що сайт — це продукт і сторінки, а не все дерево.

python3 джерела/прилади/тест_сайт_pages.py   # з кореня репозиторію; код 0 — усе зійшлось
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import сайт_pages as с  # noqa: E402

помилки = []


def перевір(умова, що):
    if not умова:
        помилки.append(що)


def замикання():
    файли = {
        "index.html", "шрифти/a.ttf", "аудит/СТАН.md", "аудит/x/p.html", "аудит/x/img/a.png", "аудит/y/z.md",
        "аудит/y/дальша.html", "аудит/y/поруч.css", "аудит/w/далі.md", "аудит/w/зайве.md", "джерела/показ.html",
        "ohliad-koloru/index.html", ".github/workflows/a.yml", "AGENTS.md", "README.md", "аудит/top.html",
    }
    тексти = {
        "index.html": '<link href="ohliad-koloru/"><a href="https://example.com/x">',
        "аудит/x/p.html": ('<a href="../y/z.md#2">z</a><a href="../y/%D0%B4%D0%B0%D0%BB%D1%8C%D1%88%D0%B0.html">'
                           '<a href="../../../поза.html"><img src=img/a.png><a href="/kod-shi-data/шрифти/a.ttf">'
                           '<a href="mailto:x@y"><a href="../СТАН.md?x=1"><a href="${шлях}">'),
        "аудит/y/дальша.html": '<style>@import "поруч.css";</style><script>fetch("../w/далі.md")</script>',
        "аудит/top.html": "",
    }

    def читати(шляхи):
        return {ш: тексти.get(ш, "").encode() for ш in шляхи}

    одн = с.одиниці(файли=файли, читати=читати)
    # аудит/y/ — тека зі сторінкою (правило 2), аудит/w/далі.md — за fetch зі сторінки, до якої веде посилання,
    # аудит/СТАН.md — за посиланням; «поза.html» — за межею сайта, mailto і шаблон `${…}` — не файли.
    очікувані = ["ohliad-koloru/", "аудит/x/", "аудит/y/", "шрифти/", "README.md", "index.html", "аудит/top.html",
                 "аудит/w/далі.md", "аудит/СТАН.md"]
    перевір(одн == sorted(очікувані), f"замикання: {одн}")
    перевір(not с.у_сайті("аудит/w/зайве.md", одн), "файл без посилання на нього — не сайт")
    перевір(not с.у_сайті("джерела/показ.html", одн), "джерела/ — не сайт")
    перевір(not с.у_сайті("AGENTS.md", одн), "файл правил сесій — не сайт")


def шаблони():
    перевір(с.шаблон("a[1]*.html") == "/a\\[1\\]\\*.html", "екранування шаблону")
    перевір(с.шаблон("аудит/айдентика/") == "/аудит/айдентика/", "шаблон теки")
    перевір(с.шаблон("#x!.md") == "/\\#x\\!.md", "екранування # і !")


def справжнє_дерево():
    одн = с.одиниці("HEAD")
    for треба in ("index.html", "build.txt", "шрифти/", "ohliad-koloru/", "показ_зонд.html", "каталог_повний.xml.gz",
                  "аудит/айдентика/", "аудит/тести/інструкція_тестувальниць/"):
        перевір(треба in одн, f"на HEAD сайт без {треба}")
    for ні in ("аудит/СТАН.md", "аудит/БЕКЛОГ.md", "аудит/наряди/x.md", "аудит/проби/живі_сцени.txt",
               "джерела/показ.html", ".github/workflows/pages.yml", "CLAUDE.md"):
        перевір(not с.у_сайті(ні, одн), f"на HEAD у сайті зайве: {ні}")
    # Шаблони sparse-checkout вибирають рівно файли одиниць (синтаксис той самий, що в .gitignore).
    файли = с.дерево("HEAD")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as ф:
        ф.write("\n".join(с.шаблон(о) for о in одн) + "\n")
    try:
        вибрані = set(subprocess.run(["git", "ls-files", "-z", "-i", "-c", f"--exclude-from={ф.name}"],
                                     capture_output=True, check=True).stdout.decode().split("\0")) - {""}
    finally:
        os.unlink(ф.name)
    сайт = {ш for ш in файли if с.у_сайті(ш, одн)}
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], check=False).returncode == 0:
        перевір(вибрані == сайт, f"шаблони вибрали {len(вибрані)} файлів, сайт — {len(сайт)}: "
                                 f"{sorted(вибрані ^ сайт)[:5]}")
    # Межа розміру: сайт розгортається за хвилини, а не як усе дерево (6 ГБ); 1 ГБ — межа сайта Pages.
    сире = subprocess.run(["git", "ls-tree", "-r", "-l", "-z", "--full-tree", "HEAD"], capture_output=True,
                          check=True).stdout
    байтів = 0
    for з in сире.split(b"\0"):
        if з:
            мета, шлях = з.split(b"\t", 1)
            if с.у_сайті(шлях.decode(), одн) and мета.split()[3] != b"-":
                байтів += int(мета.split()[3])
    перевір(0 < байтів < 500_000_000, f"сайт {байтів / 1e6:.0f} МБ — понад 500 МБ (чи порожній)")
    перевір(len(с.відбиток("HEAD", одн)) == 64 and с.відбиток("HEAD", одн) == с.відбиток("HEAD"), "відбиток")
    print(f"сайт на HEAD: {len(одн)} одиниць, {len(сайт)} файлів, {байтів / 1e6:.0f} МБ")


замикання()
шаблони()
справжнє_дерево()
for п in помилки:
    print("ВАДА:", п)
print("помилок:", len(помилки))
sys.exit(1 if помилки else 0)
