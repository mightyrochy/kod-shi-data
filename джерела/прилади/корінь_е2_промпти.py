# -*- coding: utf-8 -*-
"""прилади/корінь_е2_промпти.py — прилад кореня Е2-промпти: скільки місць коду порушують інваріант
«вимога до моделі — в одному місці» (паспорт `аудит/корені/Е2-промпти.md`, «Клас місць»).

ЧОМУ ЦЕ Є. Прилад #2227 (`промпти_одне_джерело.py`) бачив 25 з 36 промптів і лічив лише збирач. Ядро («Причини»):
місця кореня лічить прилад за класом із паспорта, який до виправлення написала не та сесія, що лагодить; храповик у CI
не дає числу рости. Цей прилад береться від УСІХ місць, де код дає моделі текст, а не від одного збирача.

КЛАС (з паспорта як правило). Місце — вимога до моделі (речення, що велить їй щось робити чи не робити: зміст, формат,
тон, мова) у тексті, який код шле моделі. Місце порушує інваріант, якщо вимога:
  1. повторена: те саме речення (або те саме іншими словами) стоїть у ≥ 2 місцях коду, чи двічі в одному зібраному
     промпті;
  2. каже формат відповіді словами, а не фразою реєстру (`фрази_формату`, `схема_відповіді.фраза_формату`);
  3. дублює те, що тримає код: перелік значень, ключів схеми чи межа, що вже є в коді;
  4. суперечить іншій вимозі того самого промпту (ознаки: протилежна полярність при тих самих словах);
  5. довжина: кожен промпт має бути коротший, ніж ДО (`база:` — довжини ДО); не коротший, чи довший за ДО — місце.

ДВА ШЛЯХИ (наряд Е2-промпти-прилад, мірило «а»):
  А — від місць відправлення: модулі, що пишуть `Оголошення(` чи несуть транспорт моделі, їхні сталі, функції-збирачі й
      усе, на що вони посилаються (за іменем, через модулі); JS-літерали з англійською вимогою чи в полі `text/content/
      system/prompt`; зібрані оголошення (імпорт) для довжин і суперечностей;
  Б — від текстів: КОЖЕН літерал будь-якого коду репозиторію (py, js, html), що виглядає вимогою до моделі; місце Б, якого
      нема в А, друкується з причиною «поза А» — це звірка, а не лічба.

Запуск із кореня репозиторію:
  python3 -W ignore джерела/прилади/корінь_е2_промпти.py [--корінь ШЛЯХ] [--база аудит/корені/Е2-промпти-довжини.json]
      [--деталі] [--звірка] [--записати-базу ШЛЯХ] [--json ВИХІД]
Друкує перелік місць `файл:рядок · пункт N · чому`, підсумки за пунктами й останній рядок `місць: <N>`; код 0.
Нічого не пише в репозиторій, крім `--записати-базу` (довжини ДО, одноразово)."""
import ast
import collections
import glob
import json
import os
import re
import sys
import warnings

warnings.simplefilter("ignore")

# ── ШАРИ: що лічимо ────────────────────────────────────────────────────────────────────────────────────────────────
# шар → чи входить у `місць:`. Усі шари, де код дає моделі текст, входять (наряд: не звужувати клас); знімки результатів
# (`траса/*.txt` — записані виходи збирача) не код, що шле, а його слід: друкуються окремо.
ШАРИ_КОРЕНЯ = ("продукт", "жнивар")                              # код Люстерка, що шле промпти моделі (рішення менеджера, 11319)
ШАРИ_ПОЗА = ("проба", "прилад", "open-source-stylist")           # поза коренем: у місцях не лічено, друкуємо окремо (--поза-коренем)
ШАРИ_ЛІЧБИ = list(ШАРИ_КОРЕНЯ)
ЗАБОРОНЕНО_ТЕКИ = (".git", "node_modules", "__pycache__")
РЕЄСТР_ФОРМИ = ("джерела/фрази_формату.py", "джерела/схема_відповіді.py")  # де слова про форму відповіді — на місці

# ── ДЕТЕКТОР ВИМОГИ ────────────────────────────────────────────────────────────────────────────────────────────────
# Вимога до моделі — речення, що ВЕЛИТЬ: починається наказовим дієсловом («Відповідай…», «Return…», «Не вигадуй…»), чи
# має модальність обов'язку/заборони («must», «never», «ніколи», «має бути», «не більше N»). Звичайне заперечення
# («did not match», «не підлягає») вимогою не є.
_ЛІТ = r"A-Za-zА-Яа-яІіЇїЄєҐґ'ʼ’\-"
_УК_НАКАЗ = ("відповідай", "повертай", "поверни", "напиши", "пиши", "склади", "складай", "обери", "обирай", "вибери",
             "вибирай", "використовуй", "називай", "опиши", "описуй", "уникай", "тримай", "дотримуйся", "згадуй",
             "ігноруй", "вигадуй", "переклади", "перекажи", "залиш", "лишай", "додавай", "додай", "познач", "позначай",
             "порівняй", "оціни", "суди", "врахуй", "бери", "дивись", "читай", "став", "пропонуй", "вказуй", "наводь",
             "зазнач", "подавай", "кажи", "говори", "пояснюй", "роби", "зроби", "виведи", "виводь", "будь", "ставай",
             "лише", "тільки", "завжди", "ніколи")
_УК_ПОЧАТОК_RE = re.compile(r"^(?:не\s+)?(?:%s)(?![%s])" % ("|".join(_УК_НАКАЗ), _ЛІТ), re.I)
_УК_БУДЬДЕ = ("ніколи", "завжди", "мусиш", "мусить", "має бути", "мають бути", "повинен", "повинна", "повинні",
              "слід ", "не більше", "не менше", "не більш ", "не менш ", "щонайбільше", "щонайменше", "заборонено",
              "рівно ", "обов'язково", "обовʼязково")
_EN_ПОЧАТОК = ("do not", "don't", "never", "always", "return", "answer", "respond", "reply", "output", "write", "use",
               "keep", "give", "pick", "choose", "select", "list", "name", "describe", "mention", "include", "omit",
               "skip", "prefer", "follow", "treat", "ignore", "compose", "judge", "rate", "say", "add", "leave", "put",
               "take", "read", "look", "consider", "stay", "stick", "limit", "avoid", "ensure", "make sure",
               "if ", "when ", "start", "begin", "check",
               "call", "copy", "drop", "fill", "mark", "pass", "send", "set", "show", "state", "tell", "try", "ask")
_EN_БУДЬДЕ = ("do not", "don't", "never ", "must", "should", "shall", "always ", "at most", "at least", "no more than",
              "exactly ", "required", "forbidden", "allowed only", "only if", "make sure", "ensure ")
_УК_СЛОВО = re.compile(r"(?<![%s])(?:%s)" % (_ЛІТ, "|".join(re.escape(x) for x in _УК_БУДЬДЕ)), re.I)
_EN_СЛОВО = re.compile(r"(?<![%s])(?:%s)(?![%s])" % (_ЛІТ, "|".join(re.escape(x.strip()) for x in _EN_БУДЬДЕ), _ЛІТ), re.I)
# речення, що не є вимогою до моделі: код, шлях, службовий рядок, лог
НЕ_ВИМОГА = re.compile(r"\.(py|js|md|json|html|yml)\b|^\s*[#@/]|=>|\bdef \b|\{\{|^\s*(?:assert|import|from)\b|\breturn\b[^.]*\(|\bawait\b|json\.loads|"
                       r"\bFileNotFound|Traceback|\bsys\.|http[s]?://|\bis missing\b")
