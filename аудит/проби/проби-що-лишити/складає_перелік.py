#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Складає перелік проб і приладів, що лишаються (наряд `Проби-що-лишити`, частина 1).

Одна команда з кореня репозиторію, на будь-якому `main`:

    python3 аудит/проби/проби-що-лишити/складає_перелік.py

Пише поруч із собою: ПЕРЕЛІК.tsv (файл, причина), ПАДАЄ.tsv (проба з очікуваним результатом, що на `main` падає,
і перший рядок помилки), ЗАПУСК.tsv (кожен запуск (г): файл, результат, секунди), ПІДСУМОК.txt (числа «було»).
Нічого не видаляє й не лагодить. Проби, що кличуть модель чи мережу, не запускає (причина «мережа» у ПІДСУМОК), решту
запускає без мережі (`unshare -rn`), у `джерела/`, не довше за ліміт. Потрібні `джерела/node_modules` (`npm ci`) для JS.

Обсяг: `.py .js .cjs .mjs .sh` у `джерела/проби/` і `джерела/прилади/` (рекурсивно). Ознаки лишити:
(а) workflow чи скрипт у `.github/` називає файл за шляхом чи glob-ом; (б) його названо в чинному файлі правил
(`ФАЙЛИ_ПЕРЕЛІКУ` приладу `корінь_пк_дотримання.py` + `ПРАВИЛА_БУДЬ_ДЕ` і `ДОДАТКИ_ПРАВИЛ` з `документ_без_коду.py`), у
рядку `прилад:`/`база:` паспорта `аудит/корені/*.md`, в наряді `аудит/наряди/*.md` (крім власного) чи в
`аудит/проби/живі_порядок.md`; (в) його імпортує те, що лишається (код поза обсягом і лишені файли обсягу: `import`/`require` скрізь, а рядок-шлях
— поза `аудит/`; скрипти `аудит/` — докази звітів, їхні переліки проб рядками не рахуються);
(г) проба з `assert` чи виходом із кодом помилки, що на `main` запускається й проходить (лише `проби/`).
Згадка — токен-шлях: повний шлях, шлях без `джерела/`, хвіст шляху чи голе ім_я файлу (надлишок безпечний: файл
лишиться); glob (`*`) рахується лише з workflow, бо в правилах і нарядах glob описує клас, а не називає файл.
"""
import argparse
import ast
import concurrent.futures
import fnmatch
import os
import re
import subprocess
import sys
import time

ТЕКА = os.path.dirname(os.path.abspath(__file__))
КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(ТЕКА)))
ОБСЯГ = ("джерела/проби", "джерела/прилади")
РОЗШИРЕННЯ = (".py", ".js", ".cjs", ".mjs", ".sh")
РОЗДІЛЬНИКИ = re.compile(r"[\s'\"`()\[\]{},;:=|<>#]+")
ВЛАСНИЙ_НАРЯД = "аудит/наряди/Проби-що-лишити.md"
МЕРЕЖА = re.compile(r"urllib\.request|import requests|from requests|http\.client|import socket|lyusterko|"
                    r"generativelanguage|ollama|11434|API_KEY|anthropic|XMLHttpRequest|\bfetch\(|playwright|chromium|"
                    r"nvidia-smi|llama|gemini_|openai|api\.github|raw\.githubusercontent", re.I)


def git(*арг):
    return subprocess.run(["git", "-C", КОРІНЬ, "-c", "core.quotepath=false", *арг], capture_output=True, text=True,
                          check=True).stdout


def читати(шлях):
    try:
        with open(os.path.join(КОРІНЬ, шлях), encoding="utf-8", errors="replace") as ф:
            return ф.read()
    except OSError:
        return ""


def файли_обсягу(усі):
    return sorted(ш for ш in усі if ш.endswith(РОЗШИРЕННЯ) and any(ш.startswith(т + "/") for т in ОБСЯГ))


def токени(текст, дозволити_glob):
    for т in РОЗДІЛЬНИКИ.split(текст):
        т = т.rstrip(".*") if False else т.rstrip(".")
        if not т.endswith(РОЗШИРЕННЯ) or len(т) > 300:
            continue
        т = т[2:] if т.startswith("./") else т
        т = т.lstrip("/")
        if "*" in т or "?" in т:
            if дозволити_glob:
                yield т
        else:
            yield т


def збіг(токен, шлях, glob):
    """Токен називає шлях: повний, без `джерела/`, хвіст за межею `/` чи голе ім_я."""
    if glob:
        return any(fnmatch.fnmatchcase(в, токен) or fnmatch.fnmatchcase(в, "*/" + токен)
                   for в in (шлях, шлях[len("джерела/"):]))
    return шлях == токен or шлях.endswith("/" + токен)


def названі(тексти, обсяг, glob):
    """{файл обсягу: перше джерело, що його називає}."""
    за_іменем = {}
    for ш in обсяг:
        за_іменем.setdefault(os.path.basename(ш), []).append(ш)
    знайдено = {}
    for джерело, текст in тексти:
        for т in set(токени(текст, glob)):
            if "*" in т or "?" in т:
                кандидати = обсяг
            else:
                кандидати = за_іменем.get(os.path.basename(т), [])
            for ш in кандидати:
                if ш not in знайдено and збіг(т, ш, "*" in т or "?" in т):
                    знайдено[ш] = джерело
    return знайдено


def літерал(текст, ім_я):
    for в in ast.parse(текст).body:
        if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == ім_я for ц in в.targets):
            return ast.literal_eval(в.value)
    return None


def файли_правил():
    пк = літерал(читати("джерела/прилади/корінь_пк_дотримання.py"), "ФАЙЛИ_ПЕРЕЛІКУ") or {}
    д = читати("джерела/прилади/документ_без_коду.py")
    будь_де = літерал(д, "ПРАВИЛА_БУДЬ_ДЕ") or set()
    додатки = літерал(д, "ДОДАТКИ_ПРАВИЛ") or set()
    return sorted(set(пк.values()) | set(будь_де) | set(додатки))


def імпорти_py(шлях, текст):
    """Шляхи, які може означати import у `.py`: відносні до теки файлу, до `джерела/`, `проби/`, `прилади/`."""
    try:
        дерево = ast.parse(текст)
    except (SyntaxError, ValueError, RecursionError):
        return set()
    імена = set()
    for в in ast.walk(дерево):
        if isinstance(в, ast.Import):
            імена |= {а.name for а in в.names}
        elif isinstance(в, ast.ImportFrom) and not в.level:
            імена.add(в.module or "")
            імена |= {(в.module or "") + "." + а.name for а in в.names}
    тека = os.path.dirname(шлях)
    бази = {тека, "джерела", "джерела/проби", "джерела/прилади", ""}
    return {os.path.normpath(os.path.join(б, ім.replace(".", "/") + ".py")) for ім in імена if ім for б in бази}


def імпорти_js(шлях, текст):
    тека = os.path.dirname(шлях)
    р = set()
    for м in re.findall(r"""(?:require\(|from\s+|import\s*\()\s*['"](\.[^'"]+)['"]""", текст):
        для = os.path.normpath(os.path.join(тека, м))
        р |= {для, для + ".js", для + ".cjs", для + ".mjs"}
    return р


def очікуваний_результат_py(текст):
    try:
        дерево = ast.parse(текст)
    except (SyntaxError, ValueError, RecursionError):
        return False
    for в in ast.walk(дерево):
        if isinstance(в, ast.Assert):
            return True
        if isinstance(в, ast.Raise) and в.exc is not None:
            ім = в.exc.func if isinstance(в.exc, ast.Call) else в.exc
            if getattr(ім, "id", "") in ("AssertionError", "SystemExit"):
                return True
        if isinstance(в, ast.Call):
            ф = в.func
            ім = ф.attr if isinstance(ф, ast.Attribute) else getattr(ф, "id", "")
            if ім in ("exit", "_exit") and в.args:
                а = в.args[0]
                if not (isinstance(а, ast.Constant) and а.value in (0, None)):
                    return True
            if ім == "SystemExit" and в.args:
                return True
    return False


def очікуваний_результат_js(текст):
    return bool(re.search(r"\bassert\b|process\.exit\(\s*(?!0\s*\))|\bthrow\b", текст))


def запустити(шлях, ліміт):
    розш = os.path.splitext(шлях)[1]
    # у `джерела/`: проби самі додають батьківську теку в шлях імпорту, відносні відкриття файлів — від неї
    відносний = os.path.relpath(os.path.join(КОРІНЬ, шлях), os.path.join(КОРІНЬ, "джерела"))
    команда = ["node", відносний] if розш in (".js", ".cjs", ".mjs") else ["python3", відносний]
    середовище = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", NODE_PATH="node_modules",
                      HTTPS_PROXY="", HTTP_PROXY="", https_proxy="", http_proxy="")
    пуск = time.time()
    try:
        р = subprocess.run(["unshare", "-rn", *команда], cwd=os.path.join(КОРІНЬ, "джерела"), env=середовище,
                           capture_output=True, text=True, timeout=ліміт, stdin=subprocess.DEVNULL,
                           errors="replace")
        код, вихід = р.returncode, (р.stderr.strip() or р.stdout.strip())
        if код in (137, 143, -9, -15):
            код, вихід = -2, "вбито (пам'ять чи сигнал), код %d" % р.returncode
    except subprocess.TimeoutExpired:
        код, вихід = -1, "ліміт %d с" % ліміт
    рядки = [р for р in вихід.splitlines() if р.strip()]
    помилка = ""
    if код:
        # перший рядок помилки: рядок виняткa (останній у traceback) — найкоротша причина
        помилка = рядки[-1] if рядки else "код виходу %d без виводу" % код
    return шлях, код, round(time.time() - пуск, 1), помилка.replace("\t", " ")[:300]


def головна():
    п = argparse.ArgumentParser()
    п.add_argument("--ліміт", type=int, default=20, help="секунд на запуск однієї проби")
    п.add_argument("--потоки", type=int, default=3)
    п.add_argument("--кеш", help="файл з уже виконаними запусками (продовження після обриву); не в репозиторії")
    п.add_argument("--бюджет", type=int, default=0, help="секунд на запуски за один виклик; вичерпано — вихід 3, повтор продовжує")
    п.add_argument("--без-запуску", action="store_true", help="лише (а)–(в): перелік неповний, для налагодження")
    а = п.parse_args()

    усі = git("ls-files", "-z").split("\0")
    усі = [ш for ш in усі if ш]
    обсяг = файли_обсягу(усі)
    проби = [ш for ш in обсяг if ш.startswith("джерела/проби/")]
    прилади = [ш for ш in обсяг if ш.startswith("джерела/прилади/")]
    причини = {}

    def додати(ш, причина):
        причини.setdefault(ш, []).append(причина)

    # (а) workflow і скрипти в .github/
    гх = [ш for ш in усі if ш.startswith(".github/") and ш.endswith((".yml", ".yaml", ".sh", ".py"))]
    def без_коментарів(текст):  # рядок `# …` чи хвіст ` # …` — не виклик
        return re.sub(r"(?m)(^|\s)#.*$", " ", текст)

    for ш, дж in названі([(д, без_коментарів(читати(д))) for д in гх], обсяг, True).items():
        додати(ш, "а: " + дж)

    # (б) чинні файли правил, паспорти, наряди, живі_порядок
    джерела_б = [(д, читати(д)) for д in файли_правил() if д in усі or os.path.exists(os.path.join(КОРІНЬ, д))]
    джерела_б.append(("аудит/проби/живі_порядок.md", читати("аудит/проби/живі_порядок.md")))
    джерела_б += [(д, читати(д)) for д in усі if д.startswith("аудит/наряди/") and д.endswith(".md")
                  and д != ВЛАСНИЙ_НАРЯД]
    паспорти = []
    for д in усі:
        if д.startswith("аудит/корені/") and д.count("/") == 2 and д.endswith(".md"):
            рядки = [р for р in читати(д).splitlines() if re.match(r"(прилад|база):", р)]
            паспорти.append((д, "\n".join(рядки)))
    for ш, дж in названі(джерела_б + паспорти, обсяг, False).items():
        додати(ш, "б: " + дж)

    # (в) імпорт чи виклик із коду поза обсягом і з лишених файлів обсягу — до нерухомої точки
    поза = [ш for ш in усі if ш.endswith((".py", ".js", ".cjs", ".mjs", ".sh", ".ps1", ".html"))
            and ш not in set(обсяг) and not ш.startswith("джерела/node_modules/")]
    за_іменем = {}
    for ш in обсяг:
        за_іменем.setdefault(os.path.basename(ш), []).append(ш)
    множина = set(обсяг)

    def рядки_коду(ш, текст):
        """Рядкові літерали коду без коментарів і докстрінгів: імпорт чи виклик за назвою, а не проза про файл."""
        if ш.endswith(".py"):
            try:
                дерево = ast.parse(текст)
            except (SyntaxError, ValueError, RecursionError):
                return текст
            докстрінги = set()
            for в in ast.walk(дерево):
                if isinstance(в, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and в.body:
                    п = в.body[0]
                    if isinstance(п, ast.Expr) and isinstance(п.value, ast.Constant):
                        докстрінги.add(id(п.value))
            return "\n".join(в.value for в in ast.walk(дерево) if isinstance(в, ast.Constant)
                             and isinstance(в.value, str) and id(в) not in докстрінги)
        if ш.endswith((".js", ".cjs", ".mjs")):
            без = re.sub(r"/\*.*?\*/", " ", текст, flags=re.S)
            без = re.sub(r"(?m)^\s*//.*$", " ", без)
            return "\n".join(м[1:-1] for м in re.findall(r"""'[^'\n]*'|"[^"\n]*"|`[^`]*`""", без))
        return текст

    def залежності(ш):
        текст = читати(ш)
        р = set()
        if ш.endswith(".py"):
            р |= {х for х in імпорти_py(ш, текст) if х in множина}
        if ш.endswith((".js", ".cjs", ".mjs")):
            р |= {х for х in імпорти_js(ш, текст) if х in множина}
        if ш.startswith("аудит/"):  # докази звітів: їхній перелік проб у рядках — не імпорт, лише import/require
            р.discard(ш)
            return р
        for т in set(токени(рядки_коду(ш, текст), False)):
            for к in за_іменем.get(os.path.basename(т), []):
                if збіг(т, к, False):
                    р.add(к)
        р.discard(ш)
        return р

    граф = {}
    джерела_в = {}
    for ш in поза:
        for х in залежності(ш):
            джерела_в.setdefault(х, ш)
    for ш in обсяг:
        граф[ш] = залежності(ш)

    def замкнути(лишені):
        черга = list(лишені)
        вже = set(лишені)
        ім = {}
        while черга:
            ш = черга.pop()
            for х in граф.get(ш, ()):
                ім.setdefault(х, ш)
                if х not in вже:
                    вже.add(х)
                    черга.append(х)
        return вже, ім

    for х, дж in джерела_в.items():
        додати(х, "в: " + дж)
    лишені, ім = замкнути(set(причини))
    for х, дж in ім.items():
        if "в: " + дж not in причини.get(х, []) and not any(р.startswith("а") or р.startswith("б") for р in причини.get(х, [])):
            додати(х, "в: " + дж)
    # у файлів, лишених лише за (в) від проби, що вилетить, причина лишається (нерухома точка нижче)

    # (г) очікуваний результат і запуск
    кандидати = []
    мережа = []
    без_очікування = []
    for ш in проби:
        if ш in лишені:
            continue
        текст = читати(ш)
        є = очікуваний_результат_js(текст) if ш.endswith((".js", ".cjs", ".mjs")) else очікуваний_результат_py(текст)
        if not є:
            без_очікування.append(ш)
        elif МЕРЕЖА.search(текст):
            мережа.append(ш)
        elif ш.endswith(".sh"):
            без_очікування.append(ш)
        else:
            кандидати.append(ш)
    результати = []
    падає = []
    не_відпрацювали = []
    if not а.без_запуску:
        з_початку = set(git("status", "--porcelain", "-uall").splitlines())
        готові = {}
        if а.кеш and os.path.exists(а.кеш):
            for р in open(а.кеш, encoding="utf-8").read().splitlines():
                ч = р.split("\t")
                if len(ч) == 4:
                    ш_, к_, с_, п_ = ч[0], int(ч[1]), float(ч[2]), ч[3]
                    if к_ == 0 and с_ > а.ліміт:
                        к_, п_ = -1, "ліміт %d с" % а.ліміт
                    готові[ш_] = (ш_, к_, с_, п_)
        початок = time.time()
        залишок = [ш for ш in кандидати if ш not in готові]
        with concurrent.futures.ThreadPoolExecutor(а.потоки) as пул:
            for р in пул.map(lambda ш: запустити(ш, а.ліміт) if not а.бюджет or time.time() - початок < а.бюджет
                             else None, залишок):
                if р:
                    готові[р[0]] = р
                    if а.кеш:
                        with open(а.кеш, "a", encoding="utf-8") as к:
                            к.write("%s\t%s\t%s\t%s\n" % р)
        if len(готові) < len(кандидати):
            print("запущено %d з %d, повторіть команду" % (len(готові), len(кандидати)), file=sys.stderr)
            sys.exit(3)
        результати = [готові[ш] for ш in кандидати]
        після = set(git("status", "--porcelain", "-uall").splitlines())
        зміни = sorted(після - з_початку)
        for ш, код, сек, пом in результати:
            if код == 0:
                додати(ш, "г: assert чи код виходу, запуск без мережі — проходить (%s с)" % сек)
            elif код < 0:
                не_відпрацювали.append((ш, пом))
            else:
                падає.append((ш, пом))
        if зміни:
            print("УВАГА: проби змінили дерево:", *зміни[:20], sep="\n  ", file=sys.stderr)
    лишені, ім = замкнути(set(причини))
    for х, дж in ім.items():
        if х not in причини:
            додати(х, "в: " + дж)

    лишені = set(причини)
    рядки = []
    for ш in обсяг:
        if ш in лишені:
            рядки.append("%s\t%s" % (ш, "; ".join(причини[ш][:3]) + ("; …" if len(причини[ш]) > 3 else "")))
    for ф, вміст in (("ПЕРЕЛІК.tsv", "файл\tпричина\n" + "\n".join(рядки) + "\n"),
                     ("ПАДАЄ.tsv", "файл\tперший рядок помилки\n" + "".join("%s\t%s\n" % к for к in падає)),
                     ("НЕ_ВІДПРАЦЮВАЛИ.tsv", "файл\tпричина\n" + "".join("%s\t%s\n" % к for к in не_відпрацювали)),
                     ("ЗАПУСК.tsv", "файл\tкод\tсекунд\tперший рядок помилки\n" + "".join(
                         "%s\t%s\t%s\t%s\n" % р for р in результати))):
        with open(os.path.join(ТЕКА, ф), "w", encoding="utf-8", newline="\n") as вихід:
            вихід.write(вміст)

    нижче = {"а": 0, "б": 0, "в": 0, "г": 0}
    for ш in лишені:
        нижче[причини[ш][0][0]] += 1
    ш_проби = [ш for ш in проби if ш in лишені]
    ш_приладів = [ш for ш in прилади if ш in лишені]
    верх = len([ш for ш in проби if ш.count("/") == 2])
    підсумок = [
        "обсяг: %s" % ", ".join(ОБСЯГ),
        "файлів коду в обсязі (.py .js .cjs .mjs .sh, рекурсивно): проби %d, прилади %d" % (len(проби), len(прилади)),
        "  з них у теці проб без підтек: %d; .py: %d; .js: %d" % (верх, len([ш for ш in проби if ш.endswith(".py")]),
                                                              len([ш for ш in проби if ш.endswith(".js")])),
        "лишається: проби %d, прилади %d (усього %d)" % (len(ш_проби), len(ш_приладів), len(лишені)),
        "  перша причина: а %d, б %d, в %d, г %d" % (нижче["а"], нижче["б"], нижче["в"], нижче["г"]),
        "на видалення: проби %d, прилади %d" % (len(проби) - len(ш_проби), len(прилади) - len(ш_приладів)),
        "кандидатів (г) (assert чи код виходу, поза а–в): %d; проходить %d, падає %d, не відпрацювали за ліміт чи пам'ять %d" % (
            len(кандидати), len(кандидати) - len(падає) - len(не_відпрацювали), len(падає), len(не_відпрацювали)),
        "не запущено — мережа чи модель у тексті: %d; без очікуваного результату (друкують факт): %d" % (
            len(мережа), len(без_очікування)),
        "  мережа: " + ", ".join(мережа[:5]) + (" …" if len(мережа) > 5 else ""),
        "проб, що імпортують модуль продукту (import за назвою з джерела/) серед усіх: %d, серед лишених: %d" % (
            len(продуктові(проби, усі)), len(продуктові(ш_проби, усі))),
    ]
    with open(os.path.join(ТЕКА, "ПІДСУМОК.txt"), "w", encoding="utf-8", newline="\n") as ф:
        ф.write("\n".join(підсумок) + "\n")
    print("\n".join(підсумок))


def продуктові(список, усі):
    модулі = {os.path.splitext(os.path.basename(ш))[0] for ш in усі
              if ш.startswith("джерела/") and ш.count("/") == 1 and ш.endswith(".py")}
    р = []
    for ш in список:
        if not ш.endswith(".py"):
            continue
        try:
            дерево = ast.parse(читати(ш))
        except (SyntaxError, ValueError, RecursionError):
            continue
        for в in ast.walk(дерево):
            імена = [а.name for а in в.names] if isinstance(в, ast.Import) else (
                [в.module or ""] if isinstance(в, ast.ImportFrom) and not в.level else [])
            if any(і.split(".")[0] in модулі for і in імена):
                р.append(ш)
                break
    return р


if __name__ == "__main__":
    головна()
