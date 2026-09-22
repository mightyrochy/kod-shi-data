# -*- coding: utf-8 -*-
"""П.14 (рядок 103, сімʼя A): де на живому шляху виняток ковтався мовчки.
ТАБЛИЦЯ — 43 спіймані винятки сімʼї ДО правки (AST по `origin/main`), з класом
і як закрито. ДЕМОНСТРАЦІЯ — `feed.описує_річ` ламають monkeypatch-ом. ДО (виміряно на `origin/main` 3fdf251): `except Exception … continue` у
`композитор_слоти` ковтав його мовчки — `пул_речей=98`, `пул_чому=None`,
`помилка=None`, тобто пул «зібрався» зі зламаним виміром і НІХТО про це не
дізнався. ПІСЛЯ: летить у `bridge.виклик` (показ.html:5565 пише рядок жінці).
Прогін: cd джерела && python3 проби/vyniatky_103a.py"""
import ast, json, pathlib, subprocess, sys
К = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(К))
ФАЙЛИ = ("композитор_слоти композитор_річ композитор_оцінка композитор_придатні композитор_полюси "
         "пакет_моделі міст_пакет міст_опис міст_вхід фід_розбір фід_добір фід_каталог фід_верхнє "
         "вердикт_моделі розбір_відповідей паспорт_нагоди реєстри").split()
ВУЗЬКІ = {"фід_каталог": "(ImportError, OSError, ValueError) — мережа й декодер фото",
          "фід_верхнє": "(ValueError, SyntaxError) — `параметри` рядком чужого фіду",
          "паспорт_нагоди": "(ValueError, TypeError) — текст моделі → `помилка_формату`"}
широких = lambda т: sum(1 for x in ast.walk(ast.parse(т)) if isinstance(x, ast.ExceptHandler) and (
    x.type is None or (isinstance(x.type, ast.Name) and x.type.id in ("Exception", "BaseException"))))
було = стало = 0
print("%-21s було стало  клас / як закрито" % "файл")
for м in ФАЙЛИ:
    б = широких(subprocess.run(["git", "show", "origin/main:джерела/%s.py" % м],
                               capture_output=True, text=True, cwd=К.parent).stdout)
    с = широких(open(К / (м + ".py"), encoding="utf-8").read())
    було += б; стало += с
    print("%-21s %3d %5d  %s" % (м, б, с, ВУЗЬКІ.get(м, "живий шлях, свій вхід — не ловиться, летить у bridge")))
print("РАЗОМ %d → %d (вузькі типи правилом `рв6_стандарт` не рахуються)" % (було, стало))

import feed as Ф, bridge as B
вх = json.load(open(К / "стенд_вх.json", encoding="utf-8"))
вх["каталог"] = Ф.каталог_на_диску("каталог_brief.xml"); вх["гілка"] = 0
def _зламаний(*a, **k): raise TypeError("зламаний вимір роду рядка")
Ф.описує_річ = _зламаний
try:
    з = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
    print("ПІСЛЯ: винятку нема — пул %s, пул_чому=%r (гілка `вікно` не взята)"
          % (з.get("пул_речей"), з.get("пул_чому")))
except TypeError as e:
    print("ПІСЛЯ: `bridge.виклик` кинув TypeError: %s → показ пише рядок жінці" % e)
