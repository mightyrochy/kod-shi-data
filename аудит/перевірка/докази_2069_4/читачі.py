"""Відтворювана інвентаризація прямих операцій із файлами перевірюваних форматів.

Список функцій відібрано оглядом усіх збігів rg; кожне місце рахується окремо.
Окремо позначено байтовий SHA256, вивід cat та іншу схему JSONL каталогу.
"""
import ast
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

КОРІНЬ = Path(__file__).resolve().parents[3]
ФУНКЦІЇ = {
    "zhnyvarka/виконавець.py": {"__init__", "_стан", "_пиши", "_магазин", "_horoshop_адреси", "_список_адреси"},
    "zhnyvarka/обхід.py": {"останні_рядки", "прочитати_стан", "записати", "main"},
    "джерела/прилади/назви_карток_зібрати.py": {"назви_із_жнив"},
    "zhnyvarka/json_прохід.py": {"журнал_збігається", "позначити"},
    "zhnyvarka/складальник.py": {"читати_записи", "писати_записи"},
}


def текст(sha, файл):
    return subprocess.check_output(["git", "show", f"{sha}:{файл}"], cwd=КОРІНЬ).decode("utf-8")


def знайти(sha):
    рядки = []
    for файл, функції in ФУНКЦІЇ.items():
        код = текст(sha, файл)
        for ф in ast.walk(ast.parse(код)):
            if not isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)) or ф.name not in функції:
                continue
            for в in ast.walk(ф):
                if not isinstance(в, ast.Call):
                    continue
                ім = в.func.id if isinstance(в.func, ast.Name) else в.func.attr if isinstance(в.func, ast.Attribute) else ""
                if ім not in {"open", "read_bytes", "read_text", "write_text", "NamedTemporaryFile", "GzipFile"}:
                    continue
                група = ("SHA256" if файл.endswith("json_прохід.py") else
                         "каталог v1" if файл.endswith("складальник.py") else "зміст жнив")
                рядки.append(dict(файл=файл, рядок=в.lineno, функція=ф.name, операція=ім, група=група))
    файл = ".github/workflows/zhnyva.yml"
    for n, р in enumerate(текст(sha, файл).splitlines(), 1):
        if 'cat "$JOURNAL_ROOT/зведення_жнив.tsv"' in р:
            рядки.append(dict(файл=файл, рядок=n, функція="harvest", операція="cat", група="вивід байтів"))
    return sorted(рядки, key=lambda р: (р["файл"], р["рядок"]))


def перевірити_читача(sha, файл, ім):
    # Виконується точний AST функції; імпорт усього приладу міняв би cwd і тягнув каталог.
    дерево = ast.parse(текст(sha, файл))
    функція = next(в for в in дерево.body if isinstance(в, ast.FunctionDef) and в.name == ім)
    простір = dict(gzip=gzip, json=json, os=os, ЗАПИСИ="")
    exec(compile(ast.Module(body=[функція], type_ignores=[]), файл, "exec"), простір)
    for вид, хвіст in (("UTF-8", 'Сукня'.encode()[:-1]), ("JSON", b'{"url":')):
        with tempfile.TemporaryDirectory(prefix="review-2069-4-reader-") as tmp:
            шлях = Path(tmp) / "test.jsonl.gz"
            with gzip.open(шлях, "wb") as ф:
                ф.write('{"url":"https://a.com/1","картка":{"назва":"Сукня"}}\n'.encode() + хвіст
                        + b'\n{"url":"https://a.com/2"}\n')
            try:
                простір[ім](tmp if ім == "назви_із_жнив" else str(шлях))
            except (UnicodeError, ValueError) as e:
                print(json.dumps(dict(sha=sha, читач=f"{файл}:{функція.lineno}", пошкодження=вид,
                                      наслідок=type(e).__name__, збережено_сусідів=False), ensure_ascii=False))
            else:
                raise AssertionError("Очікувана вада не відтворилась")


def main():
    голови = ("7a3173e767b403ffcee0030dea4a721cb4dd156b", "af743cd654d7b0cdbc9432e0018b8518f62bf649")
    for sha in голови:
        знайдені = знайти(sha)
        print(f"ГОЛОВА: {sha}")
        for р in знайдені:
            print(f"{р['файл']}:{р['рядок']} | {р['функція']} | {р['операція']} | {р['група']}")
        print(json.dumps(dict(усього=len(знайдені), зміст_жнив=sum(р["група"] == "зміст жнив" for р in знайдені),
                              SHA256=2, вивід_байтів=1, каталог_v1=2), ensure_ascii=False))
        for файл, ім in (("джерела/прилади/назви_карток_зібрати.py", "назви_із_жнив"),
                        ("zhnyvarka/складальник.py", "читати_записи")):
            перевірити_читача(sha, файл, ім)
    print("КОД 0: інвентаризацію завершено, обидва неізольовані читачі відтворили винятки ДО та ПІСЛЯ")


if __name__ == "__main__":
    main()
