# -*- coding: utf-8 -*-
"""Приховані вади, частина (б): хто правий у п.2 стандарту — `досяжність.py` чи `audit_contracts` §4.

Наряд `аудит/наряди/Приховані-розвідка.md`, частина (б). Два прилади відповідають на одне питання «цю функцію ядра
ніхто не кличе?» по-різному: `audit_contracts.мертві_функції` (обхід `відбиток.нікому`) бачить ~200 функцій без
виклику, а `досяжність.мітки` ставить їм мітку за будь-якою згадкою імені в рядку файлу — зокрема в рядковому
літералі й докстрінгу. Цей прилад бере множину §4 і для кожної функції сам обходить AST усіх відстежуваних `*.py`
(імпорт усередині функції, `модуль.ім'я`, `from м import ім'я as x`, передача ім'ям без виклику — теж посилання;
посилання зараховано, лише коли файл імпортує модуль функції чи фасад, що його реекспортує, — тезки не плутаються),
а рядки й коментарі лічить окремо, JS/HTML — лише текстом.

Вердикт на функцію:
  ядро        посилання з модуля ядра поза власним `def` → §4 хибить (функція жива або досяжна);
  тест        посилання лише з тестів чи проб (`тест_*`, `test_*`, `проби/`) → п.2 дотримано тестом;
  прилад      посилання лише з приладів/лабораторії → п.2 порушено (прилад — не живий шлях і не тест);
  текст       лише згадка в рядку, коментарі, докстрінгу чи JS → мертва; `досяжність` мітить її живою — хибить вона;
  ніхто       ніде → мертва, обидва прилади згодні.

Запуск з кореня репозиторію (~1 хв):
  python3 джерела/прилади/приховані_b_п2.py            підсумок вердиктів і згода з `досяжність.мітки`
  python3 джерела/прилади/приховані_b_п2.py --усі      рядок на функцію
Останній рядок — `місць: <N>` (функції ядра, що порушують п.2: прилад + текст + ніхто).
"""
import argparse
import ast
import collections
import io
import os
import re
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import приховані_b_поза as поза  # noqa: E402

КОРІНЬ = поза.КОРІНЬ
ДЖ = os.path.join(КОРІНЬ, "джерела")
sys.path.insert(0, ДЖ)


def _рід(р, ядро):
    if р in ядро:
        return "ядро"
    ім = os.path.basename(р)
    if ім.startswith(("тест", "test_")) or "/проби/" in р or "/тести/" in р or ім.startswith("гейти"):
        return "тест"
    return "прилад"


def _імпорти(дерево):
    """(модулі, імпортовані як модуль; {ім'я: модуль}, звідки імпортовано ім'я)."""
    модулі, імена = set(), {}
    for в in ast.walk(дерево):
        if isinstance(в, ast.Import):
            модулі |= {а.name.split(".")[-1] for а in в.names}
        elif isinstance(в, ast.ImportFrom) and в.module:
            for а in в.names:
                імена[а.name] = в.module.split(".")[-1]
                модулі.add(а.name)  # `from пакет import модуль`
    return модулі, імена


def _посилання(дерево, імена, свій):
    """{ім'я: {(рядок, модуль-джерело)}} посилань кодом і {ім'я: {рядки}} згадок у рядках. Модуль-джерело: `свій` —
    голе ім'я у власному файлі; модуль, з якого ім'я імпортовано (`from м import ім'я`); `@т:м1,м2` — атрибут
    `т.ім'я` (т — псевдонім розкрито), файл імпортує модулі м1, м2 (хто з них — звіряє `_з_модуля`)."""
    модулі, звідки = _імпорти(дерево)
    псевдо = {а.asname: а.name.split(".")[-1] for в in ast.walk(дерево) if isinstance(в, (ast.Import, ast.ImportFrom))
              for а in в.names if а.asname}
    код, текст = collections.defaultdict(set), collections.defaultdict(set)
    for в in ast.walk(дерево):
        if isinstance(в, ast.Name) and в.id in імена and not isinstance(в.ctx, ast.Store):
            код[в.id].add((в.lineno, звідки.get(в.id, свій)))
        elif isinstance(в, ast.Attribute) and в.attr in імена and not isinstance(в.ctx, ast.Store):
            т = в.value.id if isinstance(в.value, ast.Name) else в.value.attr if isinstance(в.value, ast.Attribute) \
                else ""
            код[в.attr].add((в.lineno, "@%s:%s" % (псевдо.get(т, т), ",".join(sorted(модулі)))))
        elif isinstance(в, ast.ImportFrom) and в.module:
            for а in в.names:
                if а.name in імена:
                    код[а.name].add((в.lineno, в.module.split(".")[-1]))
        elif isinstance(в, ast.Constant) and isinstance(в.value, str):
            for сл in re.findall(r"[\w]+", в.value):
                if сл in імена:
                    текст[сл].add(в.lineno)
    return код, текст


_ВСІ_МОДУЛІ = {os.path.basename(р)[:-3] for р in поза._відстежувані([".py"])}


def _реекспорт(модуль, ім, кеш={}):
    """Модуль, з якого `модуль` імпортує `ім` (фасад реекспортує тіло), або None."""
    if модуль not in кеш:
        ф = os.path.join(ДЖ, модуль + ".py")
        кеш[модуль] = _імпорти(ast.parse(io.open(ф, encoding="utf-8").read()))[1] if os.path.exists(ф) else {}
    return кеш[модуль].get(ім)


def _з_модуля(джерело, ім, мод):
    """Чи посилання з модулем-джерелом `джерело` веде до `мод.ім`."""
    if джерело.startswith("@"):
        т, модулі = джерело[1:].split(":", 1)
        if т == мод or _реекспорт(т, ім) == мод:
            return True
        # `обʼєкт.ім'я`, де обʼєкт — не модуль (екземпляр, локальне ім'я): зараховано, коли файл імпортує модуль
        return т not in _ВСІ_МОДУЛІ and мод in модулі.split(",")
    return джерело == мод or _реекспорт(джерело, ім) == мод


