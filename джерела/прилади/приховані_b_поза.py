# -*- coding: utf-8 -*-
"""Приховані вади, частина (б): пункти стандарту коду поза ядром — прилади, лабораторія, проби, жниварка, JS показу.

Наряд `аудит/наряди/Приховані-розвідка.md`, частина (б). `приховані_b_стандарт.py` обходить лише 180 модулів ядра;
стандарт же каже про будь-який модуль (п.3, 4, 13, 16, 17, 18, 20), про імена приладів (п.6) і про живий шлях
(п.14: показ і воркер — теж живий шлях, хоч і JS); одиниця п.18 тут — файл, а не рядок. Цей прилад бере ті самі функції пунктів для Python поза ядром і
лічить JS/HTML лексично (без розбору: рядки й коментарі вирізано, ідентифікатори — регуляркою).

Знаменник — усі відстежувані git файли `*.py`, `*.js`, `*.html` поза ядром, крім згенерованого `index.html` (п.19)
і `open-source-stylist/` (окремий проєкт зі своїм `AGENTS.md`; лічиться окремим рядком, у суму не йде).

Запуск з кореня репозиторію:
  python3 джерела/прилади/приховані_b_поза.py                  підсумок: пункт × тека
  python3 джерела/прилади/приховані_b_поза.py --пункт 14       усі місця пункту (файл:рядок ⇥ що)
Останній рядок — `місць: <N>` (сума без `open-source-stylist/`).
"""
import argparse
import ast
import collections
import io
import os
import re
import subprocess
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import приховані_b_стандарт as ст  # noqa: E402

КОРІНЬ = ст.КОРІНЬ
ОКРЕМО = "open-source-stylist/"


def _відстежувані(розширення):
    вихід = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"] + ["*" + р for р in розширення],
                           cwd=КОРІНЬ, capture_output=True, text=True, timeout=60).stdout
    return [р for р in вихід.splitlines() if р and р != "index.html"]


def тека(шлях):
    """Тека обліку: `джерела/прилади`, `джерела/проби`, `аудит/проби`, `zhnyvarka`, `джерела` (верхній рівень)…"""
    ч = шлях.split("/")
    if ч[0] == "open-source-stylist":
        return ОКРЕМО.rstrip("/")
    if len(ч) > 2 and ч[0] in ("джерела", "аудит"):
        return ч[0] + "/" + ч[1]
    return ч[0] if len(ч) > 1 else "."


class СканПоза(ст.Скан):
    """Той самий інтерфейс, що `Скан` ядра (`ядро`, `файл`, `дерево`, `рядки`, `відн`), але ключ — відносний шлях
    файлу поза ядром; файли, що не розбираються, — окремим списком."""

    def __init__(self):  # noqa: super не кличемо — ядро тут не потрібне
        import status
        ядро = {"джерела/%s.py" % м for м in status.МОДУЛІ_ПРОДУКТУ}
        self.ядро, self.файл, self.дерево, self.рядки, self.зламані = [], {}, {}, {}, []
        for р in _відстежувані([".py"]):
            if р in ядро:
                continue
            ф = os.path.join(КОРІНЬ, р)
            if not os.path.exists(ф):
                continue
            текст = io.open(ф, encoding="utf-8", errors="replace").read()
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.дерево[р] = ast.parse(текст)
            except SyntaxError:
                self.зламані.append(р)
                continue
            self.ядро.append(р)
            self.файл[р] = ф
            self.рядки[р] = текст.splitlines()

    def відн(self, м, рядок):
        return "%s:%d" % (м, рядок)


def п6_поза(с):
    """Імена приладів, проб і лабораторії: стандарт велить українські; латинське ім'я файлу — місце."""
    місця = []
    for р in с.ядро:
        ім = os.path.basename(р)[:-3]
        if тека(р) in ("джерела/прилади", "джерела/лабораторія", "джерела/проби", "аудит/проби") \
                and not ст._КИР.search(ім) and ім != "__init__":
            місця.append(("%s:1" % р, "латинське ім'я: %s" % ім))
    return "виміряно", місця


# ─────────────────────────────── JS і HTML ───────────────────────────────
_ЛЕКСЕМА = re.compile(r"//[^\n]*|/\*.*?\*/|`(?:\\.|[^`\\])*`|'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"", re.S)
_ІДЕНТ = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ_$][0-9A-Za-zА-Яа-яІіЇїЄєҐґ_$]*")
_СКРИПТ = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)


def _js_файли():
    """[(шлях, код, зсув рядка)]: файли `.js` цілком, `.html` — вміст тегів `<script>`."""
    з = []
    for р in _відстежувані([".js", ".mjs", ".html"]):
        ф = os.path.join(КОРІНЬ, р)
        if not os.path.exists(ф) or "/node_modules/" in р:
            continue
        текст = io.open(ф, encoding="utf-8", errors="replace").read()
        if р.endswith(".html"):
            for м in _СКРИПТ.finditer(текст):
                з.append((р, м.group(1), текст.count("\n", 0, м.start(1))))
        else:
            з.append((р, текст, 0))
    return з


