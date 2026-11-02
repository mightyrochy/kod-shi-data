# -*- coding: utf-8 -*-
"""Приховані-розвідка, частина (в), одиниці І: сила кожного ід правила у виконуваному коді проти сили корпусу.

Залишок №1 `аудит/корені/Приховані-перелік-в.md`: для кожного ід частини І (`приховані_v_обсяг.виконувані_ід`)
звірити силу емісій з FORCE означення правила (`приховані_v_обсяг.сила_корпусу`). Прилад лічить; змісту гілки не
судить.

Емісія — виклик з ід правила рядком серед аргументів і силою (`hard strong default soft hint`) рядком серед
аргументів чи іменованих аргументів (`_зн`, `зн`, `_дод`, `_з`, `_слід`, `запис`, `dict(правило=…, сила=…)`, …).
Ід-змінна першим аргументом конструктора (`КОНСТРУКТОРИ`) розв'язується літералами ід, які функція присвоює
цьому імені чи перебирає в ньому циклом. Сила-змінна (`_зн(ід, сила, …)`) розв'язується літералами сил, які функція присвоює цьому імені чи порівнює з ним
(`сила = "strong" if … else "soft"`); нерозв'язна — «?».
Знахідка словником (`dict(правило=<ід>, сила=…)`, `{"правило": …, "сила": …}`) в обхід ЄДИНОГО конструктора
`реєстр_сила.зн` — емісія без стель: її ефективна сила — заявлена; місце мітиться `[обхід]`.
Ефективна сила — найсильніша заявлена, пропущена через `реєстр_сила.зн` з реєстром констант модуля емісії
(`РЕЄСТР`/`REGISTRY`, як підставляють обгортки `_зн` модулів): стеля тіру, потім стеля корпусу `ПОЛІТИКА_РЕГІСТРУ`.

Вердикт (колонка 4):
  поза_корпусом          ід корпус не має (`корпус:поза`; сила без жодної мірки корпусу);
  без_означення          корпус ід називає, не означає (FORCE нема);
  без_сили_корпусу       означення є, FORCE у ньому прилад не знайшов;
  лише_називає           ід у виконуваному рядку, а емісії з силою нема (перелік, промпт, мовний гейт, звіт);
  сила≤корпус            ефективна сила не сильніша за FORCE корпусу;
  понад_корпус:<е>><к>   ефективна сила сильніша за FORCE корпусу — правило звучить сильніше, ніж каже корпус;
  заявка_понад:<з>><к>   заявлена сила сильніша за корпус, але стеля (тір чи корпус) зрізає до ≤ FORCE —
                         корпус тримає лише стеля, не гілка;
  зрізано_тіром:<е><<к>  гілка заявляє силу корпусу, стеля тіру констант модуля зрізає нижче за FORCE (В1, коли
                         стелю ставить мертва константа);
  питання                емісії лише в регістрі без сили («питання», «ok», «утримано»: входу нема) — звіряти
                         нема з чим;
  сила_невідома          сила емісії — вираз, який прилад не розв'язав.
Запуск з кореня: `python3 джерела/прилади/приховані_v_сила.py [--усі]` — лічба вердиктів; `--усі` — рядок на ід:
ід ⇥ FORCE корпусу ⇥ заявлені → ефективна ⇥ вердикт ⇥ місця емісій.
"""
import ast
import io
import contextlib
import importlib
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import приховані_v_обсяг as V  # noqa: E402
import ід_правил as ІП  # noqa: E402

СИЛИ = V.СИЛИ
НЕСИЛИ = ["питання", "ok", "утримано"]          # регістр без сили: «входу нема», не вирок


def _сили_імені(функція, ім):
    """Літерали сил, які функція присвоює імені `ім` чи порівнює з ним."""
    out = set()
    for в in ast.walk(функція):
        if isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
            if any(isinstance(ц, ast.Name) and ц.id == ім for ц in цілі) and в.value is not None:
                out |= {д.value for д in ast.walk(в.value) if isinstance(д, ast.Constant) and д.value in СИЛИ + НЕСИЛИ}
        elif isinstance(в, ast.Compare) and isinstance(в.left, ast.Name) and в.left.id == ім:
            out |= {д.value for д in ast.walk(в) if isinstance(д, ast.Constant) and д.value in СИЛИ}
        elif isinstance(в, ast.arguments):
            for а, д in zip(в.args[::-1], в.defaults[::-1]):
                if а.arg == ім and isinstance(д, ast.Constant) and д.value in СИЛИ:
                    out.add(д.value)
    return out