# слова про форму відповіді (п.2): ЩО вимога каже про вигляд відповіді
ФОРМА = re.compile(r"\bJSON\b|```|markdown|code fence|\bplain text\b|\b(?:one|single|only one|exactly one) (?:JSON )?object\b|"
                   r"(?:один|єдиний|лише один) (?:JSON-?)?об['ʼ’]?єкт|\bpreamble\b|без пояснен|without explanation|"
                   r"only the answer|nothing (?:more|else) (?:than|after|before|outside)\b|нічого (?:більше|після)|begins with|ends with|starts with \{|"
                   r"valid JSON|одним рядком|рівно з цими ключами|exactly these keys|no prose", re.I)
ВІДПОВІДЬ_СЛОВО = re.compile(r"відпов|answer|reply|respond|output|return|поверн|write nothing|виведи|не пиши|не додавай|"
                             r"do not wrap|not wrapped|response", re.I)
ПОЛЯРНІСТЬ_НЕ = re.compile(r"(?<![%s])(?:не|ніколи|без|заборонено|don't|do not|never|avoid|not|no|without|forbidden|"
                           r"must not|cannot|can't)(?![%s])" % (_ЛІТ, _ЛІТ), re.I)
СТОП = set("та і й або чи що як це цей ця ці для при про від по до із з у в на за the a an of to in on for and or is "
           "are be with by as at it its this that these those you your she her he his they them".split())


def корінь_репо(арг):
    if "--корінь" in арг:
        return os.path.abspath(арг[арг.index("--корінь") + 1])
    ц = os.getcwd()
    if os.path.isdir(os.path.join(ц, "джерела")):
        return ц
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def шар_файла(відн):
    """Шар за шляхом від кореня: хто пише текст, що йде моделі."""
    if відн.startswith("open-source-stylist/"):
        return "open-source-stylist"
    if відн.startswith("zhnyvarka/"):
        return "жнивар"
    if відн.startswith(("джерела/проби/", "аудит/проби/")):
        return "проба"
    if відн.startswith("джерела/прилади/"):
        return "прилад"
    if відн.startswith("джерела/траса/"):
        return "знімок"
    return "продукт"


def тестовий(відн):
    ім = os.path.basename(відн)
    return ім.startswith(("тест_", "test_")) or ім.endswith(("_test.py", ".test.js")) or "/tests/" in відн


def файли_коду(кор):
    """[(відн. шлях, тип)] — py, js, inline-js html усього коду; без тестів і службових тек."""
    вих = []
    for база, теки, файли in os.walk(кор):
        теки[:] = [т for т in теки if т not in ЗАБОРОНЕНО_ТЕКИ and not (база == кор and т in ("аудит", ".github", ".claude"))]
        for ф in файли:
            відн = os.path.relpath(os.path.join(база, ф), кор).replace(os.sep, "/")
            if відн == "джерела/прилади/корінь_е2_промпти.py" or тестовий(відн):
                continue
            if ф.endswith(".py"):
                вих.append((відн, "py"))
            elif ф.endswith(".js") and ф not in ("worker.js",) and not ф.endswith(".min.js"):  # worker.js — збірка worker_джерело.js
                вих.append((відн, "js"))
    # проби аудиту — теж код, що шле моделі (аудит/проби), крім службових
    for ф in glob.glob(os.path.join(кор, "аудит", "проби", "**", "*.*"), recursive=True):
        відн = os.path.relpath(ф, кор).replace(os.sep, "/")
        if ф.endswith((".py", ".js")) and not тестовий(відн):
            вих.append((відн, "py" if ф.endswith(".py") else "js"))
    return sorted(set(вих))


# ── ЛІТЕРАЛИ ───────────────────────────────────────────────────────────────────────────────────────────────────────
_ЛОГ = {"print", "warn", "exit", "error", "info", "debug", "warning", "exception", "critical", "add_argument",
        "ArgumentParser", "SystemExit", "write", "log", "assertEqual", "assertTrue", "assertIn"}


def _ім_виклику(n):
    f = n.func
    return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")


_КЕШ = {}


def літерали_py(текст):
    """Кеш за текстом (один файл читають обидва шляхи)."""
    if текст not in _КЕШ:
        _КЕШ[текст] = _літерали_py(текст)
    return _КЕШ[текст]


def _літерали_py(текст):
    """[(рядок, значення, вид, кінцевий рядок)] — рядкові літерали Python без докстрінгів, ключів, повідомлень винятків і логів.
    вид: «стала» (верхній рівень), «оголошення» (аргумент `Оголошення(`/`Поле(`), «функція» (тіло функції)."""
    дерево = ast.parse(текст)
    пропуск, вид_вузла = set(), {}
    for n in ast.walk(дерево):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body and \
                isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            пропуск.add(id(n.body[0].value))
        if isinstance(n, ast.Raise) or (isinstance(n, ast.Call) and _ім_виклику(n) in _ЛОГ):
            пропуск.update(id(x) for x in ast.walk(n))
        if isinstance(n, ast.Assert) and n.msg is not None:
            пропуск.update(id(x) for x in ast.walk(n.msg))
        if isinstance(n, ast.Dict):
            for к in n.keys:
                if к is not None:
                    пропуск.update(id(x) for x in ast.walk(к))
        if isinstance(n, ast.Compare):
            пропуск.update(id(x) for x in ast.walk(n))
        if isinstance(n, ast.Call) and _ім_виклику(n) in ("Оголошення", "Поле"):
            for x in ast.walk(n):
                вид_вузла[id(x)] = "оголошення"
            if _ім_виклику(n) == "Поле":      # шлях і «що» — опис поля, а не наказ: вимога лише з детектором
                for а in n.args[:2]:
                    for x in ast.walk(а):
                        вид_вузла[id(x)] = "опис_поля"
    верх = {id(x) for n in дерево.body if isinstance(n, (ast.Assign, ast.AnnAssign)) for x in ast.walk(n)}
    вих = []
    for n in ast.walk(дерево):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in пропуск:
            вид = вид_вузла.get(id(n)) or ("стала" if id(n) in верх else "функція")
            вих.append((n.lineno, n.value, вид, getattr(n, 'end_lineno', n.lineno)))
    return sorted(вих, key=lambda x: x[0])


def літерали_js(т):
    """[(рядок, значення, контекст)] — рядкові літерали JS поза коментарями; regex-літерали пропущено."""
    вих, i, n, р = [], 0, len(т), 1
    while i < n:
        c = т[i]
        if c == "\n":
            р += 1
            i += 1
            continue
        if т.startswith("//", i):
            while i < n and т[i] != "\n":
                i += 1
            continue
        if т.startswith("/*", i):
            j = т.find("*/", i + 2)
            j = n if j < 0 else j + 2
            р += т.count("\n", i, j)
            i = j
            continue
        if c in "'\"`":
            q, j, буф, р0 = c, i + 1, [], р
            while j < n:
                d = т[j]
                if d == "\\" and j + 1 < n:
                    буф.append(т[j + 1] if т[j + 1] != "n" else "\n")
                    if т[j + 1] == "\n":
                        р += 1
                    j += 2
                    continue
                if d == q:
                    break
                if d == "\n":
                    if q != "`":
                        break
                    р += 1
                if q == "`" and d == "$" and j + 1 < n and т[j + 1] == "{":
                    k, ур = j + 2, 1
                    while k < n and ур:
                        ур += (т[k] == "{") - (т[k] == "}")
                        р += т[k] == "\n"
                        k += 1
                    буф.append("{…}")
                    j = k
                    continue
                буф.append(d)
                j += 1
            вих.append((р0, "".join(буф), т[max(0, i - 40):i]))
            i = j + 1
            continue
        if c == "/":
            п = т[:i].rstrip()
            if п and (п[-1] in "(,=:[!&|?{;}" or п.endswith("return")):
                j, кл = i + 1, False
                while j < n and т[j] != "\n":
                    if т[j] == "\\":
                        j += 2
                        continue
                    if т[j] == "[":
                        кл = True
                    elif т[j] == "]":
                        кл = False
                    elif т[j] == "/" and not кл:
                        break
                    j += 1
                i = j + 1
                continue
        i += 1
    return вих


