# -*- coding: utf-8 -*-
"""Ч-1, кошик В ПОЗА РОЗМОВОЮ (CLAUDE.md п.12): ФРАЗИ, ЯКІ КОД ПИШЕ ЖІНЦІ на картці й палітрі.
Літерали з ≥2 кириличними словами (≥3 літер) І пробілом (ключ словника — не фраза) у КУРОВАНИХ
вузлах, звідки текст іде прямо на екран, — не в звіт і не в промпт. «вузол:імʼя» — лише
`імʼя.append(…)`, «вузол=імʼя» — лише присвоєння `імʼя = …`. Імена ДО і ПІСЛЯ хвилі стоять
разом: вузол, якого вже нема, дає 0. Запуск із `джерела`: python3 проби/кошик_в_лічба.py"""
import ast, io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
СЛ = re.compile(r"[а-яіїєґ]{3,}", re.I)
МІСЦЯ = {"палітра_схеми.py": ("ЛЮДСЬКА_НОТА", "ЛЮДСЬКИЙ_МИСМАТЧ", "ЛЮДСЬКИЙ_МИСМАТЧ_БЕЗ_ЧИСЕЛ",
                              "ЛЮДСЬКИЙ_МАКІЯЖ", "людська_нота", "ЗАЯВИ_НОТИ", "нота_схеми",
                              "рядок_великих", "повідомлення_великих"),
          "міст_основи.py": ("_нота_гілки",),
          "palettes.py": ("рядок_схеми_жінці", "повідомлення_схеми_жінці", "_на_чому"),
          "міст_відповіді.py": ("в[схема_жінці]", "в[нагода_жінці]", "в[носіння_жінці]",
                                "в[матеріал_жінці]"),
          # у `вердикт` жінці йде лише `жінці.append(…)`; знахідки й «без входу» — діагностика
          "річ_з_фото.py": ("_рядок_жінці", "_повідомлення_жінці", "пом_якшення", "вердикт:жінці"),
          # у `повнота_набору` жінці йде лише `рядок`; `чому` й перелік блокерів — звіт власника
          "повнота_образу.py": ("_НЕМА_В_КАТАЛОЗІ_СЛОВОМ", "_ЧОГО_БРАКУЄ_СЛОВОМ", "_СЛОТ_НА",
                                "_рядок_дібраних", "_коротко_жінці", "_реченням", "_дописати",
                                "повнота_набору=рядок"),
          "суд_погода.py": ("рядок_без_пальта", "заява_без_пальта"),
          "фід_фото.py": ("чому_без_кадру",)}
ФРАЗА = lambda в: (isinstance(в, ast.Constant) and isinstance(в.value, str) and " " in в.value
                   and len(set(СЛ.findall(в.value))) >= 2)


def фрази(вузол, лише=None, присв=None):
    """Літерали-фрази вузла без докстрінга, звужені до `лише` / `присв` (див. докстрінг модуля)."""
    тіло = вузол.body[1:] if (isinstance(вузол, ast.FunctionDef) and вузол.body and isinstance(вузол.body[0], ast.Expr)
                              and isinstance(вузол.body[0].value, ast.Constant)) else [вузол]
    гілки = tuple(тіло)
    if лише:
        гілки = [в for т in тіло for в in ast.walk(т) if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute)
                 and в.func.attr == "append" and isinstance(в.func.value, ast.Name) and в.func.value.id == лише]
    elif присв:
        гілки = [в.value for т in тіло for в in ast.walk(т) if isinstance(в, ast.Assign)
                 and any(isinstance(ц, ast.Name) and ц.id == присв for ц in в.targets)]
    return [в.value for т in гілки for в in ast.walk(т) if ФРАЗА(в)]


разом = [0, 0]
for файл, імена in МІСЦЯ.items():
    вузли = {}
    for в in ast.walk(ast.parse(io.open(файл, encoding="utf-8").read(), filename=файл)):
        if isinstance(в, ast.FunctionDef):
            вузли[в.name] = в
        elif isinstance(в, ast.Assign):
            for ц in в.targets:
                if isinstance(ц, ast.Name):
                    вузли[ц.id] = в
                elif isinstance(ц, ast.Subscript) and isinstance(ц.value, ast.Name) and isinstance(ц.slice, ast.Constant):
                    вузли.setdefault("%s[%s]" % (ц.value.id, ц.slice.value), в)
    for ім in імена:
        ключ, _, присв = ім.partition("=")
        ключ, _, лише = ключ.partition(":")
        ф = фрази(вузли[ключ], лише or None, присв or None) if ключ in вузли else []
        слів = len({w.lower() for т in ф for w in СЛ.findall(т)})
        разом = [разом[0] + len(ф), разом[1] + слів]
        print("  %-20s %-26s фраз=%-4d слів=%-4d%s" % (файл, ім, len(ф), слів, "" if ключ in вузли else " ?"))
print("ПІДСУМОК: фраз, які код пише жінці поза розмовою: %d · кириличних слів у них: %d" % tuple(разом))