ОБХІД = "<словник>"
КОНСТРУКТОРИ = ("зн", "_зн", "_зн_акс", "_зн_верх", "_дод", "_з")


def _іди_імені(функція, ім):
    """Ід правил, які функція присвоює імені `ім` (`правило = "K-OUT-28" if … else "K-OUT-39"`)."""
    out = set()
    for в in ast.walk(функція):
        if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == ім for ц in в.targets):
            out |= {д.value for д in ast.walk(в.value) if isinstance(д, ast.Constant) and isinstance(д.value, str)
                    and ІП.цілий(д.value)}
        elif isinstance(в, ast.For) and isinstance(в.target, ast.Name) and в.target.id == ім:
            out |= {д.value for д in ast.walk(в.iter) if isinstance(д, ast.Constant) and isinstance(д.value, str)
                    and ІП.цілий(д.value)}
    return out


def емісії():
    """{база ід: [(файл:рядок, модуль, {заявлені сили} | {'?'})]}"""
    out = {}
    for ф in V._продукт():
        дерево = V._ast(ф)

        def обхід(в, функція):
            for д in ast.iter_child_nodes(в):
                if isinstance(д, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    обхід(д, д)
                    continue
                п = V._поля_запису(д) if isinstance(д, (ast.Dict, ast.Call)) else None
                if п and "правило" in п and "сила" in п and isinstance(п["правило"], ast.Constant) \
                        and isinstance(п["правило"].value, str) and ІП.цілий(п["правило"].value):
                    # знахідка словником в обхід конструктора `реєстр_сила.зн`: стелі тіру й корпусу не діють
                    сили = {в.value for в in ast.walk(п["сила"]) if isinstance(в, ast.Constant)
                            and в.value in СИЛИ + НЕСИЛИ}
                    if not сили and isinstance(п["сила"], ast.Name) and функція is not None:
                        сили = _сили_імені(функція, п["сила"].id)
                    сили = {"питання" if с in НЕСИЛИ else с for с in сили} or {"?"}
                    і = п["правило"].value
                    out.setdefault(ІП.база(і) or і, []).append(
                        ("%s:%d" % (V._відн(ф), д.lineno), V._мод(ф), сили, і, ОБХІД))
                elif isinstance(д, ast.Call):
                    арг = list(д.args) + [к.value for к in д.keywords]
                    іди = [а.value for а in арг if isinstance(а, ast.Constant) and isinstance(а.value, str)
                           and ІП.цілий(а.value)]
                    ім_ід = (д.args[0] if д.args else None) if not іди else None
                    if isinstance(ім_ід, ast.Name) and функція is not None and \
                            ast.unparse(д.func).split(".")[-1] in КОНСТРУКТОРИ:
                        іди = sorted(_іди_імені(функція, ім_ід.id))
                    конструктор = ast.unparse(д.func).split(".")[-1] in КОНСТРУКТОРИ
                    сили = {а.value for а in арг if isinstance(а, ast.Constant) and а.value in СИЛИ}
                    ім_сили = [к.value for к in д.keywords if к.arg in ("сила", "strength")] or \
                              ([д.args[1]] if конструктор and len(д.args) > 1 else [])
                    if іди and конструктор and ім_сили:
                        сили = {в.value for в in ast.walk(ім_сили[0]) if isinstance(в, ast.Constant) and в.value in СИЛИ + НЕСИЛИ}
                        if not сили and isinstance(ім_сили[0], ast.Name) and функція is not None:
                            сили = _сили_імені(функція, ім_сили[0].id)
                        сили = {"питання" if с in НЕСИЛИ else с for с in сили} or {"?"}
                    if іди and сили:
                        for і in іди:
                            б = ІП.база(і) or і
                            out.setdefault(б, []).append(("%s:%d" % (V._відн(ф), д.lineno), V._мод(ф), сили, і,
                                                         ast.unparse(д.func)))
                обхід(д, функція)
        обхід(дерево, None)
    return out


_МОД = {}


def _реєстр(мод):
    if мод not in _МОД:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                м = importlib.import_module(мод)
            _МОД[мод] = getattr(м, "РЕЄСТР", None) or getattr(м, "REGISTRY", None)
        except Exception:
            _МОД[мод] = None
        if not isinstance(_МОД[мод], dict):
            _МОД[мод] = None
    return _МОД[мод]


def ефективна(ід, сила, мод, функція=""):
    """Сила на виході: сам конструктор модуля (обгортка підставляє свій реєстр), інакше `реєстр_сила.зн` з
    реєстром модуля."""
    import реєстр_сила as РС
    if функція == ОБХІД:
        return сила
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            о = importlib.import_module(мод)
            for ч in функція.split("."):
                о = getattr(о, ч)
            if getattr(о, "__name__", "") in ("зн", "_зн", "_зн_акс", "_зн_верх"):
                р = о(ід, сила, "суть", ["річ"], "чому")
                if isinstance(р, dict) and р.get("сила") in СИЛИ:
                    return р["сила"]
        except Exception:
            pass
        try:
            return РС.зн(ід, сила, "суть", ["річ"], "чому", reg=_реєстр(мод))["сила"]
        except Exception:
            return "?"


def _найсильніша(сили):
    сс = [с for с in сили if с in СИЛИ]
    return min(сс, key=СИЛИ.index) if сс else None


def вердикти():
    ем = емісії()
    out = []
    for б, місця in sorted(V.виконувані_ід().items()):
        озн = V._ознаки_ід(б)
        к = V.сила_корпусу(б)
        е = ем.get(б, [])
        заявлені = set().union(*[м[2] for м in е]) if е else set()
        з = _найсильніша(заявлені)
        еф = [ефективна(м[3], _найсильніша(м[2]), м[1], м[4]) for м in е if _найсильніша(м[2])]
        ефс = _найсильніша(еф)
        if "корпус:поза" in озн:
            в = "поза_корпусом"
        elif "корпус:без_означення" in озн:
            в = "без_означення"
        elif not е:
            в = "лише_називає"
        elif not ефс and заявлені <= {"питання"}:
            в = "питання"
        elif not ефс:
            в = "сила_невідома"
        elif not к:
            в = "без_сили_корпусу"
        elif СИЛИ.index(ефс) < СИЛИ.index(к):
            в = "понад_корпус:%s>%s" % (ефс, к)
        elif з and СИЛИ.index(з) < СИЛИ.index(к):
            в = "заявка_понад:%s>%s" % (з, к)
        elif з and СИЛИ.index(з) <= СИЛИ.index(к) < СИЛИ.index(ефс):
            в = "зрізано_тіром:%s<%s" % (ефс, к)
        else:
            в = "сила≤корпус"
        if е and "?" in заявлені and в in ("сила≤корпус", "без_сили_корпусу"):
            в += "+?"
        out.append(dict(ід=б, корпус=к or "—", заявлені=",".join(sorted(заявлені, key=lambda с: (СИЛИ + ["питання", "?"]).index(с))) or "—",
                        ефективна=ефс or "—", вердикт=в, емісії=" ".join(sorted({м[0] + ("[обхід]" if м[4] == ОБХІД else "") for м in е})[:4]),
                        обхід=sorted({м[0] for м in е if м[4] == ОБХІД}),
                        місця=місця))
    return out


def main():
    вв = вердикти()
    if "--усі" in sys.argv:
        for в in вв:
            print("\t".join(["в:І:" + в["ід"], в["корпус"], "%s → %s" % (в["заявлені"], в["ефективна"]), в["вердикт"],
                             в["емісії"] or " ".join(в["місця"][:3])]))
    л = Counter(в["вердикт"].split(":")[0] for в in вв)
    print("ід: %d · %s" % (len(вв), ", ".join("%s %d" % (к, н) for к, н in л.most_common())))
    об = sorted({м for в in вв for м in в["обхід"]})
    print("знахідок словником в обхід конструктора: %d місць, %d ід" % (len(об), sum(1 for в in вв if в["обхід"])))
    print("місць: %d" % sum(1 for в in вв if в["вердикт"].startswith(("понад_корпус", "заявка_понад"))))


if __name__ == "__main__":
    main()