def зібрати():
    import audit_contracts
    import status
    import досяжність
    ядро = {"джерела/%s.py" % м for м in status.МОДУЛІ_ПРОДУКТУ}
    мертві, _входи = audit_contracts.мертві_функції()
    функції = sorted((os.path.relpath(os.path.join(ДЖ, ф) if not os.path.isabs(ф) else ф, КОРІНЬ), ім, р)
                     for (ф, ім), р in мертві.items())
    функції = [(ф if ф.endswith(".py") else ф + ".py", ім, р) for ф, ім, р in функції]
    функції = [x for x in функції if x[0] in ядро]
    імена = {ім for _, ім, _ in функції}
    визначено = collections.defaultdict(set)  # ім'я → модулі, де його визначено (тезки розводить модуль)
    for ф, ім, _ in функції:
        визначено[ім].add(os.path.basename(ф)[:-3])
    де = {(м, ім): collections.defaultdict(list) for ім, мм in визначено.items() for м in мм}
    for р in поза._відстежувані([".py"]):
        ф = os.path.join(КОРІНЬ, р)
        if not os.path.exists(ф):
            continue
        текст = io.open(ф, encoding="utf-8", errors="replace").read()
        if not any(ім in текст for ім in імена):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                д = ast.parse(текст)
        except SyntaxError:
            continue
        свій = os.path.basename(р)[:-3]
        код, рядки = _посилання(д, імена, свій)
        рід = _рід(р, ядро)
        for ім, лл in код.items():
            for л, джерело in лл:
                for мод in визначено[ім]:
                    if _з_модуля(джерело, ім, мод):
                        де[(мод, ім)][рід].append((р, л))
        for ім, лл in рядки.items():
            for л in лл:
                for мод in визначено[ім]:
                    де[(мод, ім)]["текст"].append((р, л))
        for л, т in поза.ст._коментарі(ф):
            for ім in імена:
                if re.search(r"(?<!\w)%s(?!\w)" % re.escape(ім), т):
                    for мод in визначено[ім]:
                        де[(мод, ім)]["текст"].append((р, л))
    for р, код_js, _ in поза._js_файли():
        for ім in імена:
            if re.search(r"(?<!\w)%s(?!\w)" % re.escape(ім), код_js):
                for мод in визначено[ім]:
                    де[(мод, ім)]["текст"].append((р, 0))
    мітки = досяжність.мітки(імена)
    рядки = []
    for ф, ім, л in функції:
        д = де[(os.path.basename(ф)[:-3], ім)]
        # власний `def` — не посилання; рекурсія в тілі — теж не виклик ззовні
        свої = {(ф, л)}
        ядро_пос = [x for x in д.get("ядро", []) if x not in свої and not (x[0] == ф and x[1] > л and
                                                                            _усередині(ф, ім, л, x[1]))]
        if ядро_пос:
            вердикт = "ядро"
        elif д.get("тест"):
            вердикт = "тест"
        elif д.get("прилад"):
            вердикт = "прилад"
        elif д.get("текст"):
            вердикт = "текст"
        else:
            вердикт = "ніхто"
        приклад = (ядро_пос or д.get("тест") or д.get("прилад") or д.get("текст") or [("", 0)])[0]
        рядки.append(dict(файл=ф, ім=ім, рядок=л, вердикт=вердикт, приклад="%s:%d" % приклад,
                          досяжність=мітки.get(ім, ("?", []))[0]))
    return рядки


_ТІЛА = {}


def _усередині(ф, ім, л, рядок):
    """Чи рядок — у тілі самої функції `ім` (рекурсія чи вкладене означення)."""
    ключ = (ф, ім, л)
    if ключ not in _ТІЛА:
        д = ast.parse(io.open(os.path.join(КОРІНЬ, ф), encoding="utf-8").read())
        _ТІЛА[ключ] = next(((в.lineno, в.end_lineno) for в in ast.walk(д)
                            if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)) and в.name == ім
                            and в.lineno == л), (0, 0))
    п, к = _ТІЛА[ключ]
    return п <= рядок <= к


ПОРУШУЄ = ("прилад", "текст", "ніхто")


def main():
    п = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    п.add_argument("--усі", action="store_true")
    а = п.parse_args()
    рядки = зібрати()
    if а.усі:
        for r in рядки:
            print("%s:%d\t%s\t%s\tдосяжність=%s\t%s" % (r["файл"], r["рядок"], r["ім"], r["вердикт"], r["досяжність"],
                                                      r["приклад"]))
    в = collections.Counter(r["вердикт"] for r in рядки)
    print("функцій ядра без виклику за audit_contracts §4: %d" % len(рядки))
    print("вердикт: %s" % ", ".join("%s %d" % (к, в.get(к, 0)) for к in ("ядро", "тест", "прилад", "текст", "ніхто")))
    пари = collections.Counter((r["вердикт"], r["досяжність"]) for r in рядки)
    print("вердикт × мітка досяжності: %s" % ", ".join("%s/%s %d" % (а_, б, н) for (а_, б), н in sorted(пари.items())))
    хибить_4 = в.get("ядро", 0)
    хибить_д = sum(н for (а_, б), н in пари.items() if а_ in ПОРУШУЄ and б == "продукт")
    print("§4 хибить (кличе ядро): %d · досяжність хибить (мертва, а мітка «продукт»): %d" % (хибить_4, хибить_д))
    print("місць: %d" % sum(в.get(к, 0) for к in ПОРУШУЄ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
