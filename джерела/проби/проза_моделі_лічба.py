# -*- coding: utf-8 -*-
"""П-5 (CLAUDE.md п.12): фрази, які КОД складає українською для ФУНКЦІОНАЛЬНОЇ МОДЕЛІ.
Вузли наряду: `palettes.словами` (проза брифа → `style_rules`), `brief.ЯРЛИК_РЕБРА`,
`суд_погода._погода_словами`+`блокер_пальта`, слова осей (`БІК_СЛОВОМ` після #389). Фраза =
літерал із ≥2 кириличними словами (≥3 літер) і пробілом. Мета 0 — у перших трьох; слова осей
лишаються показу (`показ.html` гілкується словом). Нижче — живий дріт.
Запуск із `джерела`: python3 проби/проза_моделі_лічба.py"""
import ast, io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
СЛ = re.compile(r"[а-яіїєґ]{3,}", re.I)
ВУЗЛИ = [("palettes.py", "словами", 0), ("brief.py", "ЯРЛИК_РЕБРА", 0),
         ("суд_погода.py", "_погода_словами", 0), ("суд_погода.py", "блокер_пальта", 0),
         ("palettes.py", "БІК_СЛОВОМ", None), ("palettes.py", "осі", None)]
ФРАЗА = lambda в: (isinstance(в, ast.Constant) and isinstance(в.value, str) and " " in в.value
                   and len(set(СЛ.findall(в.value))) >= 2)
разом, дефектів = [0, 0], 0
for файл, ім, мета in ВУЗЛИ:
    дерево = ast.parse(io.open(файл, encoding="utf-8").read(), filename=файл)
    вузол = next((в for в in ast.walk(дерево)
                  if (isinstance(в, ast.FunctionDef) and в.name == ім)
                  or (isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == ім
                                                        for ц in в.targets))), None)
    тіло = (вузол.body[1:] if (isinstance(вузол, ast.FunctionDef) and вузол.body
                               and isinstance(вузол.body[0], ast.Expr)
                               and isinstance(вузол.body[0].value, ast.Constant)) else [вузол]) if вузол else []
    ф = [в.value for т in тіло for в in ast.walk(т) if ФРАЗА(в)]
    слів = len({w.lower() for т in ф for w in СЛ.findall(т)})
    разом = [разом[0] + len(ф), разом[1] + слів]
    дефектів += (1 if (мета is not None and len(ф) > мета) else 0)
    print("  %-16s %-18s фраз=%-4d слів=%-4d мета=%-4s%s" % (файл, ім, len(ф), слів,
          "—" if мета is None else мета, "" if вузол is not None else " вузла нема"))
print("ПІДСУМОК: фраз коду для моделі в цих вузлах: %d · кириличних слів: %d · над метою вузлів: %d"
      % (разом[0], разом[1], дефектів))
import json, bridge as B
# ЖИВИЙ ДРІТ: пакет моделі несе бриф у `правила[].рядок` (`дріт_моделі` → `style_rules`).
# Проза `palettes.словами` пізнається власними зачинами — вони є лише в ній.
ЗАЧИНИ = ("Ваші осі:", "Домінанта:", "Вікно палітри:", "Сім'ї у вашій версії:", "Ваші нейтралі:",
          "Прийоми, доступні зараз:", "Найдальші від ваших осей", "За сезоном гардероба:")
з = json.loads(B.виклик("запити", io.open("стенд_вх.json", encoding="utf-8").read()))
пр = [str((x or {}).get("рядок") or "") for x in (з["пакети"]["1"].get("правила") or [])]
свої = [x for x in пр if any(з_ in x for з_ in ЗАЧИНИ)]
print("ЖИВИЙ ДРІТ (пакет руки 1 на стенді): правил %d · з прозою `palettes.словами` %d · мета 0"
      % (len(пр), len(свої)))