def літерали_html(т):
    """Inline-скрипти html: літерали JS зі зсувом рядків."""
    вих = []
    for м in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", т, re.S):
        зсув = т.count("\n", 0, м.start(1))
        вих += [(р + зсув, з, к) for р, з, к in літерали_js(м.group(1))]
    return вих


# ── РЕЧЕННЯ ────────────────────────────────────────────────────────────────────────────────────────────────────────
_МЕЖА = re.compile(r"(?<=[.!?;])\s+(?=[A-ZА-ЯІЇЄҐ\"«(0-9•·])")


def речення(т):
    """[(зсув_рядків, речення)] — речення літерала; вузол списку чи рядок — окреме речення; зайві пробіли стиснуто."""
    вих, рядки = [], т.split("\n")
    збір, початок = [], 0
    def скинути():
        nonlocal збір
        if збір:
            зліплено = re.sub(r"\s+", " ", " ".join(збір)).strip()
            for ч in _МЕЖА.split(зліплено):
                ч = ч.strip(" ·•-–*\t")
                if len(ч) >= 20:
                    вих.append((початок, ч))
        збір = []
    for н, р in enumerate(рядки):
        с = р.strip()
        if not с:
            скинути()
            continue
        ціле = bool(re.match(r"^[·•\-–*]|^\d+[.)]\s", с)) or (збір and збір[-1].rstrip().endswith((":", ".", "!", "?", ";")))
        if ціле:
            скинути()
        if not збір:
            початок = н
        збір.append(с)
    скинути()
    return вих


def норм(с):
    return re.sub(r"\s+", " ", re.sub(r"[\"«»“”'`ʼ’]", "", с.lower())).strip(" .;:!?")


def основи(с):
    """множина основ слів (перші 6 літер) без службових."""
    return {сл[:6] for сл in re.findall(r"[a-zа-яіїєґ]{3,}", с.lower()) if сл not in СТОП}


def є_вимогою(с):
    if len(с) < 20 or len(с) > 900 or len(с.split()) < 4 or НЕ_ВИМОГА.search(с):
        return False
    if ("```" not in с and с.count("`") > 2) or с.count("·") > 3 or re.search(r"[A-Za-z_]+=\S", с):
        return False
    п = re.sub(r"^[\W\d_]+", "", с).lower()
    if мова_англ(с):
        return п.startswith(_EN_ПОЧАТОК) or bool(_EN_СЛОВО.search(с))
    return bool(_УК_ПОЧАТОК_RE.match(п)) or bool(_УК_СЛОВО.search(с))


def мова_англ(с):
    лат = len(re.findall(r"[A-Za-z]", с))
    кир = len(re.findall(r"[А-Яа-яІіЇїЄєҐґ]", с))
    return лат >= 20 and лат > 3 * кир


# ── ІНДЕКС МОДУЛІВ PYTHON (шлях А) ─────────────────────────────────────────────────────────────────────────────────
class Мод:
    def __init__(я, відн, текст):
        я.відн = відн
        я.ім = os.path.basename(відн)[:-3]
        я.текст = текст
        я.дерево = ast.parse(текст)
        я.визначення = {}      # ім'я → вузол верхнього рівня
        я.імпорти = {}         # псевдонім → (модуль, ім'я | None)
        for n in я.дерево.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                я.визначення[n.name] = n
            elif isinstance(n, ast.Assign):
                for ц in n.targets:
                    for x in ast.walk(ц):
                        if isinstance(x, ast.Name):
                            я.визначення[x.id] = n
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                я.визначення[n.target.id] = n
            elif isinstance(n, ast.Import):
                for а in n.names:
                    я.імпорти[а.asname or а.name.split(".")[0]] = (а.name, None)
            elif isinstance(n, ast.ImportFrom) and n.module:
                for а in n.names:
                    я.імпорти[а.asname or а.name] = (n.module, а.name)

    def посилання(я, вузол):
        """{(модуль, ім'я)} — на що за іменем посилається вузол (у цьому модулі чи через імпорт)."""
        вих = set()
        for x in ast.walk(вузол):
            if isinstance(x, ast.Name):
                if x.id in я.імпорти and я.імпорти[x.id][1]:
                    вих.add((я.імпорти[x.id][0], я.імпорти[x.id][1]))
                elif x.id in я.визначення:
                    вих.add((я.ім, x.id))
            elif isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id in я.імпорти \
                    and я.імпорти[x.value.id][1] is None:
                вих.add((я.імпорти[x.value.id][0], x.attr))
        return вих

    def сегмент(я, вузол):
        return ast.get_source_segment(я.текст, вузол) or ""


ТРАНСПОРТ = re.compile(r"chat/completions|/v1/messages|generateContent|api\.anthropic\.com|[\"']role[\"']\s*:\s*[\"'](?:user|system)")
ІМ_ПРОМПТУ = re.compile(r"ПРОМПТ|PROMPT|ШАБЛОН|ПРАВИЛО|ІНСТРУКЦ|НАГАДУВАНН|ПОВТОР|ПІДКАЗК|^_?ЗАГ_|ФРАЗА|ВИМОГА|ВИМОГИ")
_РЯДКОВІ_МЕТОДИ = ("replace", "format", "join", "strip", "dedent", "lower", "upper", "capitalize")


def рядкове(вузол, глиб=0):
    """Значення вузла складається з рядкових літералів (константа, f-рядок, +, %, .replace/.format, кортеж/список/словник,
    будь-якої вкладеності, де є рядки)."""
    if глиб > 8:
        return False
    if isinstance(вузол, ast.Constant):
        return isinstance(вузол.value, str)
    if isinstance(вузол, ast.JoinedStr):
        return True
    if isinstance(вузол, ast.BinOp):
        return рядкове(вузол.left, глиб + 1) or рядкове(вузол.right, глиб + 1)
    if isinstance(вузол, (ast.Tuple, ast.List, ast.Set)):
        return any(рядкове(x, глиб + 1) for x in вузол.elts)
    if isinstance(вузол, ast.Dict):
        return any(рядкове(x, глиб + 1) for x in вузол.values)
    if isinstance(вузол, ast.Call) and isinstance(вузол.func, ast.Attribute) and вузол.func.attr in _РЯДКОВІ_МЕТОДИ:
        return рядкове(вузол.func.value, глиб + 1)
    return False


