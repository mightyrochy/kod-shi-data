# -*- coding: utf-8 -*-
"""прилади/корінь_річ_запис_речі_розбір.py — розбір для приладу кореня Річ-запис-речі: Python (`ast`) і JS (acorn із
самого node через `корінь_річ_запис_речі_js.js`) зводяться до одного проміжного подання: вирази `E`, оператори `S`
(присвоєння, ітерація, повернення, вираз) з ланцюгом умов `ctrl`, функції `F` і модулі. Основа — розбір гілки
`claude/rich-zapys-rechi-prylad-2` (799a2856): лише розбір, без визначення запису й поля.

Нічого не лічить і не править: прилад `корінь_річ_запис_речі.py` імпортує це зі своєї теки."""
import ast
import os
import warnings

warnings.simplefilter("ignore", SyntaxWarning)


class E:
    """Вираз. k: name str const attr sub call cmp bool not cond bin fstr list dict comp lambda regex star other."""
    __slots__ = ("k", "v", "a", "line", "x")

    def __init__(s, k, v=None, a=(), line=0, x=None):
        s.k, s.v, s.a, s.line, s.x = k, v, list(a), line, x


class S:
    """Оператор: assign (targets, value) / expr / return / iter (target, iter) з ланцюгом умов ctrl."""
    __slots__ = ("k", "t", "val", "line", "ctrl")

    def __init__(s, k, t, val, line, ctrl):
        s.k, s.t, s.val, s.line, s.ctrl = k, t, val, line, tuple(ctrl)


class F:
    """Функція (або тіло модуля, `name == '<модуль>'`)."""
    __slots__ = ("fid", "name", "params", "stmts", "line", "file", "mod", "cls", "parent", "locals", "lang",
                 "defaults", "is_method")

    def __init__(s, fid, name, params, line, file, mod, cls, parent, lang):
        s.fid, s.name, s.params, s.line, s.file, s.mod, s.cls, s.parent, s.lang = fid, name, params, line, file, mod, cls, parent, lang
        s.stmts, s.locals, s.defaults, s.is_method = [], set(params), [], False


class Модуль:
    def __init__(s, файл, мова):
        s.файл, s.мова = файл, мова
        s.ім_я = os.path.splitext(os.path.basename(файл))[0]
        s.функції = []                  # усі F файла, у т.ч. вкладені й <модуль>
        s.тіло = None
        s.псевдоніми = {}               # ім'я → ('mod', модуль) | ('name', модуль, ім'я)


def лінія(n):
    return getattr(n, "lineno", 0) or 0


