# -*- coding: utf-8 -*-
"""П-5 (аудит/ПРОДУКТ.md п.12): фрази, які КОД складає українською для ФУНКЦІОНАЛЬНОЇ МОДЕЛІ.
Вузли наряду: `palettes.словами` (проза брифа → `style_rules`), `brief.ЯРЛИК_РЕБРА`,
`суд_погода._погода_словами`+`блокер_пальта`, слова осей (`БІК_СЛОВОМ` після #389).
`фраз` — літерали з ≥2 кириличними словами (≥3 літер) і пробілом; `склад` — із них ті, що
стоять У СКЛАДАННІ (`%`, f-рядок, `.format`, `.join`), тобто речення пише сам код.
Мета на `склад` — 0 скрізь. Мета на `фраз` — 0 там, де вузол мусить зникнути; `блокер_пальта` після рядка 4109
віддає лише код блокера (0 фраз), слова осей — показу.
Запуск із `джерела`: python3 проби/проза_моделі_лічба.py"""
import ast, io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
СЛ = re.compile(r"[а-яіїєґ]{3,}", re.I)
# Імена ДО і ПІСЛЯ хвилі стоять разом: вузол, якого вже нема, дає 0 (як у `кошик_в_лічба`).
ВУЗЛИ = [("palettes.py", "словами", 0), ("brief.py", "ЯРЛИК_РЕБРА", 0), ("brief.py", "ярлик_ребра", 0),
         ("суд_погода.py", "_погода_словами", 0), ("суд_погода.py", "блокер_пальта", 0),
         ("суд_погода.py", "погода_значеннями", 0),
         ("palettes.py", "БІК_СЛОВОМ", None), ("palettes.py", "осі", None)]
ФРАЗА = lambda в: (isinstance(в, ast.Constant) and isinstance(в.value, str) and " " in в.value
                   and len(set(СЛ.findall(в.value))) >= 2)
СКЛАД = lambda в: (isinstance(в, (ast.JoinedStr, ast.FormattedValue))
                   or (isinstance(в, ast.BinOp) and isinstance(в.op, (ast.Mod, ast.Add)))
                   or (isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute)
                       and в.func.attr in ("format", "join")))
разом, дефектів = [0, 0, 0], 0
for файл, ім, мета in ВУЗЛИ:
    дерево = ast.parse(io.open(файл, encoding="utf-8").read(), filename=файл)
    в0 = next((в for в in ast.walk(дерево)
               if (isinstance(в, ast.FunctionDef) and в.name == ім)
               or (isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == ім
                                                     for ц in в.targets))), None)
    тіло = (в0.body[1:] if (isinstance(в0, ast.FunctionDef) and в0.body and isinstance(в0.body[0], ast.Expr)
                            and isinstance(в0.body[0].value, ast.Constant)) else [в0]) if в0 else []
    ф = [в.value for т in тіло for в in ast.walk(т) if ФРАЗА(в)]
    ск = {id(в2): в2.value for т in тіло for в in ast.walk(т) if СКЛАД(в)
          for в2 in ast.walk(в) if ФРАЗА(в2)}            # той самий літерал у вкладених складаннях — раз
    слів = len({w.lower() for т in ф for w in СЛ.findall(т)})
    разом = [разом[0] + len(ф), разом[1] + len(ск), разом[2] + слів]
    дефектів += (1 if (мета is not None and len(ф) > мета) else 0) + (1 if ск else 0)
    print("  %-16s %-18s фраз=%-4d склад=%-4d слів=%-4d мета=%-4s%s" % (файл, ім, len(ф), len(ск), слів,
          "—" if мета is None else мета, "" if в0 is not None else " вузла нема"))
print("ПІДСУМОК: фраз %d · складених %d (мета 0) · кириличних слів %d · над метою: %d"
      % tuple(разом + [дефектів]))
import json, bridge as B
# ЖИВИЙ ДРІТ: пакет моделі несе бриф у `правила[].рядок` (`дріт_моделі` → `style_rules`).
ЗАЧИНИ = ("Ваші осі:", "Домінанта:", "Вікно палітри:", "Сім'ї у вашій версії:", "Ваші нейтралі:",
          "Прийоми, доступні зараз:", "Найдальші від ваших осей", "За сезоном гардероба:")
з = json.loads(B.виклик("запити", io.open("стенд_вх.json", encoding="utf-8").read()))
пр = [str((x or {}).get("рядок") or "") for x in (з["пакети"]["1"].get("правила") or [])]
print("ЖИВИЙ ДРІТ (пакет руки 1 на стенді): правил %d · з прозою `palettes.словами` %d · мета 0"
      % (len(пр), len([x for x in пр if any(з_ in x for з_ in ЗАЧИНИ)])))
