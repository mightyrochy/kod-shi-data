# -*- coding: utf-8 -*-
"""Спільний код усіх проб поділу: докстрінг — перший Expr(Constant(str)) у тілі
функції/класу/модуля, тому теж частина AST, і хвиля стандарту (СТАНДАРТ §5 п.17,
118 функцій без докстрінга) зробила б кожен новий докстрінг у поділеному модулі
падінням проби й окремою парою в поділ_очікувані.txt. dump_без_докстрінгів дає
ast.dump копії вузла з прибраними докстрінгами (сам код копії не міняється), щоб
проби порівнювали логіку, а не наявність тексту докстрінга."""
import ast
import os
import copy


def _без_докстрінгу(тіло):
    if тіло and isinstance(тіло[0], ast.Expr) and isinstance(тіло[0].value, ast.Constant) \
            and isinstance(тіло[0].value.value, str):
        return тіло[1:]
    return тіло


def dump_без_докстрінгів(node):
    вузол = copy.deepcopy(node)
    for n in ast.walk(вузол):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            n.body = _без_докстрінгу(n.body)
    return ast.dump(вузол)


РЕЄСТР = os.path.join(os.path.dirname(os.path.abspath(__file__)), "поділ_очікувані.txt")


def очікувані(модуль):
    """Множина ключів «новий_модуль::ім'я», свідомо змінених після поділу `модуль`.py.
    Читає рядковий реєстр `поділ_очікувані.txt`: один запис — один рядок
    «<модуль> | <новий_модуль>::<ім'я> | <sha>… [| нота]»; «#» і порожній рядок — не записи.
    Віддає МНОЖИНУ, тож порядок рядків і повторений ключ на вердикт не впливають — саме це
    дозволяє зливати реєстр об'єднанням (`.gitattributes`: merge=union) без конфліктів."""
    ключі = set()
    with open(РЕЄСТР, encoding="utf-8") as ф:
        for рядок in ф:
            р = рядок.strip()
            if not р or р.startswith("#"):
                continue
            поля = [ч.strip() for ч in р.split("|")]
            if len(поля) < 2:
                raise ValueError("поділ_очікувані.txt: рядок без полів — %r" % рядок)
            if поля[0] == модуль:
                ключі.add(поля[1])
    return ключі