def модулі_py(кор, файли):
    вих = {}
    for відн, тип in файли:
        if тип != "py" or шар_файла(відн) in ("знімок",):
            continue
        try:
            м = Мод(відн, open(os.path.join(кор, відн), encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError, ValueError):
            continue
        вих[(os.path.dirname(відн), м.ім)] = м
    return вих


def насіння(модулі):
    """Витоки шляху А — [(каталог, модуль, ім'я, чому)]. Модуль — СТІК, коли в ньому: `Оголошення(` (чи клас `Оголошення`),
    транспорт моделі (chat/completions, role-словник, generateContent) або стала-промпт за іменем (ПРОМПТ, ШАБЛОН, ПРАВИЛО,
    ПІДКАЗКА, ЗАГ_…). Усі визначення стоку — витоки; далі за іменами в рядкові сталі й функції інших модулів."""
    вих = []
    for (кат, ім), м in модулі.items():
        if шар_файла(м.відн) not in ШАРИ_ЛІЧБИ:
            continue
        чому = None
        if "Оголошення(" in м.текст or "class Оголошення" in м.текст:
            чому = "модуль пише Оголошення"
        elif ТРАНСПОРТ.search(м.текст):
            чому = "модуль несе транспорт моделі"
        elif re.search(r"prompt|промпт", ім, re.I):
            чому = "модуль-промпт за іменем файла"
        else:
            for назва, n in м.визначення.items():
                if isinstance(n, (ast.Assign, ast.AnnAssign)) and ІМ_ПРОМПТУ.search(назва) and n.value is not None \
                        and рядкове(n.value):
                    чому = "стала-промпт за іменем " + назва
                    break
        if чому:
            for назва in м.визначення:
                вих.append((кат, ім, назва, чому))
    return вих


def замикання(модулі, зерна):
    """{(каталог, модуль, ім'я): чому} — визначення шляху А: зерна й усе, на що вони посилаються за іменами через модулі;
    ідемо лише в рядкові сталі й функції (реєстр-словник чисел чи даних вимогою не є)."""
    за_ім = {}
    for (кат, ім), м in модулі.items():
        за_ім.setdefault(ім, []).append((кат, м))
    вих, черга = {}, []
    def знайти(кат, мд):
        ц = модулі.get((кат, мд))
        if ц is None:
            ц = (за_ім.get(мд) or [(None, None)])[0][1]
        return ц
    for кат, мд, назва, чому in зерна:
        ц = знайти(кат, мд)
        if ц is None or назва is None or назва not in ц.визначення:
            continue
        ключ = (os.path.dirname(ц.відн), ц.ім, назва)
        if ключ not in вих:
            вих[ключ] = чому
            черга.append(ключ)
    # зв'язки верхнього рівня: `ЗАЯВИ.update(ПУНКТИ)`, `Р[к] = …` — стала, що вливається в досяжну, теж іде моделі
    зв_язки = collections.defaultdict(list)
    for (кат, ім), м in модулі.items():
        for n in м.дерево.body:
            if isinstance(n, (ast.Expr, ast.AugAssign)) or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Subscript) for t in n.targets)):
                зв_язки[(кат, ім)].append((n, м.посилання(n)))
    while True:
        while черга:
            кат, ім, назва = черга.pop()
            м = модулі[(кат, ім)]
            вузол = м.визначення[назва]
            for (мд, ін) in м.посилання(вузол):
                ц = знайти(кат, мд)
                if ц is None or ін not in ц.визначення:
                    continue
                n2 = ц.визначення[ін]
                if not (isinstance(n2, (ast.FunctionDef, ast.AsyncFunctionDef)) or
                        (isinstance(n2, (ast.Assign, ast.AnnAssign)) and n2.value is not None and рядкове(n2.value))):
                    continue
                ключ = (os.path.dirname(ц.відн), ц.ім, ін)
                if ключ not in вих:
                    вих[ключ] = "через " + назва
                    черга.append(ключ)
        додано = False
        for (кат, ім), список in зв_язки.items():
            м = модулі[(кат, ім)]
            for n, реф in список:
                власні = {к for (мд, к) in реф if мд == м.ім and (os.path.dirname(м.відн), м.ім, к) in вих}
                if not власні:
                    continue
                for (мд, ін) in реф:
                    ц = знайти(кат, мд)
                    if ц is None or ін not in ц.визначення:
                        continue
                    n2 = ц.визначення[ін]
                    ключ = (os.path.dirname(ц.відн), ц.ім, ін)
                    if ключ not in вих and isinstance(n2, (ast.Assign, ast.AnnAssign)) and n2.value is not None and рядкове(n2.value):
                        вих[ключ] = "влито у " + "/".join(sorted(власні))
                        черга.append(ключ)
                        додано = True
        if not додано:
            break
    return вих


# ── ЗБІР МІСЦЬ ─────────────────────────────────────────────────────────────────────────────────────────────────────
class Місце:
    __slots__ = ("файл", "рядок", "текст", "вид", "шлях", "мова", "модуль", "ім")

    def __init__(я, файл, рядок, текст, вид, шлях, модуль="", ім=""):
        я.файл, я.рядок, я.текст, я.вид, я.шлях, я.модуль, я.ім = файл, рядок, текст, вид, шлях, модуль, ім


def вузли_промптів(модулі):
    """{(каталог, модуль): {ім'я}} — сталі, ЧИЙ текст промпт цілком: за іменем (ПРОМПТ, ШАБЛОН, ПРАВИЛО…) і ті, на які
    посилаються аргументи `Оголошення(`/`Поле(`. У них кожне речення — вимога; поза ними — лише за детектором."""
    вих = collections.defaultdict(set)
    for (кат, ім), м in модулі.items():
        for назва, n in м.визначення.items():
            if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None and ІМ_ПРОМПТУ.search(назва) and рядкове(n.value):
                вих[(кат, ім)].add(назва)
        for n in ast.walk(м.дерево):
            if isinstance(n, ast.Call) and _ім_виклику(n) in ("Оголошення", "Поле"):
                for (мд, назва) in м.посилання(n):
                    ц = модулі.get((кат, мд)) or next((v for (k, i), v in модулі.items() if i == мд), None)
                    if ц is not None and назва in ц.визначення and isinstance(ц.визначення[назва], (ast.Assign, ast.AnnAssign)) \
                            and рядкове(ц.визначення[назва].value):
                        вих[(os.path.dirname(ц.відн), ц.ім)].add(назва)
    return вих


def рядок_речення(рядки, початок, кінець, с, зсув):
    """Рядок файла, де стоїть речення: у склеєному з кількох рядків літералі (`"а" "б"`) зсув за «\\n» не працює, тож
    шукаємо початок речення в рядках літерала; не знайшли — початок + зсув."""
    зразок = re.sub(r"\s+", " ", с)[:14]
    for н in range(початок, min(кінець, len(рядки)) + 1):
        if зразок and зразок in re.sub(r"\s+", " ", рядки[н - 1]):
            return н
    return початок + зсув


# опис входу (що на фото, що в даних, що означає код збою) — не вимога (рішення менеджера 11319, п.3): у довіреному тексті
# такі речення не береться за вимогу без ознак наказу чи модальності
ОПИС_ВХОДУ = re.compile(r"^(?:на фото|на зображенні|in the photo|the photo|the image|input:|вхід:)\b|\{[^{}]*\}\W*$|^(?:not|neither|no)\s", re.I)


def речення_вимог(з, довірене):
    """Речення літерала, що є вимогами: у довіреному тексті промпту — усі з ≥ 4 слів; інакше — за детектором."""
    вих = []
    for зсув, с in речення(з):
        if є_вимогою(с):
            вих.append((зсув, с))
        elif довірене and len(с.split()) >= 4 and not НЕ_ВИМОГА.search(с) and not re.search(r"\s·\s", с) \
                and not ОПИС_ВХОДУ.search(с):
            вих.append((зсув, с))
    return вих


# JS-файл, що шле текст моделі (міст до моделі / виклик оцінки): українська вимога в ньому, якщо вона не напис екрана, —
# інструкція моделі (повторний запит `Поверни кожен із цих рядків.`)
МОДЕЛЬНИЙ_JS = re.compile(r"модельП|модельМовиП|викликОцінкиП|chat/completions|generateContent|помилка_формату")
_ІНТЕРФЕЙС_JS = re.compile(r"textContent|innerText|innerHTML|placeholder|\btitle\b|alert\(|appendChild|плитка\(|\bст\b|\bset(?:Attribute|Status)")


def _не_інтерфейс_js(рядки, р):
    """Літерал у рядку р (чи сусідніх двох) не йде в напис екрана."""
    return not _ІНТЕРФЕЙС_JS.search(" ".join(рядки[max(0, р - 3):р]))


