"""Незалежно звіряє обхід Е2-вікно на голові PR і старим приладом.

Запуск: python -X utf8 цей_файл.py <тимчасове дерево голови PR>.
Не викликає моделей і не змінює продукт: випадки живуть у TemporaryDirectory.
"""
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import types

репо = Path(sys.argv[1]).resolve()
прилад = репо / "джерела/прилади/корінь_е2_вікно.py"
база = "b25c1ea3732ec34ad93e7b00b88ce6f776851c5b"
специфікація = importlib.util.spec_from_file_location("прилад_голови", прилад)
новий = importlib.util.module_from_spec(специфікація)
специфікація.loader.exec_module(новий)
старий = types.ModuleType("прилад_бази")
старий.__file__ = str(прилад)
код_бази = subprocess.check_output(
    ["git", "show", f"{база}:джерела/прилади/корінь_е2_вікно.py"], cwd=репо
).decode("utf-8")
exec(compile(код_бази, str(прилад), "exec"), старий.__dict__)


def число(модуль, дерево):
    """Рахує порушення через публічну функцію приладу."""
    місця, _ = модуль.місця(str(дерево))
    return sum(bool(м["пункти"]) for м in місця)


усі = subprocess.check_output(["git", "ls-files", "-z"], cwd=репо).decode("utf-8").split("\0")
очікувані = sorted(
    ш for ш in усі
    if ш.startswith(("джерела/", "zhnyvarka/")) and ш.endswith((".py", ".js"))
    and not ш.startswith(("джерела/проби/", "джерела/прилади/"))
    and not any(ч.startswith(".") or ч in {"node_modules", "__pycache__", "site-packages", "venv"}
                for ч in ш.split("/")[:-1])
)
фактичні = sorted(ш for розш in (".py", ".js") for ш, _ in новий.файли_продукту(str(репо), розш))
assert фактичні == очікувані, (set(очікувані) - set(фактичні), set(фактичні) - set(очікувані))
print(f"Обхід: {len(фактичні)} файлів; Python {sum(ш.endswith('.py') for ш in фактичні)}; JS {sum(ш.endswith('.js') for ш in фактичні)}; розбіжностей з git ls-files: 0")
старий_вибір = {
    ш for ш in усі
    if (ш.startswith("джерела/показ/") and ш.endswith(".js") and ш.count("/") == 2)
    or (ш.startswith("джерела/") and ш.endswith(".py") and ш.count("/") == 1
        and not re.match(r"(?:тест|gate|audit|build_|стенд|проба|measure|pair_test)", ш.split("/")[-1]))
}
print(f"Нових файлів в обході: {len(set(фактичні) - старий_вибір)}")
print(f"Справжня голова: ДО {число(старий, репо)} -> ПІСЛЯ {число(новий, репо)}")
місця_до, _ = старий.місця(str(репо))
місця_після, _ = новий.місця(str(репо))
def ключ(м):
    шлях = м["файл"]
    if шлях.startswith("показ/"):
        шлях = "джерела/" + шлях
    return шлях, м["рядок"], м["функція"], м["пункти"]
assert sorted(map(ключ, місця_до)) == sorted(map(ключ, місця_після))
print("Наявні місця: шляхи нормалізовано; рядки, функції та пункти збігаються")

клієнт_py = '''import json, urllib.request
def надіслати(промпт):
    return urllib.request.urlopen(urllib.request.Request("http://x/v1/chat/completions", data=json.dumps({"messages": [{"role": "user", "content": промпт}], "max_tokens": 600}).encode()))
'''
клієнт_js = 'async function окремийКлієнт(дані) { return await модельП(дані); }\n'
випадки = [
    ("Python у вкладеній джерела", "джерела/клієнти/а/б/gate_новий.py", клієнт_py, 23),
    ("Python у вкладеній zhnyvarka", "zhnyvarka/а/б/в/audit_новий.py", клієнт_py, 23),
    ("JS у вкладеній джерела", "джерела/клієнти/а/б/новий.js", клієнт_js, 23),
    ("JS у вкладеній zhnyvarka", "zhnyvarka/а/б/в/новий.js", клієнт_js, 23),
    ("Python у пробах", "джерела/проби/а/новий.py", клієнт_py, 22),
    ("JS у приладах", "джерела/прилади/а/новий.js", клієнт_js, 22),
    ("Python у node_modules", "zhnyvarka/node_modules/а/новий.py", клієнт_py, 22),
    ("JS у прихованій теці", "джерела/.прихована/новий.js", клієнт_js, 22),
]
with tempfile.TemporaryDirectory(prefix="незалежна-2492-") as тимчасова:
    дерево = Path(тимчасова)
    for шлях in фактичні:
        до = дерево / шлях
        до.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(репо / шлях, до)
    for назва, шлях, текст, очік in випадки:
        файл = дерево / шлях
        файл.parent.mkdir(parents=True, exist_ok=True)
        файл.write_text(текст, encoding="utf-8")
        до, після = число(старий, дерево), число(новий, дерево)
        print(f"{назва}: ДО {до} -> ПІСЛЯ {після}; очікувано {очік}")
        assert після == очік
        файл.unlink()
    for звідки, куди in (
        ("джерела/каталог_розбір_прогін.py", "zhnyvarka/клієнти/каталог_розбір_прогін.py"),
        ("джерела/жнива_промпти.py", "джерела/клієнти/а/жнива_промпти.py"),
        ("джерела/показ/паспорт.js", "zhnyvarka/клієнти/паспорт.js"),
    ):
        звідки, куди = дерево / звідки, дерево / куди
        куди.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(звідки, куди)
        до, після = число(старий, дерево), число(новий, дерево)
        print(f"Перенесення {звідки.relative_to(дерево).as_posix()} -> {куди.relative_to(дерево).as_posix()}: ДО {до} -> ПІСЛЯ {після}; очікувано 22")
        assert після == 22
        shutil.move(куди, звідки)
print("Незалежні проби: 11 ОК; провалів: 0")
