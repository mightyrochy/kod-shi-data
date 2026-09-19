# -*- coding: utf-8 -*-
"""Самозвіт про поля-сироти рахував КОМЕНТАР про зняте присвоєння за писача (§128).

ДО ПРАВКИ: `status_перевірки._поля_без_постачальника` шукала писачів регуляркою по
СИРОМУ тексту модулів. 17.09 з `feed` прибрали `r["формальність"] = ф` і лишили про
це коментар (`feed.py:2987`, «Доти тут стояло …»). Перевірка прочитала розповідь про
знятий писач як писача, і поле мовчки вийшло зі списку сиріт — борг ЗАНИЖЕНО рівно
тим способом, проти якого написано цей модуль.
ПІСЛЯ: писачем рахується лише ВИКОНУВАНИЙ рядок (докстрінги — вузлами AST,
коментарі — хвостом після `#`). Сиріт 8 → 9; повернулась рівно `формальність`.
Прогін із теки `джерела`: `python3 проби/sam_сироти_коментар.py`."""
import ast, inspect, re, sys, pathlib
_КОРІНЬ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_КОРІНЬ))
import status_перевірки as SP, outfit, areas, feed, composer, pipeline, accessory, outer

_споживає = set(re.findall(r'r\.get\("([^"]+)"', inspect.getsource(outfit.елементи)))
_споживає |= {с["поле"] for с in accessory.АКСЕСУАР_ВИМІР.values() if с.get("поле")}
_споживає |= {с["поле"] for с in accessory.НОСІЇ_КРАЮ.values() if с.get("поле")}


def _сироти(як):
    вир = set()
    # поділ accessory і outer (19.09.2026): писачі гілок — у модулях, які фасади реекспортують
    реекспортовані = [__import__(в.module) for ф in (accessory, outer)
                      for в in ast.parse(inspect.getsource(ф)).body
                      if isinstance(в, ast.ImportFrom) and в.level == 0 and в.module]
    for м in (areas, feed, composer, pipeline, accessory, outer, *реекспортовані):
        s = як(inspect.getsource(м))
        вир |= set(re.findall(r"(\w+)\s*=", s))
        вир |= set(re.findall(r'\[\s*"([^"]+)"\s*\]\s*=', s))
        вир |= set(re.findall(r'setdefault\(\s*"([^"]+)"', s))
    return sorted(п for п in _споживає - вир
                  if п not in ("hex", "colors", "площа", "near", "id", "слот"))


_до = _сироти(lambda s: s)
print("ФАКТ · сирий текст (як було): %d сиріт — %s" % (len(_до), ", ".join(_до)))
print("ФАКТ · рядок feed.py:2987 — коментар: %r"
      % open(_КОРІНЬ / "feed.py", encoding="utf-8").read().split("\n")[2986].strip()[:72])
_зараз = SP._поля_без_постачальника()[1]
print("ФАКТ · перевірка зараз: %s" % _зараз)
print("ФАКТ · «формальність» повернулась у сироти: %s"
      % ("формальність" in _зараз and "формальність" not in _до))
