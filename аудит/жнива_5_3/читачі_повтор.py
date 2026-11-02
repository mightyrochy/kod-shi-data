"""Повтор інвентаризації 10682 та пошкодженого gzip на базі й поточних файлах."""
import ast
import gzip
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "zhnyvarka"))
from журнал_карток import прочитати


def main():
    """Друкує обходи спільного механізму й кількість збережених сусідів."""
    сп = importlib.util.spec_from_file_location("інвентар", КОРІНЬ / "аудит/перевірка/докази_2069_4/читачі.py")
    інвентар = importlib.util.module_from_spec(сп); сп.loader.exec_module(інвентар)
    for стан in ("906c686135ee7987896a8b28faff4111bb238771", "робочі файли"):
        def текст(_sha, файл):
            """Обирає точний код початкового коміту або робочої голови."""
            return ((КОРІНЬ / файл).read_text(encoding="utf-8") if стан == "робочі файли" else
                    subprocess.check_output(["git", "show", f"{стан}:{файл}"], cwd=КОРІНЬ).decode("utf-8"))
        інвентар.текст = текст
        обхід = [р for р in інвентар.знайти(стан) if р["група"] == "зміст жнив"]
        print(стан, "обходів:", len(обхід))
        for р in обхід:
            print(р)
        for файл, ім in (("джерела/прилади/назви_карток_зібрати.py", "назви_із_жнив"),
                        ("zhnyvarka/складальник.py", "читати_записи")):
            дерево = ast.parse(текст(стан, файл))
            функція = next(в for в in дерево.body if isinstance(в, ast.FunctionDef) and в.name == ім)
            простір = dict(gzip=gzip, json=json, os=os, ЗАПИСИ="", СХЕМА="v1", прочитати=прочитати)
            exec(compile(ast.Module(body=[функція], type_ignores=[]), файл, "exec"), простір)
            for вид, пошкоджене in (("UTF-8", b'\xd0'), ("JSON", b'{"url":')):
                with tempfile.TemporaryDirectory() as тека:
                    шлях = Path(тека) / "store.jsonl.gz"
                    рядки = ([dict(url="https://a/1", картка=dict(назва="Сукня")),
                              dict(url="https://a/2", картка=dict(назва="Пальто"))] if ім == "назви_із_жнив" else
                             [dict(схема="v1", початок="", кінець=""), dict(схема="v1", ід="1"), dict(схема="v1", ід="2")])
                    дані = [json.dumps(р, ensure_ascii=False).encode() + b"\n" for р in рядки]
                    with gzip.open(шлях, "wb") as ф:
                        ф.write(b"".join(дані[:-1]) + пошкоджене + b"\n" + дані[-1])
                    try:
                        вихід = простір[ім](тека if ім == "назви_із_жнив" else str(шлях))
                        кількість = len(вихід if ім == "назви_із_жнив" else вихід[1])
                        assert кількість == 2
                        наслідок = f"цілих сусідів {кількість}"
                    except (UnicodeError, ValueError) as п:
                        if стан == "робочі файли":
                            raise
                        наслідок = type(п).__name__
                    print(ім, вид, наслідок)


if __name__ == "__main__":
    main()