# ── Python → подання ───────────────────────────────────────────────────────────────────────────────────────────────
class Py:
    def __init__(s, мод):
        s.мод = мод

    def вираз(s, n):
        if n is None:
            return E("const")
        t = type(n)
        L = лінія(n)
        if t is ast.Name:
            return E("name", n.id, line=L)
        if t is ast.Constant:
            return E("str", n.value, line=L) if isinstance(n.value, str) else E("const", n.value, line=L)
        if t is ast.JoinedStr:
            return E("fstr", None, [s.вираз(v.value) if isinstance(v, ast.FormattedValue) else s.вираз(v)
                                    for v in n.values], L)
        if t is ast.Attribute:
            return E("attr", n.attr, [s.вираз(n.value)], L)
        if t is ast.Subscript:
            return E("sub", None, [s.вираз(n.value), s.вираз(n.slice)], L)
        if t is ast.Slice:
            return E("other", None, [s.вираз(x) for x in (n.lower, n.upper, n.step) if x is not None], L)
        if t is ast.Call:
            арги = [E("star", None, [s.вираз(a.value)], лінія(a)) if isinstance(a, ast.Starred) else s.вираз(a)
                    for a in n.args]
            імена = [k.arg for k in n.keywords]
            знач = [s.вираз(k.value) for k in n.keywords]
            return E("call", {"n": len(арги), "kw": імена}, [s.вираз(n.func)] + арги + знач, L)
        if t is ast.Compare:
            частини, лів = [], s.вираз(n.left)
            for оп, пр in zip(n.ops, n.comparators):
                прав = s.вираз(пр)
                частини.append(E("cmp", type(оп).__name__, [лів, прав], L))
                лів = прав
            return частини[0] if len(частини) == 1 else E("bool", "and", частини, L)
        if t is ast.BoolOp:
            return E("bool", type(n.op).__name__, [s.вираз(v) for v in n.values], L)
        if t is ast.UnaryOp:
            return E("not", None, [s.вираз(n.operand)], L) if isinstance(n.op, ast.Not) else E("other", None, [s.вираз(n.operand)], L)
        if t is ast.BinOp:
            return E("bin", type(n.op).__name__, [s.вираз(n.left), s.вираз(n.right)], L)
        if t is ast.IfExp:
            return E("cond", None, [s.вираз(n.test), s.вираз(n.body), s.вираз(n.orelse)], L)
        if t in (ast.List, ast.Tuple, ast.Set):
            return E("list", t.__name__, [s.вираз(x) for x in n.elts], L)
        if t is ast.Dict:
            a = []
            for k, v in zip(n.keys, n.values):
                a.append(s.вираз(k) if k is not None else E("star", None, [], L))
                a.append(s.вираз(v))
            return E("dict", None, a, L)
        if t in (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp):
            ген = []
            for g in n.generators:
                ген.append((s.ціль(g.target), s.вираз(g.iter), [s.вираз(i) for i in g.ifs]))
            елт = [s.вираз(n.key), s.вираз(n.value)] if t is ast.DictComp else [s.вираз(n.elt)]
            return E("comp", ген, елт, L)
        if t is ast.Lambda:
            return E("lambda", [a.arg for a in n.args.args], [s.вираз(n.body)], L)
        if t is ast.NamedExpr:
            return E("walrus", n.target.id if isinstance(n.target, ast.Name) else "", [s.вираз(n.value)], L)
        if t is ast.Starred:
            return E("star", None, [s.вираз(n.value)], L)
        if t in (ast.Await, ast.Yield, ast.YieldFrom):
            return s.вираз(n.value) if n.value is not None else E("const")
        return E("other", None, [s.вираз(c) for c in ast.iter_child_nodes(n) if isinstance(c, ast.expr)], L)

    def ціль(s, n):
        return s.вираз(n)

    def блок(s, інструкції, ф, ctrl, out):
        неявні = []
        for n in інструкції:
            t = type(n)
            ц = tuple(ctrl) + tuple(неявні)
            L = лінія(n)
            if t is ast.Assign:
                out.append(S("assign", [s.ціль(x) for x in n.targets], s.вираз(n.value), L, ц))
            elif t is ast.AnnAssign:
                if n.value is not None:
                    out.append(S("assign", [s.ціль(n.target)], s.вираз(n.value), L, ц))
            elif t is ast.AugAssign:
                ц2 = s.ціль(n.target)
                out.append(S("assign", [ц2], E("bin", "Aug", [ц2, s.вираз(n.value)], L), L, ц))
            elif t in (ast.For, ast.AsyncFor):
                out.append(S("iter", s.ціль(n.target), s.вираз(n.iter), L, ц))
                s.блок(n.body, ф, ц, out)
                s.блок(n.orelse, ф, ц, out)
            elif t is ast.While:
                тест = s.вираз(n.test)
                out.append(S("expr", None, тест, L, ц))
                s.блок(n.body, ф, ц + (тест,), out)
            elif t is ast.If:
                тест = s.вираз(n.test)
                out.append(S("expr", None, тест, L, ц))
                s.блок(n.body, ф, ц + (тест,), out)
                s.блок(n.orelse, ф, ц + (тест,), out)
                if n.body and isinstance(n.body[-1], ast.Return) and not n.orelse:
                    неявні.append(тест)       # рання повернення значення: далі — залежить від умови
            elif t in (ast.With, ast.AsyncWith):
                for it in n.items:
                    if it.optional_vars is not None:
                        out.append(S("assign", [s.ціль(it.optional_vars)], s.вираз(it.context_expr), L, ц))
                    else:
                        out.append(S("expr", None, s.вираз(it.context_expr), L, ц))
                s.блок(n.body, ф, ц, out)
            elif t is ast.Try or (hasattr(ast, "TryStar") and t is getattr(ast, "TryStar")):
                s.блок(n.body, ф, ц, out)
                for h in n.handlers:
                    s.блок(h.body, ф, ц, out)
                s.блок(n.orelse, ф, ц, out)
                s.блок(n.finalbody, ф, ц, out)
            elif t is ast.Return:
                out.append(S("return", None, s.вираз(n.value) if n.value is not None else E("const"), L, ц))
            elif t is ast.Expr:
                if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                    continue
                out.append(S("expr", None, s.вираз(n.value), L, ц))
            elif t in (ast.FunctionDef, ast.AsyncFunctionDef):
                s.функція(n, ф, ф.cls)
            elif t is ast.ClassDef:
                for ч in n.body:
                    if isinstance(ч, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        s.функція(ч, ф, n.name)
                    elif isinstance(ч, (ast.Assign, ast.AnnAssign)):
                        s.блок([ч], ф, ц, out)
            elif t in (ast.Import, ast.ImportFrom):
                s.імпорт(n)
            elif t is ast.Global:
                ф.locals.difference_update(n.names)
            elif t is ast.Delete or t is ast.Pass or t is ast.Break or t is ast.Continue or t is ast.Nonlocal:
                pass
            elif t is ast.Raise or t is ast.Assert:
                for c in ast.iter_child_nodes(n):
                    if isinstance(c, ast.expr):
                        out.append(S("expr", None, s.вираз(c), L, ц))
            elif hasattr(ast, "Match") and t is ast.Match:
                тема = s.вираз(n.subject)
                for ке in n.cases:
                    s.блок(ке.body, ф, ц + (тема,), out)

    def імпорт(s, n):
        м = s.мод
        if isinstance(n, ast.Import):
            for а in n.names:
                м.псевдоніми[а.asname or а.name.split(".")[0]] = ("mod", а.name.split(".")[-1] if а.asname else а.name.split(".")[0])
        else:
            for а in n.names:
                м.псевдоніми[а.asname or а.name] = ("name", (n.module or "").split(".")[-1], а.name)

    def функція(s, n, батько, клас):
        м = s.мод
        арг = n.args
        параметри = [a.arg for a in arg_all(арг)]
        fid = "%s:%d:%s" % (м.файл, лінія(n), n.name)
        ф = F(fid, n.name, параметри, лінія(n), м.файл, м.ім_я, клас, батько, "py")
        ф.is_method = bool(клас) and bool(параметри) and параметри[0] in ("self", "cls")
        ф.defaults = [s.вираз(d) for d in арг.defaults + [d for d in арг.kw_defaults if d is not None]]
        м.функції.append(ф)
        s.блок(n.body, ф, (), ф.stmts)
        # декоратори/значення за замовчуванням — у батьківському тілі
        return ф


def arg_all(a):
    return list(getattr(a, "posonlyargs", [])) + list(a.args) + ([a.vararg] if a.vararg else []) + \
        list(a.kwonlyargs) + ([a.kwarg] if a.kwarg else [])


def розібрати_py(файл, текст):
    м = Модуль(файл, "py")
    try:
        дерево = ast.parse(текст)
    except (SyntaxError, ValueError):
        return м
    тіло = F("%s:0:<модуль>" % файл, "<модуль>", [], 0, файл, м.ім_я, None, None, "py")
    м.тіло = тіло
    м.функції.append(тіло)
    п = Py(м)
    п.блок(дерево.body, тіло, (), тіло.stmts)
    return м


# ── JS → подання ───────────────────────────────────────────────────────────────────────────────────────────────────
class Js:
    def __init__(s, мод, зсув=0):
        s.мод, s.зсув = мод, зсув

    def L(s, n):
        return (n.get("line", 0) if isinstance(n, dict) else 0) + s.зсув

    def вираз(s, n):
        if not isinstance(n, dict):
            return E("const")
        t, L = n.get("type"), s.L(n)
        if t == "Identifier":
            return E("name", n["name"], line=L)
        if t == "Literal":
            if "regex" in n:
                return E("regex", n["regex"]["pattern"], line=L)
            v = n.get("value")
            return E("str", v, line=L) if isinstance(v, str) else E("const", v, line=L)
        if t == "TemplateLiteral":
            return E("fstr", None, [s.вираз(x) for x in n.get("expressions", [])] +
                     [E("str", q.get("value", {}).get("cooked") or "", line=L) for q in n.get("quasis", [])], L)
        if t == "MemberExpression":
            if n.get("computed"):
                return E("sub", None, [s.вираз(n["object"]), s.вираз(n["property"])], L)
            return E("attr", n["property"].get("name", ""), [s.вираз(n["object"])], L)
        if t == "ChainExpression":
            return s.вираз(n["expression"])
        if t in ("CallExpression", "NewExpression"):
            арги = [E("star", None, [s.вираз(a["argument"])], L) if a.get("type") == "SpreadElement" else s.вираз(a)
                    for a in n.get("arguments", [])]
            return E("call", {"n": len(арги), "kw": [], "new": t == "NewExpression"}, [s.вираз(n["callee"])] + арги, L)
        if t in ("BinaryExpression", "LogicalExpression"):
            оп = n["operator"]
            a = [s.вираз(n["left"]), s.вираз(n["right"])]
            if оп in ("===", "==", "!==", "!=", "in", "instanceof", "<", ">", "<=", ">="):
                return E("cmp", {"===": "Eq", "==": "Eq", "!==": "NotEq", "!=": "NotEq", "in": "In"}.get(оп, оп), a, L)
            if оп in ("&&", "||", "??"):
                return E("bool", оп, a, L)
            return E("bin", оп, a, L)
        if t == "UnaryExpression":
            return E("not", None, [s.вираз(n["argument"])], L) if n["operator"] == "!" else E("other", None, [s.вираз(n["argument"])], L)
        if t == "ConditionalExpression":
            return E("cond", None, [s.вираз(n["test"]), s.вираз(n["consequent"]), s.вираз(n["alternate"])], L)
        if t == "ArrayExpression":
            return E("list", "Array", [s.вираз(x) for x in n.get("elements", []) if x], L)
        if t == "ObjectExpression":
            a = []
            for p in n.get("properties", []):
                if p.get("type") == "SpreadElement":
                    a += [E("star", None, [], L), s.вираз(p["argument"])]
                    continue
                к = p["key"]
                ключ = E("str", к["name"] if к.get("type") == "Identifier" and not p.get("computed") else к.get("value", ""), line=L) \
                    if к.get("type") in ("Identifier", "Literal") and not p.get("computed") else s.вираз(к)
                a += [ключ, s.значення_властивості(p, L)]
            return E("dict", None, a, L)
        if t in ("FunctionExpression", "ArrowFunctionExpression"):
            ф = s.функція(n, None, None, "<лямбда>")
            return E("lambda", ф.fid, [], L, x=ф)
        if t == "AssignmentExpression":
            ц = s.вираз(n["left"])
            пр = s.вираз(n["right"])
            return E("assignx", None, [ц, пр], L)
        if t == "SequenceExpression":
            return E("other", None, [s.вираз(x) for x in n["expressions"]], L)
        if t == "SpreadElement":
            return E("star", None, [s.вираз(n["argument"])], L)
        if t in ("AwaitExpression", "YieldExpression"):
            return s.вираз(n.get("argument"))
        if t == "ThisExpression":
            return E("name", "this", line=L)
        if t == "TaggedTemplateExpression":
            return E("other", None, [s.вираз(n["tag"]), s.вираз(n["quasi"])], L)
        return E("other", None, [], L)

    def значення_властивості(s, p, L):
        # {a() {...}} / {a: function(){}} / {a: v}
        зн = p.get("value")
        return s.вираз(зн)

    def функція(s, n, батько, клас, ім_я=None):
        м = s.мод
        імя = ім_я or ((n.get("id") or {}).get("name")) or "<лямбда>"
        параметри = []
        for p in n.get("params", []):
            параметри += s.імена_шаблону(p)
        fid = "%s:%d:%s#%d" % (м.файл, s.L(n), імя, len(м.функції))
        ф = F(fid, імя, параметри, s.L(n), м.файл, м.ім_я, клас, батько, "js")
        м.функції.append(ф)
        тіло = n.get("body")
        if isinstance(тіло, dict) and тіло.get("type") == "BlockStatement":
            s.блок(тіло.get("body", []), ф, (), ф.stmts)
        elif isinstance(тіло, dict):
            ф.stmts.append(S("return", None, s.вираз(тіло), s.L(n), ()))
        for p in n.get("params", []):
            if p.get("type") == "AssignmentPattern":
                ф.defaults.append(s.вираз(p.get("right")))
        return ф

    def імена_шаблону(s, p):
        t = p.get("type") if isinstance(p, dict) else None
        if t == "Identifier":
            return [p["name"]]
        if t == "AssignmentPattern":
            return s.імена_шаблону(p["left"])
        if t == "RestElement":
            return s.імена_шаблону(p["argument"])
        if t == "ArrayPattern":
            return [x for e in p.get("elements", []) if e for x in s.імена_шаблону(e)]
        if t == "ObjectPattern":
            return [x for pr in p.get("properties", []) for x in s.імена_шаблону(pr.get("value") or pr.get("argument") or {})]
        return []

    def ціль(s, p):
        """Шаблон (деструктурування) → вираз-ціль: для об'єкта — ключі як `sub`, щоб ключ поля зберігся."""
        t = p.get("type") if isinstance(p, dict) else None
        if t == "Identifier":
            return E("name", p["name"], line=s.L(p))
        if t == "AssignmentPattern":
            return s.ціль(p["left"])
        if t == "MemberExpression":
            return s.вираз(p)
        return E("list", "Pat", [E("name", n, line=s.L(p)) for n in s.імена_шаблону(p)], s.L(p))

    def блок(s, інструкції, ф, ctrl, out):
        неявні = []
        for n in інструкції:
            if not isinstance(n, dict):
                continue
            t, L = n.get("type"), s.L(n)
            ц = tuple(ctrl) + tuple(неявні)
            if t == "VariableDeclaration":
                for d in n.get("declarations", []):
                    ініт = d.get("init")
                    пат = d.get("id")
                    if ініт is None:
                        for ім in s.імена_шаблону(пат):
                            ф.locals.add(ім)
                        continue
                    if ініт.get("type") in ("FunctionExpression", "ArrowFunctionExpression") and пат.get("type") == "Identifier":
                        ф2 = s.функція(ініт, ф, None, пат["name"])
                        ф.locals.add(пат["name"])
                        out.append(S("assign", [E("name", пат["name"], line=L)], E("lambda", ф2.fid, [], L, x=ф2), L, ц))
                        continue
                    if пат.get("type") == "ObjectPattern":
                        знач = s.вираз(ініт)
                        for пр in пат.get("properties", []):
                            if пр.get("type") == "Property" and not пр.get("computed"):
                                ключ = пр["key"].get("name", пр["key"].get("value", ""))
                                for ім in s.імена_шаблону(пр.get("value") or {}):
                                    out.append(S("assign", [E("name", ім, line=L)],
                                                 E("sub", None, [знач, E("str", ключ, line=L)], L), L, ц))
                            elif пр.get("type") == "RestElement":
                                for ім in s.імена_шаблону(пр):
                                    out.append(S("assign", [E("name", ім, line=L)], знач, L, ц))
                        continue
                    out.append(S("assign", [s.ціль(пат)], s.вираз(ініт), L, ц))
                    for ім in s.імена_шаблону(пат):
                        ф.locals.add(ім)
            elif t == "FunctionDeclaration":
                ф2 = s.функція(n, ф, None)
                ф.locals.add(n["id"]["name"])
                out.append(S("assign", [E("name", n["id"]["name"], line=L)], E("lambda", ф2.fid, [], L, x=ф2), L, ц))
            elif t == "ClassDeclaration":
                for ч in n.get("body", {}).get("body", []):
                    if ч.get("type") == "MethodDefinition":
                        ф2 = s.функція(ч["value"], ф, n["id"]["name"], ч["key"].get("name", "?"))
                        ф2.is_method = True
            elif t == "ExpressionStatement":
                вир = n["expression"]
                if вир.get("type") == "AssignmentExpression":
                    s.присвоєння(вир, ф, ц, out)
                else:
                    out.append(S("expr", None, s.вираз(вир), L, ц))
            elif t == "ReturnStatement":
                out.append(S("return", None, s.вираз(n.get("argument")) if n.get("argument") else E("const"), L, ц))
            elif t == "IfStatement":
                тест = s.вираз(n["test"])
                out.append(S("expr", None, тест, L, ц))
                s.блок(s.обгорнути(n["consequent"]), ф, ц + (тест,), out)
                if n.get("alternate"):
                    s.блок(s.обгорнути(n["alternate"]), ф, ц + (тест,), out)
                кін = s.обгорнути(n["consequent"])
                if кін and isinstance(кін[-1], dict) and кін[-1].get("type") == "ReturnStatement" and not n.get("alternate"):
                    неявні.append(тест)
            elif t in ("ForStatement",):
                if n.get("init"):
                    s.блок([n["init"]] if n["init"].get("type") == "VariableDeclaration" else
                           [{"type": "ExpressionStatement", "expression": n["init"], "line": L}], ф, ц, out)
                тест = s.вираз(n["test"]) if n.get("test") else E("const")
                s.блок(s.обгорнути(n["body"]), ф, ц + (тест,), out)
            elif t in ("ForOfStatement", "ForInStatement"):
                ліве = n["left"]
                ітер = s.вираз(n["right"])
                if ліве.get("type") == "VariableDeclaration":
                    ліве = ліве["declarations"][0]["id"]
                for ім in s.імена_шаблону(ліве):
                    ф.locals.add(ім)
                out.append(S("iter", s.ціль(ліве), ітер, L, ц))
                s.блок(s.обгорнути(n["body"]), ф, ц, out)
            elif t in ("WhileStatement", "DoWhileStatement"):
                тест = s.вираз(n["test"])
                s.блок(s.обгорнути(n["body"]), ф, ц + (тест,), out)
            elif t == "BlockStatement":
                s.блок(n.get("body", []), ф, ц, out)
            elif t == "TryStatement":
                s.блок(n["block"].get("body", []), ф, ц, out)
                if n.get("handler"):
                    s.блок(n["handler"]["body"].get("body", []), ф, ц, out)
                if n.get("finalizer"):
                    s.блок(n["finalizer"].get("body", []), ф, ц, out)
            elif t == "SwitchStatement":
                диск = s.вираз(n["discriminant"])
                for ке in n.get("cases", []):
                    тест = E("cmp", "Eq", [диск, s.вираз(ке["test"])], L) if ке.get("test") else диск
                    s.блок(ке.get("consequent", []), ф, ц + (тест,), out)
            elif t in ("ThrowStatement",):
                out.append(S("expr", None, s.вираз(n.get("argument")), L, ц))
            elif t == "LabeledStatement":
                s.блок(s.обгорнути(n["body"]), ф, ц, out)

    def обгорнути(s, n):
        if isinstance(n, dict) and n.get("type") == "BlockStatement":
            return n.get("body", [])
        return [n] if isinstance(n, dict) else []

    def присвоєння(s, n, ф, ц, out):
        L = s.L(n)
        прав = n["right"]
        if прав.get("type") == "AssignmentExpression":
            s.присвоєння(прав, ф, ц, out)
            прав = прав["left"]
        ліве = n["left"]
        if n["operator"] != "=":
            ц2 = s.ціль(ліве)
            out.append(S("assign", [ц2], E("bin", "Aug", [ц2, s.вираз(прав)], L), L, ц))
            return
        if прав.get("type") in ("FunctionExpression", "ArrowFunctionExpression"):
            ім = ліве.get("name") or (ліве.get("property") or {}).get("name") or "<лямбда>"
            ф2 = s.функція(прав, ф, None, ім)
            out.append(S("assign", [s.ціль(ліве)], E("lambda", ф2.fid, [], L, x=ф2), L, ц))
            return
        out.append(S("assign", [s.ціль(ліве)], s.вираз(прав), L, ц))


def розібрати_js(файл, дерево, зсув=0):
    м = Модуль(файл, "js")
    тіло = F("%s:0:<модуль>" % файл, "<модуль>", [], 0, файл, м.ім_я, None, None, "js")
    м.тіло = тіло
    м.функції.append(тіло)
    if not isinstance(дерево, dict) or "body" not in дерево:
        return м
    Js(м, зсув).блок(дерево["body"], тіло, (), тіло.stmts)
    return м


# ═══ ГРАФ ЗАЛЕЖНОСТЕЙ ════════════════════════════════════════════════════════════════════════════════════════════
