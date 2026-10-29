# -*- coding: utf-8 -*-
"""прилади/промпти_одне_джерело.py — мірило наряду Е2-промпти-одне-джерело: одна вимога — одне місце.

ЧОМУ ЦЕ Є. `промпти_перелік.py` лічить повтори в ЗІБРАНОМУ тексті промпту: спільна межа з `МЕЖІ` чи спільний рядок
виглядають там «повтором» у кожному промпті, хоч написані в коді раз. Вимога живе в коді, тож мірило — ДЖЕРЕЛО:
скільки разів ту саму вимогу написано руками. Лічба — AST модулів, що пишуть промпти (`МОДУЛІ`), а не зібраний текст:
константа, яку читають десять промптів, рахується один раз.

ЩО ЛІЧИТЬ (ПІСЛЯ — 0 для 1–3, 5):
  1. речення ≥ 40 знаків (без регістру й лапок), написані рядковими літералами у ≥ 2 місцях коду промптів;
  2. поля входу `Поле(...)` з одним шляхом і схожим «що» (≥ 0,6), написані у ≥ 2 місцях: спільне поле — одне
     оголошення в `спільні_вимоги`, задача міняє лише «як»;
  3. вимоги до ФОРМИ відповіді, написані словами поза реєстром `схема_відповіді` (JSON-обʼєкт, «answer_schema»,
     кінець відповіді в дужці);
  4. довжина сталої частини кожного оголошення (симв., як `промпти_перелік.ВИМІР_ІСТОРІЇ`) — ДО/ПІСЛЯ різниця;
  5. речення, що стоїть двічі в сталій частині ОДНОГО промпту.

Запуск із кореня: python3 -W ignore джерела/прилади/промпти_одне_джерело.py [--json вихід.json]
Друкує факт; нічого не пише в репозиторій. ДО — той самий запуск на `git worktree` із `origin/main`."""
import ast
import collections
import difflib
import glob
import json
import os
import re
import sys

ДЖЕРЕЛА = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ДЖЕРЕЛА)
sys.path.insert(0, os.path.join(ДЖЕРЕЛА, "прилади"))

# модулі, де пишуть слова моделі: оголошення збирача, повтори, перекладачки, запити розбору каталогу
ДОДАТКОВІ = ("мовний_шар", "жнива_промпти", "заміна_речі", "протокол", "людський_вихід", "спільні_вимоги",
             "схема_відповіді", "збирач_промптів")
# вимоги до форми відповіді словами: їх місце — `схема_відповіді` (фраза формату, кінець, повтор)
ФОРМА_СЛОВАМИ = re.compile(r"one JSON object|only one JSON|ONLY one JSON|(?:Відповідь|відповідь)[^.]{0,40}JSON-об['ʼ]єкт|"
                           r"ЛИШЕ JSON|begins with \{|answer is over|same JSON object|valid JSON string", re.I)
РЕЄСТР_ФОРМИ = ("схема_відповіді.py", "фрази_формату.py")  # реєстр форми відповіді і його нижній шар


def _норм(т):
    return re.sub(r"\s+", " ", re.sub(r"[\"«»“”'`]", "", т.lower())).strip()


def _речення(т):
    return [р.strip() for р in re.split(r"(?<=[.;!?])\s+(?=[A-ZА-ЯІЇЄҐ\"«(])", т) if len(р.strip()) >= 40]


def модулі():
    """[шлях] модулів промптів: усі, що пишуть `Оголошення(`, плюс `ДОДАТКОВІ`."""
    вих = []
    for ф in sorted(glob.glob(os.path.join(ДЖЕРЕЛА, "*.py"))):
        м = os.path.basename(ф)[:-3]
        if м.startswith("тест_"):
            continue
        if м in ДОДАТКОВІ or "Оголошення(" in open(ф, encoding="utf-8").read():
            вих.append(ф)
    return вих


def _рядки_коду(ф):
    """[(рядок, значення)] рядкових літералів модуля без докстрінгів; f-рядки й шаблони без `%`-змінних — як є."""
    дерево = ast.parse(open(ф, encoding="utf-8").read())
    док = set()
    for n in ast.walk(дерево):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and \
                isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            док.add(id(n.body[0].value))
    return [(n.lineno, n.value) for n in ast.walk(дерево)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in док]


def дублі_речень(файли):
    """{норм. речення: [(файл, рядок, речення)]} — речення у ≥ 2 різних літералах."""
    де = collections.defaultdict(list)
    for ф in файли:
        for н, т in _рядки_коду(ф):
            for р in _речення(т):
                де[_норм(р)].append((os.path.basename(ф), н, р))
    return {к: v for к, v in де.items() if len({(x[0], x[1]) for x in v}) >= 2}


