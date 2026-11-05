# -*- coding: utf-8 -*-
"""Приховані вади, частина (б): відтворювані вибірки для точності класів (кожне k-те місце).

Наряд `аудит/наряди/Приховані-розвідка.md`, частина (б). Число місць приладу — верхня межа; точність класу міряє
людина чи перевірка на вибірці. Вибірку тут не обирає ніхто: кожне k-те місце виводу приладу (k — `КРОК`,
≈ місць / 20; перше — місце 1), тож перевірка відтворює ту саму двадцятку й звіряє вердикти з `аудит/корені/Приховані-перелік-б.md`.

п.17 і п.20 прилади лічать інший клас (без докстрінга; історія й контракт), тому їхні вибірки — з усіх функцій ядра
з докстрінгом довжиною від 8 рядків (п.17: чи є «чому так» там, де рішення) і всіх коментарів ядра від 5 слів (п.20:
чи коментар збігається з кодом).

Запуск з кореня репозиторію (~2 хв):
  python3 джерела/прилади/приховані_b_вибірка.py <тека>      пише <тека>/<клас>.s, рядок на місце
"""
import io
import os
import re
import subprocess
import sys
import tokenize
import ast

ТУТ = os.path.dirname(os.path.abspath(__file__))
КОРІНЬ = os.path.dirname(os.path.dirname(ТУТ))
sys.path.insert(0, os.path.join(КОРІНЬ, "джерела"))

ДЖЕРЕЛА = {
    "Т2": ["приховані_b_точність.py", "--клас", "Т2"], "Т4": ["приховані_b_точність.py", "--клас", "Т4"],
    "Т5": ["приховані_b_точність.py", "--клас", "Т5"], "Т6": ["приховані_b_точність.py", "--клас", "Т6"],
    "п10": ["приховані_b_стандарт.py", "--пункт", "10"], "п11": ["приховані_b_стандарт.py", "--пункт", "11"],
    "п14": ["приховані_b_стандарт.py", "--пункт", "14"], "п14js": ["приховані_b_поза.py", "--пункт", "14"],
}


# крок вибірки, з яким міряно 31.10 (≈20 місць на клас; Т5 — усі 18)
КРОК = {"Т2": 20, "Т4": 2, "Т5": 1, "Т6": 8, "п10": 66, "п11": 9, "п14": 5, "п14js": 5}


def кожне_k(рядки, n=20, k=None):
    k = k or max(1, len(рядки) // n)
    return рядки[::k]


def з_приладу(аргументи, фільтр=None):
    вихід = subprocess.run([sys.executable, os.path.join(ТУТ, аргументи[0])] + аргументи[1:], cwd=КОРІНЬ,
                           capture_output=True, text=True).stdout.splitlines()
    рядки = [р for р in вихід if "\t" in р]
    return [р for р in рядки if фільтр(р)] if фільтр else рядки


def п17_п20():
    import status
    функції, коментарі = [], []
    for м in sorted(status.МОДУЛІ_ПРОДУКТУ):
        шлях = "джерела/%s.py" % м
        текст = io.open(os.path.join(КОРІНЬ, шлях), encoding="utf-8").read()
        for в in ast.walk(ast.parse(текст)):
            if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(в) \
                    and в.end_lineno - в.lineno >= 8:
                функції.append("%s:%d\t%s()" % (шлях, в.lineno, в.name))
        with io.open(os.path.join(КОРІНЬ, шлях), encoding="utf-8") as ф:
            for т in tokenize.generate_tokens(ф.readline):
                if т.type == tokenize.COMMENT and len(re.findall(r"[А-Яа-яІіЇїЄєҐґ]{3,}", т.string)) >= 5:
                    коментарі.append("%s:%d\t%s" % (шлях, т.start[0], т.string[:80]))
    return кожне_k(функції)[:20], кожне_k(коментарі)[:20], len(функції), len(коментарі)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    тека = sys.argv[1]
    os.makedirs(тека, exist_ok=True)
    for к, а in ДЖЕРЕЛА.items():
        рядки = з_приладу(а, (lambda р: "живий шлях" in р) if к == "п14js" else None)
        вибірка = кожне_k(рядки, k=КРОК[к])
        io.open(os.path.join(тека, к + ".s"), "w", encoding="utf-8").write("\n".join(вибірка) + "\n")
        print("%-5s з %d місць — %d" % (к, len(рядки), len(вибірка)))
    ф, к, нф, нк = п17_п20()
    io.open(os.path.join(тека, "п17.s"), "w", encoding="utf-8").write("\n".join(ф) + "\n")
    io.open(os.path.join(тека, "п20.s"), "w", encoding="utf-8").write("\n".join(к) + "\n")
    print("п17   з %d функцій — %d\nп20   з %d коментарів — %d" % (нф, len(ф), нк, len(к)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