def місця_шляху_а(кор, файли, модулі, видно):
    """Шлях А: вимоги в текстах, що йдуть моделі. → [Місце]."""
    вих = []
    промпти = вузли_промптів(модулі)
    за_файлом = collections.defaultdict(dict)
    for (кат, ім, н), чому in видно.items():
        за_файлом[(кат, ім)][н] = чому
    for (кат, ім), м in модулі.items():
        if шар_файла(м.відн) not in ШАРИ_ЛІЧБИ:
            continue
        імена = за_файлом.get((кат, ім), {})
        діапазони = [(м.визначення[н].lineno, getattr(м.визначення[н], "end_lineno", м.визначення[н].lineno), н)
                     for н in імена if н in м.визначення]
        довірені = [(м.визначення[н].lineno, getattr(м.визначення[н], "end_lineno", м.визначення[н].lineno))
                                        for н in промпти.get((кат, ім), ()) if н in м.визначення]
        рядки_файла = м.текст.split("\n")
        for р, з, вид, кін in літерали_py(м.текст):
            дотичне = [н for а, б, н in діапазони if а <= р <= б]
            # літерал в аргументі Оголошення(…) — завжди на шляху; решта — у досяжному визначенні
            if вид not in ("оголошення", "опис_поля") and not дотичне:
                continue
            довір = вид == "оголошення" or any(а <= р <= б for а, б in довірені)
            for зсув, с in речення_вимог(з, довір):
                вих.append(Місце(м.відн, рядок_речення(рядки_файла, р, кін, с, зсув), с, вид, "А", м.ім,
                                 дотичне[0] if дотичне else ""))
    # JS: літерал із вимогою — англійською чи в полі system/prompt/…
    for відн, тип in файли:
        if тип != "js" or шар_файла(відн) not in ШАРИ_ЛІЧБИ:
            continue
        текст = open(os.path.join(кор, відн), encoding="utf-8").read()
        рядки_js = текст.split("\n")
        модельний_js = bool(МОДЕЛЬНИЙ_JS.search(текст))
        for р, з, к in літерали_js(текст):
            ктx = bool(re.search(r"(?:system|prompt|промпт|PROMPT|ПРОМПТ|нагадуванн|ПОВТОР|instruction)\w*\s*[:=+(]\s*$", к))
            if not (мова_англ(з) or ктx or (модельний_js and _не_інтерфейс_js(рядки_js, р))):
                continue
            for зсув, с in речення(з):
                # код-рядок логу («answer_truncated · max_tokens=») словами вимоги не є: ≥ 5 слів, без « · »
                if є_вимогою(с) and len(с.split()) >= 5 and not re.search(r"\s·\s", с):
                    вих.append(Місце(відн, рядок_речення(рядки_js, р, р + з.count("\n"), с, зсув), с, "js", "А",
                                     os.path.basename(відн), ""))
    return вих


def місця_шляху_б(кор, файли):
    """Шлях Б: кожне речення-вимога будь-якого літерала коду, без огляду на те, чи йде воно моделі."""
    вих = []
    for відн, тип in файли:
        текст = open(os.path.join(кор, відн), encoding="utf-8").read()
        рядки_файла = текст.split("\n")
        if тип == "py":
            try:
                літ = літерали_py(текст)
            except SyntaxError:
                continue
        else:
            літ = [(р, з, "js", р + з.count("\n")) for р, з, _ in літерали_js(текст)]
        for р, з, вид, кін in літ:
            for зсув, с in речення(з):
                if є_вимогою(с):
                    вих.append(Місце(відн, рядок_речення(рядки_файла, р, кін, с, зсув), с, вид, "Б",
                                     os.path.basename(відн)[:-3], ""))
    return вих


# ── ПУНКТИ КЛАСУ ───────────────────────────────────────────────────────────────────────────────────────────────────
def пункт1_повтори(місця):
    """Те саме речення (чи те саме іншими словами) у ≥ 2 різних місцях коду. → [(Місце, чому)]"""
    за_норм = collections.defaultdict(list)
    для_схожих = []
    for м in місця:
        н = норм(м.текст)
        за_норм[н].append(м)
        ос = основи(м.текст)
        if len(ос) >= 6:
            для_схожих.append((м, ос))
    вих, взято = [], set()
    for н, л in за_норм.items():
        розр = {(х.файл, х.рядок) for х in л}
        if len(розр) >= 2:
            for х in л:
                вих.append((х, "те саме речення ще в %s" % ", ".join(sorted("%s:%d" % ш for ш in розр if ш != (х.файл, х.рядок))[:2])))
                взято.add(id(х))
    # схоже іншими словами: Жаккар основ ≥ 0,75
    інд = collections.defaultdict(list)
    for м, ос in для_схожих:
        for о in ос:
            інд[о].append((м, ос))
    пари = set()
    for м, ос in для_схожих:
        кандидати = collections.Counter()
        for о in ос:
            for ін, іос in інд[о]:
                if ін is not м:
                    кандидати[id(ін)] += 1
        за_ід = {id(x): (x, y) for x, y in для_схожих}
        for k, c in кандидати.items():
            ін, іос = за_ід[k]
            if (ін.файл, ін.рядок) == (м.файл, м.рядок) or норм(ін.текст) == норм(м.текст):
                continue
            жк = len(ос & іос) / len(ос | іос)
            if жк >= 0.75:
                пари.add(frozenset((id(м), id(ін))))
    за_ід = {id(x): x for x, _ in для_схожих}
    партнери = collections.defaultdict(list)
    for п in пари:
        а, б = (за_ід[i] for i in п)
        партнери[id(а)].append(б)
        партнери[id(б)].append(а)
    for k, л in sorted(партнери.items(), key=lambda kv: (за_ід[kv[0]].файл, за_ід[kv[0]].рядок, за_ід[kv[0]].текст)):
        х = за_ід[k]
        if id(х) not in взято:
            ін = min(л, key=lambda y: (y.файл, y.рядок, y.текст))
            вих.append((х, "те саме іншими словами ще в %s:%d" % (ін.файл, ін.рядок)))
            взято.add(id(х))
    return вих


def пункт2_формат(місця):
    """Формат відповіді словами поза реєстром. → [(Місце, чому)]"""
    вих = []
    for м in місця:
        if м.файл in РЕЄСТР_ФОРМИ:
            continue
        if ФОРМА.search(м.текст) and ВІДПОВІДЬ_СЛОВО.search(м.текст):
            вих.append((м, "формат відповіді словами: «%s»" % ФОРМА.search(м.текст).group(0)))
    return вих


ДІАПАЗОНИ_КОЛЕКЦІЙ = {}   # «файл:ІМ» → (файл, перший рядок, останній рядок) визначення колекції