def дублі_полів(файли):
    """[(шлях, [(файл, рядок, що)])] — `Поле("шлях", "що", …)` зі схожим «що» у ≥ 2 місцях."""
    за_шляхом = collections.defaultdict(list)
    for ф in файли:
        for n in ast.walk(ast.parse(open(ф, encoding="utf-8").read())):
            if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) == "Поле" and \
                    len(n.args) >= 2 and all(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in n.args[:2]):
                за_шляхом[n.args[0].value].append((os.path.basename(ф), n.lineno, n.args[1].value))
    вих = []
    for шлях, л in за_шляхом.items():
        групи = []
        for x in л:
            for г in групи:
                if difflib.SequenceMatcher(None, _норм(г[0][2]), _норм(x[2])).ratio() >= 0.6:
                    г.append(x)
                    break
            else:
                групи.append([x])
        вих += [(шлях, г) for г in групи if len(г) >= 2]
    return вих


def форма_словами(файли):
    """[(файл, рядок, початок)] — літерали про форму відповіді поза реєстром форми."""
    вих = []
    for ф in файли:
        if os.path.basename(ф) in РЕЄСТР_ФОРМИ:
            continue
        for н, т in _рядки_коду(ф):
            if ФОРМА_СЛОВАМИ.search(т) and len(т) < 700:
                вих.append((os.path.basename(ф), н, re.sub(r"\s+", " ", т)[:70]))
    return вих


def довжини():
    """{клас: симв. сталої частини оголошення} — як `промпти_перелік.ВИМІР_ІСТОРІЇ`, за іменем «модуль.ІМ'Я»."""
    import warnings
    warnings.simplefilter("ignore")
    import промпти_перелік as ПП
    вих, повтор_у_промпті = {}, {}
    for кл, о, _ in ПП.оголошення():
        import збирач_промптів as ЗП
        межі = ЗП.МЕЖІ_EN if о.мова_промпту == "en" else ЗП.МЕЖІ
        try:
            скелет = ЗП.скелет(о) if о.відповідь_як == "json" else None
        except Exception:
            скелет = None
        стале = {"role": о.роль, "input": ["%s — %s; %s" % (п.шлях, п.що, п.як) for п in о.вхід],
                 "rules": list(о.правила), "codes": list(о.коди), "limits": [межі.get(x, "") for x in о.межі],
                 "answer_schema": скелет, "end": о.наприкінці or ""}
        вих[кл] = len(json.dumps(стале, ensure_ascii=False))
        # речення, що стоїть двічі в сталій частині одного промпту (без скелета: там підписи листків)
        л = collections.Counter(_норм(р) for ч in ([о.роль] + list(о.правила) + list(о.коди) + [о.наприкінці or ""]
                                                   + [п.що + ". " + п.як for п in о.вхід]
                                                   + [межі.get(x, "") for x in о.межі])
                                for р in _речення(ч))
        повтор_у_промпті[кл] = sum(н - 1 for н in л.values() if н > 1)
    return вих, повтор_у_промпті


def main(арг):
    файли = модулі()
    р, п, ф = дублі_речень(файли), дублі_полів(файли), форма_словами(файли)
    д, в = довжини()
    print("модулів промптів: %d" % len(файли))
    print("1. речень у ≥2 місцях коду: %d (зайвих знаків %d)" % (
        len(р), sum(len(v[0][2]) * (len({(x[0], x[1]) for x in v}) - 1) for v in р.values())))
    print("2. полів входу з одним шляхом, написаних у ≥2 місцях: %d (зайвих оголошень %d)" % (
        len(п), sum(len(г) - 1 for _, г in п)))
    print("3. вимог до форми відповіді словами поза реєстром: %d" % len(ф))
    print("4. стала частина, симв.: сума %d" % sum(д.values()))
    print("5. речень, що стоять двічі в одному промпті: %d" % sum(в.values()))
    if "--деталі" in арг:
        for к, v in sorted(р.items(), key=lambda kv: -len(kv[1][0][2])):
            print("  [1]", len(v), v[0][2][:80].replace("\n", " "), "|", "; ".join("%s:%d" % (a, b) for a, b, _ in v))
        for шлях, г in п:
            print("  [2]", шлях, "|", "; ".join("%s:%d" % (a, b) for a, b, _ in г))
        for x in ф:
            print("  [3] %s:%d %s" % x)
        for к, н in sorted(в.items()):
            if н:
                print("  [5]", к, н)
    if "--json" in арг:
        шлях = арг[арг.index("--json") + 1]
        json.dump({"речення": len(р), "поля": sum(len(г) - 1 for _, г in п), "форма": len(ф), "довжини": д,
                   "повтор_у_промпті": в}, open(шлях, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
