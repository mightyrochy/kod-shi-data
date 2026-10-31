# -*- coding: utf-8 -*-
"""Лічить місця кореня Е2-текст-жінці за паспортом, не змінюючи продукт.

А: стоки DOM, атрибутів, розмітки, вставок і виклики входів точки →
походження через писачів, параметри, повернення. Договори варіантів входів
виводяться з викликів усередині модуля, а не з переліку імен варіантів.
Невідомий тип не звільняється від перевірки за іменем поля.
Б: джерела моделі, моста й даних → присвоєння, повернення, параметри →
всі стоки, включно з відхиленими А. Розбіжності друкуються для пояснення.
HTML у Python перелічується окремо для перевірки досяжності екрана.
Запуск (з кореня репозиторію): python3 джерела/прилади/корінь_е2_текст_жінці.py джерела [--сталі] [--збіг] [--довідник] [--файли]
Вивід: місця `файл:рядок · пункт · чому`, підсумки за пунктами, останній рядок `місць: <N>`, код 0 (формат храповика)."""
import ast, os, re, sys
from походження_тексту import Походження, невідповідний

ТУТ = next((а for а in sys.argv[1:] if not а.startswith("--")),
           "джерела" if os.path.isdir(os.path.join("джерела", "показ")) else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ТОЧКА = ("текстЖінціП", "збійЖінціП")                  # точка виходу (паспорт); станТекстуЖінціП — її сторож
СЛУЖБОВИЙ_ВИХІД = ("діагнозВласникаП",)                # прихований блок власника, не екран жінки
ВЛАСТИВОСТІ = {"textContent", "innerHTML", "innerText", "outerHTML", "placeholder", "title", "alt", "label", "nodeValue",
               "value", "text", "data", "ariaLabel"}
РОЗМІТКА = {"innerHTML", "outerHTML"}
КЛЮЧІ_ОБЄКТА = {"textContent", "innerHTML", "innerText", "placeholder", "ariaLabel"}
АТРИБУТИ = {"aria-label", "title", "placeholder", "alt", "value", "label", "content"}
ВИКЛИКИ_ТЕКСТ = {"createTextNode": "П1", "alert": "П1", "confirm": "П1", "prompt": "П1", "SpeechSynthesisUtterance": "П1",
                  "Notification": "П1", "setCustomValidity": "П1"}
ВСТАВКИ = {"append", "prepend", "replaceChildren", "before", "after", "replaceWith", "appendData"}
ЧИСЛОВІ = {"length", "size", "count", "toFixed", "toLocaleString", "indexOf", "lastIndexOf", "findIndex", "getTime",
           "getFullYear", "getMonth", "getDate", "charCodeAt", "codePointAt", "localeCompare", "includes", "some", "every",
           "has", "test", "startsWith", "endsWith", "isArray", "now", "random", "toPrecision", "valueOf"}
ПЕРЕНОС = {"join", "slice", "substring", "substr", "trim", "trimStart", "trimEnd", "replace", "replaceAll", "split", "map",
           "filter", "concat", "toLowerCase", "toUpperCase", "toLocaleLowerCase", "toLocaleUpperCase", "padStart", "padEnd",
           "flat", "flatMap", "reverse", "sort", "at", "pop", "shift", "find", "reduce", "repeat", "normalize", "toString",
           "values", "keys", "entries", "from", "assign", "stringify", "fromEntries", "freeze", "of", "match", "matchAll",
           "forEach", "then", "finally", "catch", "call", "apply", "bind", "charAt", "toSorted", "copyWithin", "fill"}
КЛЮЧОВІ = {"if", "for", "while", "switch", "catch", "function", "return", "typeof", "new", "await", "async", "yield",
           "else", "do", "try", "finally", "throw", "const", "let", "var", "of", "in", "instanceof", "delete", "void", "case",
           "break", "continue", "class", "default", "extends", "super", "this", "with"}
ЛАНЦЮГОВІ_МЕТОДИ_ПОДІЙ = {"addEventListener", "removeEventListener", "setTimeout", "setInterval", "requestAnimationFrame"}
ЗБІР_МЕТОДИ_ЕЛЕМЕНТА = {"map", "filter", "forEach", "find", "some", "every", "flatMap", "sort", "findIndex", "reduce",
                        "findLast", "toSorted"}

# ───────────────────────────────────── лексер ─────────────────────────────────────
ПУНКТ3 = ("===", "!==", "**=", "...", "<<=", ">>=", ">>>", "&&=", "||=", "??=")
ПУНКТ2 = ("=>", "==", "!=", "<=", ">=", "&&", "||", "??", "?.", "++", "--", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=",
          "**", "<<", ">>")
ПІСЛЯ_ЯКИХ_РЕГЕКС = {"(", ",", "=", ":", "[", "!", "&", "|", "?", "{", "}", ";", "+", "-", "*", "%", "<", ">", "~", "^",
                     "return", "typeof", "case", "=>", "&&", "||", "??", "==", "===", "!=", "!==", "void", "await", "of"}
ІДЕНТ = re.compile(r"[\w$ʼ’]+")
ЧИСЛО = re.compile(r"0[xX][0-9a-fA-F_]+n?|\d[\d_]*\.?\d*(?:[eE][+-]?\d+)?n?|\.\d+")


def лекс(к, і=0, р=1, вкладене=False):
    """Розбиває JavaScript на токени з рядками, включно з вкладеними шаблонами."""
    ток, н, гл = [], len(к), 0
    while і < н:
        с = к[і]
        if с == "\n":
            р += 1; і += 1; continue
        if с in " \t\r﻿":
            і += 1; continue
        if к.startswith("//", і):
            j = к.find("\n", і); і = н if j < 0 else j; continue
        if к.startswith("/*", і):
            j = к.find("*/", і + 2); j = н if j < 0 else j + 2
            р += к.count("\n", і, j); і = j; continue
        if с in "'\"":
            j = і + 1
            while j < н and к[j] != с and к[j] != "\n":
                j += 2 if к[j] == "\\" else 1
            ток.append(["str", к[і + 1:j], р]); і = j + 1; continue
        if с == "`":
            частини, буф, j, р0 = [], [], і + 1, р
            while j < н and к[j] != "`":
                if к[j] == "\\":
                    буф.append(к[j:j + 2]); р += к[j + 1:j + 2] == "\n"; j += 2; continue
                if к.startswith("${", j):
                    частини.append(("s", "".join(буф))); буф = []
                    вн, j, р = лекс(к, j + 2, р, True)
                    частини.append(("e", вн)); continue
                if к[j] == "\n":
                    р += 1
                буф.append(к[j]); j += 1
            частини.append(("s", "".join(буф))); ток.append(["tpl", частини, р0]); і = j + 1; continue
        м = ЧИСЛО.match(к, і) if (с.isdigit() or (с == "." and к[і + 1:і + 2].isdigit())) else None
        if м:
            ток.append(["num", м.group(0), р]); і = м.end(); continue
        if с.isalpha() or с in "_$ʼ":
            м = ІДЕНТ.match(к, і)
            ток.append(["id", м.group(0), р]); і = м.end(); continue
        if с == "/":
            перед = ток[-1][1] if ток and ток[-1][0] in ("p", "id") else (None if not ток else "x")
            if перед is None or перед in ПІСЛЯ_ЯКИХ_РЕГЕКС:
                j, кл = і + 1, False
                while j < н and (кл or к[j] != "/") and к[j] != "\n":
                    if к[j] == "\\": j += 2; continue
                    if к[j] == "[": кл = True
                    elif к[j] == "]": кл = False
                    j += 1
                j += 1
                while j < н and к[j].isalpha(): j += 1
                ток.append(["re", к[і:j], р]); і = j; continue
        п = next((x for x in ПУНКТ3 if к.startswith(x, і)), None) or next((x for x in ПУНКТ2 if к.startswith(x, і)), None) or с
        if вкладене:
            if п == "{": гл += 1
            elif п == "}":
                if гл == 0:
                    return ток, і + 1, р
                гл -= 1
        ток.append(["p", п, р]); і += len(п)
    return (ток, і, р) if вкладене else ток


def пари(ток):
    """Зіставляє позиції парних дужок у потоці токенів."""
    пар, стек = {}, []
    for і, т in enumerate(ток):
        if т[0] != "p": continue
        if т[1] in "([{": стек.append(і)
        elif т[1] in ")]}" and стек:
            j = стек.pop(); пар[j] = і; пар[і] = j
    return пар


def розділити(ток, пар, а, б, роздільник=","):
    """частини [а,б) по верхньорівневих роздільниках"""
    вих, поч, і = [], а, а
    while і < б:
        т = ток[і]
        if т[0] == "p" and т[1] in "([{" and і in пар:
            і = пар[і] + 1; continue
        if т[0] == "p" and т[1] == роздільник:
            вих.append((поч, і)); поч = і + 1
        і += 1
    if поч < б or вих:
        вих.append((поч, б))
    return [(x, y) for x, y in вих if x < y]


def текст_токенів(ток, а, б, межа=90):
    """Складає короткий читабельний вираз для доказу у виводі."""
    ч = []
    for т in ток[а:б]:
        ч.append("'" + т[1] + "'" if т[0] == "str" else "`…`" if т[0] == "tpl" else str(т[1]))
    return re.sub(r"\s+", " ", " ".join(ч))[:межа]


# ─────────────────────────────── модуль: функції, області, присвоєння ───────────────────────────────
class Функція:
    __slots__ = ("ід", "ім", "парам", "а", "б", "заг_а", "бат", "вираз", "мод", "кб", "літерали")

    def __init__(с, мод, ім, парам, а, б, заг_а, вираз):
        """Зберігає межі, параметри та область функції JavaScript."""
        с.мод, с.ім, с.парам, с.а, с.б, с.заг_а, с.вираз, с.бат, с.кб, с.літерали = мод, ім, парам, а, б, заг_а, вираз, None, None, None


class Модуль:
    def __init__(с, шлях, ток, зсув=0, служб=False):
        """Будує області, писачів і виклики одного джерела."""
        с.шлях, с.ток, с.пар, с.зсув, с.служб = шлях, ток, пари(ток), зсув, служб
        с.функції, с.оголош, с.присв, с.виклики, с.стоки, с.поля_запис = [], {}, [], [], [], []
        с.позиції = {}                                  # (і оголошення, ключ імені) → місце імені в шаблоні `[a, b] of X`
        с.кеш_охоплення = {}
        с._функції(); с._оголошення(); с._присвоєння()

    def функції_в(с, a, b):
        """Повертає функції, оголошені всередині діапазону токенів."""
        if not hasattr(с, "_заг"): с._заг = [ф.заг_а for ф in sorted(с.функції, key=lambda f: f.заг_а)]; с._відс = sorted(с.функції, key=lambda f: f.заг_а)
        import bisect
        return с._відс[bisect.bisect_left(с._заг, a):bisect.bisect_left(с._заг, b)]

    def рядок(с, і):
        """Переводить позицію токена в рядок файла-джерела."""
        return с.ток[min(max(і, 0), len(с.ток) - 1)][2] + с.зсув if с.ток else 0

    # ── функції
    def _параметри(с, а, б):
        """Читає позиції параметрів, включно з деструктуризацією."""
        вих = []
        for x, y in розділити(с.ток, с.пар, а, б):
            ідс = [с.ток[k][1] for k in range(x, y) if с.ток[k][0] == "id" and с.ток[k][1] not in КЛЮЧОВІ
                   and not (k > x and с.ток[k - 1][1] in (".", "?."))]
            if с.ток[x][1] in ("{", "["):
                вих.append(("*", ідс))
            elif ідс:
                вих.append((ідс[0], ідс[:1]))
        return вих

    def _функції(с):
        """Знаходить функції, стрілки й методи та їхні області."""
        т, пар, н = с.ток, с.пар, len(с.ток)
        for і in range(н):
            if т[і][0] == "id" and т[і][1] == "function":
                j = і + 1
                if j < н and т[j][1] == "*": j += 1
                ім = None
                if j < н and т[j][0] == "id": ім = т[j][1]; j += 1
                if j < н and т[j][1] == "(" and j in пар and пар[j] + 1 < н and т[пар[j] + 1][1] == "{":
                    о = пар[j] + 1
                    if ім is None and і >= 2 and т[і - 1][1] == "=" and т[і - 2][0] == "id": ім = т[і - 2][1]
                    с.функції.append(Функція(с, ім, с._параметри(j + 1, пар[j]), о + 1, пар[о], і, False))
            elif т[і][1] == "=>":
                if т[і - 1][1] == ")" and (і - 1) in пар:
                    о = пар[і - 1]; парам = с._параметри(о + 1, і - 1); поч = о
                elif т[і - 1][0] == "id":
                    парам = [(т[і - 1][1], [т[і - 1][1]])]; поч = і - 1
                else:
                    continue
                if поч >= 1 and т[поч - 1][1] == "async": поч -= 1
                ім = т[поч - 2][1] if поч >= 2 and т[поч - 1][1] == "=" and т[поч - 2][0] == "id" else None
                if і + 1 < н and т[і + 1][1] == "{" and (і + 1) in пар:
                    с.функції.append(Функція(с, ім, парам, і + 2, пар[і + 1], поч, False))
                else:
                    с.функції.append(Функція(с, ім, парам, і + 1, с.кінець_виразу(і + 1), поч, True))
            elif (т[і][0] == "id" and т[і][1] not in КЛЮЧОВІ and і + 1 < н and т[і + 1][1] == "(" and (і + 1) in пар
                  and пар[і + 1] + 1 < н and т[пар[і + 1] + 1][1] == "{" and і >= 1
                  and (т[і - 1][1] in ("{", ",") or (т[і - 1][1] == "async" and і >= 2 and т[і - 2][1] in ("{", ",")))):
                j = пар[і + 1] + 1
                с.функції.append(Функція(с, т[і][1], с._параметри(і + 2, пар[і + 1]), j + 1, пар[j], і, False))
        for ф in с.функції:
            ф.ід = (с.шлях, ф.заг_а, ф.а)
        с.функції.sort(key=lambda ф: (ф.заг_а, -ф.б))

    def кінець_виразу(с, а, кома=True):
        """кінець виразу, що починається в `а`: `;`/закрита дужка/(кома) на глибині 0 або перенос рядка без продовження"""
        т, пар, н, і = с.ток, с.пар, len(с.ток), а
        while і < н:
            x = т[і]
            if x[0] == "p":
                if x[1] in "([{" and і in пар:
                    і = пар[і] + 1; continue
                if x[1] in ")]}" or x[1] == ";" or (x[1] == "," and кома): return і
            if x[1] == "=>" and і + 1 < н and т[і + 1][1] == "{" and (і + 1) in пар:
                і = пар[і + 1] + 1; continue
            if і + 1 < н and т[і + 1][2] > x[2]:
                наст = т[і + 1]
                if not (x[0] == "p" and x[1] not in (")", "]", "}", "++", "--")) and not (
                        наст[0] == "p" and наст[1] in ("+", "-", "*", "/", "?", ":", ".", "?.", "&&", "||", "??", ",", ")", "]", "}",
                                                       "=", "==", "===", "!=", "!==", "<", ">", "<=", ">=", "=>", "(", "[")):
                    return і + 1
            і += 1
        return н

    def охоплює(с, і):
        """внутрішня функція, що містить токен `і` (параметри — теж її)"""
        if і in с.кеш_охоплення: return с.кеш_охоплення[і]
        вих = None
        for ф in с.функції:
            if ф.заг_а <= і < ф.б + (0 if ф.вираз else 1) and (вих is None or ф.заг_а >= вих.заг_а): вих = ф
        с.кеш_охоплення[і] = вих
        return вих

    def батько(с, ф):
        """Знаходить найближчу зовнішню функцію для вкладеної."""
        if ф.бат is None:
            ін = None
            for g in с.функції:
                if g is not ф and g.заг_а <= ф.заг_а and ф.б <= g.б and (g.заг_а, -g.б) != (ф.заг_а, -ф.б) and (
                        ін is None or g.заг_а >= ін.заг_а): ін = g
            ф.бат = ін or False
        return ф.бат or None

    # ── оголошення
    def _оголошення(с):
        """Прив’язує оголошені імена до їхніх областей."""
        т, пар, н = с.ток, с.пар, len(с.ток)

        def додай(і, ім):
            """Записує ім’я в найближчу область оголошення."""
            ф = с.охоплює(і)
            с.оголош.setdefault(ф.ід if ф else None, set()).add(ім)
        for ф in с.функції:
            for ім, ідс in ф.парам:
                for x in ідс: с.оголош.setdefault(ф.ід, set()).add(x)
        for і in range(н):
            x = т[і]
            if x[0] == "id" and x[1] in ("const", "let", "var") and і + 1 < н:
                j = і + 1
                if т[j][1] in ("{", "[") and j in пар:
                    for k in range(j + 1, пар[j]):
                        if т[k][0] == "id" and т[k][1] not in КЛЮЧОВІ and т[k][1] and (k + 1 >= н or т[k + 1][1] != ":") and т[k - 1][1] not in (".", "?."):
                            додай(і, т[k][1])
                    continue
                while j < н:
                    if т[j][0] == "id" and т[j][1] not in КЛЮЧОВІ: додай(і, т[j][1])
                    k = с.кінець_виразу(j + 2) if j + 1 < н and т[j + 1][1] == "=" else j + 1
                    if k < н and т[k][1] == ",": j = k + 1
                    else: break
            elif x[0] == "id" and x[1] == "catch" and і + 2 < н and т[і + 1][1] == "(" and т[і + 2][0] == "id":
                додай(і, т[і + 2][1])
            elif x[0] == "id" and x[1] == "function" and і + 1 < н and т[і + 1][0] == "id":
                додай(і, т[і + 1][1])

    def ключ(с, і, ім):
        """Розрізняє однойменні змінні за областю оголошення."""
        ф = с.охоплює(і)
        while ф:
            if ім in с.оголош.get(ф.ід, ()): return (ф.ід, ім)
            ф = с.батько(ф)
        return ("G", ім)

    # ── присвоєння: (ключ, вид, (а, б)) — вираз-джерело в цьому ж модулі
    def _присвоєння(с):
        """Перелічує писачів змінних і контейнерів та виклики."""
        т, пар, н = с.ток, с.пар, len(с.ток)
        ОП = {"=", "+=", "||=", "&&=", "??="}
        for і in range(н):
            x = т[і]
            if x[0] == "id" and x[1] not in КЛЮЧОВІ and (і == 0 or т[і - 1][1] not in (".", "?.")) and і + 1 < н:
                наст = т[і + 1]
                if наст[0] == "p" and наст[1] in ОП:
                    с.присв.append((с.ключ(і, x[1]), "=", (і + 2, с.кінець_виразу(і + 2)), і))
                    continue
                # контейнер: X.push(..) / X.f = .. / X[..] = ..
                j = і + 1
                while j < н and т[j][1] in (".", "?.", "[", "("):
                    if т[j][1] == "[":
                        if j not in пар: break
                        j = пар[j] + 1
                    elif т[j][1] == "(":
                        # `X.get(к).push(…)` / `X.get(к).f = …` — запис у значення `Map` (11786); чи `X` — `Map`,
                        # судить походження, для іншого `X` такий запис не рахується, як і досі.
                        if not (т[j - 1][1] == "get" and j in пар and пар[j] + 1 < н and т[пар[j] + 1][1] in (".", "?.", "[")):
                            break
                        j = пар[j] + 1
                    elif j + 1 < н and т[j + 1][0] == "id":
                        j += 2
                    else: break
                if j > і + 1 and j < н:
                    if т[j][1] in ОП and т[j - 1][1] != "]" and т[j - 1][0] == "id" and т[j - 1][1] in ВЛАСТИВОСТІ:
                        pass                        # це сток, не контейнер
                    elif т[j][1] in ОП:
                        с.присв.append((с.ключ(і, x[1]), "поле", (j + 1, с.кінець_виразу(j + 1)), і))
                    elif т[j][1] == "(" and j in пар and т[j - 1][1] in ("push", "unshift", "add", "set", "splice", "assign", "append", "concat"):
                        for a, b in розділити(т, пар, j + 1, пар[j]):
                            с.присв.append((с.ключ(і, x[1]), "поле", (a, b), і))
        for і in range(н):
            if т[і][0] == "id" and т[і][1] == "assign" and і >= 2 and т[і - 1][1] == "." and т[і - 2][1] == "Object" \
                    and і + 1 < н and т[і + 1][1] == "(" and (і + 1) in пар:
                ч = розділити(т, пар, і + 2, пар[і + 1])
                if ч and т[ч[0][0]][0] == "id":
                    for a, b in ч[1:]:
                        с.присв.append((с.ключ(і, т[ч[0][0]][1]), "поле", (a, b), і))
        # поля за іменем: `X.f = вираз` і `{f: вираз}` (псевдоніми контейнера не губимо)
        for і in range(н):
            x = т[і]
            if x[0] == "id" and x[1] not in ВЛАСТИВОСТІ and і >= 1 and т[і - 1][1] in (".", "?.") and і + 1 < н \
                    and т[і + 1][0] == "p" and т[і + 1][1] in ("=", "+=", "||=", "??="):
                с.поля_запис.append((x[1], (і + 2, с.кінець_виразу(і + 2)), і))
            elif x[0] in ("id", "str") and і >= 1 and т[і - 1][1] in ("{", ",") and і + 1 < н and т[і + 1][1] == ":" \
                    and x[1] not in КЛЮЧІ_ОБЄКТА:
                с.поля_запис.append((x[1], (і + 2, с.кінець_виразу(і + 2)), і))
        # деструктуризація та цикли for..of/in
        for і in range(н):
            x = т[і]
            if x[0] == "id" and x[1] in ("const", "let", "var") and і + 1 < н and т[і + 1][1] in ("{", "[") and (і + 1) in пар:
                j = пар[і + 1] + 1
                if j < н and т[j][1] in ("=", "of", "in"):
                    а, б = j + 1, с.кінець_виразу(j + 1) if т[j][1] == "=" else (пар[і - 1] if False else с.кінець_виразу(j + 1))
                    позиція, k = 0, і + 2
                    while k < пар[і + 1]:
                        if т[k][1] == "," and т[і + 1][1] == "[":
                            позиція += 1
                        elif т[k][0] == "id" and т[k][1] not in КЛЮЧОВІ and (k + 1 >= н or т[k + 1][1] != ":") and т[k - 1][1] not in (".", "?."):
                            с.присв.append((с.ключ(і, т[k][1]), "елемент" if т[j][1] != "=" else "=", (а, б), і))
                            if т[і + 1][1] == "[" and т[j][1] == "of" and т[k - 1][1] in ("[", ",") and т[k + 1][1] in (",", "]"):
                                # Ім'я на верхньому рівні шаблону масиву в `for…of`: елемент ітерації, місце `позиція` (11786).
                                с.позиції[(і, с.ключ(і, т[k][1]))] = позиція
                        if т[k][1] in ("[", "{", "(") and k in пар and т[і + 1][1] == "[":
                            # Вкладений шаблон — імена в ньому без місця.
                            for q in range(k + 1, пар[k]):
                                if т[q][0] == "id" and т[q][1] not in КЛЮЧОВІ and (q + 1 >= н or т[q + 1][1] != ":") and т[q - 1][1] not in (".", "?."):
                                    с.присв.append((с.ключ(і, т[q][1]), "елемент" if т[j][1] != "=" else "=", (а, б), і))
                            k = пар[k] + 1
                            continue
                        k += 1
            elif x[0] == "id" and x[1] in ("const", "let", "var") and і + 2 < н and т[і + 1][0] == "id" and т[і + 2][0] == "id" \
                    and т[і + 2][1] in ("of", "in"):
                а = і + 3
                б = пар[і - 1] if (і >= 1 and т[і - 1][1] == "(" and (і - 1) in пар) else с.кінець_виразу(а)
                с.присв.append((с.ключ(і, т[і + 1][1]), "елемент", (а, б), і))
        # виклики відомих імен (для параметрів): (ім, [діапазони аргументів], індекс токена)
        for і in range(н):
            x = т[і]
            if x[0] == "id" and і + 1 < н and т[і + 1][1] == "(" and (і + 1) in пар and x[1] not in КЛЮЧОВІ:
                if і >= 1 and т[і - 1][1] in ("function", "async") : continue
                с.виклики.append((x[1], розділити(т, пар, і + 2, пар[і + 1]), і))




# ─────────────────────────────────── програма: усі модулі разом ───────────────────────────────────
class Програма:
    def __init__(с, модулі, закріплені=()):
        """Зв’язує виклики й джерела між усіма модулями показу."""
        с.модулі, с.закріплені = модулі, set(закріплені)
        с.за_ім, с.ф_за_ід = {}, {}
        for м in модулі:
            for ф in м.функції:
                с.ф_за_ід[ф.ід] = ф
                if ф.ім: с.за_ім.setdefault(ф.ім, []).append(ф)
        с.присв = {}
        for м in модулі:
            for к, в, д, і in м.присв: с.присв.setdefault(к, []).append((м, в, д, і))
        с.виклики_ім = {}                                 # ім'я → усі виклики (для обгорток вузла)
        for м in модулі:
            for ім, арг, і in м.виклики:
                if ім in с.за_ім: с.виклики_ім.setdefault(ім, []).append((м, арг, і))
        с.виклики = {}                                    # ід функції → виклики, що веду́ть саме до неї (за видимістю імені)
        for м in модулі:
            for ім, арг, і in м.виклики:
                if ім in с.за_ім:
                    for ф in с.цілі(м, і, ім): с.виклики.setdefault(ф.ід, []).append((м, арг, і))
        с.ключі_catch = set()
        for м in модулі:
            т = м.ток
            for і in range(len(т) - 2):
                if т[і][1] == "catch" and т[і + 1][1] == "(" and т[і + 2][0] == "id":
                    с.ключі_catch.add(м.ключ(і + 2, т[і + 2][1]))
        с.джерела_фн = с._досяжні_джерела()

    def цілі(с, м, і, ім):
        """функції з іменем `ім`, видимі з місця виклику: найближча область, що оголошує це ім'я (локальна стрілка `знайти` у
        `картки.js` не плутається з однойменною глобальною функцією); невідомо де — усі однойменні"""
        всі = с.за_ім.get(ім, ())
        if і is None or len(всі) < 2: return list(всі)
        область = м.охоплює(і)
        while True:
            знайдено = [ф for ф in всі if (ф.мод.батько(ф) or None) is область]
            if знайдено: return знайдено
            if область is None: return list(всі)
            область = м.батько(область) or None

    def _досяжні_джерела(с):
        """функції, що (транзитивно) досягають fetch/postMessage/Pyodide: їхній результат — дані ззовні"""
        з, всі = set(), [ф for м in с.модулі for ф in м.функції]
        ЗОВНІ = ("fetch", "postMessage", "runPythonAsync", "runPython", "loadPyodide", "XMLHttpRequest", "FileReader")
        for ф in всі:
            т = ф.мод.ток
            if any(т[і][0] == "id" and т[і][1] in ЗОВНІ for і in range(ф.а, min(ф.б, len(т)))): з.add(ф.ід)
        зміна = True
        while зміна:
            зміна = False
            for ф in всі:
                if ф.ід in з: continue
                т = ф.мод.ток
                for і in range(ф.а, min(ф.б, len(т)) - 1):
                    if (т[і][0] == "id" and т[і + 1][1] == "(" and т[і][1] in с.за_ім and (і == 0 or т[і - 1][1] not in (".", "?."))
                            and any(g.ід in з for g in с.за_ім[т[і][1]])):
                        з.add(ф.ід); зміна = True; break
        return з

    def _верх(с, т, пар, а, б, шукані):
        """позиції верхньорівневих токенів із `шукані`"""
        вих, і = [], а
        while і < б:
            if т[і][0] == "p" and т[і][1] in "([{" and і in пар: і = пар[і] + 1; continue
            if т[і][0] == "p" and т[і][1] in шукані: вих.append(і)
            і += 1
        return вих

    def _зворотний(с, ф):
        """опис першого параметра функції, переданої аргументом `приймач.метод(cb)`: ранг або (початок, кінець) приймача"""
        if ф.кб is not None: return ф.кб if ф.кб != -1 else None
        м, т, пар = ф.мод, ф.мод.ток, ф.мод.пар
        з, j = None, ф.заг_а - 1
        if j >= 0 and т[j][1] in ("(", ","):
            k = j
            while k >= 0:
                if т[k][0] == "p" and т[k][1] in ")]}" and k in пар: k = пар[k] - 1; continue
                if т[k][0] == "p" and т[k][1] == "(" and k in пар and пар[k] > ф.заг_а: break
                k -= 1
            if k >= 1 and т[k][1] == "(" and т[k - 1][0] == "id":
                метод = т[k - 1][1]
                приймач = (початок_ланцюга(м, k - 2), k - 2) if k >= 3 and т[k - 2][1] in (".", "?.") else None
                if метод == "catch": з = 3
                elif метод in ЗБІР_МЕТОДИ_ЕЛЕМЕНТА or метод in ("then", "finally"):
                    з = приймач if (приймач and метод != "reduce") else 2
                elif метод == "addEventListener":
                    з = 3 if т[k + 1][0] == "str" and т[k + 1][1] == "message" else 2
                elif метод == "Promise": з = 0
                else: з = 2
        if з is None and ф.заг_а >= 2 and т[ф.заг_а - 1][1] == "=" and т[ф.заг_а - 2][0] == "id":
            з = 3 if т[ф.заг_а - 2][1] in ("onmessage", "onerror", "onunhandledrejection") else (2 if ф.ім is None else None)
        ф.кб = з if з is not None else -1
        return з


def початок_ланцюга(м, j):
    """початок ланцюга приймача, що закінчується перед токеном `j`"""
    т, пар, k = м.ток, м.пар, j - 1
    while k >= 0:
        x = т[k]
        if x[0] == "p" and x[1] in (")", "]") and k in пар: k = пар[k] - 1; continue
        if x[0] in ("id", "str", "num", "tpl"):
            if k >= 1 and т[k - 1][1] in (".", "?."): k -= 2; continue
            return k
        break
    return k + 1


# ───────────────────────────────────────── стоки (шлях А) ─────────────────────────────────────────
class Сток:
    __slots__ = ("мод", "і", "а", "б", "вид", "обгортка", "точка", "ф", "чим", "ключове", "джерела", "вхід", "писачі",
                 "елементи")

    def __init__(с, мод, і, а, б, вид, ф):
        """Зберігає позицію запису екрана, його вид та договір входу."""
        с.мод, с.і, с.а, с.б, с.вид, с.ф, с.обгортка, с.точка, с.чим, с.ключове = мод, і, а, б, вид, ф, False, False, "", False
        с.джерела, с.вхід = frozenset({'невідоме'}), 'поза'
        с.писачі = ()
        с.елементи = ()                                 # (ід, тег, атрибути) — доказ ключового поля


ЕЛЕМЕНТИ = {}                           # id → (тег, атрибути) з розмітки показу (HTML і рядки в JS)
РОЗМІТКА_ЕЛ = re.compile(r"<(input|select|textarea|option|button)\b([^>]*?)>", re.I)


def ключовий_елемент(тег, атр):
    """`.value` такого елемента — не видимий текст: option, select, приховане поле, перемикачі й поля, чиє значення
    браузер санітизує до свого виду (`color` — код `#rrggbb`, `number` — число або порожньо, `range` — число): текст
    іншого виду браузер відкидає, тож чужа мова, латинка чи службовий код на екран так не доходять (11838)"""
    тег = тег.lower()
    return тег in ("option", "select") or bool(re.search(r"type\s*=\s*[\"']?(hidden|checkbox|radio|range|file|color|number)(?![\w-])", атр, re.I)) \
        or bool(re.search(r"(?<![\w-])hidden(?![\w-])", атр))


# ───────────────────── сталі значення: ід елемента з таблиці продукту (11838) ─────────────────────
НЕВІДОМО = type('НЕВІДОМО', (), {'__repr__': lambda с: 'НЕВІДОМО', '__bool__': lambda с: False})()


class Безладний(list):
    """Елементи без доведеного порядку (`sort` з порівнянням): перелік відомий, індекс — ні."""


def довідник_дерева(тека):
    """Значення закріпленої таблиці `ДОВІДНИК` — експорт виміряного дерева тим самим викликом, що вшиває збірка
    (`build_артефакт._довідник_показу`: `прилади/експорт_показу.довідник()`). Не зібрався — НЕВІДОМО."""
    import json, subprocess
    try:
        р = subprocess.run([sys.executable, '-X', 'utf8', '-c',
                            "import json, sys; sys.path.insert(0, 'прилади'); from експорт_показу import довідник; "
                            "print(json.dumps(довідник(), ensure_ascii=False))"],
                           cwd=тека, capture_output=True, encoding='utf-8', timeout=600)
        return json.loads(р.stdout.strip().split("\n")[-1]) if р.returncode == 0 and р.stdout.strip() else НЕВІДОМО
    except (OSError, ValueError, subprocess.SubprocessError):
        return НЕВІДОМО


def правда(v):
    """Істинність значення за JavaScript: порожній масив і об'єкт — істина."""
    return v is not None and v is not False and v != 0 and v != '' if not isinstance(v, (list, dict)) else True


class Сталі:
    """Значення виразу показу, яке прилад обчислює точно, без виконання коду (11838).

    Знає літерали (рядок, число, масив, об'єкт, `true`/`false`/`null`), стрілки з виразом-тілом і шаблонами параметрів,
    `||`/`??`, поле й індекс, `Object.entries/keys/values` і `map`/`flatMap`/`filter`/`sort`/`slice` масиву. Ім'я —
    закріплена таблиця (`ДОВІДНИК` — значенням експорту дерева) або стала верхнього рівня: один писач — її `const`, і
    кожна стала, яку читає її вираз, — закріплена або оголошена раніше в тому самому модулі так, що між двома
    оголошеннями стоять лише оголошення `const`, обчислені тут же (чистий вираз нічого не змінює, тож інший код між
    ними не виконувався). Решта, зокрема виклик функції коду, тернарний вираз і невідома стала, — НЕВІДОМО.
    """
    ПЕРЕБІР = frozenset(('forEach', 'map', 'filter', 'find', 'findIndex', 'findLast', 'some', 'every', 'flatMap'))
    ЧИТАННЯ = ПЕРЕБІР | frozenset(('includes', 'indexOf', 'lastIndexOf', 'slice', 'join', 'concat', 'at', 'entries',
                                   'keys', 'values', 'toString', 'reduce'))

    def __init__(с, п, значення):
        """`значення` — {ім'я закріпленої таблиці: її значення}."""
        с.п, с.значення, с.кеш, с.в_роботі = п, значення, {}, set()

    @staticmethod
    def _верх(м, а, б):
        """Позиції токенів верхнього рівня діапазону (дужки — одним кроком)."""
        т, пар, вих, і = м.ток, м.пар, [], а
        while і < б:
            вих.append(і)
            і = пар[і] + 1 if т[і][0] == 'p' and т[і][1] in '([{' and і in пар else і + 1
        return вих

    def вираз(с, м, а, б, ото=None, г=0):
        """Значення токенів (а, б) модуля `м` за оточенням параметрів `ото`; НЕВІДОМО — не обчислено."""
        т, ото = м.ток, ото or {}
        if г > 60 or а >= б:
            return НЕВІДОМО
        стрілка = с._стрілка(м, а, б, ото)
        if стрілка is not None:
            return стрілка
        верх = с._верх(м, а, б)
        if any(т[k][0] == 'p' and т[k][1] not in ('.', '?.', '(', '[', '{', '||', '??') for k in верх):
            return НЕВІДОМО                                 # інший оператор (тернарний, `&&`, арифметика…) не обчислюємо
        розрізи = [k for k in верх if т[k][0] == 'p' and т[k][1] in ('||', '??')]
        if розрізи:
            межі = [а] + [k + 1 for k in розрізи] + [б + 1]
            v = с.вираз(м, межі[0], розрізи[0], ото, г + 1)
            for н, k in enumerate(розрізи):
                if v is НЕВІДОМО:
                    return НЕВІДОМО
                if (т[k][1] == '||' and not правда(v)) or (т[k][1] == '??' and v is None):
                    v = с.вираз(м, межі[н + 1], межі[н + 2] - 1, ото, г + 1)
            return v
        return с._ланцюг(м, а, б, ото, г)

    def _стрілка(с, м, а, б, ото):
        """Стрілка з виразом-тілом на весь діапазон → ('фн', модуль, шаблони, тіло, оточення); інакше None."""
        т, пар = м.ток, м.пар
        if т[а][0] == 'id' and а + 1 < б and т[а + 1][1] == '=>':
            шаблони, тіло = [(а, а + 1)], а + 2
        elif т[а][1] == '(' and а in пар and пар[а] + 1 < б and т[пар[а] + 1][1] == '=>':
            шаблони, тіло = розділити(т, пар, а + 1, пар[а]), пар[а] + 2
        else:
            return None
        if тіло >= б or (т[тіло][1] == '{' and тіло in пар):
            return НЕВІДОМО                                 # тіло-блок не обчислюємо
        return ('фн', м, шаблони, (тіло, б), dict(ото))

    def _звязати(с, м, а, б, v, ото):
        """Кладе в `ото` імена шаблону параметра (а, б) для значення `v`; False — шаблон не знаємо."""
        т, пар = м.ток, м.пар
        if б - а == 1 and т[а][0] == 'id':
            ото[т[а][1]] = v
            return True
        if т[а][1] in ('[', '{') and а in пар and пар[а] == б - 1:
            частини = розділити(т, пар, а + 1, б - 1)
            for н, (x, y) in enumerate(частини):
                if x >= y:
                    continue
                if т[а][1] == '[':
                    ел = v[н] if isinstance(v, list) and not isinstance(v, Безладний) and н < len(v) else (
                        None if isinstance(v, list) and not isinstance(v, Безладний) else НЕВІДОМО)
                    if not с._звязати(м, x, y, ел, ото):
                        return False
                elif y - x == 1 and т[x][0] == 'id':
                    ото[т[x][1]] = v.get(т[x][1]) if isinstance(v, dict) else НЕВІДОМО
                elif y - x >= 3 and т[x][0] in ('id', 'str') and т[x + 1][1] == ':':
                    if not с._звязати(м, x + 2, y, v.get(т[x][1]) if isinstance(v, dict) else НЕВІДОМО, ото):
                        return False
                else:
                    return False
            return True
        return False

    def виклик(с, ф, арг, г):
        """Значення стрілки `ф` на аргументах `арг`."""
        if not (isinstance(ф, tuple) and ф and ф[0] == 'фн'):
            return НЕВІДОМО
        _, м, шаблони, (а, б), ото = ф
        ото = dict(ото)
        for н, (x, y) in enumerate(шаблони):
            if x < y and not с._звязати(м, x, y, арг[н] if н < len(арг) else None, ото):
                return НЕВІДОМО
        return с.вираз(м, а, б, ото, г + 1)

    def _ланцюг(с, м, а, б, ото, г):
        """Первинний вираз і його поля, індекси й виклики методів."""
        т, пар = м.ток, м.пар
        x, і = т[а], а + 1
        if x[0] == 'str':
            v = x[1]
        elif x[0] == 'num':
            try:
                v = float(x[1].replace('_', '')) if any(ч in x[1] for ч in '.eE') else int(x[1].replace('_', ''), 0)
            except ValueError:
                return НЕВІДОМО
        elif x[0] == 'tpl':
            v = x[1][0][1] if len(x[1]) == 1 else НЕВІДОМО
        elif x[0] == 'id':
            if x[1] in ('true', 'false', 'null', 'undefined'):
                v = {'true': True, 'false': False}.get(x[1])
            elif x[1] in ото:
                v = ото[x[1]]
            elif x[1] == 'Object' and а + 2 < б and т[а + 1][1] == '.' and т[а + 3][1] == '(' and (а + 3) in пар \
                    and т[а + 2][1] in ('entries', 'keys', 'values'):
                о = с.вираз(м, а + 4, пар[а + 3], ото, г + 1)
                if not isinstance(о, dict):
                    return НЕВІДОМО
                v = {'entries': [[к, з] for к, з in о.items()], 'keys': list(о), 'values': list(о.values())}[т[а + 2][1]]
                і = пар[а + 3] + 1
            else:
                v = с.стала(м, а, x[1])
        elif x[1] == '(' and а in пар:
            v, і = с.вираз(м, а + 1, пар[а], ото, г + 1), пар[а] + 1
        elif x[1] == '[' and а in пар:
            v = []
            for y, z in розділити(т, пар, а + 1, пар[а]):
                if y >= z:
                    continue
                if т[y][1] == '...':
                    е = с.вираз(м, y + 1, z, ото, г + 1)
                    if not isinstance(е, list):
                        return НЕВІДОМО
                    v += е
                else:
                    v.append(с.вираз(м, y, z, ото, г + 1))
            і = пар[а] + 1
        elif x[1] == '{' and а in пар:
            v = {}
            for y, z in розділити(т, пар, а + 1, пар[а]):
                if y >= z:
                    continue
                if z - y == 1 and т[y][0] == 'id':
                    v[т[y][1]] = ото[т[y][1]] if т[y][1] in ото else с.стала(м, y, т[y][1])
                elif z - y >= 3 and т[y][0] in ('id', 'str', 'num') and т[y + 1][1] == ':':
                    v[т[y][1]] = с.вираз(м, y + 2, z, ото, г + 1)
                elif т[y][1] == '...':
                    е = с.вираз(м, y + 1, z, ото, г + 1)
                    if not isinstance(е, dict):
                        return НЕВІДОМО
                    v.update(е)
                else:
                    return НЕВІДОМО
            і = пар[а] + 1
        else:
            return НЕВІДОМО
        while і < б and v is not НЕВІДОМО:
            if т[і][1] in ('.', '?.') and і + 1 < б and т[і + 1][0] == 'id':
                ім, і = т[і + 1][1], і + 2
                if і < б and т[і][1] == '(' and і in пар:
                    v, і = с._метод(м, v, ім, розділити(т, пар, і + 1, пар[і]), ото, г), пар[і] + 1
                elif v is None and т[і - 2][1] == '?.':
                    v = None
                elif isinstance(v, dict):
                    v = v.get(ім)
                elif isinstance(v, (list, str)) and ім == 'length':
                    v = НЕВІДОМО if isinstance(v, Безладний) else len(v)
                else:
                    return НЕВІДОМО
            elif т[і][1] == '[' and і in пар:
                к = с.вираз(м, і + 1, пар[і], ото, г + 1)
                if isinstance(v, dict) and isinstance(к, (str, int)) and not isinstance(к, bool):
                    v = v.get(str(к))
                elif isinstance(v, list) and not isinstance(v, Безладний) and isinstance(к, int) and not isinstance(к, bool):
                    v = v[к] if 0 <= к < len(v) else None
                else:
                    return НЕВІДОМО
                і = пар[і] + 1
            else:
                return НЕВІДОМО
        return v

    def _метод(с, м, v, ім, арг, ото, г):
        """Чистий метод масиву на відомому значенні."""
        if not isinstance(v, list):
            return НЕВІДОМО
        безлад = isinstance(v, Безладний)
        аргз = [с.вираз(м, x, y, ото, г + 1) for x, y in арг if x < y]
        if ім in ('map', 'flatMap', 'filter'):
            if len(аргз) != 1:
                return НЕВІДОМО
            вих = []
            for н, е in enumerate(v):
                р = с.виклик(аргз[0], [е, НЕВІДОМО if безлад else н], г)
                if р is НЕВІДОМО:
                    return НЕВІДОМО
                if ім == 'map':
                    вих.append(р)
                elif ім == 'flatMap':
                    вих += р if isinstance(р, list) else [р]
                elif правда(р):
                    вих.append(е)
            return Безладний(вих) if безлад else вих
        if ім == 'sort':
            return Безладний(v)
        if ім == 'slice' and not аргз:
            return Безладний(v) if безлад else list(v)
        return НЕВІДОМО

    def стала(с, м, і, ім):
        """Значення імені на позиції `і`: закріплена таблиця чи стала верхнього рівня з одним писачем-`const`."""
        ключ = м.ключ(і, ім)
        if ключ[0] != 'G':
            return НЕВІДОМО
        if ім in с.значення:
            return с.значення[ім]
        оголошення = с.оголошення(ключ)
        if оголошення is None or ключ in с.в_роботі:
            return НЕВІДОМО
        if ключ not in с.кеш:
            м2, а, б, j = оголошення
            с.в_роботі.add(ключ)
            v = с.вираз(м2, а, б)
            # Стала, яку читає вираз, мусить мати те саме значення, що на час свого оголошення.
            for k in range(а, б):
                if м2.ток[k][0] == 'id' and not (k and м2.ток[k - 1][1] in ('.', '?.')) and м2.ключ(k, м2.ток[k][1])[0] == 'G' \
                        and м2.ток[k][1] not in с.значення and not (k + 1 < б and м2.ток[k + 1][1] == ':'):
                    інше = с.оголошення(м2.ключ(k, м2.ток[k][1]))
                    if інше is not None and not с.поспіль(інше, оголошення):
                        v = НЕВІДОМО
            с.в_роботі.discard(ключ)
            с.кеш[ключ] = v
        return с.кеш[ключ]

    def оголошення(с, ключ):
        """(модуль, а, б, і) єдиного писача імені — `const` верхнього рівня; інакше None."""
        записи = с.п.присв.get(ключ, ())
        if len(записи) != 1:
            return None
        м2, вид, (а, б), j = записи[0]
        if вид != '=' or not j or м2.ток[j - 1][1] != 'const' or м2.охоплює(j) is not None:
            return None
        return м2, а, б, j

    def поспіль(с, раніше, пізніше):
        """Між оголошеннями `раніше` і `пізніше` одного модуля — лише оголошення `const`, чиї вирази тут обчислено."""
        м, _, б0, j0 = раніше
        м2, _, _, j1 = пізніше
        if м is not м2 or j0 >= j1:
            return False
        т, k = м.ток, б0
        while k < j1 - 1:
            if т[k][1] == ';':
                k += 1
                continue
            if т[k][1] != 'const' or k + 2 >= len(т) or т[k + 1][0] != 'id' or т[k + 2][1] != '=':
                return False
            ключ = м.ключ(k + 1, т[k + 1][1])
            о = с.оголошення(ключ)
            if о is None or о[3] != k + 1 or с.стала(м, k + 1, т[k + 1][1]) is НЕВІДОМО:
                return False
            k = о[2]
        return k == j1 - 1

    def закритий_перелік(с, м, і, ім):
        """Рядки сталої-масиву, які ніхто не змінює й не віддає: кожна згадка — читання методом без колбека з третім
        параметром, `.length`, індекс без присвоєння чи `of`; масив — лише рядків. Інакше None."""
        v = с.стала(м, і, ім)
        if not isinstance(v, list) or not all(isinstance(е, str) for е in v):
            return None
        ключ = м.ключ(і, ім)
        for м2 in с.п.модулі:
            т, пар = м2.ток, м2.пар
            for k, (вид, зн, _) in enumerate(т):
                if вид != 'id' or зн != ім or (k and т[k - 1][1] in ('.', '?.')) or м2.ключ(k, ім) != ключ:
                    continue
                if (k and т[k - 1][1] == 'const') or (k and т[k - 1][1] == 'of'):
                    continue
                if k + 2 < len(т) and т[k + 1][1] in ('.', '?.') and т[k + 2][1] == 'length' and \
                        not (k + 3 < len(т) and т[k + 3][1] in ('=', '+=', '-=', '++', '--')):
                    continue
                if k + 3 < len(т) and т[k + 1][1] in ('.', '?.') and т[k + 2][1] in с.ЧИТАННЯ and т[k + 3][1] == '(' and (k + 3) in пар:
                    колбеки = [ф for ф in м2.функції if k + 3 < ф.заг_а < пар[k + 3] and м2.батько(ф) is м2.охоплює(k)]
                    if all(len(ф.парам) < 3 for ф in колбеки):
                        continue
                if k + 1 < len(т) and т[k + 1][1] == '[' and (k + 1) in пар and not (
                        пар[k + 1] + 1 < len(т) and т[пар[k + 1] + 1][1] in ('=', '+=', '-=', '||=', '??=', '&&=', '++', '--')):
                    continue
                return None
        return frozenset(v)

    def рядки_імені(с, м, і):
        """Рядки, які може мати ім'я на позиції `і`: стала-рядок, елемент закритого переліку в параметрі колбека
        перебору (`X.forEach(і => …)`) чи в `for (const і of X)`; невідомо — None."""
        ім = м.ток[і][1]
        ключ = м.ключ(і, ім)
        записи = с.п.присв.get(ключ, ())
        if len(записи) == 1 and записи[0][1] == 'елемент':
            м2, _, (а, б), j = записи[0]
            т = м2.ток
            if j + 2 < len(т) and т[j][1] == 'const' and т[j + 2][1] == 'of' and б - а == 1 and т[а][0] == 'id':
                return с.закритий_перелік(м2, а, т[а][1])
            return None
        if ключ[0] == 'G':
            v = с.стала(м, і, ім)
            return frozenset((v,)) if isinstance(v, str) else None
        ф = с.п.ф_за_ід.get(ключ[0])
        if not записи and ф is not None and ф.парам and ф.парам[0] == (ім, [ім]):
            опис = с.п._зворотний(ф)
            т = ф.мод.ток
            if isinstance(опис, tuple) and т[ф.заг_а - 1][1] == '(' and опис[1] + 1 < len(т) and т[опис[1] + 1][1] in с.ПЕРЕБІР:
                а, б = опис
                if б - а == 1 and т[а][0] == 'id':
                    return с.закритий_перелік(ф.мод, а, т[а][1])
        return None


def опис_елемента(д):
    """Коротко: тег, ід і тип елемента з розмітки."""
    тег, атр = д
    ід = re.search(r"\bid\s*=\s*[\"']([^\"']+)", атр)
    тип = re.search(r"\btype\s*=\s*[\"']?([\w-]+)", атр)
    return '%s#%s%s' % (тег, ід.group(1) if ід else '?', '[%s]' % тип.group(1) if тип else '')


def ключове_поле(п, м, крапка, ел):
    """елемент перед `.value =` — option/select/приховане поле? Невідомий елемент — видимий (місце)"""
    т = м.ток
    поч = початок_ланцюга(м, крапка)
    ток = т[поч:крапка]
    докази = п.докази_поля = []
    сталі = getattr(п, 'сталі', None)

    def за_ідами(м2, а):
        """Елементи, чиї іди може мати ім'я `$(ім)` (11838): кожен ід — з розмітки, інакше видимий."""
        іди = сталі.рядки_імені(м2, а) if сталі else None
        if іди:
            докази.extend(ел.get(і) or ('?', '') for і in sorted(іди))
    if len(ток) >= 4 and ток[0][1] == "$" and ток[2][0] == "str": докази.append(ел.get(ток[2][1]))
    elif len(ток) == 4 and ток[0][1] == "$" and ток[1][1] == "(" and ток[2][0] == "id" and ток[3][1] == ")": за_ідами(м, поч + 2)
    elif len(ток) >= 6 and ток[0][1] == 'document' and ток[2][1] in ('getElementById', 'querySelector') and ток[4][0] == 'str':
        докази.append(ел.get(ток[4][1].lstrip('#')))
    elif len(ток) == 1 and ток[0][0] == "id":
        # Тимчасове поле буфера обміну приховане CSS, хоча не має type=hidden.
        ключ_вузла = м.ключ(поч, ток[0][1])
        for к in range(len(т) - 6):
            if т[к][0] == 'id' and м.ключ(к, т[к][1]) == ключ_вузла and [x[1] for x in т[к + 1:к + 5]] == ['.', 'style', '.', 'cssText'] and т[к + 5][1] == '=' and т[к + 6][0] == 'str':
                if re.search(r'(?:opacity\s*:\s*0(?:\D|$)|display\s*:\s*none|visibility\s*:\s*hidden)', т[к + 6][1]): return True
        for м2, вид, (a, b), i in п.присв.get(м.ключ(поч, ток[0][1]), ()):
            з_виразу_м = м2.ток[a:b]
            if len(з_виразу_м) >= 4 and з_виразу_м[0][1] == "$" and з_виразу_м[2][0] == "str": докази.append(ел.get(з_виразу_м[2][1]))
            elif len(з_виразу_м) == 4 and з_виразу_м[0][1] == "$" and з_виразу_м[1][1] == "(" and з_виразу_м[2][0] == "id" \
                    and з_виразу_м[3][1] == ")":
                за_ідами(м2, a + 2)
            elif з_виразу_м and з_виразу_м[0][1] in ("ел", "createElement") or (len(з_виразу_м) > 2 and з_виразу_м[2][1] == "createElement"):
                k = next((q[1] for q in з_виразу_м if q[0] == "str"), None)
                if k: докази.append((k, ""))
    докази = [д for д in докази if д]
    п.докази_поля = докази
    return bool(докази) and all(ключовий_елемент(*д) for д in докази)


def входи_модуля(п):
    """Виводить варіанти входів із викликів у модулі, включно з поверненням елемента.

    Кореневі функції задають договори тексту; решта успадковує договір
    через переданий параметр, незалежно від свого імені.
    """
    входи = {'текстЖінціП': {(1, 'проза')}, 'збійЖінціП': {(2, 'збій')},
             'назваЖінціП': {(1, 'назва')}, 'їїСловаП': {(1, 'її')},
             'розміткаЖінціП': {(1, 'проза')}, 'полеЕкранаП': {(2, 'поза')}}
    def залежності(м, а, б, бачені=None):
        """Параметри, від яких залежить аргумент, включно з локальними псевдонімами."""
        бачені = set() if бачені is None else бачені
        вих = set()
        for і in range(а, б):
            тип, ім, _ = м.ток[і]
            if тип != 'id' or (і > а and м.ток[і - 1][1] in ('.', '?.')): continue
            вих.add(ім)
            ключ = м.ключ(і, ім)
            if ключ in бачені: continue
            бачені.add(ключ)
            for м2, _, (х, у), _ in п.присв.get(ключ, ()):
                вих.update(залежності(м2, х, у, бачені))
        return вих
    for м in п.модулі:
        if not відображене(м.шлях).endswith('показ/мовний_шар.js'): continue
        for і, x in enumerate(м.ток):
            if x[1] != '=' or і < 2 or м.ток[і - 1][1] not in ВЛАСТИВОСТІ or м.ток[і - 2][1] != '.': continue
            ф = м.охоплює(і)
            if not ф or not ф.ім or ф.ім in входи or ф.ім in СЛУЖБОВИЙ_ВИХІД: continue
            імена = залежності(м, і + 1, м.кінець_виразу(і + 1))
            for н, (_, параметри) in enumerate(ф.парам):
                if імена.intersection(параметри): входи.setdefault(ф.ім, set()).add((н, 'поза'))
    зміна = True
    while зміна:
        зміна = False
        for м in п.модулі:
            if not відображене(м.шлях).endswith('показ/мовний_шар.js'): continue
            for ім, арг, і in м.виклики:
                if ім not in входи: continue
                ф = м.охоплює(і)
                if not ф or not ф.ім or ф.ім in ('текстЖінціП', 'назваЖінціП', 'їїСловаП', 'збійЖінціП', 'розміткаЖінціП'): continue
                for к, вид in list(входи[ім]):
                    if к >= len(арг): continue
                    а, б = арг[к]
                    імена = залежності(м, а, б)
                    for н, (_, параметри) in enumerate(ф.парам):
                        if імена.intersection(параметри) and (н, вид) not in входи.get(ф.ім, set()):
                            входи.setdefault(ф.ім, set()).add((н, вид)); зміна = True
    return входи


def знайти_стоки(п):
    """Знаходить записи екрана й зовнішні виклики його входів."""
    стоки = []
    виняток = lambda ф: ф is not None and ф.ім in ТОЧКА + ("станТекстуЖінціП",) + СЛУЖБОВИЙ_ВИХІД
    п.у_точці = 0
    п.входи = входи_модуля(п)
    п.елементи = dict(ЕЛЕМЕНТИ)
    for м in п.модулі:
        т, пар, н = м.ток, м.пар, len(м.ток)
        модуль_точки = відображене(м.шлях).endswith("показ/мовний_шар.js")   # пише лише через `полеЕкранаП`: запис після сторожа — сама точка
        for і, x in enumerate(т):
            ф = м.охоплює(і)
            while ф is not None and not виняток(ф): ф = м.батько(ф)
            if ф is not None: continue
            ф = м.охоплює(і)
            знайдено = []                                     # (вид, а, б)
            if x[0] == "p" and x[1] in ("=", "+=") and і >= 3 and т[і - 1][1] == ']' and і - 1 in пар and т[пар[і - 1] + 1][0] == 'str' and т[пар[і - 1] + 1][1] in ВЛАСТИВОСТІ:
                властивість = т[пар[і - 1] + 1][1]
                знайдено.append(('П2' if властивість in РОЗМІТКА else 'П1', і + 1, м.кінець_виразу(і + 1), '[' + властивість + ']'))
            elif x[0] == "p" and x[1] in ("=", "+=") and і >= 2 and т[і - 1][0] == "id" and т[і - 1][1] in ВЛАСТИВОСТІ and т[і - 2][1] in (".", "?.") \
                    and not (т[і - 1][1] == "data" and і >= 4 and т[і - 3][1] == "source"):          # `source.data` фото — не на екран
                знайдено.append(("П2" if т[і - 1][1] in РОЗМІТКА else "П1", і + 1, м.кінець_виразу(і + 1), "." + т[і - 1][1]))
            elif x[0] == "id" and x[1] in КЛЮЧІ_ОБЄКТА and і + 1 < len(т) and т[і + 1][1] == ":" and і >= 1 and т[і - 1][1] in ("{", ","):
                знайдено.append(("П2" if x[1] in РОЗМІТКА else "П1", і + 2, м.кінець_виразу(і + 2), "{" + x[1] + ":}"))
            elif x[0] == "id" and і + 1 < len(т) and т[і + 1][1] == "(" and (і + 1) in пар:
                арг = розділити(т, пар, і + 2, пар[і + 1])
                перед_крапка = і >= 1 and т[і - 1][1] in (".", "?.")
                if x[1] in ВИКЛИКИ_ТЕКСТ and (not перед_крапка or x[1] in ("createTextNode", "setCustomValidity") or (і >= 2 and т[і - 2][1] == "window")) and арг:
                    знайдено.append((ВИКЛИКИ_ТЕКСТ[x[1]], арг[0][0], арг[0][1], x[1] + "()"))
                elif x[1] in ("insertAdjacentHTML", "insertAdjacentText") and len(арг) > 1:
                    знайдено.append(("П2" if x[1].endswith("HTML") else "П1", арг[1][0], арг[1][1], x[1] + "()"))
                elif x[1] == "Option" and арг and і >= 1 and т[і - 1][1] == "new":
                    знайдено.append(("П1", арг[0][0], арг[0][1], "new Option()"))
                elif x[1] == "setAttribute" and len(арг) > 1 and (т[арг[0][0]][0] != "str" or т[арг[0][0]][1] in АТРИБУТИ):
                    знайдено.append(("П1", арг[1][0], арг[1][1], "атрибут " + str(т[арг[0][0]][1])))
                elif x[1] in п.входи and not перед_крапка:
                    for к, договір in sorted(п.входи[x[1]]):
                        if к < len(арг) and договір not in ('проза', 'збій'):
                            знайдено.append(("П7", арг[к][0], арг[к][1], x[1] + "()"))
                elif x[1] in ВСТАВКИ and перед_крапка:
                    for a, b in арг:
                        знайдено.append(("П4?", a, b, "." + x[1] + "()"))
            for вид, a, b, чим in знайдено:
                if a >= b: continue
                с = Сток(м, і, a, b, вид, ф)
                с.чим = чим
                if вид == "П4?":
                    с.вид = "П4"
                if модуль_точки: п.у_точці += 1; continue
                if вид == "П7":
                    с.вхід = next(договір for к, договір in sorted(п.входи[чим[:-2]]) if к < len(арг) and арг[к] == (a, b))
                с.точка = any(т[k][0] == "id" and т[k][1] in ТОЧКА for k in range(a, b))
                if чим == ".value":
                    с.ключове, с.елементи = ключове_поле(п, м, і - 2, ЕЛЕМЕНТИ), tuple(п.докази_поля)
                стоки.append(с)
    # обгортки: функція, чий параметр лягає в сток як є
    обгортки, значення_обгорток, договори, приховані = {}, set(), {}, {}
    for с in стоки:
        if с.ф is None or not с.ф.ім or с.б - с.а > 4: continue
        if not п.виклики_ім.get(с.ф.ім): continue
        імена = [с.мод.ток[k][1] for k in range(с.а, с.б) if с.мод.ток[k][0] == "id" and с.мод.ток[k][1] not in КЛЮЧОВІ]
        if len(імена) == 1:
            for k, (ім2, ідс) in enumerate(с.ф.парам):
                if імена[0] in ідс and ім2 != "*":
                    обгортки.setdefault(с.ф.ім, set()).add(k); с.обгортка = True
                    договори[(с.ф.ім, k)] = с.вхід
                    приховані.setdefault((с.ф.ім, k), []).append(с.ключове)
                    if с.чим == ".value": значення_обгорток.add(с.ф.ім)
    for ім, номери in обгортки.items():
        for м2, арг, і in п.виклики_ім.get(ім, ()):
            ф = м2.охоплює(і)
            for k in номери:
                if k < len(арг):
                    с = Сток(м2, і, арг[k][0], арг[k][1], "П3", ф)
                    с.чим = ім + "()"
                    с.вхід = договори.get((ім, k), 'поза')
                    с.ключове = all(приховані.get((ім, k), [False]))
                    if ім in значення_обгорток and арг and м2.ток[арг[0][0]][0] == "str":
                        інфо = ЕЛЕМЕНТИ.get(м2.ток[арг[0][0]][1])
                        if інфо and ключовий_елемент(*інфо): с.ключове = True
                    с.точка = any(м2.ток[q][0] == "id" and м2.ток[q][1] in ТОЧКА for q in range(арг[k][0], арг[k][1]))
                    стоки.append(с)
    аналіз = Походження(п, розділити, п.входи)
    for с in стоки:
        аналіз.докази.clear()
        с.джерела = аналіз.походження(с.мод, с.а, с.б)
        с.писачі = tuple(sorted(аналіз.докази))
    return стоки, обгортки




def є_місцем(с):
    """Місце визначає договір входу й походження даних, без ваг і порогів."""
    return not с.ключове and невідповідний(с.джерела, с.вхід)


# ───────────────────────────────── шлях Б: від джерел уперед ─────────────────────────────────
def позиції_значення(т, пар, а, б):
    """ідентифікатори й токени у позиціях ЗНАЧЕННЯ (не умова, не порівняння, не довжина, не індекс)"""
    вих = []
    while а < б and т[а][1] == ";": а += 1
    if а >= б or any(т[і][1] == "=>" for і in п_верх(т, пар, а, б, ("=>",))): return вих
    if т[а][0] == "id" and т[а][1] in ("function", "class", "typeof", "void", "delete"): return вих
    q = п_верх(т, пар, а, б, ("?",))
    if q:
        лічба, к = 1, q[0] + 1
        while к < б:
            if т[к][0] == "p" and т[к][1] in "([{" and к in пар: к = пар[к] + 1; continue
            if т[к][0] == "p" and т[к][1] == "?": лічба += 1
            elif т[к][0] == "p" and т[к][1] == ":":
                лічба -= 1
                if лічба == 0: break
            к += 1
        return позиції_значення(т, пар, q[0] + 1, к) + позиції_значення(т, пар, к + 1, б)
    for оп in (("||", "??"), ("&&",)):
        ч, поч = [], а
        for і in п_верх(т, пар, а, б, оп): ч.append((поч, і)); поч = і + 1
        if ч:
            ч.append((поч, б))
            for x, y in (ч if оп[0] == "||" else ч[-1:]): вих += позиції_значення(т, пар, x, y)
            return вих
    if п_верх(т, пар, а, б, ("==", "===", "!=", "!==", "<", ">", "<=", ">=")): return вих
    поч, ч, арифм = а, [], False
    for і in п_верх(т, пар, а, б, ("+", "-", "*", "/", "%", "**", "&", "|", "^", "<<", ">>")):
        if і == а or (т[і - 1][0] == "p" and т[і - 1][1] not in (")", "]", "}")): continue
        if т[і][1] == "+": ч.append((поч, і)); поч = і + 1
        else: арифм = True
    if арифм and not ч: return вих
    ч.append((поч, б))
    if len(ч) > 1:
        for x, y in ч: вих += позиції_значення(т, пар, x, y)
        return вих
    if т[а][0] == "p" and т[а][1] in ("!", "-", "~", "++", "--"): return вих
    і = а + 1 if (т[а][0] == "id" and т[а][1] in ("await", "new")) or (т[а][0] == "p" and т[а][1] in ("+", "...")) else а
    числовий = т[і][0] == "id" and т[і][1] in ("Number", "parseInt", "parseFloat", "isNaN", "isFinite", "Boolean", "Math", "Date", "Intl", "BigInt") \
        or (т[і][0] == "id" and т[і][1] in ТОЧКА + СЛУЖБОВИЙ_ВИХІД)
    while і < б:
        x = т[і]
        if x[0] == "tpl":
            for вид, зн in x[1]:
                if вид == "e": вих += [(зн, пари(зн), k) for k in позиції_значення(зн, пари(зн), 0, len(зн))]
            і += 1; continue
        if x[0] == "p" and x[1] == "[" and і in пар and і > а: і = пар[і] + 1; continue          # індекс
        if x[0] == "p" and x[1] in ("(", "[", "{") and і in пар:
            if x[1] == "{":
                for aa, bb in розділити(т, пар, і + 1, пар[і]):
                    вих += позиції_значення(т, пар, aa + 2 if aa + 1 < bb and т[aa + 1][1] == ":" else aa, bb)
            else:
                for aa, bb in розділити(т, пар, і + 1, пар[і]): вих += позиції_значення(т, пар, aa, bb)
            і = пар[і] + 1; continue
        if x[0] == "id":
            if і >= 1 and т[і - 1][1] in (".", "?."):
                if x[1] in ("length", "size") or (x[1] in ЧИСЛОВІ and x[1] not in ПЕРЕНОС): числовий = True
                else: вих.append(("м", x[1], і))
            else:
                вих.append(і)
        і += 1
    return [] if числовий else вих


def шлях_б(п, стоки):
    """Уперед: джерела (виняток, `.message`, `*_жінці`, функції, що досягають fetch/postMessage) → змінні → стоки.
    Згадка проста (без винятку умов і чисел) — розбіжності з А пояснюються у виводі."""
    заражені, фн = set(), set(п.джерела_фн)
    заражені |= п.ключі_catch
    поля_джерела = set()                   # поля, у які пишеться джерело (за іменем, як у А)

    def згадує(м, т, пар, а, б, ск):
        """Перевіряє досяжність джерела у значенні виразу шляху Б."""
        for v in позиції_значення(т, пар, а, б):
            if isinstance(v, tuple) and v[0] == "м":
                if v[1] == "message" or v[1].endswith("_жінці") or v[1] in поля_джерела: return True
                continue
            if isinstance(v, tuple):                     # токен із шаблону: (список токенів, пари, індекс)
                зт, зп, k = v
                if зт[k][1] == "fetch" or м.ключ(ск, зт[k][1]) in заражені: return True
                if k + 1 < len(зт) and зт[k + 1][1] == "(" and зт[k][1] in п.за_ім and any(g.ід in фн for g in п.за_ім[зт[k][1]]): return True
                continue
            x = т[v]
            if x[1] == "fetch": return True
            if v + 1 < len(т) and т[v + 1][1] == "(" and x[1] in п.за_ім and any(g.ід in фн for g in п.за_ім[x[1]]): return True
            if м.ключ(v if т is м.ток else ск, x[1]) in заражені: return True
        return False
    зміна = True
    while зміна:
        зміна = False
        for ключ, ряд in п.присв.items():
            if ключ in заражені: continue
            for м, вид, (а, б), і in ряд:
                if згадує(м, м.ток, м.пар, а, б, і): заражені.add(ключ); зміна = True; break
        for ф in п.ф_за_ід.values():
            if ф.ід in фн: continue
            м, т = ф.мод, ф.мод.ток
            ок = False
            if ф.вираз: ок = згадує(м, т, м.пар, ф.а, ф.б, ф.а)
            else:
                for і in range(ф.а, min(ф.б, len(т))):
                    if т[і][1] == "return" and м.охоплює(і) is ф and згадує(м, т, м.пар, і + 1, м.кінець_виразу(і + 1), і + 1): ок = True; break
            if ок: фн.add(ф.ід); зміна = True
        for ід_ф, ряд in п.виклики.items():
            for ф in (п.ф_за_ід[ід_ф],):
                for м, арг, і in ряд:
                    for k, (a, b) in enumerate(арг):
                        if k < len(ф.парам) and ф.парам[k][0] != "*":
                            ключ = (ф.ід, ф.парам[k][0])
                            if ключ not in заражені and згадує(м, м.ток, м.пар, a, b, a): заражені.add(ключ); зміна = True
        for м in п.модулі:                          # поля за іменем
            for ім, (а, б), і in м.поля_запис:
                if ім not in поля_джерела and згадує(м, м.ток, м.пар, а, б, і): поля_джерела.add(ім); зміна = True
        for ф in п.ф_за_ід.values():                # зворотні виклики з джерелом приймача
            if ф.парам and any((ф.ід, x) not in заражені for x in ф.парам[0][1]):
                оп = п._зворотний(ф)
                if оп == 3 or (isinstance(оп, tuple) and згадує(ф.мод, ф.мод.ток, ф.мод.пар, оп[0], оп[1], оп[1])):
                    for x in ф.парам[0][1]: заражені.add((ф.ід, x))
                    зміна = True
    вих = set()
    for с in стоки:
        if згадує(с.мод, с.мод.ток, с.мод.пар, с.а, с.б, с.а): вих.add((відображене(с.мод.шлях), с.мод.рядок(с.і), с.вид))
    return вих, len(заражені)


def п_верх(т, пар, а, б, шукані):
    """Знаходить оператори поза вкладеними дужками."""
    вих, і = [], а
    while і < б:
        if т[і][0] == "p" and т[і][1] in "([{" and і in пар: і = пар[і] + 1; continue
        if т[і][0] == "p" and т[і][1] in шукані: вих.append(і)
        і += 1
    return вих




# ───────────────────────────────────────── збирання й вивід ─────────────────────────────────────────
СКРИПТ = re.compile(r"<script(?P<а>[^>]*)>(?P<т>.*?)</script>", re.S | re.I)
ДИНАМІКА_РОЗМІТКИ = re.compile(r"\$\{|\{\{|__[А-ЯІЇЄҐA-Z_]{3,}__|\bon[a-z]+\s*=\s*[\"']")


def прочитати(шлях):
    """Читає джерело у кодуванні UTF-8."""
    with open(шлях, encoding="utf8") as ф: return ф.read()


def джерела_розмітки(тека):
    """Перелічує складання HTML у Python для звірки досяжності екрана.

    Це кандидати шляху від джерел: без запису в екран вони не додають
    другого місця. Стійкість підрахунку не залежить від установлення ядра.
    """
    вих = []
    тег = re.compile(r'<(?:div|span|p|b|h[1-6]|input|option|table|a)\b')
    for ф in sorted(os.listdir(тека)):
        if not ф.endswith('.py'): continue
        текст = прочитати(os.path.join(тека, ф))
        дерево = ast.parse(текст, filename=ф)
        for вузол in ast.walk(дерево):
            літерали = []
            if isinstance(вузол, ast.JoinedStr):
                літерали = [ч.value for ч in вузол.values if isinstance(ч, ast.Constant) and isinstance(ч.value, str)]
            elif isinstance(вузол, ast.BinOp) and isinstance(вузол.op, (ast.Add, ast.Mod)) and isinstance(вузол.left, ast.Constant) and isinstance(вузол.left.value, str):
                літерали = [вузол.left.value]
            elif isinstance(вузол, ast.Call) and isinstance(вузол.func, ast.Attribute) and вузол.func.attr == 'format' and isinstance(вузол.func.value, ast.Constant) and isinstance(вузол.func.value.value, str):
                літерали = [вузол.func.value.value]
            if any(тег.search(ч) for ч in літерали):
                вих.append((ф, вузол.lineno))
    return sorted(set(вих))


def модулі_html(шлях, ім):
    """Виділяє вбудовані скрипти й динамічні ділянки HTML з рядками джерела."""
    текст, вих, розмітка = прочитати(шлях), [], []
    кінець = 0
    k = 0
    for м in СКРИПТ.finditer(текст):
        розмітка.append((текст[кінець:м.start()], текст.count("\n", 0, кінець)))
        кінець = м.end()
        if "src=" in м.group("а"): continue
        k += 1
        зсув = текст.count("\n", 0, м.start("т"))
        вих.append(Модуль("%s#%d" % (ім, k), лекс(м.group("т")), зсув))
    розмітка.append((текст[кінець:], текст.count("\n", 0, кінець)))
    динаміка = []
    for ч, рядок0 in розмітка:
        for н, р in enumerate(ч.split("\n")):
            if ДИНАМІКА_РОЗМІТКИ.search(р): динаміка.append("%s:%d" % (ім, рядок0 + н + 1))
    return вих, динаміка


def відображене(модуль_шлях):
    """Повертає файл без номера вбудованого скрипту."""
    return модуль_шлях.split("#")[0]


def обчислити(тека, закріплені=("ДОВІДНИК",)):
    """Читає весь показ і локальні скрипти сторінки, зокрема поза текою показу."""
    показ = os.path.join(тека, "показ")
    шляхи = {os.path.relpath(os.path.join(корінь, ф), тека).replace(os.sep, '/')
             for корінь, _, файли in os.walk(показ) for ф in файли if ф.endswith(('.js', '.mjs'))}
    html = прочитати(os.path.join(тека, 'показ.html'))
    for ф in re.findall(r'<script\b[^>]*\bsrc\s*=\s*[\"\']([^\"\']+)', html, re.I):
        if not re.match(r'\w+:|//', ф):
            шляхи.add(ф.split('?')[0])
    модулі = [Модуль(ф, лекс(прочитати(os.path.join(тека, ф)))) for ф in sorted(шляхи)]
    мод_html, динаміка = модулі_html(os.path.join(тека, "показ.html"), "показ.html")
    ЕЛЕМЕНТИ.clear()
    тексти = [прочитати(os.path.join(тека, "показ.html"))]
    for м in модулі + мод_html:
        for т in м.ток:
            if т[0] == "str": тексти.append(т[1])
            elif т[0] == "tpl": тексти += [ч[1] for ч in т[1] if ч[0] == "s"]
    for тх in тексти:
        for мм in РОЗМІТКА_ЕЛ.finditer(тх):
            ід = re.search(r"\bid\s*=\s*[\"']([^\"']+)[\"']", мм.group(2))
            if ід: ЕЛЕМЕНТИ.setdefault(ід.group(1), (мм.group(1), мм.group(2)))
    п = Програма(модулі + мод_html, закріплені)
    п.корінь = тека
    п.довідник = довідник_дерева(тека) if "ДОВІДНИК" in закріплені else НЕВІДОМО
    п.сталі = Сталі(п, {"ДОВІДНИК": п.довідник} if п.довідник is not НЕВІДОМО else {})
    стоки, обгортки = знайти_стоки(п)
    служб_модулі = []
    for шлях, ім in ((os.path.join(тека, "проба.html"), "проба.html"), (os.path.join(тека, "..", "показ_зонд.html"), "показ_зонд.html")):
        if os.path.exists(шлях): служб_модулі += модулі_html(шлях, ім)[0]
    службові = Програма(служб_модулі) if служб_модулі else None
    стоки_служб = знайти_стоки(службові)[0] if службові else []
    return п, стоки, обгортки, динаміка, стоки_служб


def пункт(с):
    """Відносить запис вбудованого скрипту до окремого пункту класу."""
    return "П5" if с.мод.шлях.startswith("показ.html") else с.вид


def подія(с):
    """Дає спільний ключ події для звірки двох шляхів."""
    return (відображене(с.мод.шлях), с.мод.рядок(с.і), с.вид)


def писач(с):
    """Відділяє доведений допис коду від її слів і недоведеного джерела."""
    if с.джерела & {'модель', 'складено', 'код', 'напис коду'}:
        return 'продукт'
    if 'невідоме' in с.джерела or not с.джерела:
        return 'недоведений'
    return 'жінка' if 'її' in с.джерела else 'продукт'


def самоперевірка():
    """Звіряє договори входів, походження, стоки та незалежність шляху Б."""
    import tempfile
    точка = '''
function полеЕкранаП(е, поле, т){ е[поле || 'textContent'] = т; }
function текстЖінціП(е, т){ полеЕкранаП(е, null, т); return т; }
function збійЖінціП(е, вид, причина){ полеЕкранаП(е, null, 'Збій'); }
function назваЖінціП(е, т){ полеЕкранаП(е, null, т); return т; }
function їїСловаП(е, т){ полеЕкранаП(е, null, т); return т; }
function елНазваП(тег, клас, т){ const е = document.createElement(тег); назваЖінціП(е, т); return е; }
function їїСловаЕлП(тег, клас, т){ const е = document.createElement(тег); їїСловаП(е, т); return е; }
function іншаНазва(е, т){ const копія = т; назваЖінціП(е, копія); }
'''
    проби = [
        ('назва-невідоме', "function ф(д){ назваЖінціП(document.body, д.назва); }", 1),
        ('варіант-ключ', "function ф(д){ елНазваП('b', null, String(д.схема).replace(/_/g, ' ')); }", 1),
        ('варіант-її', "async function ф(){ const д = await fetch('/m'); їїСловаЕлП('b', null, д.текст); }", 1),
        ('псевдонім-входу', "function ф(д){ іншаНазва(document.body, д); }", 1),
        ('модель-назва', "async function ф(){ const д = await (await fetch('/m')).json(); назваЖінціП(document.body, д.назва); }", 1),
        ('модель-її-назва', "async function ф(){ const д = await (await fetch('/m')).json(); їїСловаП(document.body, д.назва); }", 1),
        ('модель-її-текст', "async function ф(){ const д = await (await fetch('/m')).json(); їїСловаП(document.body, д.текст); }", 1),
        ('її-ввід', "їїСловаП(document.body, document.getElementById('ввід').value);", 0),
        ('її-запис', "const д = {назва: document.getElementById('ввід').value}; їїСловаП(document.body, д.назва);", 0),
        ('її-допис', "їїСловаП(document.body, document.getElementById('ввід').value + ' допис');", 1),
        ('назва-з-вводу', "const д = {назва: document.getElementById('ввід').value}; назваЖінціП(document.body, 'Назва: ' + д.назва);", 0),
        ('стале', "document.body.textContent = 'Напис';", 0),
        ('стала-таблиця', "const Т = {a:'Напис', b:'Інший'}; function ф(ключ){ document.body.textContent = Т[ключ]; }", 0),
        ('число', "function ф(д){ document.body.textContent = Number(д); }", 0),
        ('невідомий-тип', "function ф(д){ document.body.textContent = String(д); }", 1),
        ('шаблон', "function ф(д){ document.body.innerHTML = `<b>${д.текст}</b>`; }", 1),
        ('append', "function ф(д){ document.body.append(д); }", 1),
        ('alert', "function ф(д){ alert(д); }", 1),
        ('value', "function ф(д){ document.getElementById('ввід').value = д; }", 1),
        ('ключ', "function ф(д){ document.getElementById('ключ').value = д; }", 0),
        ('приховане-css', "function коп(д){ const т = document.createElement('textarea'); т.value = д; т.style.cssText='opacity:0'; document.body.appendChild(т); } function ф(д){ коп(д); }", 0),
        ('атрибут', "function ф(д){ document.body.setAttribute('aria-label', д); }", 1),
        ('дужки', "function ф(д){ document.body['title'] = д; }", 1),
        ('вузли', "function рендер(){ fetch('/m'); const е = document.createElement('div'); текстЖінціП(е, 'Текст'); return е; } document.body.replaceChildren(...рендер().childNodes);", 0),
        ('точка-допис', "function ф(д){ document.body.textContent = текстЖінціП(null, д) + д; }", 1),
        ('точка', "function ф(д){ текстЖінціП(document.body, д); }", 0),
        ('сховище-її', "localStorage.setItem('ім', $('ввід').value); їїСловаП(document.body, localStorage.getItem('ім'));", 0),
        ('сховище-модель', "localStorage.setItem('ім', fetch('/m')); їїСловаП(document.body, localStorage.getItem('ім'));", 1),
        ('сховище-без-писача', "їїСловаП(document.body, localStorage.getItem('ім'));", 1),
        ('сховище-змішане', "localStorage.setItem('ім', $('ввід').value); localStorage.setItem('ім', fetch('/m')); їїСловаП(document.body, localStorage.getItem('ім'));", 1),
        ('сховище-чужий-ключ', "localStorage.setItem('інший', $('ввід').value); їїСловаП(document.body, localStorage.getItem('ім'));", 1),
        ('сховище-обгортка', "function писати(к, з){localStorage.setItem(к, з);} function читати(к){return localStorage.getItem(к);} писати('її', $('ввід').value); писати('м', fetch('/m')); їїСловаП(document.body, читати('її'));", 0),
        ('сховище-допис', "localStorage.setItem('ім', $('ввід').value + ' допис'); їїСловаП(document.body, localStorage.getItem('ім'));", 1),
        ('сховище-поле', "localStorage.setItem('п', JSON.stringify({ім: $('ввід').value, інше: fetch('/m')})); їїСловаП(document.body, JSON.parse(localStorage.getItem('п')).ім);", 0),
        ('сховище-сеанс', "sessionStorage.setItem('ім', $('ввід').value); їїСловаП(document.body, localStorage.getItem('ім'));", 1),
        ('сховище-динамічний-писач', "function ф(ключ){localStorage.setItem(ключ, fetch('/m'));} localStorage.setItem('ім', $('ввід').value); їїСловаП(document.body, localStorage.getItem('ім'));", 1),
        ('бд-поле', "indexedDB.open('б'); const s = d.transaction('п').objectStore('п'); s.put({ім: $('ввід').value}, 'я'); const r = s.get('я'); їїСловаП(document.body, r.result.ім);", 0),
        ('бд-getAll', "indexedDB.open('б'); const s = d.transaction('п').objectStore('п'); s.put({ім: $('ввід').value}, 'я'); const r = s.getAll(); r.result.forEach(з=>їїСловаП(document.body, з.ім));", 0),
        ('бд-Promise', "indexedDB.open('б'); const s = d.transaction('п').objectStore('п'); s.put({ім: $('ввід').value}, 'я'); function читати(){return new Promise((рез, від)=>{ const r = s.get('я'); r.onsuccess=()=>рез(r.result); });} їїСловаП(document.body, читати().ім);", 0),
        ('бд-обгортка', "indexedDB.open('б'); function tx(ім, дія){ const s = d.transaction(ім).objectStore(ім); дія(s); } tx('п', s=>s.put({ім: $('ввід').value}, 'я')); const r = d.transaction('п').objectStore('п').get('я'); їїСловаП(document.body, r.result.ім);", 0),
        ('бд-чужий-магазин', "indexedDB.open('б'); d.transaction('а').objectStore('а').put({ім: $('ввід').value}, 'я'); const r = d.transaction('б').objectStore('б').get('я'); їїСловаП(document.body, r.result.ім);", 1),
        ('бд-префікси', "indexedDB.open('б'); function писати(к, з){d.transaction('п').objectStore('п').put(з, к);} писати('п:' + ід, {ім: $('ввід').value}); писати('м:' + ід, {ім: fetch('/m')}); const r = d.transaction('п').objectStore('п').get('п:' + активний); їїСловаП(document.body, r.result.ім);", 0),
        ('бд-дві-бази', "indexedDB.open('а'); indexedDB.open('б'); const s = d.transaction('п').objectStore('п'); s.put({ім: $('ввід').value}, 'я'); їїСловаП(document.body, s.get('я').result.ім);", 1),
        ('бд-then', "indexedDB.open('б'); const s = d.transaction('п').objectStore('п'); s.put({ім: $('ввід').value}, 'я'); function читати(){return дб().then(d=>new Promise((рез, від)=>{ const r = s.get('я'); r.onsuccess=()=>рез(r.result); r.onerror=()=>від(r.error); }));} їїСловаП(document.body, читати().ім);", 0),
        ('каталог-писач-поля', "const fs = require('node:fs'); fs.writeFileSync('каталог.json', JSON.stringify([{ім: $('ввід').value, код: невідоме}])); async function ф(){ const д=await (await fetch('каталог.json')).json(); д.forEach(р=>назваЖінціП(document.body, р.ім)); }", 0),
        ('каталог-невідомий-писач', "async function ф(){ const д=await (await fetch('каталог.json')).json(); д.forEach(р=>назваЖінціП(document.body, р.ім)); }", 1),
        ('каталог-змішаний-писач', "const fs = require('node:fs'); fs.writeFileSync('каталог.json', JSON.stringify([{ім: $('ввід').value}])); fs.writeFileSync('каталог.json', JSON.stringify([{ім: невідоме}])); async function ф(){ const д=await (await fetch('каталог.json')).json(); д.forEach(р=>назваЖінціП(document.body, р.ім)); }", 1),
        ('каталог-інше-поле', "const fs = require('node:fs'); fs.writeFileSync('каталог.json', JSON.stringify([{ім: $('ввід').value, код: невідоме}])); async function ф(){ const д=await (await fetch('каталог.json')).json(); д.forEach(р=>назваЖінціП(document.body, р.код)); }", 1),
        ('каталог-інший-файл', "const fs = require('node:fs'); fs.writeFileSync('інший.json', JSON.stringify([{ім: $('ввід').value}])); async function ф(){ const д=await (await fetch('каталог.json')).json(); д.forEach(р=>назваЖінціП(document.body, р.ім)); }", 1),
        ('сховище-пара-контекстів', "function писати(к, з){localStorage.setItem(к, JSON.stringify(з));} function читати(к){return JSON.parse(localStorage.getItem(к));} писати('її', {т: $('ввід').value}); писати('м', {т: невідоме}); їїСловаП(document.body, читати('м').т);", 1),
        ('каталог-чуже-імя-методу', "const fs={writeFileSync(){}}; fs.writeFileSync('каталог.json', JSON.stringify([{ім: $('ввід').value}])); async function ф(){const д=await (await fetch('каталог.json')).json(); д.forEach(р=>назваЖінціП(document.body, р.ім));}", 1),
        ('поле-порожній-писач', "function ф(){const п={назви:{}}; назваЖінціП(document.body, п.назви[ід] || '');}", 1),
        ('поле-вкладений-писач', "const п={назви:{}}; п.назви[ід] = невідоме; назваЖінціП(document.body, п.назви[ід]);", 1),
        ('порожній-запас', "indexedDB.open('б'); const s = d.transaction('п').objectStore('п'); s.put({ім: $('ввід').value}, 'я'); const r = s.getAll(); (r.result || []).forEach(з=>їїСловаП(document.body, з.ім));", 0),
        ('порожній-змінна', "function читати(){ return [{ім: $('ввід').value}]; } let сп = []; сп = читати(); сп.forEach(з=>їїСловаП(document.body, з.ім));", 0),
        ('порожній-гілка', "function читати(){ return [{ім: $('ввід').value}]; } const р = читати(); (Array.isArray(р) ? р : []).forEach(з=>їїСловаП(document.body, з.ім));", 0),
        ('порожній-у-записі', "const з = {сп: []}; з.сп.push({ім: fetch('/m')}); інше(з); з.сп.forEach(х=>їїСловаП(document.body, х.ім));", 1),
        ('порожній-доповнений', "const сп = []; сп.push({ім: fetch('/m')}); сп.forEach(з=>їїСловаП(document.body, з.ім));", 1),
        ('порожній-переданий', "function заповнити(а){ а.push({ім: fetch('/m')}); } const сп = []; заповнити(сп); сп.forEach(з=>їїСловаП(document.body, з.ім));", 1),
        ('assign-останній', "const д = Object.assign({інше: 1}, {назва: $('ввід').value}); їїСловаП(document.body, д.назва);", 0),
        ('assign-перезапис', "const д = Object.assign({назва: $('ввід').value}, {назва: fetch('/m')}); їїСловаП(document.body, д.назва);", 1),
        ('assign-невідомий-аргумент', "const д = Object.assign({назва: $('ввід').value}, невідоме); їїСловаП(document.body, д.назва);", 1),
        ('assign-ніхто', "const д = Object.assign({}, {інше: 1}); їїСловаП(document.body, д.назва);", 1),
        ('spread-останній', "const б = {інше: fetch('/m')}; const д = {...б, назва: $('ввід').value}; їїСловаП(document.body, д.назва);", 0),
        ('spread-після-ключа', "const д = {назва: $('ввід').value, ...невідоме}; їїСловаП(document.body, д.назва);", 1),
        ('цикл-її', "indexedDB.open('б'); function писати(к, з){ d.transaction('кв').objectStore('кв').put(з, к); } function читати(к){ return d.transaction('кв').objectStore('кв').get(к).result; } let П = []; П = читати('п') || []; if (!П.length){ П = [{ід: 1, назва: ''}]; писати('п', П); } const а = П.find(x=>x.ід === 1); const нова = ($('ввід').value || '').trim(); if (а && нова){ а.назва = нова; писати('п', П); } П.forEach(п=>назваЖінціП(document.body, п.назва || 'Без назви'));", 0),
        ('цикл-сталий-напис', "indexedDB.open('б'); function писати(к, з){ d.transaction('кв').objectStore('кв').put(з, к); } function читати(к){ return d.transaction('кв').objectStore('кв').get(к).result; } let П = []; П = читати('п') || []; if (!П.length){ П = [{ід: 1, назва: 'мій профіль'}]; писати('п', П); } const а = П.find(x=>x.ід === 1); const нова = ($('ввід').value || '').trim(); if (а && нова){ а.назва = нова; писати('п', П); } П.forEach(п=>назваЖінціП(document.body, п.назва || 'Без назви'));", 1),
        ('цикл-сталий-push', "indexedDB.open('б'); function писати(к, з){ d.transaction('кв').objectStore('кв').put(з, к); } function читати(к){ return d.transaction('кв').objectStore('кв').get(к).result; } let П = []; П = читати('п') || []; П.push({ід: 2, назва: 'профіль ' + (П.length + 1)}); писати('п', П); const а = П.find(x=>x.ід === 1); const нова = ($('ввід').value || '').trim(); if (а && нова){ а.назва = нова; писати('п', П); } П.forEach(п=>назваЖінціП(document.body, п.назва || 'Без назви'));", 1),
        ('цикл-без-писача', "indexedDB.open('б'); function писати(к, з){ d.transaction('кв').objectStore('кв').put(з, к); } function читати(к){ return d.transaction('кв').objectStore('кв').get(к).result; } let П = []; П = читати('п') || []; писати('п', П); П.forEach(п=>назваЖінціП(document.body, п.назва || 'Без назви'));", 1),
        ('цикл-модель', "indexedDB.open('б'); function писати(к, з){ d.transaction('кв').objectStore('кв').put(з, к); } function читати(к){ return d.transaction('кв').objectStore('кв').get(к).result; } let П = []; П = читати('п') || []; П.push({ід: 2, назва: fetch('/m')}); писати('п', П); const а = П.find(x=>x.ід === 1); const нова = ($('ввід').value || '').trim(); if (а && нова){ а.назва = нова; писати('п', П); } П.forEach(п=>назваЖінціП(document.body, п.назва || 'Без назви'));", 1),
        ('цикл-лічильник', "indexedDB.open('б'); const s = d.transaction('кв').objectStore('кв'); const ч = s.get('н'); const н = (ч.result || 0) + 1; s.put(н, 'н'); document.body.textContent = '№ ' + н;", 0),
        ('носій-не-втеча', "let С = []; С.push({ім: $('ввід').value}); localStorage.setItem('с', JSON.stringify(С)); С.forEach(з=>їїСловаП(document.body, з.ім));", 0),
        ('носій-без-ключа', "function передати(з){ інше(з); } let С = []; С.push({ім: $('ввід').value}); передати(С); С.forEach(з=>їїСловаП(document.body, з.ім));", 1),
        ('псевдонім-запис', "const сп = [{ім: $('ввід').value}]; const е = сп.find(х=>х); е.ім = fetch('/m'); сп.forEach(з=>їїСловаП(document.body, з.ім));", 1),
        ('псевдонім-її', "const сп = [{ім: ''}]; for (const е of сп) е.ім = $('ввід').value; сп.forEach(з=>їїСловаП(document.body, з.ім));", 0),
        ('напис-у-полі', "const з = {ім: $('ввід').value || 'Без імені'}; їїСловаП(document.body, з.ім);", 1),
        ('порожнє-у-полі', "const з = {ім: ($('ввід').value || '').trim()}; їїСловаП(document.body, з.ім);", 0),
        ('напис-показу', "const з = {ім: $('ввід').value}; назваЖінціП(document.body, з.ім || 'Без імені');", 0),
        ('число-у-полі', "const з = {ім: $('ввід').value || 0}; їїСловаП(document.body, з.ім);", 1),
        ('null-у-полі', "const з = {ім: ($('ввід').value || '').trim() || null}; назваЖінціП(document.body, з.ім || 'Без імені');", 0),
        ('сховище-напис', "localStorage.setItem('ім', $('ввід').value); localStorage.setItem('ім', 'Типове'); їїСловаП(document.body, localStorage.getItem('ім'));", 1),
        # 11822: її ввід поза `$(…).value` — ціль події вводу, розпізнане мовлення, її слова через пробіл.
        ('ціль-вводу-її', "const та = document.createElement('textarea'); let з = ''; та.oninput = e => { з = e.target.value; }; їїСловаП(document.body, з);", 0),
        ('ціль-вводу-слухач', "const та = document.createElement('textarea'); let з = ''; та.addEventListener('input', e => { з = e.currentTarget.value; }); їїСловаП(document.body, з);", 0),
        ('ціль-вводу-чужий-поряд', "const та = document.createElement('textarea'); let з = ''; та.oninput = e => { з = e.target.value; }; fetch('/m').then(р => { з = р; }); їїСловаП(document.body, з);", 1),
        ('ціль-не-вводу', "const та = document.createElement('div'); let з = ''; та.onclick = e => { з = e.target.value; }; їїСловаП(document.body, з);", 1),
        ('мовлення-її', "const К = window.SpeechRecognition || window.webkitSpeechRecognition || null; const р = new К(); let з = ''; р.onresult = п => { з = Array.from(п.results).map(x => x[0].transcript).join(' '); }; їїСловаП(document.body, з);", 0),
        ('мовлення-не-клас', "const р = new Інше(); let з = ''; р.onresult = п => { з = Array.from(п.results).map(x => x[0].transcript).join(' '); }; їїСловаП(document.body, з);", 1),
        ('мовлення-допис', "const р = new webkitSpeechRecognition(); let з = ''; р.onresult = п => { з = 'Сказала: ' + п.results[0][0].transcript; }; їїСловаП(document.body, з);", 1),
        ('мовлення-інше-поле', "const р = new webkitSpeechRecognition(); let з = ''; р.onresult = п => { з = п.message; }; їїСловаП(document.body, з);", 1),
        ('пробіл-між-її', "їїСловаП(document.body, $('ввід').value + ' ' + $('ввід').value.replace(/\\s+/g, ' '));", 0),
        ('заміна-не-пробілу', "їїСловаП(document.body, $('ввід').value.replace(/а/g, 'б'));", 1),
        # 11780: порожній літерал під ключем запису, доповнений через тримача чи псевдонім `v = X.поле`.
        ('порожній-поле-псевдонім', "const О = {}; О.р = {сп: []}; const р = О.р; р.сп.push({ім: $('ввід').value}); (О.р.сп || []).forEach(х => їїСловаП(document.body, х.ім));", 0),
        ('порожній-поле-серіалізація', "const О = {}; О.р = {сп: []}; const р = О.р; р.сп.push({ім: $('ввід').value}); localStorage.setItem('к', JSON.stringify({сп: р.сп})); (О.р.сп || []).forEach(х => їїСловаП(document.body, х.ім));", 0),
        ('порожній-поле-чужий-поряд', "const О = {}; О.р = {сп: []}; const р = О.р; р.сп.push({ім: $('ввід').value}); р.сп.push({ім: fetch('/m')}); (О.р.сп || []).forEach(х => їїСловаП(document.body, х.ім));", 1),
        ('порожній-поле-копія', "const О = {}; О.р = {сп: []}; const к = Object.assign({}, О.р); к.сп.push({ім: невідоме}); (О.р.сп || []).forEach(х => їїСловаП(document.body, х.ім));", 1),
        ('порожній-поле-передано', "const О = {}; О.р = {сп: []}; інше(О.р.сп); (О.р.сп || []).forEach(х => їїСловаП(document.body, х.ім));", 1),
        # 11861: поле в літералі запису, який повертає функція; писачі поля — через усі змінні з її виклику.
        ('псевдонім-виклику-чужий', "const В = {}; function відп(п){ if (!В[п]) В[п] = {ім: ''}; return В[п]; } function а(п){ const вх = відп(п); const та = document.createElement('textarea'); та.oninput = e => { вх.ім = e.target.value; }; їїСловаП(document.body, вх.ім || ''); } function б(п){ const в = відп(п); в.ім = fetch('/m'); }", 1),
        ('псевдонім-виклику-її', "const В = {}; function відп(п){ if (!В[п]) В[п] = {ім: ''}; return В[п]; } function а(п){ const вх = відп(п); const та = document.createElement('textarea'); та.oninput = e => { вх.ім = e.target.value; }; їїСловаП(document.body, вх.ім || ''); } function б(п){ const в = відп(п); в.ім = $('ввід').value; }", 0),
        ('свіжий-запис-виклику', "function нове(){ const з = {ім: ''}; return з; } function а(){ const вх = нове(); вх.ім = $('ввід').value; їїСловаП(document.body, вх.ім); } function б(){ const в = нове(); в.ім = fetch('/m'); }", 0),
        # Доповнення 31.10 (11833, 11786, 11823): свій писач знімає місце, чужий поряд — лишає.
        ('сховище-цикл-її', "let С = {ім: ''}; function стан(){ return {ім: С.ім}; } function зберегти(){ localStorage.setItem('с', JSON.stringify(стан())); } function відн(з){ С = {ім: з.ім}; } відн(JSON.parse(localStorage.getItem('с'))); С.ім = $('ввід').value; їїСловаП(document.body, С.ім);", 0),
        ('сховище-цикл-чужий-поряд', "let С = {ім: ''}; function стан(){ return {ім: С.ім}; } function зберегти(){ localStorage.setItem('с', JSON.stringify(стан())); } function відн(з){ С = {ім: з.ім}; } відн(JSON.parse(localStorage.getItem('с'))); С.ім = $('ввід').value; localStorage.setItem('с', JSON.stringify({ім: fetch('/m')})); їїСловаП(document.body, С.ім);", 1),
        ('розрізнювач-свій', "const Ч = []; Ч.push({хто: 'людина', текст: $('ввід').value}); Ч.push(Object.assign({хто: 'ші', текст: fetch('/m')}, {})); Ч.forEach(р => { if (р.хто === 'ші') текстЖінціП(document.body, р.текст); else їїСловаП(document.body, р.текст); });", 0),
        ('розрізнювач-чужий-поряд', "const Ч = []; Ч.push({хто: 'людина', текст: $('ввід').value}); Ч.push({хто: 'людина', текст: fetch('/m')}); Ч.forEach(р => { if (р.хто === 'ші') текстЖінціП(document.body, р.текст); else їїСловаП(document.body, р.текст); });", 1),
        ('розрізнювач-незнаний', "const Ч = []; Ч.push({хто: 'людина', текст: $('ввід').value}); Ч.push({хто: інше(), текст: fetch('/m')}); Ч.forEach(р => { if (р.хто === 'ші') текстЖінціП(document.body, р.текст); else їїСловаП(document.body, р.текст); });", 1),
        ('розрізнювач-переписано', "const Ч = []; Ч.push({хто: 'людина', текст: $('ввід').value}); Ч.push({хто: 'ші', текст: fetch('/m')}); Ч.forEach(р => { р.хто = 'людина'; }); Ч.forEach(р => { if (р.хто === 'ші') текстЖінціП(document.body, р.текст); else їїСловаП(document.body, р.текст); });", 1),
        ('розрізнювач-копія', "function коп(р){ return {хто: р.хто, текст: р.текст}; } const Ч = []; Ч.push({хто: 'людина', текст: $('ввід').value}); Ч.push({хто: 'ші', текст: fetch('/m')}); const К = Ч.map(коп); К.forEach(р => { if (р.хто === 'ші') текстЖінціП(document.body, р.текст); else їїСловаП(document.body, р.текст); });", 0),
        ('розрізнювач-копія-чужа', "function коп(р){ return {хто: р.хто, текст: р.опис}; } const Ч = []; Ч.push({хто: 'людина', текст: $('ввід').value, опис: ''}); Ч.push({хто: 'ші', текст: fetch('/m'), опис: fetch('/m')}); const К = Ч.map(коп); К.forEach(р => { if (р.хто === 'ші') текстЖінціП(document.body, р.текст); else їїСловаП(document.body, р.текст); });", 1),
        ('map-за-імʼям-свій', "function ім(р){ return р.ім; } const С = [{ім: $('ввід').value}]; С.map(ім).forEach(т => їїСловаП(document.body, т));", 0),
        ('map-за-імʼям-чужий', "function ім(р){ return р.ім; } const С = [{ім: $('ввід').value}, {ім: fetch('/m')}]; С.map(ім).forEach(т => їїСловаП(document.body, т));", 1),
        ('масив-гілка-свій', "function відн(з){ const С = Array.isArray(з.сп) ? з.сп : []; С.forEach(х => їїСловаП(document.body, х.ім)); } відн({}); відн({сп: [{ім: $('ввід').value}]});", 0),
        ('масив-гілка-чужий', "function відн(з){ const С = Array.isArray(з.сп) ? з.сп : []; С.forEach(х => їїСловаП(document.body, х.ім)); } відн({}); відн({сп: [{ім: $('ввід').value}, {ім: fetch('/m')}]});", 1),
        ('масив-без-умови', "function відн(з){ const С = з.сп || []; С.forEach(х => їїСловаП(document.body, х.ім)); } відн({ім: 'x'}); відн({сп: [{ім: $('ввід').value}]});", 1),
        ('втеча-повернення-читання', "let С = []; const дай = () => С; С.push({ім: $('ввід').value}); function ф(сп){ return (сп || С).find(х => х); } ф(дай()); С.forEach(х => їїСловаП(document.body, х.ім));", 0),
        ('втеча-повернення-запис', "let С = []; const дай = () => С; С.push({ім: $('ввід').value}); дай().push({ім: fetch('/m')}); С.forEach(х => їїСловаП(document.body, х.ім));", 1),
        ('втеча-аргумент-запис', "let С = []; С.push({ім: $('ввід').value}); function доп(сп){ сп.push({ім: fetch('/m')}); } доп(С); С.forEach(х => їїСловаП(document.body, х.ім));", 1),
        ('назва-поза-її', "const з = {назва: $('ввід').value}; полеЕкранаП(document.body, 'textContent', з.назва);", 0),
        ('назва-поза-чужа', "const з = {назва: fetch('/m')}; полеЕкранаП(document.body, 'textContent', з.назва);", 1),
        ('мапа-свій', "const М = new Map(); М.set('к', []); М.get('к').push({ім: $('ввід').value}); for (const [к, сп] of М) сп.forEach(х => їїСловаП(document.body, х.ім));", 0),
        ('мапа-чужий-поряд', "const М = new Map(); М.set('к', []); М.get('к').push({ім: $('ввід').value}); М.get('к').push({ім: fetch('/m')}); for (const [к, сп] of М) сп.forEach(х => їїСловаП(document.body, х.ім));", 1),
        ('мапа-get-окремо', "const М = new Map(); М.set('к', []); М.get('к').push({ім: $('ввід').value}); const с = М.get('к'); с.push({ім: fetch('/m')}); for (const [к, сп] of М) сп.forEach(х => їїСловаП(document.body, х.ім));", 1),
        ('мапа-втеча', "const М = new Map(); М.set('к', []); М.get('к').push({ім: $('ввід').value}); обробити(М); for (const [к, сп] of М) сп.forEach(х => їїСловаП(document.body, х.ім));", 1),
        ('розрізнювач-не-дорівнює', "const Ч = []; Ч.push({хто: 'людина', текст: $('ввід').value}); Ч.push({хто: 'ші', текст: fetch('/m')}); Ч.forEach(р => { if (р.хто !== 'ші') їїСловаП(document.body, р.текст); else текстЖінціП(document.body, р.текст); });", 0),
        ('розрізнювач-не-дорівнює-чужий', "const Ч = []; Ч.push({хто: 'людина', текст: $('ввід').value}); Ч.push({хто: 'гість', текст: fetch('/m')}); Ч.forEach(р => { if (р.хто !== 'ші') їїСловаП(document.body, р.текст); else текстЖінціП(document.body, р.текст); });", 1),
        ('два-виклики-свій', "function ім(р){ return р.ім; } const А = [{ім: $('ввід').value}]; const Б = [{ім: $('ввід').value}]; А.map(ім).forEach(т => їїСловаП(document.body, т)); Б.map(ім).forEach(т => їїСловаП(document.body, т));", 0),
        ('два-виклики-чужий', "function ім(р){ return р.ім; } const А = [{ім: $('ввід').value}]; const Б = [{ім: fetch('/m')}]; А.map(ім).forEach(т => їїСловаП(document.body, т)); Б.map(ім).forEach(т => їїСловаП(document.body, т));", 1),
        # 11838: ід елемента зі сталого переліку чи закріпленої таблиці; поле, чиє значення санітизує браузер.
        ('перелік-ід-ключові', "const ІДИ = ['при', 'чис']; ІДИ.forEach(і => { const е = $(і); if (!е) return; е.value = fetch('/m'); });", 0),
        ('перелік-ід-видимий-поряд', "const ІДИ = ['при', 'ввід']; ІДИ.forEach(і => { const е = $(і); if (!е) return; е.value = fetch('/m'); });", 1),
        ('перелік-ід-доповнено', "const ІДИ = ['при']; ІДИ.push(інше()); ІДИ.forEach(і => { $(і).value = fetch('/m'); });", 1),
        ('перелік-ід-передано', "const ІДИ = ['при']; обробити(ІДИ); ІДИ.forEach(і => { $(і).value = fetch('/m'); });", 1),
        ('перелік-ід-колбек-масив', "const ІДИ = ['при']; ІДИ.forEach((і, н, весь) => { весь.push(інше()); $(і).value = fetch('/m'); });", 1),
        ('перелік-ід-не-перебір', "const ІДИ = ['при']; ІДИ.then(і => { $(і).value = fetch('/m'); });", 1),
        ('перелік-ід-стала', "const ІД = 'при'; $(ІД).value = fetch('/m');", 0),
        ('перелік-ід-довідник', "const ДОВІДНИК = __ДОВІДНИК_ПОКАЗУ__; const О = ДОВІДНИК.поля; const ІДИ = Object.entries(О).flatMap(([к, о]) => (о.показ || []).map(п => п[0])).sort((а, б) => а - б); for (const і of ІДИ) $(і).value = fetch('/m');", 0),
        ('перелік-ід-довідник-видимий', "const ДОВІДНИК = __ДОВІДНИК_ПОКАЗУ__; const О = ДОВІДНИК.поля_з_вводом; const ІДИ = Object.entries(О).flatMap(([к, о]) => (о.показ || []).map(п => п[0])); for (const і of ІДИ) $(і).value = fetch('/m');", 1),
        ('перелік-ід-код-між', "const ДОВІДНИК = __ДОВІДНИК_ПОКАЗУ__; const О = ДОВІДНИК.поля; змінити(О); const ІДИ = Object.entries(О).flatMap(([к, о]) => (о.показ || []).map(п => п[0])); for (const і of ІДИ) $(і).value = fetch('/m');", 1),
        ('поле-число', "$('чис').value = fetch('/m');", 0),
        ('поле-число-текст-поряд', "$('чис').value = fetch('/m'); $('текст').value = fetch('/m');", 1),
        ('каталог-python-кандидат', "async function ф(){const д=await (await fetch('каталог.json')).json(); назваЖінціП(document.body, д.name);}", 1),
    ]
    хиб = 0
    with tempfile.TemporaryDirectory() as тека:
        os.makedirs(os.path.join(тека, "показ"))
        with open(os.path.join(тека, 'показ', 'мовний_шар.js'), 'w', encoding='utf8') as ф: ф.write(точка)
        with open(os.path.join(тека, 'показ.html'), 'w', encoding='utf8') as ф:
            ф.write('<input id="ввід"><select id="ключ"></select><input type="hidden" id="при"><input type="number" id="чис">'
                    '<input type="text" id="текст">')
        os.makedirs(os.path.join(тека, "прилади"))
        with open(os.path.join(тека, 'прилади', 'експорт_показу.py'), 'w', encoding='utf8') as ф:
            ф.write("def довідник():\n    return {'поля': {'а': {'показ': [('при', 0)]}, 'б': {'показ': [('чис', 1, '18')]}, 'в': {}},\n"
                    "            'поля_з_вводом': {'а': {'показ': [('при', 0)]}, 'б': {'показ': [('ввід', 1)]}}}\n")
        with open(os.path.join(тека, 'писач.py'), 'w', encoding='utf8') as ф:
            ф.write("def запис(крамниця):\n    return {'name': крамниця['title']}\n")
        for ім, код, очікується in проби:
            with open(os.path.join(тека, 'показ', 'проба.js'), 'w', encoding='utf8') as ф: ф.write(код)
            п, стоки, _, _, _ = обчислити(тека)
            вих = [с for с in стоки if not с.обгортка and є_місцем(с)]
            ок = len(вих) == очікується
            if ім in ('цикл-сталий-напис', 'цикл-сталий-push'):
                # Місце — через сталий напис у полі її імені, а не через цикл (рішення 31.10, 11787).
                ок = ок and all('напис коду' in с.джерела and 'невідоме' not in с.джерела for с in вих)
            if ім == 'цикл-без-писача':
                ок = ок and all('невідоме' in с.джерела for с in вих)
            if ім.startswith('перелік-ід-') and очікується:
                # Лишилось з тієї причини, що в назві: видимий ід серед доведених чи перелік не доведено зовсім.
                іди = {опис_елемента(д) for с in стоки for д in с.елементи}
                ок = ок and (('input#ввід' in іди) if ім.endswith('видимий-поряд') or ім.endswith('довідник-видимий') else not іди)
            if ім == 'каталог-python-кандидат':
                ок = ок and any('писач.py:2' in д and 'недоведений' in д for с in вих for д in с.писачі)
            print('%s: %d, очікується %d — %s' % (ім, len(вих), очікується, 'так' if ок else 'НІ'))
            хиб += not ок
            if ім == 'модель-її-назва':
                # Навмисно міняємо лише рішення А: сигнал Б має зберегтися.
                всі = [с for с in стоки if not с.обгортка]
                до = шлях_б(п, всі)[0]
                for с in всі: с.ключове = True
                після = шлях_б(п, всі)[0]
                ок = bool(до) and до == після
                хиб += not ок
                print('незалежність Б від рішення А: ' + ('так' if ок else 'НІ'))
        with open(os.path.join(тека, 'показ', 'проба.js'), 'w', encoding='utf8') as ф: ф.write('')
        with open(os.path.join(тека, 'зовні.js'), 'w', encoding='utf8') as ф: ф.write('document.body.title = невідоме;')
        with open(os.path.join(тека, 'показ.html'), 'w', encoding='utf8') as ф:
            ф.write('<script src="зовні.js"></script><script>document.body.textContent = невідоме;</script>')
        _, стоки, _, _, _ = обчислити(тека)
        ок = {пункт(с) for с in стоки if є_місцем(с)} == {'П1', 'П5'}
        хиб += not ок
        print('скрипт поза показом і вбудований скрипт: ' + ('так' if ок else 'НІ'))
        with open(os.path.join(тека, 'розмітка.py'), 'w', encoding='utf8') as ф: ф.write("текст = '<b>%s</b>' % дані")
        ок = джерела_розмітки(тека) == [('розмітка.py', 1)]
        хиб += not ок
        print('джерело розмітки Python: ' + ('так' if ок else 'НІ'))
    print('самоперевірка: %d випадків, хиб %d' % (len(проби) + 3, хиб))
    return not хиб


def main():
    """Друкує місця, пояснення звірки й підсумкове число для храповика."""
    if "--самоперевірка" in sys.argv:
        sys.exit(0 if самоперевірка() else 1)
    п, стоки, обгортки, динаміка, стоки_служб = обчислити(ТУТ)
    місця, сталі, числа, точкою, внутрішні, ключі, її_слова, назви = {}, {}, {}, 0, 0, {}, {}, {}
    for с in sorted(стоки, key=lambda s: (відображене(s.мод.шлях), s.мод.рядок(s.і))):
        ключ = подія(с) + (с.а, с.б)
        if с.обгортка: внутрішні += 1; continue
        if с.ключове: ключі.setdefault(ключ, с); continue
        if 'її' in с.джерела and not є_місцем(с): її_слова.setdefault(ключ, с); continue
        if є_місцем(с): місця.setdefault(ключ, с)
        elif с.джерела <= {"стале", "перевірено", "вузол", "елемент"}: сталі.setdefault(ключ, с)
        elif "назва" in с.джерела: назви.setdefault(ключ, с)
        else: числа.setdefault(ключ, с)
        if с.точка and not є_місцем(с): точкою += 1
    за_пунктом = {}
    for с in місця.values():
        р = за_пунктом.setdefault(пункт(с), [0, 0, 0]); р[0] += 1; р[1 if "модель" in с.джерела else 2] += 1
    опис = {"П1": "запис тексту в DOM (textContent, value, placeholder, title, alt, createTextNode, setAttribute, alert)",
            "П2": "розмітка (innerHTML, outerHTML, insertAdjacentHTML)",
            "П3": "крізь обгортку вузла (`ел(тег, клас, текст)` і подібні: параметр лягає в DOM)",
            "П4": "вставка тексту вузлом (append, replaceChildren, … з текстовим аргументом)",
            "П5": "вбудований скрипт `показ.html` (будь-який запис П1–П4)",
            "П6": "розмітка поза `показ/` і скриптами з динамічним маркером",
            "П7": "вхід точки виходу з не своїм текстом (`назваЖінціП`: код кольору, ключ, текст моделі, невідомий тип; `їїСловаП`: не її слова)"}
    def рядок_місця(с, показувати_сталі=False):
        """Форматує місце з пунктом класу та доведеним походженням."""
        ім = відображене(с.мод.шлях); л = с.мод.рядок(с.і)
        чому = 'походження: ' + ', '.join(sorted(с.джерела)) + '; договір: ' + с.вхід
        чому += '; ' + ('писач недоведений' if писач(с) == 'недоведений' else 'писач-' + писач(с))
        вираз = текст_токенів(с.мод.ток, с.а, с.б)
        return "%s:%d · %s%s · %s: %s" % (ім, л, пункт(с), "" if пункт(с) == с.вид else "/" + с.вид, чому, вираз)
    for с in місця.values(): print(рядок_місця(с))
    if '--писачі' in sys.argv:
        for с in sorted(стоки, key=lambda с: (с.мод.шлях, с.і, с.а)):
            if с.обгортка or с.ключове:
                continue
            print(('місце · ' if є_місцем(с) else 'не місце · ') + рядок_місця(с))
            for доказ in с.писачі:
                print('  писач · ' + доказ)
        for с in sorted(стоки, key=lambda с: (с.мод.шлях, с.і, с.а)):
            if с.ключове and not с.обгортка:
                print('ключ · %s:%d · %s · елементи: %s' % (відображене(с.мод.шлях), с.мод.рядок(с.і), с.чим,
                                                          ', '.join(map(опис_елемента, с.елементи)) or 'за записом'))
    групи_писачів = {'продукт': 0, 'жінка': 0, 'недоведений': 0}
    for с in місця.values():
        групи_писачів[писач(с)] += 1
    print('— місця за писачем: ' + ' · '.join('%s %d' % пара for пара in групи_писачів.items()))
    for х in динаміка: print("%s · П6 · динамічний маркер у розмітці" % х)
    if "--сталі" in sys.argv:
        for с in сталі.values(): print("стале ·", рядок_місця(с))
    if "--збіг" in sys.argv:
        б_стоки, зараж = шлях_б(п, [с for с in стоки if not с.обгортка])
        а_т = {подія(с) for с in місця.values()}
        а_всі = {подія(с) for с in місця.values()}
        пояснення = {}
        for с in стоки:
            пояснення.setdefault(подія(с), set()).add("ключ" if с.ключове else ", ".join(sorted(с.джерела)))
        print("— збіг шляхів: А (усі місця): %d · Б (джерело досягає стоку): %d · спільних: %d · заражених ключів Б: %d" % (len(а_т), len(б_стоки), len(а_т & б_стоки), зараж))
        for х in sorted(б_стоки - а_т):
            print("  лише Б · %s:%d · %s · рішення А: %s" % (х[0], х[1], х[2], "; ".join(sorted(пояснення.get(х, {"невідоме"})))) )
        for х in sorted(а_т - б_стоки):
            print("  лише А · %s:%d · %s" % х)
        ключі_py = set()
        for ф in os.listdir(ТУТ):
            if ф.endswith(".py") and not ф.startswith(("тест", "проба")):
                к = прочитати(os.path.join(ТУТ, ф))
                ключі_py |= set(re.findall(r"[\"']([^\W\d][\w]{2,40})[\"']\s*:", к)) | set(re.findall(r"\[[\"']([^\W\d][\w]{2,40})[\"']\]\s*=(?!=)", к))
        у_стоках = {}
        for с in місця.values():
            for v in позиції_значення(с.мод.ток, с.мод.пар, с.а, с.б):
                if isinstance(v, tuple) and v[0] == "м" and v[1] in ключі_py:
                    у_стоках.setdefault(v[1], set()).add("%s:%d" % (відображене(с.мод.шлях), с.мод.рядок(с.і)))
        print("— поля, які Python кладе в пакет і які екран пише в стоки-місця: %d полів, %d місць" % (len(у_стоках), len(set().union(*у_стоках.values()) if у_стоках else ())))
        for ім in sorted(у_стоках, key=lambda x: -len(у_стоках[x])): print("  %s · %d" % (ім, len(у_стоках[ім])))
        поля = set()
        for ф in os.listdir(ТУТ):
            if ф.endswith(".py"):
                поля |= set(re.findall(r"[\"'](\w+_жінці)[\"']", прочитати(os.path.join(ТУТ, ф))))
        читання = {}
        for м in п.модулі:
            for і, x in enumerate(м.ток):
                if x[0] == "id" and x[1] in поля and і >= 1 and м.ток[і - 1][1] in (".", "?.") or (x[0] == "str" and x[1] in поля):
                    читання.setdefault(x[1], []).append("%s:%d" % (відображене(м.шлях), м.рядок(і)))
        print("— поля *_жінці, які кладе Python: %d · читає екран: %d" % (len(поля), len(читання)))
        for ім in sorted(поля): print("  %s · %s" % (ім, ", ".join(читання.get(ім, ["екран не читає"]))[:140]))
    print("— підсумки за пунктами класу (місць · з них джерело моделі T · інші U):")
    всього = 0
    for к in ("П1", "П2", "П3", "П4", "П5", "П7"):
        р = за_пунктом.get(к, [0, 0, 0]); всього += р[0]
        print("  %s · %d · T %d · U %d · %s" % (к, р[0], р[1], р[2], опис[к]))
    print("  П6 · %d · %s" % (len(динаміка), опис["П6"])); всього += len(динаміка)
    викликів = sum(1 for м in п.модулі for і, x in enumerate(м.ток) if x[0] == "id" and x[1] in ТОЧКА and і + 1 < len(м.ток)
                   and м.ток[і + 1][1] == "(" and not (і >= 1 and м.ток[і - 1][1] == "function"))
    print("— викликів точки виходу (`текстЖінціП`, `збійЖінціП`): %d" % викликів)
    print("— поза місцями: ключі `.value` (option, select, приховані, числові й кольорові поля) %d · її слова дослівно %d · назви з полів даних у входах точки %d · записів у модулі точки виходу %d"
          % (len(ключі), len(її_слова), len(назви), п.у_точці))
    if "--ключі" in sys.argv:
        for с in list(ключі.values()) + list(її_слова.values()): print("не місце ·", рядок_місця(с).replace("[1.5]", "її слова"))
    print("— поза місцями: сталих написів %d · чисел %d · крізь точку виходу %d · внутрішніх записів обгорток %d (обгортки: %s)"
          % (len(сталі), len(числа), точкою, внутрішні, ", ".join("%s(%s)" % (ім, ",".join(map(str, sorted(н)))) for ім, н in sorted(обгортки.items())) or "—"))
    служб = {подія(с) + (с.а,) for с in стоки_служб if є_місцем(с) and not с.обгортка}
    print("— поза екраном жінки (службові сторінки власника `проба.html`, `показ_зонд.html`, не рахуються): %d" % len(служб))
    за_чим = {}
    for с in місця.values(): за_чим[с.чим] = за_чим.get(с.чим, 0) + 1
    print("— за способом запису (місць): " + " · ".join("%s %d" % (к, v) for к, v in sorted(за_чим.items(), key=lambda x: -x[1])))
    if "--файли" in sys.argv:
        рахунок = {}
        for с in стоки:
            if not с.обгортка: рахунок.setdefault(відображене(с.мод.шлях), [0, 0])[0 if є_місцем(с) else 1] += 1
        for ф in sorted(os.listdir(os.path.join(ТУТ, "показ"))):
            if ф.endswith(".js"): рахунок.setdefault("показ/" + ф, [0, 0])
        print("— по файлах (місць · решта стоків):")
        for ф, (a, b) in sorted(рахунок.items()): print("  %s · %d · %d" % (ф, a, b))
        кандидати = джерела_розмітки(ТУТ)
        print('— складання HTML поза показом: кандидати до перевірки досяжності (не додаткові стоки):')
        for ф, ряд in кандидати: print('  %s:%d' % (ф, ряд))
    if "--довідник" in sys.argv:
        _, стоки2, _, _, _ = обчислити(ТУТ, ())
        м2 = {подія(с) + (с.а, с.б) for с in стоки2 if not с.обгортка and є_місцем(с)}
        print("— ДОВІДНИК (`__ДОВІДНИК_ПОКАЗУ__`, таблиці продукту з репозиторію) лічено сталим написом; якби він був даними: %d місць, а так %d"
              % (len(м2), len(місця)))
    print("— ід елементів із таблиць (`$(і)` з переліку): ДОВІДНИК — %s" % (
        "експорт дерева `прилади/експорт_показу.довідник()`" if п.довідник is not НЕВІДОМО else "експорт не зібрався, іди з нього невідомі"))
    print("місць: %d" % всього)


if __name__ == "__main__":
    import threading
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.setrecursionlimit(10000)
    threading.stack_size(16 * 1024 * 1024)
    код = []
    def запуск():
        """Передає код завершення й винятки з потоку CLI."""
        try: main()
        except SystemExit as вихід:
            код.append(вихід.code or 0)
        except BaseException:
            import traceback; traceback.print_exc(); код.append(1)
    потік = threading.Thread(target=запуск)
    потік.start(); потік.join()
    sys.exit(код[0] if код else 0)