def колекції_коду(кор, файли):
    """{ім'я «файл:ІМ'Я»: множина рядків} — переліки значень і ключів, що тримає код (≥ 3 рядків ≥ 3 знаків)."""
    вих = {}
    for відн, тип in файли:
        if тип != "py" or шар_файла(відн) not in ШАРИ_КОРЕНЯ:
            continue
        try:
            д = ast.parse(open(os.path.join(кор, відн), encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in d_верх(д):
            ім = n.targets[0].id
            if not ім.isupper() and not ім.lstrip("_").isupper():
                continue
            try:
                в = ast.literal_eval(n.value)
            except Exception:
                continue
            ел = set()
            if isinstance(в, dict):
                ел = {к for к in в if isinstance(к, str)}
            elif isinstance(в, (list, tuple, set, frozenset)):
                ел = {к for к in в if isinstance(к, str)}
            ел = {к for к in ел if 3 <= len(к) <= 40 and re.fullmatch(r"[\w\- ]+", к)}
            if len(ел) >= 3:
                вих["%s:%s" % (відн, ім)] = ел
                ДІАПАЗОНИ_КОЛЕКЦІЙ["%s:%s" % (відн, ім)] = (відн, n.lineno, getattr(n, "end_lineno", n.lineno))
    for ф in glob.glob(os.path.join(кор, "джерела", "*.schema.json")):
        try:
            дані = json.load(open(ф, encoding="utf-8"))
        except Exception:
            continue
        def обхід(вузол, шлях):
            if isinstance(вузол, dict):
                if isinstance(вузол.get("enum"), list):
                    ел = {x for x in вузол["enum"] if isinstance(x, str) and 3 <= len(x) <= 40}
                    if len(ел) >= 3:
                        вих["%s:enum@%s" % (os.path.relpath(ф, кор).replace(os.sep, "/"), шлях)] = ел
                for к, х in вузол.items():
                    обхід(х, шлях + "/" + к)
            elif isinstance(вузол, list):
                for х in вузол:
                    обхід(х, шлях)
        обхід(дані, "")
    return вих


def d_верх(д):
    return [n for n in д.body if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)]


_МЕЖІ_СЛОВО = re.compile(r"(?<![%s])(?:щонайбільше|щонайменше|не більше|не менше|не більш|рівно|at most|at least|no more than|"
                         r"up to|exactly|between)(?![%s])" % (_ЛІТ, _ЛІТ), re.I)


_РОЗДІЛ_СПИСКУ = re.compile(r"\s*(?:,|;|/|\||\bor\b|\band\b|\bабо\b|\bчи\b|\bта\b|\bі\b|\bй\b)\s*", re.I)


def елементи_списку(с):
    """Елементи переліків у реченні: частини між комами/«or»/«|», очищені від лапок і артиклів."""
    вих = []
    for ч in _РОЗДІЛ_СПИСКУ.split(с):
        ч = re.sub(r"^(?:the|a|an|це|той)\s+", "", ч.strip(" «»\"'`().:").lower())
        вих.append(ч)
    return вих


def елементи_з_поясненнями(с):
    """Переліки виду «a — пояснення; b — пояснення; c — пояснення»: голови частин між «;» перед тире."""
    вих = []
    for ч in re.split(r";\s+", с):
        if re.search(r"\s[—–-]\s", ч):
            г = re.split(r"\s[—–-]\s", ч, maxsplit=1)[0].split(": ")[-1]
            вих.append(re.sub(r"^(?:the|a|an|це|той)\s+", "", г.strip(" «»\"'`().:").lower()))
        else:
            вих.append("")
    return вих


def пункт3_дубль_коду(місця, колекції, числа_коду=None):
    """Вимога перелічує (≥ 3 поспіль, цілими елементами списку) значення чи ключі, які вже тримає код (сталі-переліки й
    enum схем). Числові межі, що збігаються зі сталою коду, тут НЕ лічено: збіг числа без спільного змісту хибний. → [(Місце, чому)]"""
    вих = []
    для_кожного = {ім: {е.lower() for е in ел} for ім, ел in колекції.items()}
    for м in місця:
        ел = елементи_списку(м.текст)
        ел_пояс = елементи_з_поясненнями(м.текст)
        знайдено = None
        for ім, мн in для_кожного.items():
            діап = ДІАПАЗОНИ_КОЛЕКЦІЙ.get(ім)
            if діап and діап[0] == м.файл and діап[1] <= м.рядок <= діап[2]:   # саму себе стала не дублює; реєстр поруч — дублює
                continue
            макс = 0
            for список in (ел, ел_пояс):
                серія = 0
                for е in список:
                    серія = серія + 1 if е in мн else 0
                    макс = max(макс, серія)
            if макс >= 3:
                знайдено = (ім, макс)
                break
        if знайдено:
            вих.append((м, "перелік із %d значень поспіль уже тримає код: %s" % (знайдено[1], знайдено[0])))
            continue
    return вих


def k_частка(к, ел):
    return к >= 3 and к >= 0.5 * min(len(ел), 6)


def числа_меж(кор, файли):
    """{'число': «файл:ІМ'Я»} — цілі сталі коду з іменем межі (МЕЖА/ЛІМІТ/МАКС/МІН/СТЕЛЯ/MAX/MIN/LIMIT) і значенням ≥ 3."""
    вих = {}
    for відн, тип in файли:
        if тип != "py" or шар_файла(відн) not in ШАРИ_КОРЕНЯ:
            continue
        try:
            д = ast.parse(open(os.path.join(кор, відн), encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in d_верх(д):
            ім = n.targets[0].id
            if re.search(r"МЕЖ|ЛІМІТ|МАКС|МІН|СТЕЛЯ|MAX|MIN|LIMIT|ДОВЖИН", ім):
                try:
                    в = ast.literal_eval(n.value)
                except Exception:
                    continue
                if isinstance(в, int) and not isinstance(в, bool) and 3 <= в <= 99:
                    вих.setdefault(str(в), "%s:%s" % (відн, ім))
    return вих


_ЧИСЛО_МЕЖІ = re.compile(r"(?:at most|no more than|up to|exactly|не більше ніж|не більше|щонайбільше|рівно)\s+(\d+)\s+([\w'ʼ’-]+)", re.I)


def пункт4_суперечності(групи):
    """групи: {назва промпту: [Місце]} → [(Місце, чому)] — вимоги одного промпту, що суперечать: (а) ті самі слова при
    протилежній полярності («не називай X» / «називай X»); (б) одна межа з різними числами («at most 3 items» / «рівно 5 items»)."""
    вих = []
    for назва, л in groups_items(групи):
        ознаки = []
        числа = collections.defaultdict(list)
        for м in л:
            ос = основи(ПОЛЯРНІСТЬ_НЕ.sub(" ", м.текст))
            ознаки.append((м, ос, bool(ПОЛЯРНІСТЬ_НЕ.search(м.текст))))
            for ч, іменник in _ЧИСЛО_МЕЖІ.findall(м.текст):
                числа[іменник.lower()[:5]].append((int(ч), м))
        for i in range(len(ознаки)):
            for j in range(i + 1, len(ознаки)):
                а, ос_а, нег_а = ознаки[i]
                б, ос_б, нег_б = ознаки[j]
                if нег_а == нег_б or len(ос_а) < 5 or len(ос_б) < 5:
                    continue
                жк = len(ос_а & ос_б) / len(ос_а | ос_б)
                if жк >= 0.6:
                    вих.append((б, "суперечить «%s» (%s:%d): ті самі слова, протилежна полярність" % (а.текст[:60], а.файл, а.рядок)))
        for ключ, пари in числа.items():
            if len({ч for ч, _ in пари}) > 1:
                (ч0, м0), (ч1, м1) = пари[0], next(x for x in пари if x[0] != пари[0][0])
                вих.append((м1, "межа «%s»: %d (%s:%d) проти %d" % (ключ, ч0, м0.файл, м0.рядок, ч1)))
    return вих


def groups_items(групи):
    return групи.items()


def самоперевірка():
    """Вигадані приклади на кожен пункт: прилад бачить, що має бачити, і мовчить, де не має. → (пройшло, усього)"""
    П = Місце
    перевірки = []
    а, б = П("х.py", 1, "Never name shops or brands in the answer text.", "стала", "А"), \
        П("у.py", 2, "Never name shops or brands in the answer text.", "стала", "А")
    перевірки.append(("п1 те саме речення", len(пункт1_повтори([а, б])) == 2))
    в = П("в.py", 3, "Write the answer in plain Ukrainian only, no English words.", "стала", "А")
    перевірки.append(("п1 різні вимоги не повтор", not пункт1_повтори([а, в])))
    ф = П("ф.py", 4, "Return only one JSON object without explanations and without ```.", "стала", "А")
    перевірки.append(("п2 формат словами", len(пункт2_формат([ф])) == 1 and not пункт2_формат([в])))
    кол = {"к.py:СЛОТИ": {"top", "bottom", "outer", "shoes"}}
    г = П("г.py", 5, "Slots are: top, bottom, outer, shoes.", "стала", "А")
    д = П("д.py", 6, "Describe the top and the bottom as one outfit.", "стала", "А")
    перевірки.append(("п3 перелік із коду", len(пункт3_дубль_коду([г], кол, {})) == 1 and not пункт3_дубль_коду([д], кол, {})))
    е = П("е.py", 7, "Do not mention brand names or shop names in the answer text.", "стала", "А")
    є = П("е.py", 8, "Mention brand names and shop names in the answer text.", "стала", "А")
    перевірки.append(("п4 полярність", len(пункт4_суперечності({"п": [е, є]})) == 1 and not пункт4_суперечності({"п": [е, в]})))
    ж = П("ж.py", 9, "Pick at most 3 items for the outfit.", "стала", "А")
    з = П("ж.py", 10, "Pick exactly 5 items for the outfit.", "стала", "А")
    перевірки.append(("п4 числа", len(пункт4_суперечності({"п": [ж, з]})) == 1))
    перевірки.append(("детектор: наказ є, опис нема", є_вимогою("Не називай крамниць і брендів у відповіді.")
                      and not є_вимогою("Бажання золота стелі не підлягає, його підстава слово.")))
    return перевірки


# ── ЗІБРАНІ ПРОМПТИ (довжини, повтор у зібраному) ──────────────────────────────────────────────────────────────────
def зібрані_оголошення(кор):
    """{'модуль.ІМ': [рядки сталої частини]} — кожне оголошення збирача: роль, вхід, правила, коди, межі, кінець.
    Імпорт модулів (як їх вантажить сам збирач); модуль, що не вантажиться, — у `збої`."""
    sys.path.insert(0, os.path.join(кор, "джерела"))
    збої = []
    try:
        import збирач_промптів as ЗП
    except Exception as e:  # прилад не падає: число лишається, збій названо
        return {}, ["збирач_промптів: %s" % e]
    вих, бачено = {}, set()
    for ф in sorted(glob.glob(os.path.join(кор, "джерела", "*.py"))):
        ім = os.path.basename(ф)[:-3]
        if ім.startswith("тест_") or ім == "збирач_промптів":
            continue
        if "Оголошення(" not in open(ф, encoding="utf-8").read():
            continue
        try:
            мод = __import__(ім)
        except Exception as e:
            збої.append("%s: %s" % (ім, type(e).__name__))
            continue
        try:
            if callable(getattr(мод, "фото_речей", None)):
                мод.фото_речей()
        except Exception:
            pass
        for н, в in vars(мод).items():
            пари = [(н, в)] if isinstance(в, ЗП.Оголошення) else (
                [("%s[%s]" % (н, к), х) for к, х in в.items() if isinstance(х, ЗП.Оголошення)] if isinstance(в, dict) else [])
            for нн, о in пари:
                if id(о) in бачено:
                    continue
                бачено.add(id(о))
                межі = ЗП.МЕЖІ_EN if о.мова_промпту == "en" else ЗП.МЕЖІ
                частини = [о.роль] + sorted({"%s — %s. %s" % (п.шлях.split(".")[-1].replace("[]", ""), п.що, п.як)
                                            for п in о.вхід}) + list(о.правила) + list(о.коди) + [межі.get(x, "") for x in о.межі] \
                    + [о.наприкінці or ""]
                вих["джерела/%s.py:%s" % (ім, нн)] = [ч for ч in частини if ч]
    return вих, збої


def довжини_js(кор, файли):
    """{'файл:ІМ': символів} — JS-сталі-промпти англійською: `const ПОВТОР_… = '…' + '…';` (ім'я за ІМ_ПРОМПТУ)."""
    вих = {}
    for відн, тип in файли:
        if тип != "js" or шар_файла(відн) not in ШАРИ_КОРЕНЯ:
            continue
        текст = open(os.path.join(кор, відн), encoding="utf-8").read()
        for м in re.finditer(r"^const\s+([\w$А-Яа-яІіЇїЄєҐґ]+)\s*=\s*", текст, re.M):
            ім = м.group(1)
            if not ІМ_ПРОМПТУ.search(ім):
                continue
            j, лапка = м.end(), None
            while j < len(текст):
                c = текст[j]
                if лапка:
                    if c == "\\":
                        j += 1
                    elif c == лапка:
                        лапка = None
                elif c in "'\"`":
                    лапка = c
                elif c == ";":
                    break
                j += 1
            літ = літерали_js(текст[м.end():j])
            значення = "".join(з for _, з, _ in літ)
            if len(значення) >= 120 and мова_англ(значення):
                вих["%s:%s" % (відн, ім)] = len(значення)
    return вих


def довжини_сталих(кор, модулі):
    """{'файл:ІМ': символів} — довжина кожної сталої-промпту за іменем (ПРОМПТ, ШАБЛОН, ПРАВИЛО, ПІДКАЗКА…) — кореня, не
    уламка: на неї не посилається інша така стала того ж модуля. Текст розгорнуто з іменами модуля, а підставлені
    `.replace(…, УЛАМОК)` дописано."""
    вих = {}
    for (кат, ім), м in модулі.items():
        if шар_файла(м.відн) not in ШАРИ_ЛІЧБИ:
            continue
        значення = {}
        def згорнути(вузол, глиб=0):
            if глиб > 300:     # довгий ланцюг «а + б + в + …» — глибина лівого вкладення = число доданків
                return ""
            if isinstance(вузол, ast.Constant) and isinstance(вузол.value, str):
                return вузол.value
            if isinstance(вузол, ast.Name):
                return значення.get(вузол.id, "")
            if isinstance(вузол, ast.BinOp) and isinstance(вузол.op, (ast.Add, ast.Mod)):
                return згорнути(вузол.left, глиб + 1) + (згорнути(вузол.right, глиб + 1) if isinstance(вузол.op, ast.Add) else "")
            if isinstance(вузол, ast.JoinedStr):
                return "".join(згорнути(x, глиб + 1) if isinstance(x, ast.Constant) else "{…}" for x in вузол.values)
            if isinstance(вузол, ast.Call) and isinstance(вузол.func, ast.Attribute) and вузол.func.attr in ("replace", "format", "strip"):
                if вузол.func.attr == "replace" and len(вузол.args) >= 2:   # підставлений уламок теж іде моделі
                    арг1 = вузол.args[1]
                    if isinstance(арг1, ast.IfExp):                         # два варіанти уламка: беремо довший
                        вставка = max((згорнути(арг1.body, глиб + 1), згорнути(арг1.orelse, глиб + 1)), key=len)
                    else:
                        вставка = згорнути(арг1, глиб + 1)
                    return згорнути(вузол.func.value, глиб + 1) + вставка
                return згорнути(вузол.func.value, глиб + 1)
            return ""
        промптові, посилання = {}, collections.Counter()
        for n in м.дерево.body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                значення[n.targets[0].id] = згорнути(n.value)
                if ІМ_ПРОМПТУ.search(n.targets[0].id) and рядкове(n.value):
                    промптові[n.targets[0].id] = n
        for ім_ст, n in промптові.items():
            for x in ast.walk(n.value):
                if isinstance(x, ast.Name) and x.id in промптові and x.id != ім_ст:
                    посилання[x.id] += 1
        for ім_ст in промптові:
            if not посилання[ім_ст] and len(значення[ім_ст]) >= 120:
                вих["%s:%s" % (м.відн, ім_ст)] = len(значення[ім_ст])
        # уламки, які функція підставляє в промпт `.replace(…, УЛАМОК | А if умова else Б)`: довжина кожного варіанта окремо,
        # щоб зміна коротшого варіанта не лишалась невидимою
        for x in ast.walk(м.дерево):
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == "replace" and len(x.args) >= 2:
                вузли = [x.args[1]] if not isinstance(x.args[1], ast.IfExp) else [x.args[1].body, x.args[1].orelse]
                for в in вузли:
                    if isinstance(в, ast.Name) and в.id in значення and len(значення[в.id]) >= 120 \
                            and "%s:%s" % (м.відн, в.id) not in вих:
                        вих["%s:%s" % (м.відн, в.id)] = len(значення[в.id])
    return вих


# ── ГОЛОВНЕ ────────────────────────────────────────────────────────────────────────────────────────────────────────
def зібрати_все(кор, з_б=True):
    файли = файли_коду(кор)
    модулі = модулі_py(кор, файли)
    видно = замикання(модулі, насіння(модулі))
    а = місця_шляху_а(кор, файли, модулі, видно)
    б = місця_шляху_б(кор, [ф for ф in файли if шар_файла(ф[0]) in ШАРИ_ЛІЧБИ]) if з_б else []
    return файли, модулі, видно, а, б


def основа_лічби(кор, з_б=False):
    файли, модулі, видно, а, б = зібрати_все(кор, з_б)
    унікальні = {}
    for м in а:
        унікальні.setdefault((м.файл, м.рядок, норм(м.текст)), м)
    місця = list(унікальні.values())
    колекції = колекції_коду(кор, файли)
    числа = числа_меж(кор, файли)
    п1 = пункт1_повтори(місця)
    п2 = пункт2_формат(місця)
    п3 = пункт3_дубль_коду(місця, колекції, числа)
    # суперечності: за промптом — оголошення (зібраний), решта — за модулем-власником
    зібрані, збої = зібрані_оголошення(кор)
    групи = collections.defaultdict(list)
    пошук = collections.defaultdict(list)
    for м in місця:
        пошук[норм(м.текст)].append(м)
    for ім, частини in зібрані.items():
        for ч in частини:
            for _, с in речення(ч):
                if є_вимогою(с):
                    знайдено = пошук.get(норм(с))
                    групи[ім].append(знайдено[0] if знайдено else Місце(ім.split(":")[0], 0, с, "оголошення", "А"))
    за_модулем = collections.defaultdict(list)
    for м in місця:
        if м.вид != "оголошення":
            за_модулем[м.файл].append(м)
    for файл, л in за_модулем.items():
        групи["файл:" + файл] = л
    п4 = пункт4_суперечності(групи)
    # повтор у зібраному оголошенні: те саме речення двічі в сталій частині
    п1_збір = []
    for ім, частини in зібрані.items():
        лічильник = collections.Counter(норм(с) for ч in частини for _, с in речення(ч) if є_вимогою(с))
        for н, к in лічильник.items():
            if к > 1:
                м = (пошук.get(н) or [Місце(ім.split(":")[0], 0, н, "оголошення", "А")])[0]
                п1_збір.append((м, "двічі в зібраному промпті %s" % ім))
    довжини = {ім: sum(len(ч) for ч in ч_) for ім, ч_ in зібрані.items()}
    довжини.update(довжини_сталих(кор, модулі))
    довжини.update(довжини_js(кор, файли))
    return {"місця": місця, "п1": п1 + п1_збір, "п2": п2, "п3": п3, "п4": п4, "довжини": довжини, "а": а, "б": б,
            "видно": видно, "збої": збої, "файли": файли, "зібрані": зібрані}


def main(арг):
    if "--самоперевірка" in арг:
        п = самоперевірка()
        for ім, ок in п:
            print("самоперевірка: %s — %s" % (ім, "так" if ок else "НІ"))
        print("самоперевірка: %d з %d" % (sum(ок for _, ок in п), len(п)))
        return 0
    кор = корінь_репо(арг)
    р = основа_лічби(кор, "--звірка" in арг)
    # довжини проти бази ДО
    база = {}
    шлях_бази = арг[арг.index("--база") + 1] if "--база" in арг else os.path.join(кор, "аудит", "корені", "Е2-промпти-довжини.json")
    if os.path.exists(шлях_бази):
        база = json.load(open(шлях_бази, encoding="utf-8")).get("довжини", {})
    п5 = []
    сума = sum(р["довжини"].values())
    сума_до = 0
    for ім, л in sorted(р["довжини"].items()):
        до = база.get(ім, л)          # промпта нема в базі ДО — рахуємо рівним собі: новий промпт теж «не коротший»
        сума_до += до
        файл = ім.split(":")[0]
        if л >= до:
            п5.append((файл, ім, "не коротший за ДО: %d → %d" % (до, л) if ім in база else "нема в базі ДО, не коротший за себе (%d симв.)" % л))
        if л > до:
            п5.append((файл, ім, "довший за ДО: %d → %d" % (до, л)))
    if сума >= сума_до:      # переніс тексту між промптами довжини не зменшує
        п5.append(("аудит/корені/Е2-промпти-довжини.json", "сума", "сума довжин не менша за ДО: %d → %d" % (сума_до, сума)))
        if сума > сума_до:
            п5.append(("аудит/корені/Е2-промпти-довжини.json", "сума", "сума довжин більша за ДО: %d → %d" % (сума_до, сума)))
    рядки = []
    бачено = set()
    for н, ключ in ((1, "п1"), (2, "п2"), (3, "п3"), (4, "п4")):
        for м, чому in sorted(р[ключ], key=lambda x: (x[0].файл, x[0].рядок, x[1])):
            ід = (н, м.файл, м.рядок, норм(м.текст))
            if ід in бачено:
                continue
            бачено.add(ід)
            рядки.append((н, "%s:%d · пункт %d · %s%s" % (м.файл, м.рядок, н, чому,
                                                         (" · «%s»" % м.текст[:110]) if "--деталі" in арг else "")))
    for файл, ім, чому in п5:
        рядки.append((5, "%s:0 · пункт 5 · %s · %s" % (файл, ім, чому)))
    for _, р_ in рядки:
        print(р_)
    підсумок = collections.Counter(н for н, _ in рядки)
    print("---")
    print("пункт 1 повтори: %d" % підсумок[1])
    print("пункт 2 формат словами: %d" % підсумок[2])
    print("пункт 3 дубль коду: %d" % підсумок[3])
    print("пункт 4 ознак суперечності (полярність, числові межі; суперечності за змістом, з кодом і граматикою, прилад не міряє): %d" % підсумок[4])
    print("пункт 5 довжина (не коротший/довший за ДО, нема в базі): %d з %d промптів" % (підсумок[5], len(р["довжини"])))
    шари = collections.Counter(шар_файла(м.файл) for м in р["місця"])
    print("вимог у текстах, що йдуть моделі (шлях А): %d; за шарами: %s" % (len(р["місця"]), dict(шари)))
    print("промптів: %d (оголошень збирача %d, сталих-коренів %d)" % (len(р["довжини"]), len(р["зібрані"]), len(р["довжини"]) - len(р["зібрані"])))
    if "--поза-коренем" in арг:     # лише довідка: шари поза коренем (проби, прилади, open-source-stylist) у `місць:` не входять
        ШАРИ_ЛІЧБИ[:] = ШАРИ_ПОЗА
        інш = основа_лічби(кор)
        ключі = {(н, м.файл, м.рядок, норм(м.текст)) for н, к in ((1, "п1"), (2, "п2"), (3, "п3")) for м, _ in інш[к]}
        за_шаром = collections.Counter((шар_файла(ф), н) for н, ф, _, _ in ключі)
        print("поза коренем (у місцях НЕ лічено): %d; за шарами і пунктами: %s" % (len(ключі), dict(sorted(за_шаром.items()))))
        ШАРИ_ЛІЧБИ[:] = ШАРИ_КОРЕНЯ
    if р["збої"]:
        print("не завантажено модулів (їх оголошення не лічено): %s" % "; ".join(р["збої"]))
    if "--звірка" in арг:
        а = {(м.файл, м.рядок) for м in р["а"]}
        for м in sorted(р["б"], key=lambda x: (x.файл, x.рядок)):
            if (м.файл, м.рядок) not in а:
                print("поза А: %s:%d · %s" % (м.файл, м.рядок, м.текст[:100]))
    if "--записати-базу" in арг:
        sha = арг[арг.index("--sha") + 1] if "--sha" in арг else ""
        json.dump({"про": "довжини сталої частини кожного промпту ДО (симв.); прилад: джерела/прилади/корінь_е2_промпти.py",
                   "main": sha, "довжини": р["довжини"]},
                  open(арг[арг.index("--записати-базу") + 1], "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print("місць: %d" % len(рядки))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
