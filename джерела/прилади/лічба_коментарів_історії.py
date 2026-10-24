#!/usr/bin/env python3
"""Рахує рядки коментарів і докстрінгів та позначає службові посилання.

Приймає файли або каталоги. Python розбирає токенами й AST, JavaScript і HTML —
рядковими маркерами. Вихід: загальна лічба, лічба збігів і, якщо не вимкнено,
їхні адреси. Прилад нічого не виправляє і не є гейтом.
"""

import argparse
import ast
import io
from pathlib import Path
import re
import tokenize


СУФІКСИ = {".py", ".js", ".html"}
ОЗНАКИ = re.compile(
    r"(?:"
    r"\b(?:19|20)\d{2}[./-]\d{1,2}(?:[./-]\d{1,2})?\b|"
    r"\b\d{1,2}[./-]\d{1,2}[./-](?:19|20)\d{2}\b|"
    r"\b(?:PR|MR)\s*#?\d+\b|"
    r"(?<![\w#])#\d{2,}\b|"
    r"\bряд(?:ок|ки|ка|ку|ком|ках|ків)\s+(?:дошки\s+)?\d+|"
    r"\bЖИВІ?[-‑ ]?\d+"
    r")",
    re.IGNORECASE,
)


def файли(шляхи):
    for назва in шляхи:
        шлях = Path(назва)
        if шлях.is_file() and шлях.suffix in СУФІКСИ:
            yield шлях
        elif шлях.is_dir():
            yield from (
                файл
                for файл in sorted(шлях.rglob("*"))
                if файл.is_file() and файл.suffix in СУФІКСИ
            )


def докстрінги(дерево):
    for вузол in ast.walk(дерево):
        if not isinstance(вузол, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not вузол.body:
            continue
        вираз = вузол.body[0]
        if isinstance(вираз, ast.Expr) and isinstance(вираз.value, ast.Constant):
            if isinstance(вираз.value.value, str):
                yield вираз.lineno, вираз.end_lineno, вираз.value.value


def рядки_python(шлях):
    сире = шлях.read_bytes()
    текст = сире.decode(tokenize.detect_encoding(io.BytesIO(сире).readline)[0])
    рядки = текст.splitlines()
    зайняті = set()
    for токен in tokenize.generate_tokens(io.StringIO(текст).readline):
        if токен.type == tokenize.COMMENT:
            зайняті.add(токен.start[0])
            yield токен.start[0], токен.string
    for початок, кінець, значення in докстрінги(ast.parse(текст)):
        for номер in range(початок, кінець + 1):
            if номер not in зайняті:
                yield номер, рядки[номер - 1]


def рядки_розмітки(шлях):
    у_блоці = False
    for номер, рядок in enumerate(шлях.read_text(encoding="utf-8").splitlines(), 1):
        чистий = рядок.strip()
        if шлях.suffix == ".html":
            if "<!--" in чистий:
                у_блоці = True
            if у_блоці:
                yield номер, чистий
            if "-->" in чистий:
                у_блоці = False
        else:
            if у_блоці or чистий.startswith("//") or "/*" in чистий:
                yield номер, чистий
            if "/*" in чистий:
                у_блоці = True
            if "*/" in чистий:
                у_блоці = False


def main():
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument("шляхи", nargs="+", help="файли або каталоги")
    парсер.add_argument("--без-переліку", action="store_true", help="не друкувати адреси збігів")
    аргументи = парсер.parse_args()
    усього = збігів = 0
    for шлях in файли(аргументи.шляхи):
        джерело = рядки_python(шлях) if шлях.suffix == ".py" else рядки_розмітки(шлях)
        for номер, рядок in джерело:
            усього += 1
            if ОЗНАКИ.search(рядок):
                збігів += 1
                if not аргументи.без_переліку:
                    print(f"{шлях}:{номер}: {рядок.strip()}")
    print(f"{усього} рядків коментарів; {збігів} з ознакою історії")


if __name__ == "__main__":
    main()