def _без_рядків(код):
    """Код з вирізаними коментарями й рядками (переноси рядків збережено — номери рядків не зсуваються);
    коментарі — окремо [(рядок, текст)]."""
    коментарі = []

    def заміна(м):
        т = м.group(0)
        if т.startswith("//") or т.startswith("/*"):
            коментарі.append((код.count("\n", 0, м.start()) + 1, т))
        return ('""' if т[0] in "'\"`" else "") + "\n" * т.count("\n")
    return _ЛЕКСЕМА.sub(заміна, код), коментарі


def жив_js(р):
    """Живий шлях JS: показ (`джерела/показ*`), воркер, `показ.html`."""
    return р.startswith("джерела/показ") or os.path.basename(р).startswith("worker")


def js_пункти(файли):
    """п.3, 4, 14, 16, 20 для JS/HTML: {пункт: [(місце, що)]}."""
    м = collections.defaultdict(list)
    for р, код, зсув in файли:
        чистий, коментарі = _без_рядків(код)
        рядків = код.count("\n") + 1
        if not р.endswith(".html") and рядків > 1500:
            м[16].append(("%s:1" % р, "%d рядків" % рядків))
        бачено = set()
        for і, рядок in enumerate(чистий.split("\n"), 1):
            for ім in _ІДЕНТ.findall(рядок):
                if ім in бачено:
                    continue
                бачено.add(ім)
                if re.search(r"[а-яіїєґА-ЯІЇЄҐ][a-zA-Z]|[a-zA-Z][а-яіїєґА-ЯІЇЄҐ]", ім):
                    if ст._ГОМОГЛІФ.search(ім.lower()):
                        м[4].append(("%s:%d" % (р, і + зсув), "гомогліф: %s" % ім))
                    if ст._сегменти_змішані(ім):
                        м[3].append(("%s:%d" % (р, і + зсув), "змішане ім'я: %s" % ім))
        for мт in re.finditer(r"\bcatch\s*(\([^)]*\))?\s*\{", чистий):
            рівень, к = 1, мт.end()
            while к < len(чистий) and рівень:
                рівень += {"{": 1, "}": -1}.get(чистий[к], 0)
                к += 1
            тіло = чистий[мт.end():к - 1]
            if re.search(r"\bthrow\b|console\.|помилк|[Пп]омилк|збій|[Зз]бій|чому|Чому|\bкод\b|error|Error|reject|warn|журнал|log\(|alert", тіло):
                continue
            і = чистий.count("\n", 0, мт.start()) + 1 + зсув
            м[14].append(("%s:%d" % (р, і), "catch ковтає мовчки%s%s" % (
                " (порожній)" if not тіло.strip() else "", " · живий шлях" if жив_js(р) else "")))
        for і, т in коментарі:
            if ст._ІСТОРІЯ.search(т):
                м[20].append(("%s:%d" % (р, і + зсув), "історія: %s" % ст._ІСТОРІЯ.search(т).group(0)))
            if ст._КОНТРАКТ.search(т):
                м[20].append(("%s:%d" % (р, і + зсув), "контракт: %s" % ст._КОНТРАКТ.search(т).group(0)))
    return м


ПУНКТИ_PY = {3: ст.п3, 4: ст.п4, 6: п6_поза, 13: ст.п13, 14: ст.п14, 16: ст.п16, 17: ст.п17, 18: ст.п18, 20: ст.п20}


def зібрати():
    """{пункт: [(місце, що)]} для Python і JS поза ядром + сам скан (знаменник)."""
    с = СканПоза()
    місця = collections.defaultdict(list)
    for н, ф in ПУНКТИ_PY.items():
        місця[н] += ф(с)[1]
    # п.18 поза ядром — одиниця файл (скрипт проби робить роботу кожним рядком верхнього рівня): перше місце файлу
    перші = {}
    for м, що in місця[18]:
        перші.setdefault(м.rsplit(":", 1)[0], (м, що))
    місця[18] = sorted(перші.values())
    js = _js_файли()
    for н, з in js_пункти(js).items():
        місця[н] += з
    return с, js, місця


def main():
    п = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    п.add_argument("--пункт", type=int, default=None)
    а = п.parse_args()
    с, js, місця = зібрати()
    if а.пункт:
        for м, що in місця.get(а.пункт, []):
            print("%s\t%s" % (м, що))
        print("місць: %d" % sum(1 for м, _ in місця.get(а.пункт, []) if not м.startswith(ОКРЕМО)))
        return 0
    теки = collections.Counter(тека(р) for р in с.ядро)
    js_теки = collections.Counter(тека(р) for р, _, _ in js)
    print("знаменник: Python %d файлів (%s), не розбираються %d; JS/HTML %d блоків (%s)" % (
        len(с.ядро), ", ".join("%s %d" % x for x in теки.most_common()), len(с.зламані),
        len(js), ", ".join("%s %d" % x for x in js_теки.most_common())))
    разом = 0
    for н in sorted(місця):
        свої = [м for м, _ in місця[н] if not м.startswith(ОКРЕМО)]
        разом += len(свої)
        за_теками = collections.Counter(тека(м.split(":")[0]) for м in свої)
        осс = len(місця[н]) - len(свої)
        print("п.%-2d місць %-5d %s%s" % (н, len(свої), ", ".join("%s %d" % x for x in за_теками.most_common(6)),
                                         " · open-source-stylist %d окремо" % осс if осс else ""))
    if с.зламані:
        print("не розбираються: %s" % ", ".join(с.зламані[:10]))
    print("місць: %d" % разом)
    return 0


if __name__ == "__main__":
    sys.exit(main())
