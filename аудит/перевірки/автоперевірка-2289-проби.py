"""Відтворення зауважень #2289 без викликів моделей і правок реалізації.

python аудит/перевірки/автоперевірка-2289-проби.py <дерево голови PR>
"""
import ast
import importlib.util
import json
from pathlib import Path
import random
import re
import sys


корінь = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(корінь / "джерела"))
шлях = корінь / "джерела/прилади/корінь_е2_промпти.py"
специфікація = importlib.util.spec_from_file_location("прилад_2289", шлях)
прилад = importlib.util.module_from_spec(специфікація)
специфікація.loader.exec_module(прилад)


def довжини(відносний, текст):
    модуль = прилад.Мод(відносний, текст)
    return прилад.довжини_сталих(
        str(корінь), {(str(Path(відносний).parent), модуль.ім): модуль}
    )


# Реальний складений промпт жнив: додаємо вимогу тільки в його контракт крою.
відносний = "джерела/жнива_промпти.py"
текст = (корінь / відносний).read_text(encoding="utf-8")
дерево = ast.parse(текст)
контракт = next(
    вузол.value for вузол in дерево.body
    if isinstance(вузол, ast.Assign)
    and isinstance(вузол.targets[0], ast.Name)
    and вузол.targets[0].id == "_КРІЙ_СУКНІ"
)
рядки = текст.splitlines(keepends=True)
додаток = " Always inspect every visible seam before choosing the construction."
# Зберігаємо ліву частину присвоєння, замінюємо тільки літерал у пам'яті.
новий = "".join(рядки[:контракт.lineno - 1]) + "_КРІЙ_СУКНІ = " + repr(контракт.value + додаток) + "\n" + "".join(рядки[контракт.end_lineno:])
до, після = довжини(відносний, текст), довжини(відносний, новий)
import жнива_промпти as жнива
реальний_до = len(жнива._підставити(жнива.ПРОМПТ_ОДЯГ, "сукня", сукня=True))
старий = жнива._КРІЙ_СУКНІ
try:
    жнива._КРІЙ_СУКНІ = старий + додаток
    реальний_після = len(жнива._підставити(жнива.ПРОМПТ_ОДЯГ, "сукня", сукня=True))
finally:
    жнива._КРІЙ_СУКНІ = старий

print(json.dumps({
    "проба": "довжина контракту сукні",
    "реальний_промпт_до": реальний_до,
    "реальний_промпт_після": реальний_після,
    "прилад_до": до[відносний + ":ПРОМПТ_ОДЯГ"],
    "прилад_після": після[відносний + ":ПРОМПТ_ОДЯГ"],
    "усі_довжини_приладу_незмінні": до == після,
}, ensure_ascii=False))

# Пункт 3 має однаково працювати для того самого реєстру в будь-якому файлі.
місце = прилад.Місце(
    "джерела/приклад.py", 2,
    "Slots are: top, bottom, outer, shoes.", "стала", "А"
)
значення = {"top", "bottom", "outer", "shoes"}
print(json.dumps({
    "проба": "реєстр у тому самому файлі",
    "п3_реєстр_поруч": len(прилад.пункт3_дубль_коду(
        [місце], {"джерела/приклад.py:СЛОТИ": значення}, {})),
    "п3_реєстр_в_іншому_файлі": len(прилад.пункт3_дубль_коду(
        [місце], {"джерела/реєстр.py:СЛОТИ": значення}, {})),
}, ensure_ascii=False))

# Вже знайдений шляхом А функціональний промпт відсутній у базі довжин.
відносний = "open-source-stylist/system/adapter/prompt.py"
вимір = довжини(відносний, (корінь / відносний).read_text(encoding="utf-8"))
print(json.dumps({
    "проба": "функціональний промпт",
    "файл": відносний,
    "промптів_у_довжинах": len(вимір),
}, ensure_ascii=False))

відносний = "джерела/мовний_шар.py"
дерево = ast.parse((корінь / відносний).read_text(encoding="utf-8"))
заборона_поради = next(в for в in ast.walk(дерево)
    if isinstance(в, ast.Constant) and isinstance(в.value, str)
    and 'when she asked nothing, nothing' in в.value)
місце = прилад.Місце(відносний, заборона_поради.lineno,
                     заборона_поради.value, "оголошення", "А")
print(json.dumps({
    "проба": "зміст помилково названий форматом",
    "рядок": заборона_поради.lineno,
    "п2_формат_словами": len(прилад.пункт2_формат([місце])),
    "текст": заборона_поради.value,
}, ensure_ascii=False))

if "--вибірка" in sys.argv:
    сирий = Path(sys.argv[sys.argv.index("--вибірка") + 1]).read_bytes()
    вивід = сирий.decode("utf-16" if сирий[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig")
    місця = [р for р in вивід.splitlines() if re.search(" · пункт [1-4] · ", р)]
    print("ВИБІРКА МІСЦЬ, seed=2910")
    for рядок in random.Random(2910).sample(місця, 20):
        print(рядок)
    зайняті = {р.split(":")[0] for р in вивід.splitlines() if " · пункт " in р}
    файли = [(ф, т) for ф, т in прилад.файли_коду(str(корінь))
             if ф not in зайняті and прилад.шар_файла(ф) not in ("проба", "прилад")]
    print("ВИБІРКА ФАЙЛІВ БЕЗ МІСЦЬ, seed=2913")
    ознаки = re.compile(r"\b(return|respond|answer|use|keep|must|never|always|only|prompt|system|schema)\b|повер|відпов|промпт|використ|завжди|ніколи|лише|тільки|заборон", re.I)
    for файл, тип in random.Random(2913).sample(файли, 20):
        текст = (корінь / файл).read_text(encoding="utf-8")
        print(файл)
        if тип == "py":
            try:
                літерали = [(в.lineno, в.value) for в in ast.walk(ast.parse(текст))
                            if isinstance(в, ast.Constant) and isinstance(в.value, str)]
            except SyntaxError:
                літерали = []
        else:
            літерали = [(р, з) for р, з, _ in прилад.літерали_js(текст)]
        for рядок, значення in літерали:
            if ознаки.search(значення):
                print(" ", рядок, repr(значення[:300]))
