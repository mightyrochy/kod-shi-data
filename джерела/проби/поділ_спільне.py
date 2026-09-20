# -*- coding: utf-8 -*-
"""Спільний код усіх проб поділу: докстрінг — перший Expr(Constant(str)) у тілі
функції/класу/модуля, тому теж частина AST, і хвиля стандарту (СТАНДАРТ §5 п.17,
118 функцій без докстрінга) зробила б кожен новий докстрінг у поділеному модулі
падінням проби й окремою парою в поділ_очікувані.json. dump_без_докстрінгів дає
ast.dump копії вузла з прибраними докстрінгами (сам код копії не міняється), щоб
проби порівнювали логіку, а не наявність тексту докстрінга."""
import ast
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
