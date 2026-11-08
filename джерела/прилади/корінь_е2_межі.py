# -*- coding: utf-8 -*-
"""прилади/корінь_е2_межі.py — прилад кореня Е2-межі: місця коду за класом паспорта `аудит/корені/Е2-межі.md`.

Клас — правило, а не перелік прикладів: місце — кожна точка `джерела/` (Python і JS), де код шле моделі запит або
читає, приймає чи виправляє її відповідь; воно порушує інваріант, якщо хоч один із пунктів 1–7 класу. Прилад не править
коду й не бере списку місць руками: усе — з AST Python і з тексту показу.

ДВА ШЛЯХИ, ОДИН НАБІР ТОЧОК (мірило наряду, (а)):
  А — від викликів моделі: JS-виклик `модельП`/`модельП_блоки` (і обгортки) і Python-клієнт сервера моделі
      (`choices`) → ендпойнт моста (`містП('…')`) → його Python-обробник → читачі відповіді й збирачі промпта в
      конусі обробника.
  Б — від читачів полів відповіді: Python — потік «сирого тексту моделі» (ключі входів моста, чий опис у
      `ЗОВНІШНІ_ВХОДИ` називає відповідь моделі, і `choices`) до розбору/реєстру/правки; JS — змінні, що тримають
      відповідь `модельП…`, і все, що з ними роблять, крім передачі мосту → конус обробника → виклики в JS.
  В — п.6 «дріт без виду» (помічник `корінь_е2_межі_дріт.py`): від підписів полів входу моделі назад потоком значення
      до джерела коду; шляхи А і Б його не бачать (це вхід, а не відповідь), тож у «розбіжності» він не йде.
  Точка — виклик/читач; обидва шляхи збирають одні й ті самі точки, розбіжність (точка лише з одного шляху) друкується
  в розділі «розбіжності».

ПУНКТИ КЛАСУ — ЩО ЛІЧИТЬСЯ (кожне — механічне правило, помилка правила видна в переліку `файл:рядок · пункт · чому`):
  1  схеми нема в реєстрі `схема_відповіді.py` чи поле читається повз перевірку нею: (а) розбір/регулярка/пошук над
     текстом моделі поза реєстром і протоколом; (б) читання реєстром через форму БЕЗ `схема_протоколу` (поля
     відповіді нічим не перевіряються); (в) відповідь моделі, яку JS читає сам (не передає мосту).
  2  розбіжність не повертається моделі словами на один повтор: ендпойнт (чи клієнт) читає відповідь, а в усьому
     його конусі нема жодного знака повтору словами (`промпт_повтору`, `повторний_виклик`, `помилка_формату`,
     `format_error`, `пояснити_повтор`, `повтор`); для JS — знака повтору нема в обгортці виклику.
  3  після повтору нема запасного ходу чи рядка звіту: (а) результат перевірки/сторожа не вживається; (б) гілка
     невдачі читача — `raise` чи порожнє значення без причини; (в) JS: виклик моделі з `throw` у обгортці, а ні вона,
     ні її викликачі не ловлять збій у рядок звіту; (г) відхилене перевіркою (схемою чи сторожем) записано в рядок
     звіту, а запасного ходу коду нема: Python — гілка, що пише запис відхиленого (`відкинуто`/`відхилено`/… із
     ключем `чому`, крім записів, де відхилене лишено: `лишено`/`показано`; і гілка губить його: присвоєно порожнє,
     `continue`/`return` чи порожнє в самому записі), у функції конуса без запасного ходу; JS — `catch` у функції
     виклику моделі, що лише пише причину в запис ходу, без запасного ходу в її тілі. Запасний
     хід — імʼя з коренем `шаблон`/`запасн` у тій самій функції: шаблон заяви коду, запасна заява. Місце лічиться в
     кожній гілці, а не лише в пораді: порада — приклад, не межа. `raise` покриває лише лов нагору (`try`, чий
     `except` не кидає далі й вживає причину чи запасний хід), а не запасний хід ім'ям деінде у викликачі;
     (д) зупинка кроку (рішення 08.11, нічний прогін 07.11: руки 1–2 ж4_робота_живіт): Python — `raise` будівника
     дроту (`дріт_моделі`, функції з іменем дроту), якого не ловить ні він, ні викликачі нагору: виняток виходить з
     мосту разом із прийнятою відповіддю; JS — `збій = true` на шляху виклику моделі без запасного ходу в блоці:
     крок руки втрачено, що код знав, — лише в рядку звіту; (е) після останньої спроби (`["повтор"] = None`) причину
     відхилення записано значенням, що на гілці `None`: запасний хід показу стоїть на причині, і відхилене йде далі,
     у кеш, як прийняте (рядок 14277); (є) її слова, яких шар не прочитав (рішення 08.11, #3379; 14095): рядок звіту
     шару `… step=layer … code=not_taken` — поле ходу знято лише в журнал (`не_взято`, `не_взято_кодом`), а не в
     `не_записано` репліки, тож заяви їй нема; рядок у функції `…_рядком` — місце в її виклику. Не місця: блок під
     `if <ім'я>:`, чиє ім'я йде в `не_записано=` (сказано їй), і виклик над `невідомо` (перекладач сам сказав «unknown»).
  4  гілка ремонту формату: (а) текст моделі правиться (`replace`, `strip(символи)`, `re.sub`, зріз за знайденим,
     дописані дужки) і потрапляє у розбір; (б) обʼєкт після розбору перероблюється і зміна пишеться в `нотатки`
     (код сам називає це ремонтом форми).
  5  вхід моделі — не дані коду: у дрот, який збирає промпт, іде слово/назва крамниці (`назва`, `опис`, `бренд`…)
     чи повний `ід` речі без перетворення на номер для дроту.
  6  вид поля (`her`/`hand`/`reading`/`default`) читається чи оголошується поза `паспорт_поля.py`; і «дріт без виду»
     (шлях В, помічник `корінь_е2_межі_дріт.py`; рішення менеджера 31.10, Г6 і певність літералом): поле входу
     моделі, чий підпис приписує значення їй чи факту, а писач — функція коду, що дає значення не копією її слова чи
     дотику (типове `or`, поріг, вивід з іншого поля, вимір коду); `setdefault` поля її паспорта значенням коду;
     `впевненість` літералом у записі без виду; вид, який код знав, губиться на дроті з підписом «її».
  7  код читає її слова, щоб вибрати код чи джерело: регулярка, пошук чи порівняння над її вільним текстом
     (ключі входів, чий опис називає її слова, і слова-цитати `уривок`/`quote`).

ВИНЯТОК КЛАСУ (рішення менеджера 05.11, паспорт `аудит/корені/Е2-межі.md`, «Рішення»; `аудит/ПРОДУКТ.md`, п.1):
  руки 3–4 — лише для тестів («лишати, не міняти»), їхні місця в коді обробки й розбору рук 3–4
  (`джерела/руки_без_коду.py`; у показі — стадія `стадіяРукБезКаталогу` у `збирання_руки.js`) не лічаться, прилад
  друкує їх окремим рядком винятку.

ЧОГО ПРИЛАД НЕ ЛІЧИТЬ (питання менеджерові в PR, не звуження): див. ПИТАННЯ нижче; транспорт (`модельП`,
`модельП_блоки`, `worker*.js`) — лише пересилає запит, не читає відповіді за форматом; проби (`проби/`) — окремий
рядок, у `місць` не входять.

Вивід: перелік `файл:рядок · пункт · чому [шлях]`, підсумки за пунктами, розбіжності шляхів, окремий рядок винятку,
останній рядок `місць: <N>` (N — різних `файл:рядок`), код 0. Запуск з кореня репозиторію (чи з `--корінь <шлях>`):
python3 джерела/прилади/корінь_е2_межі.py [--json] [--проби] [--тихо] [--тест]
"""
import ast
import json
import os
import re
import sys
import warnings

import обсяг_приладу as ОБСЯГ  # Д10: непрочитане — код 1, не менше місць

warnings.simplefilter("ignore", SyntaxWarning)

БУКВА = r"[\wА-Яа-яЇїІіЄєҐґʼ'$]"
РЕЄСТР_МОД = {"схема_відповіді", "протокол", "схеми_розбору", "фрази_формату"}
НЕ_ШЛЯХ = re.compile(r"^(тест|gate_|audit_|build_|стенд|батарея_|measure_|pair_test|rule_genus|status_перевірки|"
                     r"скласти|склад$|мутанти|корпус$|таблиця_збирання|траса_петлі|звірка|зведення|рв\d|replay)")
РОЗБІР_ПРОТОКОЛУ = {"розбір", "розібрати_json", "розбір_останній", "розбір_за_схемою"}
МЕТОДИ_РЕЄСТРУ = {"прочитати", "виконати_розбір"}
РЕГУЛЯРКИ = {"search", "match", "fullmatch", "findall", "finditer", "sub", "subn", "split"}
ТЕКСТОВІ = {"strip", "lstrip", "rstrip", "replace", "lower", "upper", "casefold", "removeprefix", "removesuffix",
            "split", "rsplit", "splitlines", "format", "encode", "decode", "title", "capitalize", "group", "groups",
            "get", "items", "values", "keys", "join", "copy"}
ПРАВКИ = {"replace", "removeprefix", "removesuffix"}
ЧИТАННЯ_МЕТОДИ = {"startswith", "endswith", "find", "rfind", "index", "rindex", "count"}
ПРОПУСК_КОНТЕЙНЕРІВ = {"str", "list", "tuple", "set", "sorted", "reversed", "next", "iter", "min", "max",
                       "repr", "frozenset", "enumerate", "zip", "filter", "map"}
ЗНАКИ_ПОВТОРУ = {"промпт_повтору", "повторний_виклик", "помилка_формату", "format_error", "пояснити_повтор", "повтор",
                 "промптПовторуП", "повтор_словами"}
ТЕКСТ_КРАМНИЦІ = {"назва", "name", "title", "опис", "description", "бренд", "brand", "магазин", "shop", "продавець"}
ПЕРЕТВОРЮВАЧІ_ІД = {"_ід_усюди", "ід_усюди", "ід_на_дріт", "ід_на_дріт_усюди"}
ВИДИ_ПОЛЯ = {"her", "hand", "reading", "default"}
ПОЛЯ_МОДЕЛІ_ПАРАМ = {"відповідь_моделі", "json_моделі", "текст_моделі", "відповідь_сира", "сира", "сирий_текст",
                     "перша_відповідь", "перелік_речей", "тексти_моделі", "текст_відповіді"}
ОПИС_ВІДПОВІДІ = re.compile(r"сира\b|відповід\w*\s+(?:\w+\s+){0,2}модел|(?:текст|json|JSON)\s+модел|відповід\w+ шару|choices\[0\]",
                            re.I)
ОПИС_СЛІВ_ЇЇ = re.compile(r"(?:її|жінки)\s+(?:вільн\w+\s+)?(?:слов|текст|реплік|питанн)|вільний текст|дослівн", re.I)
СЛОВА_ЇЇ_ІМЕНА = {"уривок", "слова_розмови", "слова_ходу"}
ІМЯ_ВІДПОВІДІ = re.compile(r"^(?:відповід|json_|текст_моделі|тексти_моделі|перша_відповідь|choices|сир)")
ЗАПИС_ВІДХИЛЕНОГО = {"відкинуто", "відхилено", "відхилені", "відкинуті"}
ЛИШЕНО_ВІДХИЛЕНЕ = {"лишено", "показано"}
ЗАПАСНИЙ_ХІД = re.compile(r"шаблон|запасн", re.I)
# п.3(д): будівник дроту — переводить дані коду руки на вхід моделі, тож його `raise` залежить від даних виклику.
# `збирач_промптів` — шаблон над оголошенням: його `raise` звіряє оголошення зі схемою (CI будує кожен промпт); не лічиться
МОДУЛІ_ВХОДУ = {"дріт_моделі"}
ПОЛЯ_РЕЧІ_ДРОТУ = {"photo", "name", "slot", "kind", "replace", "n"}
ІМЯ_ДРОТУ = re.compile(r"для_моделі|для_шару|дрот|дріт|вхід_моделі")  # функції, що самі називають себе будівниками входу моделі
ІМЯ_СЛІВ = re.compile(r"^(?:слова|слів|репліка|питання|уривок|цитата|quote)")
ІМЕНА_ТЕКСТУ_JS = re.compile(r"^(сира|відповідь|текст|тф|т[0-9]?|відп|сирий|вихід)$")

ПИТАННЯ = [
    "п.6 «губиться до картки й стилістки»: рішення менеджера 31.10 (Г6, рядок 12009) — лічити; лічить шлях В "
    "(`корінь_е2_межі_дріт.py`)",
    "п.7: лічаться лише її слова (вільний текст і цитати); слова крамниць і каталогу (назва, колір, опис) п.12 теж "
    "забороняє читати — чи вони клас цього кореня, чи ПС-15 окремо, рішення менеджера",
    "п.5: «бракує того, що код знає» статично не видно — не лічиться; лічаться слова крамниці й повний ід у дроті",
    "проби (`джерела/проби/`) шлють запити й читають відповіді, але це вимірювання, не продукт: окремий рядок, "
    "у `місць` не входять",
]


# ── ДЕРЕВО ────────────────────────────────────────────────────────────────────
def корінь_репозиторію():
    """Корінь, з якого брати `джерела/`: поточна тека, якщо в ній є `джерела/`, інакше тека над приладом."""
    if "--корінь" in sys.argv:
        return os.path.abspath(sys.argv[sys.argv.index("--корінь") + 1])
    if os.path.isdir(os.path.join(os.getcwd(), "джерела")):
        return os.getcwd()
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


КОРІНЬ = корінь_репозиторію()
ДЖЕРЕЛА = os.path.join(КОРІНЬ, "джерела")
ПОКАЗ = os.path.join(ДЖЕРЕЛА, "показ")


def прочитати_файл(шлях):
    with open(шлях, encoding="utf-8") as ф:
        return ф.read()


def відн(шлях):
    return os.path.relpath(шлях, КОРІНЬ)


def модулі_продукту():
    """Імена модулів продукту: `status.МОДУЛІ_ПРОДУКТУ` (список ядра) плюс модулі поза ним, що самі шлють запит
    моделі чи читають реєстр відповіді (жнива, розбір каталогу): вони клас кореня, хоч і не вантажаться в показ."""
    ядро = set()
    шлях = os.path.join(ДЖЕРЕЛА, "status.py")
    if os.path.exists(шлях):
        for в in ast.walk(ast.parse(прочитати_файл(шлях))):
            if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == "МОДУЛІ_ПРОДУКТУ" for ц in в.targets):
                ядро = {е.value for е in ast.walk(в.value) if isinstance(е, ast.Constant) and isinstance(е.value, str)}
    вих = {}
    for ім in sorted(os.listdir(ДЖЕРЕЛА)):
        if not ім.endswith(".py"):
            continue
        мод = ім[:-3]
        текст = прочитати_файл(os.path.join(ДЖЕРЕЛА, ім))
        в_ядрі = мод in ядро or (not НЕ_ШЛЯХ.match(мод) and ('"choices"' in текст or "схема_відповіді" in текст))
        if not в_ядрі or НЕ_ШЛЯХ.match(мод):
            continue
        дерево = ОБСЯГ.розібрати(текст, "джерела/" + ім)
        if дерево is not None:
            вих[мод] = дерево
    return вих


class Модуль:
    """Індекс модуля: функції (включно з методами), імпорти, скомпільовані регулярки верхнього рівня."""

    def __init__(self, ім, дерево):
        self.ім, self.дерево = ім, дерево
        self.модулі, self.імена, self.функції, self.зразки = {}, {}, {}, set()
        for в in ast.walk(дерево):
            if isinstance(в, ast.Import):
                for а in в.names:
                    self.модулі[а.asname or а.name] = а.name
            elif isinstance(в, ast.ImportFrom) and в.module and not в.level:
                for а in в.names:
                    self.імена[а.asname or а.name] = (в.module, а.name)
        for в in дерево.body:
            if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.функції[в.name] = в
            elif isinstance(в, ast.ClassDef):
                for м in в.body:
                    if isinstance(м, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.функції["%s.%s" % (в.name, м.name)] = м
            elif isinstance(в, ast.Assign) and isinstance(в.value, ast.Call) and isinstance(в.value.func, ast.Attribute) \
                    and в.value.func.attr == "compile":
                self.зразки |= {ц.id for ц in в.targets if isinstance(ц, ast.Name)}


def текст_імені(в):
    """Імʼя/атрибут виклику одним рядком: `a.b.c` → «a.b.c» (інше — порожньо)."""
    if isinstance(в, ast.Name):
        return в.id
    if isinstance(в, ast.Attribute):
        ліво = текст_імені(в.value)
        return (ліво + "." if ліво else "") + в.attr
    return ""


def константи_рядків(в):
    return [е.value for е in ast.walk(в) if isinstance(е, ast.Constant) and isinstance(е.value, str)]


# ── РЕЄСТР ФОРМ ───────────────────────────────────────────────────────────────
def форми_реєстру(модулі):
    """{назва форми: має `схема_протоколу`} з `СХЕМИ_ВІДПОВІДІ` (`СхемаВідповіді(...)`) і з присвоєнь `СХЕМИ_ВІДПОВІДІ[...] =`."""
    вих = {}
    мод = модулі.get("схема_відповіді")
    if not мод:
        return вих
    def з_виклику(в):
        if isinstance(в, ast.Call) and текст_імені(в.func).endswith("СхемаВідповіді"):
            назва = next((к.value.value for к in в.keywords if к.arg == "назва" and isinstance(к.value, ast.Constant)), None)
            схема = any(к.arg == "схема_протоколу" for к in в.keywords)
            return назва, схема
        return None, False
    for в in ast.walk(мод.дерево):
        if isinstance(в, ast.Dict):
            for к, з in zip(в.keys, в.values):
                н, с = з_виклику(з)
                if н:
                    вих[н] = с
        if isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Subscript):
            н, с = з_виклику(в.value)
            if н:
                вих[н] = с
    return вих


def ключі_моделі_з_входів(модулі):
    """Ключі входів моста, чий опис у `ЗОВНІШНІ_ВХОДИ` називає відповідь моделі (сира, json моделі, текст моделі), і ключі,
    чий опис називає її вільні слова. Сталий `choices` — відповідь сервера моделі."""
    м, ж = {"choices"}, set()
    for мод in модулі.values():
        for в in ast.walk(мод.дерево):
            if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == "ЗОВНІШНІ_ВХОДИ" for ц in в.targets) \
                    and isinstance(в.value, ast.Dict):
                for к, з in zip(в.value.keys, в.value.values):
                    if isinstance(к, ast.Constant) and isinstance(к.value, str) and isinstance(з, ast.Constant) \
                            and isinstance(з.value, str):
                        if ОПИС_ВІДПОВІДІ.search(з.value) and ІМЯ_ВІДПОВІДІ.search(к.value):
                            м.add(к.value)
                        if ОПИС_СЛІВ_ЇЇ.search(з.value) and ІМЯ_СЛІВ.search(к.value):
                            ж.add(к.value)
    return м | ПОЛЯ_МОДЕЛІ_ПАРАМ, ж | СЛОВА_ЇЇ_ІМЕНА


# ── PYTHON: ПОТІК ТЕКСТУ МОДЕЛІ ───────────────────────────────────────────────
М, Ж = ("М",), ("Ж", 0)
ГЛИБИНА_СЛІВ = 2          # на скільки викликів углиб ідуть її слова: далі це вже не її слова, а похідні


def є_ж(мітки):
    return any(л[0] == "Ж" for л in мітки)


def порожнє_значення(в):
    """Вираз — «ніщо»: None, "", 0, False, порожній контейнер (гілка невдачі без причини)."""
    if isinstance(в, ast.Constant):
        return not в.value
    if isinstance(в, (ast.List, ast.Tuple, ast.Set)):
        return not в.elts
    if isinstance(в, ast.Dict):
        return not в.keys
    return False


class Аналіз:
    """Потік міток по Python: `М` — сирий текст моделі, `Ж` — її слова, `Р` — текст моделі після правки (з походженням).
    Події (читання, розбір, правка, реєстр) збирає в `self.події` за ключем (файл, рядок, вид, дія)."""

    def __init__(self, модулі, ключі_м, ключі_ж, форми):
        self.м = {ім: Модуль(ім, д) for ім, д in модулі.items()}
        self.ключі_м, self.ключі_ж, self.форми = ключі_м, ключі_ж, форми
        self.параметри, self.повертає, self.події = {}, {}, {}
        self.приймальники = {}      # (мод, функція) → рядок першої події читання
        self.тримає_м = set()       # функції, де хоч одна змінна несе текст моделі
        for мод in self.м.values():
            for ім, ф in мод.функції.items():
                self.засіяти(мод, ім, ф)

    # ── розв'язання викликів ──
    def ціль(self, мод, виклик):
        ф = виклик.func
        if isinstance(ф, ast.Name):
            if ф.id in мод.функції:
                return (мод.ім, ф.id)
            if ф.id in мод.імена:
                м, ім = мод.імена[ф.id]
                if м in self.м and ім in self.м[м].функції:
                    return (м, ім)
        if isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name) and ф.value.id in мод.модулі:
            м = мод.модулі[ф.value.id]
            if м in self.м and ф.attr in self.м[м].функції:
                return (м, ф.attr)
        return None

    def бібліотека(self, мод, виклик):
        """(модуль бібліотеки чи джерел, імʼя) для `json.loads`, `re.search`, `протокол.розбір`, `розбір(...)`."""
        ф = виклик.func
        if isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name):
            return мод.модулі.get(ф.value.id) or (мод.імена.get(ф.value.id) or (ф.value.id,))[0], ф.attr
        if isinstance(ф, ast.Name) and ф.id in мод.імена:
            return мод.імена[ф.id]
        return None, None

    # ── насіння: параметри читачів реєстру ──
    def засіяти(self, мод, ім, ф):
        """Перший параметр читача протоколу/реєстру — сирий текст моделі (щоб побачити правки всередині реєстру)."""
        if мод.ім == "протокол" and ф.name in РОЗБІР_ПРОТОКОЛУ or (мод.ім == "схема_відповіді" and ф.name == "прочитати"):
            п = [а.arg for а in ф.args.args if а.arg != "self"]
            if п:
                self.параметри.setdefault((мод.ім, ім), {}).setdefault(п[0], set()).add(М)

    # ── мітки виразу ──
    def мітки(self, мод, в, зм):
        if в is None:
            return set()
        if isinstance(в, ast.Name):
            return set(зм.get(в.id, ())) | ({Ж} if в.id in СЛОВА_ЇЇ_ІМЕНА else set())
        if isinstance(в, ast.Subscript):
            к = в.slice
            if isinstance(к, ast.Constant) and isinstance(к.value, str):
                if к.value in self.ключі_м:
                    return {М}
                if к.value in self.ключі_ж:
                    return {Ж}
            return self.мітки(мод, в.value, зм)
        if isinstance(в, (ast.Tuple, ast.List, ast.Set)):
            return set().union(set(), *(self.мітки(мод, е, зм) for е in в.elts))
        if isinstance(в, ast.Dict):          # контейнер слів — не слова: `"ключ" in словник` читає ключ, не текст
            return set()
        if isinstance(в, ast.BoolOp):
            return set().union(*(self.мітки(мод, з, зм) for з in в.values))
        if isinstance(в, ast.IfExp):
            return self.мітки(мод, в.body, зм) | self.мітки(мод, в.orelse, зм)
        if isinstance(в, ast.BinOp):
            return self.мітки(мод, в.left, зм) | self.мітки(мод, в.right, зм)
        if isinstance(в, ast.JoinedStr):
            return set().union(set(), *(self.мітки(мод, з.value, зм) for з in в.values if isinstance(з, ast.FormattedValue)))
        if isinstance(в, (ast.Starred, ast.Await)):
            return self.мітки(мод, в.value, зм)
        if isinstance(в, ast.NamedExpr):
            return self.мітки(мод, в.value, зм)
        if isinstance(в, ast.Call):
            return self.мітки_виклику(мод, в, зм)
        return set()

    def мітки_виклику(self, мод, в, зм):
        ф = в.func
        арг = [self.мітки(мод, а, зм) for а in в.args]
        if isinstance(ф, ast.Attribute):
            if ф.attr == "get" and в.args and isinstance(в.args[0], ast.Constant):
                if в.args[0].value in self.ключі_м:
                    return {М}
                if в.args[0].value in self.ключі_ж:
                    return {Ж}
            if ф.attr in МЕТОДИ_РЕЄСТРУ:
                return set()
            if ф.attr in ТЕКСТОВІ:
                власні = self.мітки(мод, ф.value, зм)
                if ф.attr in ПРАВКИ or (ф.attr in {"strip", "lstrip", "rstrip"} and в.args and not self.пробіли(в.args[0])):
                    return self.після_правки(мод, в, власні, "." + ф.attr)
                return власні
        if isinstance(ф, ast.Name) and ф.id in ПРОПУСК_КОНТЕЙНЕРІВ:
            return set().union(set(), *арг)
        б, ім = self.бібліотека(мод, в)
        if б == "re" and ім in РЕГУЛЯРКИ and len(в.args) > (2 if ім in {"sub", "subn"} else 1):
            власні = арг[2 if ім in {"sub", "subn"} else 1]
            return self.після_правки(мод, в, власні, "re." + ім) if ім in {"sub", "subn"} else власні
        if б in {"json", "ast"} or ім in РОЗБІР_ПРОТОКОЛУ:
            return set()
        ц = self.ціль(мод, в)
        if ц:
            return set(self.повертає.get(ц, ()))
        return set()

    @staticmethod
    def пробіли(в):
        return isinstance(в, ast.Constant) and isinstance(в.value, str) and not в.value.strip()

    def після_правки(self, мод, в, власні, оп):
        """Текст моделі після правки: нова мітка `Р` з походженням (файл, рядок) — вона й дає п.4, якщо потрапить у розбір."""
        if М not in власні and not any(л[0] == "Р" for л in власні):
            return власні
        return власні | {("Р", мод.ім, в.lineno, оп)}

    # ── події ──
    def подія(self, мод, ім, вузол, вид, дія, мітки):
        ключ = (мод.ім, вузол.lineno, вид, дія)
        запис = self.події.setdefault(ключ, dict(модуль=мод.ім, функція=ім, рядок=вузол.lineno, вид=вид, дія=дія,
                                                 мітки=set()))
        запис["мітки"] |= мітки
        if вид in {"парс", "реєстр", "читання"}:
            self.приймальники.setdefault((мод.ім, ім), вузол.lineno)

    def форма_реєстру(self, мод, ф, в):
        """Назви форм реєстру, якими читає `.прочитати`: `СХЕМИ_ВІДПОВІДІ["Х"]`, `схема_за_назвою("Х")`, змінна з такого виразу,
        `визначити_схему(...)` (динамічна — усі форми, що вона може віддати: наявні в реєстрі без обмежень)."""
        вираз = в.func.value if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) else в
        if isinstance(вираз, ast.Name):
            for п in ast.walk(ф):
                if isinstance(п, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == вираз.id for ц in п.targets):
                    return self.форма_реєстру(мод, ф, п.value)
            return set()
        текст = текст_імені(вираз.func) if isinstance(вираз, ast.Call) else ""
        if текст.endswith("визначити_схему"):
            return {"*динамічна*"}
        назви = {с for с in константи_рядків(вираз) if с in self.форми}
        if not назви:
            назви = {с.upper() for с in константи_рядків(вираз) if с.upper() in self.форми}
        return назви

    def пройти(self, мод, ім, ф):
        """Один прохід функції: мітки змінних, події, передача міток у параметри викликаних функцій."""
        зм = {п: set(м) for п, м in self.параметри.get((мод.ім, ім), {}).items()}
        for а in ф.args.posonlyargs + ф.args.args + ф.args.kwonlyargs:
            if а.arg in СЛОВА_ЇЇ_ІМЕНА:
                зм.setdefault(а.arg, set()).add(Ж)
        для_мітки = [в for в in ast.walk(ф)]
        назви_функції = {а.arg for а in ф.args.posonlyargs + ф.args.args + ф.args.kwonlyargs}
        for в in для_мітки:
            if isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for ц in (в.targets if isinstance(в, ast.Assign) else [в.target]):
                    назви_функції |= {н.id for н in ast.walk(ц) if isinstance(н, ast.Name)}
        змінилось = False
        for _ in range(3):
            for в in для_мітки:
                if isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and в.value is not None:
                    м = self.мітки(мод, в.value, зм)
                    цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                    if м:
                        for ц in цілі:
                            if isinstance(ц, (ast.Tuple, ast.List)):  # розпаковка кількох значень: її слова не розкладаємо
                                м = {л for л in м if л[0] != "Ж"}
                            for н in ast.walk(ц):
                                if isinstance(н, ast.Name):
                                    зм.setdefault(н.id, set()).update(м)
                elif isinstance(в, (ast.For, ast.comprehension)):
                    м = self.мітки(мод, в.iter, зм)
                    ключі_словника = set()  # ключі словника (`.items()` — перший елемент, `.keys()`) — коди, не її слова
                    if isinstance(в.iter, ast.Call) and isinstance(в.iter.func, ast.Attribute):
                        if в.iter.func.attr == "keys":
                            ключі_словника = {н.id for н in ast.walk(в.target) if isinstance(н, ast.Name)}
                        elif в.iter.func.attr == "items" and isinstance(в.target, ast.Tuple) and в.target.elts:
                            ключі_словника = {н.id for н in ast.walk(в.target.elts[0]) if isinstance(н, ast.Name)}
                    if м:
                        for н in ast.walk(в.target):
                            if isinstance(н, ast.Name) and н.id in ключі_словника:
                                зм.setdefault(н.id, set()).update({л for л in м if л[0] != "Ж"})
                            elif isinstance(н, ast.Name):  # змінна циклу не скидає її слова на однойменну змінну функції
                                зм.setdefault(н.id, set()).update(
                                    {л for л in м if л[0] != "Ж"} if н.id in назви_функції else м)
                elif isinstance(в, ast.NamedExpr):
                    м = self.мітки(мод, в.value, зм)
                    if м and isinstance(в.target, ast.Name):
                        зм.setdefault(в.target.id, set()).update(м)
        if any(М in м or any(л[0] == "Р" for л in м) for м in зм.values()):
            self.тримає_м.add((мод.ім, ім))
        for в in для_мітки:
            if isinstance(в, ast.Return) and в.value is not None:
                м = {л for л in self.мітки(мод, в.value, зм) if л[0] != "Ж"}
                if м - self.повертає.get((мод.ім, ім), set()):
                    self.повертає.setdefault((мод.ім, ім), set()).update(м)
                    змінилось = True
            elif isinstance(в, ast.Call):
                змінилось |= self.виклик(мод, ім, ф, в, зм)
            elif isinstance(в, ast.Compare):
                self.порівняння(мод, ім, в, зм)
            elif isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Slice):
                м = self.мітки(мод, в.value, зм)
                межі = [в.slice.lower, в.slice.upper]
                if (М in м or any(л[0] == "Р" for л in м)) and any(е is not None and not isinstance(е, ast.Constant)
                                                                    for е in межі):
                    self.подія(мод, ім, в, "правка", "зріз за знайденим", м)
            elif isinstance(в, ast.BinOp) and isinstance(в.op, ast.Add):
                м = self.мітки(мод, в, зм)
                const = [е for е in (в.left, в.right) if isinstance(е, ast.Constant) and isinstance(е.value, str)]
                if (М in м) and const and re.fullmatch(r"[\s\[\]{}\"']+", const[0].value or "x") and const[0].value.strip():
                    self.подія(мод, ім, в, "правка", "дописані дужки", м)
        return змінилось

    def виклик(self, мод, ім, ф, в, зм):
        """Подія виклику над міченим текстом і передача міток аргументів у параметри викликаної функції."""
        змінилось = False
        б, ч = self.бібліотека(мод, в)
        арг = [self.мітки(мод, а, зм) for а in в.args]
        власні = self.мітки(мод, в.func.value, зм) if isinstance(в.func, ast.Attribute) else set()
        сирі = lambda м: М in м or any(л[0] == "Р" for л in м)
        if isinstance(в.func, ast.Attribute) and в.func.attr in МЕТОДИ_РЕЄСТРУ and арг and сирі(арг[0]):
            self.подія(мод, ім, в, "реєстр", "%s: %s" % (в.func.attr, ",".join(sorted(self.форма_реєстру(мод, ф, в)))
                                                         or "?"), арг[0])
        elif (б == "протокол" and ч in РОЗБІР_ПРОТОКОЛУ or (isinstance(в.func, ast.Name) and в.func.id in РОЗБІР_ПРОТОКОЛУ
                                                           and мод.імена.get(в.func.id, ("",))[0] == "протокол")) \
                and арг and сирі(арг[0]):
            self.подія(мод, ім, в, "парс", "протокол." + (ч or ""), арг[0])
        elif (б, ч) in {("json", "loads"), ("ast", "literal_eval")} and арг and сирі(арг[0]):
            self.подія(мод, ім, в, "парс", "%s.%s" % (б, ч), арг[0])
        elif isinstance(в.func, ast.Attribute) and в.func.attr == "raw_decode" and арг and сирі(арг[0]):
            self.подія(мод, ім, в, "парс", "raw_decode", арг[0])
        elif б == "re" and ч in РЕГУЛЯРКИ and len(в.args) > (2 if ч in {"sub", "subn"} else 1) \
                and сирі(арг[2 if ч in {"sub", "subn"} else 1]):
            self.подія(мод, ім, в, "правка" if ч in {"sub", "subn"} else "читання", "re." + ч,
                       арг[2 if ч in {"sub", "subn"} else 1])
        elif isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name) and в.func.value.id in мод.зразки \
                and в.func.attr in РЕГУЛЯРКИ and арг and сирі(арг[0]):
            self.подія(мод, ім, в, "правка" if в.func.attr in {"sub", "subn"} else "читання", "регулярка." + в.func.attr,
                       арг[0])
        elif isinstance(в.func, ast.Attribute) and сирі(власні):
            if в.func.attr in ПРАВКИ or (в.func.attr in {"strip", "lstrip", "rstrip"} and в.args
                                         and not self.пробіли(в.args[0])):
                self.подія(мод, ім, в, "правка", "." + в.func.attr, власні)
            elif в.func.attr in ЧИТАННЯ_МЕТОДИ:
                self.подія(мод, ім, в, "читання", "." + в.func.attr, власні)
        # її слова: регулярка й пошук над ними
        if б == "re" and ч in РЕГУЛЯРКИ and ч not in {"sub", "subn"} and len(в.args) > 1 and є_ж(арг[1]):  # sub — нормалізація, не вибір
            self.подія(мод, ім, в, "слова", "re." + ч, арг[1])
        elif isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name) and в.func.value.id in мод.зразки \
                and в.func.attr in РЕГУЛЯРКИ and в.func.attr not in {"sub", "subn"} and арг and є_ж(арг[0]):
            self.подія(мод, ім, в, "слова", "регулярка." + в.func.attr, арг[0])
        elif isinstance(в.func, ast.Attribute) and є_ж(власні) and в.func.attr in ЧИТАННЯ_МЕТОДИ:
            self.подія(мод, ім, в, "слова", "." + в.func.attr, власні)
        # передача міток у параметри
        ц = self.ціль(мод, в)
        if ц:
            цф = self.м[ц[0]].функції[ц[1]]
            п = [а.arg for а in цф.args.posonlyargs + цф.args.args]
            if п and п[0] in {"self", "cls"}:
                п = п[1:]
            пари = list(zip(п, в.args)) + [(к.arg, к.value) for к in в.keywords if к.arg in п]
            for назва, вираз in пари:
                прямо = self.пряме_слово(вираз)
                м = {(("Ж", л[1] + 1) if л[0] == "Ж" else л) for л in self.мітки(мод, вираз, зм)
                     if л[0] != "Ж" or (прямо and л[1] < ГЛИБИНА_СЛІВ)}
                if м - self.параметри.get(ц, {}).get(назва, set()):
                    self.параметри.setdefault(ц, {}).setdefault(назва, set()).update(м)
                    змінилось = True
        return змінилось

    @staticmethod
    def пряме_слово(в):
        """Її слова йдуть у параметр лише самі: ім'я змінної чи `str()`/`.strip()`/`.lower()` від нього, не елемент контейнера."""
        while True:
            if isinstance(в, ast.Name):
                return True
            if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "str" and len(в.args) == 1:
                в = в.args[0]
            elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr in {"strip", "lower", "casefold"}:
                в = в.func.value
            else:
                return False

    def порівняння(self, мод, ім, в, зм):
        """`"…" in текст_моделі` і порівняння її слів із літералом — читання."""
        if len(в.ops) == 1 and isinstance(в.ops[0], (ast.In, ast.NotIn)) and isinstance(в.left, ast.Constant) \
                and isinstance(в.left.value, str):
            м = self.мітки(мод, в.comparators[0], зм)
            if М in м:
                self.подія(мод, ім, в, "читання", "in", м)
            elif є_ж(м) and self.пряме_слово(в.comparators[0]):  # `"…" in слова`, не ключ у словнику
                self.подія(мод, ім, в, "слова", "in", м)
        elif len(в.ops) == 1 and isinstance(в.ops[0], (ast.Eq, ast.NotEq, ast.In, ast.NotIn)):
            # її слова (пряма змінна) проти літерала чи переліку літералів: `уривок == "вечір"`, `слова in ("а", "б")`
            ліве, праве = в.left, в.comparators[0]
            літерал = lambda е: (isinstance(е, ast.Constant) and isinstance(е.value, str)) or \
                (isinstance(е, (ast.Tuple, ast.List, ast.Set)) and е.elts and all(isinstance(х, ast.Constant) and isinstance(х.value, str) for х in е.elts))
            for слово, інше in ((ліве, праве), (праве, ліве)):
                if isinstance(в.ops[0], (ast.In, ast.NotIn)) and слово is праве:
                    continue
                if літерал(інше) and self.пряме_слово(слово) and є_ж(self.мітки(мод, слово, зм)):
                    self.подія(мод, ім, в, "слова", "==" if isinstance(в.ops[0], (ast.Eq, ast.NotEq)) else "in", self.мітки(мод, слово, зм))
                    break

    def виконати(self):
        for _ in range(14):
            зміни = [self.пройти(мод, ім, ф) for мод in self.м.values() for ім, ф in мод.функції.items()]
            if not any(зміни):
                break
        return self


# ── PYTHON: СТРУКТУРА (без потоку) ────────────────────────────────────────────
ЗНАКИ_JSON = {"}", "]", "{", "[", ",", '"', ":", '\\"'}


def батьки(ф):
    return {id(д): п for п in ast.walk(ф) for д in ast.iter_child_nodes(п)}


def імена_вузла(в):
    """Імена, які вузол AST несе: змінна, атрибут, ключове слово, функція."""
    return [в.id] if isinstance(в, ast.Name) else [в.attr] if isinstance(в, ast.Attribute) \
        else [в.arg] if isinstance(в, ast.keyword) and в.arg \
        else [в.name] if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)) else []


class Структура:
    """Знахідки, яким не потрібен потік: ремонт обʼєкта (`нотатки`), дописані знаки JSON, ігнорований сторож, гілка
    невдачі читача, дрот із словами крамниці, вид поля поза `паспорт_поля.py`."""

    def __init__(self, аналіз):
        self.а = аналіз
        self.м = аналіз.м
        self._прямі_викликачі = None

    def викликачі(self, ключ):
        """Прямі викликачі функції (модуль, імʼя) за графом викликів — лише справжні виклики, без прив'язок до реєстру."""
        if self._прямі_викликачі is None:
            зв = {}
            for мод in self.м.values():
                for ім, ф in мод.функції.items():
                    for в in ast.walk(ф):
                        if isinstance(в, ast.Call):
                            ц = self.а.ціль(мод, в)
                            if ц and ц != (мод.ім, ім):
                                зв.setdefault(ц, set()).add((мод.ім, ім))
            self._прямі_викликачі = зв
        return self._прямі_викликачі.get(ключ, set())

    def запасний_хід_у_викликачах(self, ключ, глибина=3, шлях=frozenset(), ловлять=False):
        """Запасний хід стоїть у викликачах: КОЖЕН викликач функції має його сам (шаблон/`запасн…`) чи, нагору до
        `глибина` ланок, усі його викликачі мають. `ловлять` (для `raise` читача): викликач, що кожен виклик тримає в
        `try`, чий `except` не кидає далі й несе причину (`as е` вживано в тілі), теж запасний хід — збій стає рядком
        звіту. Нема викликачів у продукті чи хоч один без ходу — False (місце лишається)."""
        вик = self.викликачі(ключ) - шлях
        if not вик or глибина <= 0:
            return False
        for м, ім in вик:
            ф = self.м[м].функції[ім]
            if self.є_запасний_хід(ф) or (ловлять and self.виклики_ловлять_з_причиною(self.м[м], ф, ключ)):
                continue
            if not self.запасний_хід_у_викликачах((м, ім), глибина - 1, шлях | {ключ}, ловлять):
                return False
        return True

    ВИНЯТКИ_ЗБОЮ = {"Exception", "BaseException", "ValueError", "OSError", "RuntimeError", "LookupError"}

    def виклики_ловлять_з_причиною(self, мод, ф, ключ):
        """Усі виклики `ключ` у `ф` стоять у тілі `try`, чий обробник ловить збій, не кидає далі й вживає причину."""
        пб = батьки(ф)
        виклики = [в for в in ast.walk(ф) if isinstance(в, ast.Call) and self.а.ціль(мод, в) == ключ]
        if not виклики:
            return False

        def ловить(обр):
            типи = [] if обр.type is None else [обр.type] if not isinstance(обр.type, ast.Tuple) else list(обр.type.elts)
            if обр.type is not None and not any(текст_імені(т).split(".")[-1] in self.ВИНЯТКИ_ЗБОЮ for т in типи):
                return False
            if any(isinstance(н, ast.Raise) for ст in обр.body for н in ast.walk(ст)):
                return False
            return (bool(обр.name) and any(isinstance(н, ast.Name) and н.id == обр.name
                                           for ст in обр.body for н in ast.walk(ст))) \
                or any(ЗАПАСНИЙ_ХІД.search(т) for ст in обр.body for н in ast.walk(ст) for т in імена_вузла(н))

        for в in виклики:
            дитя, п, захищено = в, пб.get(id(в)), False
            while п is not None and not захищено:
                if isinstance(п, ast.Try) and дитя in п.body and any(ловить(о) for о in п.handlers):
                    захищено = True
                дитя, п = п, пб.get(id(п))
            if not захищено:
                return False
        return True

    def ловлять_усі(self, ключ, глибина=6, шлях=frozenset()):
        """Виняток із функції `ключ` не виходить нагору: КОЖЕН прямий викликач тримає кожен її виклик у `try`, чий
        `except` ловить збій, не кидає далі й вживає причину чи запасний хід, або, нагору до `глибина` ланок, усі його
        викликачі ловлять так само. Запасний хід ім'ям деінде у викликачі винятку не ловить: `raise` минає його й
        виходить з мосту (п.3(д), рішення 08.11). Нема викликачів у обсязі приладу — виняток виходить (False)."""
        вик = self.викликачі(ключ) - шлях
        if not вик or глибина <= 0:
            return False
        for м, ім in вик:
            if self.виклики_ловлять_з_причиною(self.м[м], self.м[м].функції[ім], ключ):
                continue
            if not self.ловлять_усі((м, ім), глибина - 1, шлях | {ключ}):
                return False
        return True

    @staticmethod
    def вільні_кидки(ф):
        """Рядки `raise` у `ф`, які не ловить її власний `try` (тіло `try` з обробником); `raise` в обробнику
        `except` кидає далі — вільний."""
        пб = батьки(ф)
        вих = []
        for н in ast.walk(ф):
            if not isinstance(н, ast.Raise):
                continue
            дитя, п, зловлено = н, пб.get(id(н)), False
            while п is not None and п is not ф:
                if isinstance(п, ast.Try) and п.handlers and дитя in п.body:
                    зловлено = True
                    break
                дитя, п = п, пб.get(id(п))
            if not зловлено:
                вих.append(н.lineno)
        return sorted(set(вих))

    # п.3(д): `raise` будівника входу моделі виходить з мосту — хід руки втрачено разом із прийнятою відповіддю
    def кидок_будівника(self, функції_конуса):
        """Будівник входу моделі (модулі `МОДУЛІ_ВХОДУ`, функція з іменем дроту) у конусі ендпойнта чи клієнта, чий
        `raise` не ловить ні він, ні викликачі нагору (`ловлять_усі`): виняток виходить з мосту, і що код уже
        прийняв із попередньої відповіді (вердикт складання перед ремонтом), губиться з усім кроком."""
        вих = []
        for мод, ім, ф in self.функції():
            if (мод.ім, ім) not in функції_конуса or мод.ім in РЕЄСТР_МОД:
                continue
            if not (мод.ім in МОДУЛІ_ВХОДУ or ІМЯ_ДРОТУ.search(ім.split(".")[-1])):
                continue
            рядки = self.вільні_кидки(ф)
            if рядки and not self.ловлять_усі((мод.ім, ім)):
                for р in рядки:
                    вих.append((мод.ім, ім, р, "`raise` будівника входу моделі `%s` не ловить ні він, ні викликачі до "
                                "обробника мосту — виняток виходить з мосту, і крок губить і те, що код уже прийняв "
                                "(зупинка без запасного ходу)" % ім))
        return вих

    # п.3(е): після останньої спроби причину відхилення погашено — показ бере відповідь як прийняту
    def причина_погашена(self, функції_конуса):
        """Функція закриває повтор (`…["повтор"] = None`) і в тій самій функції пише причину (`…["причина"]`)
        значенням, що на якійсь гілці — `None`: відхилене перевіркою після другої спроби йде без причини, і запасний
        хід показу (він стоїть на причині) не спрацьовує — відхилене йде далі, у кеш, як прийняте."""
        def ключ_підписки(ц, ім_ключа):
            return isinstance(ц, ast.Subscript) and isinstance(ц.slice, ast.Constant) and ц.slice.value == ім_ключа

        def може_none(в):
            if isinstance(в, ast.Constant) and в.value is None:
                return True
            return isinstance(в, ast.IfExp) and (може_none(в.body) or може_none(в.orelse))
        вих = []
        for мод, ім, ф in self.функції():
            if (мод.ім, ім) not in функції_конуса or мод.ім in РЕЄСТР_МОД:
                continue
            присв = [в for в in ast.walk(ф) if isinstance(в, ast.Assign) and len(в.targets) == 1]
            if not any(ключ_підписки(в.targets[0], "повтор") and isinstance(в.value, ast.Constant) and в.value.value is None
                       for в in присв):
                continue
            for в in присв:
                if ключ_підписки(в.targets[0], "причина") and може_none(в.value):
                    вих.append((мод.ім, ім, в.lineno, "після останньої спроби (`повтор` = None) причину відхилення в `%s` "
                                "погашено (`None` на гілці) — запасний хід показу стоїть на причині, тож відхилене йде "
                                "далі, у кеш, як прийняте" % ім))
        return вих

    # п.3(є): її слова, яких шар не прочитав, знято рядком лише в журналі — заяви їй нема (рішення 08.11, #3379)
    def слова_зняті_без_заяви(self, функції_конуса):
        """Рядок звіту шару `… · step=layer · … · code=not_taken` (поле ходу знято) — місце, коли знятого нема в
        `не_записано` репліки (лише воно дає перекладачеві `not_recorded` кодом поля, `мовний_шар.розмова_з_відповіді`):
        `не_взято` / `не_взято_кодом` — журнал і звіт власника, а не заява їй. Рядок у функції `…_рядком` —
        місце в кожному її виклику. Не місця: блок під `if <ім'я>:`, чиє ім'я стоїть у `не_записано=` тієї самої
        функції (знято — і сказано їй); виклик над `невідомо` — перекладач сам сказав «unknown», її слів не знято."""
        def літерали(ф):
            докстрінг = ф.body[0].value if ф.body and isinstance(ф.body[0], ast.Expr) else None
            return [н for н in ast.walk(ф) if isinstance(н, ast.Constant) and isinstance(н.value, str) and н is not докстрінг
                    and "step=layer" in н.value and "code=not_taken" in н.value]

        def код(л):
            return л.value.split(" · ", 1)[0]

        def сказано_їй(ф, н, пб):
            заява = set()
            for к in ast.walk(ф):
                if isinstance(к, ast.keyword) and к.arg == "не_записано":
                    заява |= {і.id for і in ast.walk(к.value) if isinstance(і, ast.Name)}
            п = пб.get(id(н))
            while п is not None and п is not ф:
                if isinstance(п, ast.If) and {і.id for і in ast.walk(п.test) if isinstance(і, ast.Name)} & заява:
                    return True
                п = пб.get(id(п))
            return False

        def над_невідомим(н, пб):
            п = пб.get(id(н))
            while п is not None:
                if isinstance(п, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
                    return any("невідомо" in ast.unparse(г.iter) for г in п.generators)
                if isinstance(п, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return False
                п = пб.get(id(п))
            return False
        помічники, вих = {}, []
        for мод, ім, ф in self.функції():
            if мод.ім in РЕЄСТР_МОД:
                continue
            лл = літерали(ф)
            if лл and ім.split(".")[-1].endswith("_рядком"):
                помічники[ім.split(".")[-1]] = код(лл[0])
                continue
            if (мод.ім, ім) not in функції_конуса:
                continue
            пб = батьки(ф)
            for л in лл:
                if not сказано_їй(ф, л, пб):
                    вих.append((мод.ім, ім, л.lineno, "поле ходу знято (`%s`) рядком лише в журналі (`не_взято_кодом`): "
                                "у `не_записано` репліки його нема — заяви їй, що сказане не взято, нема" % код(л)))
        for мод, ім, ф in self.функції():
            if (мод.ім, ім) not in функції_конуса or мод.ім in РЕЄСТР_МОД or ім.split(".")[-1] in помічники:
                continue
            пб = батьки(ф)
            for в in ast.walk(ф):
                if isinstance(в, ast.Call) and текст_імені(в.func).split(".")[-1] in помічники \
                        and not над_невідомим(в, пб) and not сказано_їй(ф, в, пб):
                    п_ім = текст_імені(в.func).split(".")[-1]
                    вих.append((мод.ім, ім, в.lineno, "її слова, яких шар не прочитав і після повтору, знято (`%s`, "
                                "`%s`) рядком лише в журналі (`не_взято`): у `не_записано` репліки їх нема — заяви їй, "
                                "що сказане не взято, нема" % (помічники[п_ім], п_ім)))
        return вих

    def функції(self):
        for мод in self.м.values():
            for ім, ф in мод.функції.items():
                yield мод, ім, ф

    # п.4(б): запис у `нотатки` — код сам називає це ремонтом форми
    def нотатки(self):
        """Гілка ремонту: блок, де код пише в `нотатки` і міняє дані (присвоєння, зріз, видалення) — одне місце на гілку,
        на першому записі. Блок лише з записом і `continue`/`return` (повідомлення про відхилене) — не ремонт."""
        def запис(ст):
            ціль = None
            if isinstance(ст, ast.Expr) and isinstance(ст.value, ast.Call) and isinstance(ст.value.func, ast.Attribute) \
                    and ст.value.func.attr in {"append", "extend"}:
                ціль = ст.value.func.value
            elif isinstance(ст, ast.AugAssign):
                ціль = ст.target
            while isinstance(ціль, ast.Subscript):
                ціль = ціль.value
            return isinstance(ціль, ast.Name) and ціль.id == "нотатки"
        вих = []
        for мод, ім, ф in self.функції():
            for блок in self.блоки(ф):
                записи = [ст for ст in блок if запис(ст)]
                змінює = any((isinstance(ст, (ast.Assign, ast.AugAssign, ast.Delete)) and not запис(ст)) or
                             (isinstance(ст, ast.Return) and ст.value is not None and not (isinstance(ст.value, ast.Constant) and ст.value.value is None))
                             for ст in блок)  # повернути виправлене — теж зміна
                if записи and змінює:
                    вих.append((мод.ім, ім, записи[0].lineno, "гілка ремонту: запис у `нотатки` й зміна даних відповіді в одному "
                                "блоці — код сам називає це ремонтом форми відповіді"))
        return вих

    # п.4(а): функція з текстом моделі дописує/екранує знаки JSON у вихідному буфері — одна гілка ремонту на функцію
    def знаки_json(self):
        вих = []
        for мод, ім, ф in self.функції():
            if (мод.ім, ім) not in self.а.тримає_м:
                continue
            знаки = []
            for в in ast.walk(ф):
                const = None
                if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr in {"append", "insert"} \
                        and в.args and isinstance(в.args[-1], ast.Constant) \
                        and not (isinstance(в.func.value, ast.Name) and в.func.value.id.startswith("стек")):
                    const = в.args[-1]
                elif isinstance(в, ast.AugAssign) and isinstance(в.op, ast.Add) and isinstance(в.value, ast.Constant):
                    const = в.value
                if const is not None and isinstance(const.value, str) and const.value in ЗНАКИ_JSON:
                    знаки.append(const.value)
            if знаки:
                вих.append((мод.ім, ім, ф.lineno, "функція `%s` дописує/екранує знаки JSON у тексті моделі (%d вставок: %s) — "
                            "ремонт форми" % (ім, len(знаки), " ".join(sorted(set(знаки))))))
        return вих

    # п.3(а): сторож/перевірка, чий результат не вживається
    def сторож_ігнорований(self, функції_конуса):
        вих = []
        for мод, ім, ф in self.функції():
            if (мод.ім, ім) not in функції_конуса or мод.ім in РЕЄСТР_МОД:
                continue
            пб = батьки(ф)
            for в in ast.walk(ф):
                if not isinstance(в, ast.Call):
                    continue
                назва = текст_імені(в.func)
                кінець = назва.split(".")[-1]
                if not (кінець == "перевірити" or кінець.startswith("сторож") or кінець.startswith("_сторож")):
                    continue
                п = пб.get(id(в))
                if isinstance(п, ast.Expr):
                    вих.append((мод.ім, ім, в.lineno, "результат перевірки/сторожа `%s` не вживається — відхилене йде далі" % назва))
                elif isinstance(п, ast.Assign) and len(п.targets) == 1 and isinstance(п.targets[0], ast.Name):
                    ім_зм = п.targets[0].id
                    читається = any(isinstance(н, ast.Name) and н.id == ім_зм and isinstance(н.ctx, ast.Load)
                                    for н in ast.walk(ф))
                    if not читається:
                        вих.append((мод.ім, ім, в.lineno, "результат перевірки `%s` записано й не читано" % назва))
        return вих

    # п.3(г): відхилене перевіркою записано в звіт, а запасного ходу коду в функції нема
    def відхилене_без_ходу(self, функції_конуса):
        вих = []
        for мод, ім, ф in self.функції():
            if (мод.ім, ім) not in функції_конуса or мод.ім in РЕЄСТР_МОД or self.є_запасний_хід(ф) \
                    or self.запасний_хід_у_викликачах((мод.ім, ім)):
                continue
            for блок in self.блоки(ф):
                запис = next((ст for ст in блок if self.запис_відхиленого(ст)), None)
                if запис is not None and self.втрата_в_гілці(блок, запис):
                    вих.append((мод.ім, ім, запис.lineno, "відхилене перевіркою записано в `%s`, а запасного ходу коду "
                                "(шаблон заяви, `запасн…`) у функції `%s` нема — що код знає, жінка не побачить" %
                                (self.запис_відхиленого(запис), ім)))
        return вих

    @staticmethod
    def втрата_в_гілці(блок, запис):
        """Гілка справді губить відхилене: в ній присвоєно порожнє, є `continue`/`break`/`return`, або сам запис несе
        порожнє (`теми=[]`) — нічого не лишено. Запис, де решту показано (обрізане речення), втратою не лічиться."""
        if any(isinstance(ст, (ast.Continue, ast.Break, ast.Return)) or
               (isinstance(ст, ast.Assign) and порожнє_значення(ст.value)) for ст in блок):
            return True
        return any(isinstance(в, ast.keyword) and в.arg and порожнє_значення(в.value) and в.arg != "зняте"
                   for в in ast.walk(запис))

    @staticmethod
    def є_запасний_хід(ф):
        for в in ast.walk(ф):
            назви = [в.id] if isinstance(в, ast.Name) else [в.attr] if isinstance(в, ast.Attribute) \
                else [в.arg] if isinstance(в, ast.keyword) and в.arg \
                else [в.name] if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)) else []
            if any(ЗАПАСНИЙ_ХІД.search(н) for н in назви):
                return True
        return False

    @staticmethod
    def запис_відхиленого(ст):
        """Імʼя списку звіту, коли `ст` пише в нього запис відхиленого (з ключем `чому`, не «лишено»); інакше None."""
        if isinstance(ст, ast.AugAssign) and isinstance(ст.target, ast.Name) and ст.target.id in ЗАПИС_ВІДХИЛЕНОГО \
                and isinstance(ст.op, ast.Add):
            return ст.target.id
        if not (isinstance(ст, ast.Expr) and isinstance(ст.value, ast.Call) and isinstance(ст.value.func, ast.Attribute)
                and ст.value.func.attr in {"append", "extend"} and isinstance(ст.value.func.value, ast.Name)
                and ст.value.func.value.id in ЗАПИС_ВІДХИЛЕНОГО):
            return None
        ключі = set()
        for а in ст.value.args:
            for в in ast.walk(а):
                if isinstance(в, ast.keyword) and в.arg:
                    ключі.add(в.arg)
                elif isinstance(в, ast.Dict):
                    ключі |= {к.value for к in в.keys if isinstance(к, ast.Constant)}
        if "чому" not in ключі or ключі & ЛИШЕНО_ВІДХИЛЕНЕ:
            return None
        return ст.value.func.value.id

    # п.3(б): гілка невдачі читача — зупинка чи втрата без причини
    def невдача_читача(self, внутрішні=frozenset()):
        """`внутрішні` — читачі, що їх кличе інший читач: невдачу кінцево розв'язує зовнішній, тут вона лише сигнал нагору."""
        вих = []
        події = {}
        for п in self.а.події.values():
            if п["вид"] in {"парс", "реєстр"} and п["модуль"] not in РЕЄСТР_МОД:
                події.setdefault((п["модуль"], п["функція"]), []).append(п["рядок"])
        for мод, ім, ф in self.функції():
            рядки = події.get((мод.ім, ім))
            if not рядки or (мод.ім, ім) in внутрішні:
                continue
            імʼям = self.запасний_хід_у_викликачах((мод.ім, ім))
            ловлять = self.ловлять_усі((мод.ім, ім))

            def покрито(д):
                """Порожній вихід — запасний хід у викликачах ім'ям; `raise` — лише лов нагору (`ловлять_усі`):
                запасний хід ім'ям деінде у викликачі винятку не ловить (рішення 08.11)."""
                return ловлять if д.startswith("raise") else імʼям
            пб = батьки(ф)
            for блок in self.блоки(ф):
                for і, в in enumerate(блок):
                    вираз_подія = [н for н in ast.walk(в) if isinstance(н, ast.Call) and н.lineno in рядки] \
                        if isinstance(в, (ast.Assign, ast.Expr, ast.Return)) else []
                    if isinstance(в, ast.Try) and any(isinstance(н, ast.Call) and н.lineno in рядки
                                                       for ст in в.body for н in ast.walk(ст)):
                        for обр in в.handlers:
                            д = self.невдача(обр.body)
                            if д and not покрито(д):
                                вих.append((мод.ім, ім, обр.lineno, "гілка невдачі розбору (except): " + д))
                    if not вираз_подія or not isinstance(в, ast.Assign):
                        continue
                    імена = {н.id for ц in в.targets for н in ast.walk(ц) if isinstance(н, ast.Name)}
                    for наст in блок[і + 1:і + 4]:
                        if isinstance(наст, ast.If) and any(isinstance(н, ast.Name) and н.id in імена
                                                            for н in ast.walk(наст.test)):
                            гілка = self.гілка_невдачі(наст)
                            д = self.невдача(гілка, self.у_тілі_try(наст, пб)) if гілка else None
                            if д and not покрито(д):
                                вих.append((мод.ім, ім, наст.lineno, "гілка невдачі розбору: " + д))
                            break
        return вих

    @staticmethod
    def блоки(ф):
        for в in ast.walk(ф):
            for поле in ("body", "orelse", "finalbody"):
                б = getattr(в, поле, None)
                if isinstance(б, list) and б and isinstance(б[0], ast.stmt):
                    yield б

    @staticmethod
    def гілка_невдачі(якщо):
        """Гілка `if`, що виконується, коли розбір не вдався: `not x`, `x is None` → тіло; інакше `else`."""
        т = якщо.test
        негатив = (isinstance(т, ast.UnaryOp) and isinstance(т.op, ast.Not)) or \
            (isinstance(т, ast.Compare) and any(isinstance(о, (ast.Is, ast.Eq)) for о in т.ops)
             and any(isinstance(с, ast.Constant) and с.value is None for с in т.comparators))
        if isinstance(т, ast.BoolOp) and isinstance(т.op, ast.Or):
            негатив = any((isinstance(з, ast.UnaryOp) and isinstance(з.op, ast.Not)) or
                          (isinstance(з, ast.Compare) and any(isinstance(с, ast.Constant) and с.value is None
                                                              for с in з.comparators) and isinstance(з.ops[0], ast.Is))
                          for з in т.values)
        return якщо.body if негатив else якщо.orelse

    @staticmethod
    def у_тілі_try(вузол, пб):
        """Вузол стоїть у тілі `try` з обробником: `raise` тут ловить власний `except`, а не зупиняє хід."""
        дитя, п = вузол, пб.get(id(вузол))
        while п is not None:
            if isinstance(п, ast.Try) and п.handlers and дитя in п.body:
                return True
            дитя, п = п, пб.get(id(п))
        return False

    @staticmethod
    def невдача(гілка, у_try=False):
        """Опис «поганої» гілки невдачі: `raise` (зупинка) або лише порожній вихід без причини (втрата); інакше None."""
        if not гілка:
            return None
        if not у_try and any(isinstance(н, ast.Raise) for ст in гілка for н in ast.walk(ст)):
            return "raise — зупинка без запасного ходу"
        if all(isinstance(ст, (ast.Pass, ast.Continue, ast.Break)) or
               (isinstance(ст, ast.Return) and (ст.value is None or порожнє_значення(ст.value))) for ст in гілка):
            return "порожній вихід без причини — втрата без рядка звіту"
        return None

    def перетворений_будівник(self, б, модулі_збирача, ребра, кеш_конусів=None):
        """Будівник, чий результат на кожному шляху до моделі йде через функцію-перетворювач ід."""
        if кеш_конусів is None:
            кеш_конусів = {}

        def у_конусі(старт):
            if старт not in кеш_конусів:
                кеш_конусів[старт] = конус(старт, ребра)
            return кеш_конусів[старт]

        шляхи = [з for з in модулі_збирача if з == б or б in у_конусі(з)]
        if not шляхи:
            return False
        for зб_мод, зб_ім in шляхи:
            мод_об = self.м.get(зб_мод)
            if not мод_об or зб_ім not in мод_об.функції:
                return False
            ф_зб = мод_об.функції[зб_ім]

            def веде(н):
                if not isinstance(н, ast.Call):
                    return False
                ц = self.а.ціль(мод_об, н)
                return ц == б or (ц is not None and б in у_конусі(ц))

            стан_зм = {}

            def оцінити(в):
                if isinstance(в, ast.Call):
                    ім = текст_імені(в.func).split(".")[-1]
                    if ім in ПЕРЕТВОРЮВАЧІ_ІД:
                        всі = list(ast.walk(в))
                        if any(isinstance(н, ast.Call) and н is not в and веде(н) for н in всі) \
                                or any(isinstance(н, ast.Name) and стан_зм.get(н.id) in ("сирий", "перетворений") for н in всі):
                            return "перетворений"
                    if веде(в):
                        return "сирий"
                if isinstance(в, ast.Name):
                    return стан_зм.get(в.id)
                ст_під = None
                for д in ast.iter_child_nodes(в):
                    с = оцінити(д)
                    if с == "сирий":
                        return "сирий"
                    if с == "перетворений":
                        ст_під = "перетворений"
                return ст_під

            має_сирий = False
            дійшов_перетвореним = False
            for ст in ast.walk(ф_зб):
                if isinstance(ст, ast.Assign):
                    ст_знач = оцінити(ст.value)
                    if ст_знач:
                        for ц in ст.targets:
                            if isinstance(ц, ast.Name):
                                стан_зм[ц.id] = ст_знач
                elif isinstance(ст, ast.Call) and текст_імені(ст.func).endswith("зібрати"):
                    for арг in ст.args + [кв.value for кв in ст.keywords]:
                        с = оцінити(арг)
                        if с == "сирий":
                            має_сирий = True
                        elif с == "перетворений":
                            дійшов_перетвореним = True

            if має_сирий or not дійшов_перетвореним:
                return False
        return True

    # п.5: дріт моделі — слова крамниці й повний ід
    def дріт(self, модулі_збирача, ребра=None):
        if ребра is None:
            ребра = ребра_викликів(self.а)
        вих = []
        кеш_перетворених = {}
        кеш_конусів = {}
        for мод, ім, ф in self.функції():
            if мод.ім != "дріт_моделі" and not ІМЯ_ДРОТУ.search(ім):
                continue
            б = (мод.ім, ім)
            for в in ast.walk(ф):
                пари = []
                if isinstance(в, ast.Dict):
                    пари = [(к.value, з) for к, з in zip(в.keys, в.values) if isinstance(к, ast.Constant)]
                elif isinstance(в, ast.Call) and текст_імені(в.func) == "dict":
                    пари = [(к.arg, к.value) for к in в.keywords if к.arg]
                elif isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Subscript) \
                        and isinstance(в.targets[0].slice, ast.Constant):
                    пари = [(в.targets[0].slice.value, в.value)]
                for ключ, значення in пари:
                    ключ_к = str(ключ)
                    з = self.ключ_значення(значення)
                    if з in ТЕКСТ_КРАМНИЦІ and ключ_к not in {"id", "ід"}:
                        вих.append((мод.ім, ім, значення.lineno if hasattr(значення, "lineno") else в.lineno,
                                    "у дроті моделі поле `%s` ← слово крамниці `%s` (замість коду)" % (ключ_к, з)))
                    if з in {"ід", "id"} and ключ_к in {"id", "ід", "item", "thing", "photo", "item_id"} \
                            and not isinstance(значення, ast.Call) \
                            and {str(к) for к, _ in пари} & ПОЛЯ_РЕЧІ_ДРОТУ:  # id палітри чи основи — код, не річ
                        if б not in кеш_перетворених:
                            кеш_перетворених[б] = self.перетворений_будівник(б, модулі_збирача, ребра, кеш_конусів)
                        if not кеш_перетворених[б]:
                            вих.append((мод.ім, ім, значення.lineno, "у дроті моделі поле `%s` ← повний ід `%s` без перетворення на номер для дроту" % (ключ_к, з)))
        return вих

    # п.5: перелік речей у контексті входу (`items=…` / `"items": …`) — будівник, що не зветься «для_моделі»
    # (напр. вхід перекладу коментаря в `мова`): картка речі несе слово крамниці чи повний ід
    def дріт_контекст(self):
        вих = set()
        for мод, ім, ф in self.функції():
            for в in ast.walk(ф):
                переліки = []
                if isinstance(в, ast.Call) and текст_імені(в.func) == "dict":
                    переліки = [к.value for к in в.keywords if к.arg == "items"]
                elif isinstance(в, ast.Dict):
                    переліки = [з for к, з in zip(в.keys, в.values) if isinstance(к, ast.Constant) and к.value == "items"]
                for картка in (к for п in переліки for к in ast.walk(п)):
                    пари = []
                    if isinstance(картка, ast.Dict):
                        пари = [(к.value, з) for к, з in zip(картка.keys, картка.values) if isinstance(к, ast.Constant)]
                    elif isinstance(картка, ast.Call) and текст_імені(картка.func) == "dict":
                        пари = [(к.arg, к.value) for к in картка.keywords if к.arg]
                    if not {str(к) for к, _ in пари} & {"id", "slot", "kind"}:
                        continue
                    for ключ, значення in пари:
                        for глибше in ast.walk(значення):
                            з = self.ключ_значення(self.без_обгортки(глибше))
                            if з in ТЕКСТ_КРАМНИЦІ:
                                вих.add((мод.ім, ім, глибше.lineno, "у переліку речей контексту моделі поле `%s` ← слово "
                                         "крамниці `%s` (замість коду)" % (ключ, з)))
                        з = self.ключ_значення(self.без_обгортки(значення))
                        if з in {"ід", "id"} and str(ключ) in {"id", "ід"}:
                            вих.add((мод.ім, ім, значення.lineno, "у переліку речей контексту моделі поле `%s` ← повний ід "
                                     "`%s` без перетворення на місцевий номер" % (ключ, з)))
        return sorted(вих)

    @staticmethod
    def без_обгортки(в):
        """`str(х)` / `х or ""` → `х`: обгортка не робить слово крамниці чи ід кодом."""
        while True:
            if isinstance(в, ast.Call) and текст_імені(в.func) == "str" and len(в.args) == 1:
                в = в.args[0]
            elif isinstance(в, ast.BoolOp) and isinstance(в.op, ast.Or):
                в = в.values[0]
            else:
                return в

    @staticmethod
    def ключ_значення(в):
        """Ключ, яким значення читається з картки речі: `х["назва"]` / `х.get("назва")`; інакше None."""
        if isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant):
            return в.slice.value
        if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" and в.args \
                and isinstance(в.args[0], ast.Constant):
            return в.args[0].value
        return None

    # п.6: вид поля поза паспорт_поля.py
    def види_поля(self):
        вих = []
        for мод, ім, ф in [(м, "<модуль>", м.дерево) for м in self.м.values()]:
            if мод.ім == "паспорт_поля":
                continue
            for в in ast.walk(ф):
                if isinstance(в, (ast.Tuple, ast.Set, ast.List)) and len({е.value for е in в.elts if isinstance(е, ast.Constant)
                                                                         and е.value in ВИДИ_ПОЛЯ}) >= 2:
                    вих.append((мод.ім, ім, в.lineno, "перелік видів поля her/hand/reading/default оголошено поза `паспорт_поля.py`"))
                elif isinstance(в, ast.Compare):
                    const = [с for с in [в.left] + в.comparators if isinstance(с, ast.Constant) and с.value in ВИДИ_ПОЛЯ]
                    інше = ast.unparse(в)
                    if const and re.search(r"джерел|source|\.kind|вид", інше):
                        вих.append((мод.ім, ім, в.lineno, "вид поля `%s` порівнюється поза `паспорт_поля.py`" % const[0].value))
                elif isinstance(в, ast.Call):
                    for к in в.keywords:
                        if к.arg in {"джерело", "source", "kind"} and isinstance(к.value, ast.Constant) \
                                and к.value.value in ВИДИ_ПОЛЯ and not any(й.arg == "choice" for й in в.keywords):
                            вих.append((мод.ім, ім, в.lineno, "вид поля `%s` задано літералом поза `паспорт_поля.py`" % к.value.value))
        return вих


# ── КОНУСИ ОБРОБНИКІВ ─────────────────────────────────────────────────────────
def привʼязані_до_реєстру(а):
    """Функції, які реєстр кличе сам: `розбір=`/`сторож=` у `СхемаВідповіді(...)` і в словнику `РОЗБІР`."""
    вих = set()
    for мод in а.м.values():
        for в in ast.walk(мод.дерево):
            if isinstance(в, ast.Call):
                for к in в.keywords:
                    if к.arg in {"розбір", "сторож"} and isinstance(к.value, ast.Name):
                        ц = а.ціль(мод, ast.Call(func=к.value, args=[], keywords=[]))
                        if ц:
                            вих.add(ц)
    return вих


def ребра_викликів(а):
    р = {}
    привʼязані = привʼязані_до_реєстру(а)
    for мод in а.м.values():
        for ім, ф in мод.функції.items():
            ребра = {ц for в in ast.walk(ф) if isinstance(в, ast.Call) for ц in [а.ціль(мод, в)] if ц}
            if any(isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute)
                   and в.func.attr in {"виконати_розбір", "перевірити", "прочитати"} for в in ast.walk(ф)):
                ребра |= привʼязані
            р[(мод.ім, ім)] = ребра
    return р


def конус(старт, ребра):
    видно, черга = set(), [старт]
    while черга:
        х = черга.pop()
        if х in видно or х not in ребра:
            continue
        видно.add(х)
        черга.extend(ребра[х] - видно)
    return видно


def ендпойнти_моста(а):
    """{імʼя ендпойнта: (модуль, функція)} зі словника в `bridge.виклик` (імена з `from … import … as …`)."""
    мод = а.м.get("bridge")
    if not мод or "виклик" not in мод.функції:
        return {}
    вих = {}
    for в in ast.walk(мод.функції["виклик"]):
        сл = в.value.func if isinstance(в, ast.Return) and isinstance(в.value, ast.Call) else None
        if isinstance(сл, ast.Subscript) and isinstance(сл.value, ast.Dict):
            for к, з in zip(сл.value.keys, сл.value.values):
                if isinstance(к, ast.Constant) and isinstance(з, ast.Name) and з.id in мод.імена:
                    м, ф = мод.імена[з.id]
                    if м in а.м and ф in а.м[м].функції:
                        вих[к.value] = (м, ф)
    return вих


def клієнти_сервера(а):
    """Функції, що самі кличуть сервер моделі (константа `choices` у тілі): (модуль, функція)."""
    вих = []
    for мод in а.м.values():
        for ім, ф in мод.функції.items():
            if "choices" in {с.value for с in ast.walk(ф) if isinstance(с, ast.Constant)}:
                вих.append((мод.ім, ім))
    return sorted(вих)


def є_знак_повтору(ф):
    for в in ast.walk(ф):
        назви = []
        if isinstance(в, ast.Name):
            назви = [в.id]
        elif isinstance(в, ast.Attribute):
            назви = [в.attr]
        elif isinstance(в, ast.keyword) and в.arg:
            назви = [в.arg]
        elif isinstance(в, ast.Constant) and isinstance(в.value, str):
            назви = [в.value]
        elif isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
            назви = [в.name]
        if any(н in ЗНАКИ_ПОВТОРУ for н in назви):
            return True
    return False


# ── JS ────────────────────────────────────────────────────────────────────────
def без_коментарів_js(т):
    т = re.sub(r"/\*.*?\*/", lambda м: "\n" * м.group(0).count("\n"), т, flags=re.S)
    return re.sub(r"(?m)(^|[^:\\'\"`])//.*$", r"\1", т)


ПОЧАТОК_ФУНКЦІЇ_JS = re.compile(r"^(?:async\s+)?function\s+(%s+)|^(?:const|let)\s+(%s+)\s*=\s*(?:async\s*)?(?:function\b|\(|%s+\s*=>)" %
                                (БУКВА, БУКВА, БУКВА))
МОДЕЛЬ_JS = re.compile(r"(?<![\w.`])((?:%s+\.)?модель%s*)\(" % (БУКВА, БУКВА))
ЗНАК_ПОВТОРУ_JS = re.compile(r"помилка_формату|промпт_повтору|повторний_виклик|промптПовторуП|format_error|\.повтор\b|\bповтор\b")
ЗВІТ_JS = re.compile(r"запис|причина|журнал|Журнал|звіт|повідом|помилка|console|лиш")


def функції_js(текст):
    """[(імʼя, рядок початку, тіло)]: функції верхнього рівня — `function`/`async function` і `const х = (async) (…) =>` у
    першій колонці; тіло — до наступної такої."""
    рядки = текст.split("\n")
    початки = []
    for і, р in enumerate(рядки):
        м = ПОЧАТОК_ФУНКЦІЇ_JS.match(р)
        if м:
            початки.append((і, м.group(1) or м.group(2)))
    вих = []
    for н, (і, ім) in enumerate(початки):
        кінець = початки[н + 1][0] if н + 1 < len(початки) else len(рядки)
        вих.append((ім, і + 1, "\n".join(рядки[і:кінець])))
    return вих


class ПоказJS:
    """Показ: функції, виклики моделі, обгортки, ендпойнти й виклики одна одної."""

    def __init__(self, тексти=None):
        """`тексти` — {імʼя файлу: текст} для самоперевірки; без нього — усі `.js` показу з диска."""
        self.ф = {}               # імʼя → dict(файл, рядок, тіло)
        if тексти is None:
            тексти = {ім_ф: прочитати_файл(os.path.join(ПОКАЗ, ім_ф)) for ім_ф in sorted(os.listdir(ПОКАЗ))
                      if ім_ф.endswith(".js")}
        for ім_ф, текст in sorted(тексти.items()):
            for ім, рядок, тіло in функції_js(текст):
                self.ф.setdefault(ім, dict(файл="джерела/показ/" + ім_ф, рядок=рядок, тіло=без_коментарів_js(тіло)))
        шаблон_виклику = re.compile(r"(?<![\w.]|%s)(%s+)\(" % (БУКВА, БУКВА))
        self.виклики = {ім: {в for в in set(шаблон_виклику.findall(д["тіло"])) if в in self.ф and в != ім}
                        for ім, д in self.ф.items()}
        self.кличуть = {ім: {х for х, ц in self.виклики.items() if ім in ц} for ім in self.ф}

    def сайти(self):
        """Кожен виклик моделі: (функція, файл, рядок, імʼя виклику); транспорт (самі `модель…`) не рахується."""
        вих = []
        for ім, д in self.ф.items():
            if ім.startswith("модель"):
                continue
            for м in МОДЕЛЬ_JS.finditer(д["тіло"]):
                вих.append((ім, д["файл"], д["рядок"] + д["тіло"][:м.start()].count("\n"), м.group(1)))
        return вих

    def власники(self, ім):
        """Функції, що володіють потоком виклику: сама, коли кличе міст (`містП('…')`), інакше — хто її кличе (вгору)."""
        вих, черга, видно = set(), [ім], set()
        while черга:
            х = черга.pop()
            if х in видно:
                continue
            видно.add(х)
            if "містП(" in self.ф[х]["тіло"] or х == ім and re.search(r"містП", self.ф[х]["тіло"]):
                вих.add(х)
            else:
                черга.extend(self.кличуть.get(х, ()))
        return вих or {ім}

    def ендпойнти(self, власники, функція=None):
        """Ендпойнти моста власників потоку й функцій, які вони (і сама функція виклику) кличуть напряму:
        `читатиВідповідьКольоруП = т => містП('колір', …)` кличе міст за функцію, де стоїть виклик моделі."""
        вузли = set(власники) | ({функція} if функція else set())
        тіла = [self.ф[о]["тіло"] for о in вузли] + [self.ф[к]["тіло"] for о in вузли for к in self.виклики.get(о, ())]
        return sorted({е for т in тіла for е in re.findall(r"містП\('([^']+)'", т)})

    def вгору(self, імена, глибина=3):
        вих, межа = set(імена), set(імена)
        for _ in range(глибина):
            межа = {к for х in межа for к in self.кличуть.get(х, ())} - вих
            вих |= межа
        return вих

    @staticmethod
    def блок_що_містить(маска, поз):
        """Межі найглибшого `{…}`, що містить позицію (`маска` — тіло без вмісту рядків); весь текст, якщо блоку нема."""
        глибина, початок = 0, 0
        for і in range(поз - 1, -1, -1):
            if маска[і] == "}":
                глибина += 1
            elif маска[і] == "{":
                if глибина == 0:
                    початок = і
                    break
                глибина -= 1
        else:
            return 0, len(маска)
        глибина = 0
        for і in range(початок, len(маска)):
            if маска[і] == "{":
                глибина += 1
            elif маска[і] == "}":
                глибина -= 1
                if глибина == 0:
                    return початок, і
        return початок, len(маска)

    def збій_без_ходу(self):
        """п.3(г) у JS: функція, що кличе модель (чи міст), ловить збій `catch`, який лише пише причину в запис ходу
        (`….причина = …`), без запасного ходу в тілі функції: хід кінчається втратою з рядком звіту."""
        вих = []
        власники = {функція for функція, *_ in self.сайти()}
        for ім, д in self.ф.items():
            тіло = д["тіло"]
            if ім.startswith("модель") or ЗАПАСНИЙ_ХІД.search(тіло) or not (ім in власники or МОДЕЛЬ_JS.search(тіло)):
                continue
            for м in re.finditer(r"catch\s*(?:\([^)]*\))?\s*\{", тіло):
                від, до = self.блок_що_містить(тіло, м.end() + 1)
                вміст = тіло[м.end():до]
                решта = re.sub(r"[\w.]*\.\w*(?:причина|помилка)\w*\s*=\s*[^;\n]*;?", "", вміст)
                if re.search(r"\.причина\s*=", вміст) and not решта.strip() and not re.search(r"\bthrow\b", вміст):
                    вих.append((ім, д["файл"], д["рядок"] + тіло[:м.start()].count("\n"),
                                "`catch` виклику моделі в `%s` лише пише причину в запис ходу, а запасного ходу коду "
                                "(шаблон, `запасн…`) нема — хід кінчається втратою з рядком звіту" % ім))
        return вих

    def збій_кроку_без_ходу(self):
        """п.3(д) у JS: на шляху виклику моделі (функція кличе модель чи міст, або, до 3 ланок, кличе таку) код ставить
        `збій = true` — крок руки втрачено, жінка бачить «Цей образ не вимальовувався», — а в найглибшому блоці `{…}`
        цього рядка нема запасного ходу коду (шаблон, `запасн…`): що код знав (прийнятий вердикт, найповніший кандидат,
        чому відхилено), лишається лише в рядку звіту."""
        джерела_виклику = {ім for ім, д in self.ф.items()
                           if not ім.startswith("модель") and (МОДЕЛЬ_JS.search(д["тіло"]) or "містП(" in д["тіло"])}
        вих = []
        for ім in sorted(self.вгору(джерела_виклику)):
            д = self.ф[ім]
            тіло = д["тіло"]
            маска = re.sub(r"(['\"`])(?:\\.|(?!\1).)*\1", lambda м: м.group(1) + " " * (len(м.group(0)) - 2) + м.group(1),
                           тіло, flags=re.S)
            for м in re.finditer(r"(?<![\w.])(?:\w+\.)?збій\s*=\s*true\b", маска):
                від, до = self.блок_що_містить(маска, м.start())
                if ЗАПАСНИЙ_ХІД.search(тіло[від:до + 1]):
                    continue
                вих.append((ім, д["файл"], д["рядок"] + тіло[:м.start()].count("\n"),
                            "`%s` у `%s`: крок руки втрачено, а запасного ходу коду (шаблон, `запасн…`) у блоці нема — що "
                            "код знав, лишається лише в рядку звіту" % (м.group(0), ім)))
        return вих

    def читачі(self):
        """Читання відповіді моделі в JS: змінна, що тримає результат `модель…(…)`, і її вживання, крім передачі мосту.
        Однойменна змінна у вкладеній функції (власне оголошення, яке не охоплює присвоєння з моделі) — інша змінна."""
        вих = []
        for ім, д in self.ф.items():
            if ім.startswith("модель"):
                continue
            тіло = д["тіло"]
            маска = re.sub(r"(['\"`])(?:\\.|(?!\1).)*\1", lambda м: м.group(1) + " " * (len(м.group(0)) - 2) + м.group(1), тіло, flags=re.S)
            змінні = set(re.findall(r"(?:const|let|var)?\s*(%s+)\s*=\s*(?:await\s+)?(?:%s+\.)?модель%s*\(" %
                                    (БУКВА, БУКВА, БУКВА), тіло))
            змінні |= set(re.findall(r"(?:const|let|var)\s+(%s+)\s*=\s*(?:await\s+)?блокиВТекст\(" % БУКВА, тіло))
            for зм in sorted(змінні):
                екр = re.escape(зм)
                присвоєння = [м.start() for м in re.finditer(r"(?<![\w.])%s\s*=\s*(?:await\s+)?(?:%s+\.)?(?:модель%s*|блокиВТекст)\(" %
                                                              (екр, БУКВА, БУКВА), тіло)]
                власні = [м.start() for м in re.finditer(r"(?:\b(?:const|let|var)\s+%s\s*=|[(,]\s*%s\s*[,)]\s*=>|\b%s\s*=>)" %
                                                         (екр, екр, екр), тіло)
                          if м.start() not in присвоєння and not any(abs(м.start() - а) < 12 for а in присвоєння)]
                for м in re.finditer(r"JSON\.parse\(\s*%s\b|(?<![\w.])%s\.(?:match|replace|replaceAll|test|includes|indexOf|"
                                     r"startsWith|endsWith|split|slice|substring|toLowerCase|search)\(|\.(?:test|exec)\(\s*%s\b" %
                                     (екр, екр, екр), тіло):
                    затінено = False
                    for о in власні:
                        if о > м.start():
                            continue
                        від, до = self.блок_що_містить(маска, о)
                        if від <= м.start() <= до and not any(від <= а <= до for а in присвоєння):
                            затінено = True
                    if not затінено:
                        вих.append((ім, д["файл"], д["рядок"] + тіло[:м.start()].count("\n"), зм, м.group(0)))
        return вих


# ── ВИНЯТОК КЛАСУ: РУКИ 3–4 ───────────────────────────────────────────────────
# Рішення менеджера 05.11 (паспорт аудит/корені/Е2-межі.md, «Рішення»; аудит/ПРОДУКТ.md, п.1):
# «Руки 2–4 — лише для тестів», «Руки 3–4 … — лишати, не міняти». Їхні місця в коді обробки
# й розбору рук 3–4 (`джерела/руки_без_коду.py`) — не місця кореня. Межі функцій рук 3–4 —
# з AST модуля (не номери рядків): точки входу промптів і читачі відповідей рук 3–4.
ВИНЯТОК_ФАЙЛ = "джерела/руки_без_коду.py"
# `відповідь_руки` — власний читач відповіді рук 3–4 (рішення менеджера 08.11 на рядок 14417, #3426): спільний
# `протокол.розбір_останній` ремонт формату знімає, а руки 3–4 читають, як доти; його місця лічить рядок винятку
ВИНЯТОК_ФУНКЦІЇ = (
    "особа", "проза_руки", "опис_для_жінки", "промпт_руки",
    "промпт_переліку", "речі_переліку", "опис_образ", "re_огорожа", "відповідь_руки",
)
ВИНЯТОК_СТАЛІ = ("ОБРАЗ", "ПЕРЕЛІК")
# JS-стадія рук 3–4 (`збирання_руки.js`): гілка «рука без каталогу» — той самий виняток (рішення 05.11)
ВИНЯТОК_JS = {"джерела/показ/збирання_руки.js": ("стадіяРукБезКаталогу",)}


def межі_винятку_рук(текст, файл=ВИНЯТОК_ФАЙЛ, функції=ВИНЯТОК_ФУНКЦІЇ, сталі=ВИНЯТОК_СТАЛІ):
    """{файл: [(перший, останній рядок)]} — межі функцій і сталих рук 3–4 з AST модуля."""
    межі = []
    for в in ast.parse(текст).body:
        if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)) and в.name in функції:
            межі.append((в.lineno, getattr(в, "end_lineno", в.lineno)))
        elif isinstance(в, (ast.Assign, ast.AnnAssign)):
            цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
            if any(isinstance(ц, ast.Name) and ц.id in сталі for ц in цілі):
                межі.append((в.lineno, getattr(в, "end_lineno", в.lineno)))
    return {файл: межі}


def у_винятку_рук(файл, рядок, межі):
    """Чи належить рядок файлу межам винятку рук 3–4."""
    норм_файл = файл.replace("\\", "/")
    return any(від <= рядок <= до for від, до in межі.get(норм_файл, ()))


def _тест_винятку():
    """Самоперевірка винятку рук 3–4."""
    тест_код = (
        "def проза_руки(т): return т\n"
        "def опис_для_жінки(п): return {}\n"
        "def інша_функція(х): return х\n"
    )
    межі = межі_винятку_рук(тест_код, "тест.py", ("проза_руки", "опис_для_жінки"), ())
    assert у_винятку_рук("тест.py", 1, межі), "проза_руки має бути у винятку"
    assert у_винятку_рук("тест.py", 2, межі), "опис_для_жінки має бути у винятку"
    assert not у_винятку_рук("тест.py", 3, межі), "інша_функція не має бути у винятку"
    assert not у_винятку_рук("інший.py", 1, межі), "інший файл не має бути у винятку"


def _тест_перетворення_ід():
    """Дві проби п.5: синтетичний будівник із `id: р['ід']` через `_ід_усюди` — не місце; без нього — місце."""
    код1 = (
        "def будівник_для_моделі(р):\n"
        "    return {'id': р['ід'], 'photo': 'ф1'}\n"
        "\n"
        "def промпт_зібрати(р):\n"
        "    return _ЗП.зібрати('ТЕСТ', _ід_усюди(будівник_для_моделі(р)))\n"
    )
    код2 = (
        "def будівник_для_моделі(р):\n"
        "    return {'id': р['ід'], 'photo': 'ф1'}\n"
        "\n"
        "def промпт_зібрати(р):\n"
        "    return _ЗП.зібрати('ТЕСТ', будівник_для_моделі(р))\n"
    )
    а1 = Аналіз({"синтетика": ast.parse(код1)}, set(), set(), {})
    ст1 = Структура(а1)
    ребра1 = ребра_викликів(а1)
    зб1 = {("синтетика", "промпт_зібрати")}
    місця1 = ст1.дріт(зб1, ребра1)
    assert len(місця1) == 0, "будівник через _ід_усюди не має давати місця, знайдено: %r" % місця1

    а2 = Аналіз({"синтетика": ast.parse(код2)}, set(), set(), {})
    ст2 = Структура(а2)
    ребра2 = ребра_викликів(а2)
    зб2 = {("синтетика", "промпт_зібрати")}
    місця2 = ст2.дріт(зб2, ребра2)
    assert len(місця2) == 1, "будівник без перетворення має давати місце, знайдено: %r" % місця2
    assert "без перетворення на номер для дроту" in місця2[0][3]


def _тест_запасного_ходу_у_викликачах():
    """П.3(б, г): запасний хід у викликачі (міжпроцедурно) — не місце; без нього ні у функції, ні у викликачах — місце."""
    низ = (
        "def _запит(в):\n"
        "    ж = json.loads(в)\n"
        "    if not ж:\n"
        "        raise ValueError('порожньо')\n"
        "    return ж\n"
        "def _суд(в, відкинуто):\n"
        "    if not в:\n"
        "        відкинуто.append({'чому': 'порожньо'})\n"
        "        return []\n"
        "    return в\n"
    )
    з_ходом = "def верх(в):\n    try:\n        return _запит(в)\n    except ValueError:\n        return запасна_заява()\n"
    з_ходом2 = "def верх2(в):\n    return _суд(в, [])\n" + "def верх3(в):\n    return шаблон_заяви(верх2(в))\n"
    без_ходу = "def інший(в):\n    return _запит(в)\n"

    def _ловить(*частини):
        мод = {"низ": ast.parse(низ)}
        for і, ч in enumerate(частини):
            мод["в%d" % і] = ast.parse(ч.replace("_запит(", "низ._запит("))
            мод["в%d" % і].body.insert(0, ast.parse("import низ").body[0])
        return Структура(Аналіз(мод, set(), set(), {})).запасний_хід_у_викликачах(("низ", "_запит"), ловлять=True)

    def місця(*частини):
        мод = {"низ": ast.parse(низ)}
        for і, ч in enumerate(частини):
            мод["в%d" % і] = ast.parse(ч.replace("_запит(", "низ._запит(").replace("_суд(", "низ._суд("))
            мод["в%d" % і].body.insert(0, ast.parse("import низ").body[0])
        а = Аналіз(мод, set(), set(), {})
        ст = Структура(а)
        ключі = {("низ", "_запит"), ("низ", "_суд")}
        # місце п.3(г) у `_суд`; п.3(б) перевіряємо правилом викликачів напряму (читач `_запит` без потоку моделі в синтетиці)
        г = ст.відхилене_без_ходу(ключі)
        б = ст.запасний_хід_у_викликачах(("низ", "_запит"))
        return г, б

    г, б = місця(з_ходом, з_ходом2)
    assert б and not г, "запасний хід у викликачах — не місце: б=%r г=%r" % (б, г)
    г, б = місця(з_ходом + без_ходу)
    assert not б, "один викликач без ходу — місце лишається"
    з_ловом = "def верхL(в):\n    try:\n        return _запит(в)\n    except Exception as е:\n        return {'помилка': str(е)}\n"
    мовчки = "def верхM(в):\n    try:\n        return _запит(в)\n    except Exception:\n        return {}\n"
    кидає = "def верхR(в):\n    try:\n        return _запит(в)\n    except Exception as е:\n        raise\n"
    ланцюг = "def середній(в):\n    return _запит(в)\n" + "def верхС(в):\n    try:\n        return середній(в)\n    except ValueError as е:\n        return str(е)\n"
    _, б = місця(з_ловом)
    assert not б, "ловлення з причиною — не запасний хід за імʼям (лише для raise)"
    for ім_, код in (("ловить з причиною", з_ловом), ("ланцюг", ланцюг)):
        assert _ловить(код), "%s: raise покрито викликачем, що ловить" % ім_
    for ім_, код in (("мовчки", мовчки), ("кидає далі", кидає), ("без викликача", "def x():\n    return 1\n")):
        assert not _ловить(код), "%s: raise лишається місцем" % ім_
    г, б = місця("def самотній():\n    return 1\n")
    assert not б and len(г) == 1, "нема викликачів — місце лишається: б=%r г=%r" % (б, г)
    г, б = місця("def верх2(в):\n    return _суд(в, [])\n")
    assert not б and len(г) == 1, "викликач без ходу — місце лишається: г=%r" % г


def _тест_п3_зупинки():
    """П.3(д, е, є) (рішення 08.11, нічний прогін 07.11; є — #3379): `raise` будівника дроту без лову нагору — місце, навіть коли
    викликач має запасний хід ім'ям; лов із причиною — ні. Причина, погашена після останньої спроби, — місце.
    JS: `збій = true` на шляху виклику моделі без запасного ходу в блоці — місце; із запасним ходом — ні."""
    дріт = ("def кандидати(д):\n"
            "    def номер(р):\n"
            "        if р in д:\n"
            "            raise ValueError('різні факти')\n"
            "        return р\n"
            "    return [номер(р) for р in д]\n")
    імʼям = "import дріт_моделі\ndef від_моделі(в):\n    запасна_порада = 1\n    return дріт_моделі.кандидати(в)\n"
    ловить = ("import дріт_моделі\ndef від_моделі(в):\n    try:\n        return дріт_моделі.кандидати(в)\n"
              "    except ValueError as е:\n        return {'причина': str(е)}\n")

    def кидки(верх):
        мод = {"дріт_моделі": ast.parse(дріт), "міст": ast.parse(верх)}
        ст = Структура(Аналіз(мод, set(), set(), {}))
        return ст.кидок_будівника({("дріт_моделі", "кандидати"), ("міст", "від_моделі")})
    assert len(кидки(імʼям)) == 1, "запасний хід ім'ям винятку не ловить — місце"
    assert not кидки(ловить), "викликач ловить із причиною — не місце"
    погашено = ("def кінцева(р, с):\n    р['причина'] = с[-1].get('причина') if с[0].get('причина') else None\n"
                "    р['повтор'] = None\n    return р\n")
    несе = "def кінцева(р, с):\n    р['причина'] = с[-1].get('причина')\n    р['повтор'] = None\n    return р\n"
    for код, треба in ((погашено, 1), (несе, 0)):
        ст = Структура(Аналіз({"шар": ast.parse(код)}, set(), set(), {}))
        assert len(ст.причина_погашена({("шар", "кінцева")})) == треба, "причина після останньої спроби: %r" % код
    js = ("async function крок(к){\n  const в = await містП('від_моделі', к);\n"
          "  if (!в.образи.length){ збій = true; діагноз.push('no_outfit'); }\n  return в;\n}\n"
          "async function рука(к){\n  try{ await крок(к); }\n  catch(e){ стан.збій = true; діагноз.push(String(e)); }\n}\n"
          "async function рукаЗ(к){\n  try{ await крок(к); }\n  catch(e){ стан.збій = true; стан.текст = шаблонЗбою(e); }\n}\n"
          "function інше(){\n  збій = true;\n}\n")
    # п.3(є): знято рядком лише в журналі — місце; під `if` з іменем у `не_записано=` чи над `невідомо` — ні
    шар = ("def знято_рядком(п, с):\n    return 'not_read · step=layer · field=%s · code=not_taken' % п\n"
           "def невзяте_рядком(п, с):\n    return 'unknown_value · step=layer · field=%s · code=not_taken' % п\n"
           "def прийняти(р, знято, невідомо):\n"
           "    return dict(не_взято=[знято_рядком(к, 1) for к in знято] + [невзяте_рядком(к, 1) for к in невідомо])\n"
           "def шов(в, п):\n    без = [р for р in в if р]\n"
           "    if без:\n        п['н'] = ['own_item_without_status · step=layer · code=not_taken']\n"
           "    if в.get('w'):\n        п['н'] = ['place_words_without_place · step=layer · code=not_taken']\n"
           "    return dict(не_записано=[1] if без else [])\n")
    ст = Структура(Аналіз({"шар": ast.parse(шар)}, set(), set(), {}))
    знято = sorted((ім, р) for _, ім, р, _ in ст.слова_зняті_без_заяви({("шар", "прийняти"), ("шар", "шов")}))
    assert знято == [("прийняти", 6), ("шов", 12)], "п.3(є): %r" % знято
    місця = ПоказJS({"т.js": js}).збій_кроку_без_ходу()
    assert sorted(ф for ф, *_ in місця) == ["крок", "рука"], "JS п.3(д): %r" % місця


# ── ЗБІРКА МІСЦЬ ──────────────────────────────────────────────────────────────
ПУНКТИ = {1: "схеми нема в реєстрі / поле повз перевірку нею", 2: "розбіжність не повертається моделі словами",
          3: "нема запасного ходу чи рядка звіту / відхилене йде далі", 4: "гілка ремонту формату",
          5: "вхід моделі — не дані коду", 6: "вид поля не з одного джерела", 7: "код читає її слова"}


def файл_модуля(ім):
    return "джерела/%s.py" % ім


class Місця:
    """Набір місць: (файл, рядок, пункт) → {чому, шляхи}."""

    def __init__(self):
        self.д = {}

    def додати(self, файл, рядок, пункт, чому, шлях):
        з = self.д.setdefault((файл, рядок, пункт), dict(чому=[], шляхи=set()))
        if чому not in з["чому"]:
            з["чому"].append(чому)
        з["шляхи"].add(шлях)


def зібрати():
    модулі = модулі_продукту()
    індекс = {н: Модуль(н, д) for н, д in модулі.items()}
    форми = форми_реєстру(індекс)
    ключі_м, ключі_ж = ключі_моделі_з_входів(індекс)
    а = Аналіз(модулі, ключі_м, ключі_ж, форми).виконати()
    ст = Структура(а)
    js = ПоказJS()
    ребра = ребра_викликів(а)
    ендп = ендпойнти_моста(а)
    клієнти = клієнти_сервера(а)
    конуси = {"ендпойнт " + е: конус(ф, ребра) for е, ф in ендп.items()}
    конуси.update({"клієнт %s.%s" % к: конус(к, ребра) for к in клієнти})
    у_конусі = set().union(*конуси.values()) if конуси else set()
    м = Місця()
    інфо = dict(модулів=len(модулі), ендпойнтів=len(ендп), клієнтів=клієнти, js_функцій=len(js.ф))

    # ── шлях Б: читачі відповіді ──
    for п in a_події_відсортовані(а):
        файл = файл_модуля(п["модуль"])
        в_реєстрі = п["модуль"] in РЕЄСТР_МОД
        if п["вид"] == "парс" and not в_реєстрі:
            м.додати(файл, п["рядок"], 1, "читач формату повз реєстр: %s над текстом моделі" % п["дія"], "Б")
        elif п["вид"] == "читання" and not в_реєстрі:
            м.додати(файл, п["рядок"], 1, "відповідь моделі читається повз реєстр: %s" % п["дія"], "Б")
        elif п["вид"] == "реєстр":
            назви = п["дія"].split(": ", 1)[1].split(",") if ": " in п["дія"] else []
            без_схеми = [н for н in назви if н == "*динамічна*" and any(not с for с in форми.values())
                         or н in форми and not форми[н]]
            if без_схеми and п["модуль"] not in РЕЄСТР_МОД:
                м.додати(файл, п["рядок"], 1, "форма %s читається реєстром без схеми протоколу — поля нічим не перевіряються" %
                         "/".join(без_схеми), "Б")
        elif п["вид"] == "правка":
            if any(л[0] == "Р" for л in п["мітки"]) or М in п["мітки"]:
                м.додати(файл, п["рядок"], 4, "текст моделі правиться (%s) до розбору — ремонт формату" % п["дія"], "Б")
        elif п["вид"] == "слова" and not в_реєстрі:
            м.додати(файл, п["рядок"], 7, "код читає її слова: %s" % п["дія"], "Б")
    for мод, ім, рядок, чому in ст.нотатки() + ст.знаки_json():
        м.додати(файл_модуля(мод), рядок, 4, чому, "Б")
    читачі = {(п["модуль"], п["функція"]) for п in a_події_відсортовані(а) if п["вид"] in {"парс", "реєстр"} and п["модуль"] not in РЕЄСТР_МОД}
    внутрішні = {x for x in читачі if any(x != y and x in конус(y, ребра) for y in читачі)}
    for мод, ім, рядок, чому in ст.невдача_читача(внутрішні):
        м.додати(файл_модуля(мод), рядок, 3, чому, "Б")
    for мод, ім, рядок, чому in ст.сторож_ігнорований(у_конусі):
        м.додати(файл_модуля(мод), рядок, 3, чому, "Б")
    for мод, ім, рядок, чому in ст.відхилене_без_ходу(у_конусі):
        м.додати(файл_модуля(мод), рядок, 3, чому, "Б")
    for мод, ім, рядок, чому in ст.причина_погашена(у_конусі):
        м.додати(файл_модуля(мод), рядок, 3, чому, "Б")
    for мод, ім, рядок, чому in ст.кидок_будівника(у_конусі):
        м.додати(файл_модуля(мод), рядок, 3, чому, "А")
    for мод, ім, рядок, чому in ст.слова_зняті_без_заяви(у_конусі):
        м.додати(файл_модуля(мод), рядок, 3, чому, "Б")
    for мод, ім, рядок, чому in ст.види_поля():
        м.додати(файл_модуля(мод), рядок, 6, чому, "Б")
    # п.6 «дріт без виду» — шлях В: від підписів полів входу моделі назад потоком значення (помічник)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import корінь_е2_межі_дріт as ДРІТ
    for мод, рядок, чому in ДРІТ.місця_п6(ДЖЕРЕЛА, Модуль, Аналіз, НЕ_ШЛЯХ, set(модулі)):
        м.додати(файл_модуля(мод), рядок, 6, чому, "В")
    # п.2 у Python: функція-приймальник, у конусі якої нема знака повтору словами
    приймальники = {}
    for п in a_події_відсортовані(а):
        if п["вид"] in {"парс", "реєстр"} and п["модуль"] not in РЕЄСТР_МОД:
            ключ = (п["модуль"], п["функція"])
            приймальники[ключ] = min(приймальники.get(ключ, 10 ** 9), п["рядок"])
    for ключ, рядок in приймальники.items():
        власні = [н for н, к in конуси.items() if ключ in к]
        повтор = any(є_знак_повтору(а.м[x[0]].функції[x[1]]) for н in власні for x in конуси[н]) if власні else \
            є_знак_повтору(а.м[ключ[0]].функції[ключ[1]])
        # повтор складає викликач читача (читач лише розбирає): два рівні викликачів
        викликачі, межа = set(), {ключ}
        for _ in range(2):
            межа = {у for у, ц in ребра.items() if ц & межа} - викликачі - {ключ}
            викликачі |= межа
        повтор = повтор or any(є_знак_повтору(а.м[x[0]].функції[x[1]]) for x in викликачі if x[0] in а.м and x[1] in а.м[x[0]].функції)
        if not повтор:
            м.додати(файл_модуля(ключ[0]), рядок, 2, "приймальник `%s`: у його конусі нема знака повтору словами "
                     "(`промпт_повтору`/`повторний_виклик`/`помилка_формату`/`format_error`)" % ключ[1], "Б")

    # ── шлях А: від викликів моделі ──
    збирачі = {x for x in у_конусі if any(текст_імені(в.func).endswith("зібрати") for в in ast.walk(а.м[x[0]].функції[x[1]])
                                          if isinstance(в, ast.Call))}
    for мод, ім, рядок, чому in ст.дріт(збирачі, ребра):
        м.додати(файл_модуля(мод), рядок, 5, чому, "А")
    for мод, ім, рядок, чому in ст.дріт_контекст():
        м.додати(файл_модуля(мод), рядок, 5, чому, "А")
    for функція, файл, рядок, виклик in js.сайти():
        власники = js.власники(функція)
        ендп_js = js.ендпойнти(власники, функція)
        кидає = any("throw new Error" in js.ф[о]["тіло"] for о in власники)
        ловить = any(re.search(r"catch[^{]*\{[^}]{0,400}", js.ф[х]["тіло"]) and
                     any(ЗВІТ_JS.search(б) for б in re.findall(r"catch[^{]*\{([^}]{0,400})", js.ф[х]["тіло"]))
                     for х in js.вгору(власники))
        if кидає and not ловить:
            м.додати(файл, рядок, 3, "виклик моделі `%s` (%s): збій зупиняє хід (`throw`), а ні обгортка, ні її викликачі "
                     "не ловлять його в рядок звіту" % (виклик, функція), "А")
    for функція, файл, рядок, чому in js.збій_без_ходу():
        м.додати(файл, рядок, 3, чому, "А")
    for функція, файл, рядок, чому in js.збій_кроку_без_ходу():
        м.додати(файл, рядок, 3, чому, "А")
    for функція, файл, рядок, зм, дія in js.читачі():
        м.додати(файл, рядок, 1, "JS читає відповідь моделі `%s` сам (%s) замість передати мосту" % (зм, дія.strip()), "Б")
        if re.search(r"replace|slice|substring|split", дія):
            м.додати(файл, рядок, 4, "JS править відповідь моделі `%s` (%s)" % (зм, дія.strip()), "Б")
    # шлях А для місць Python: функція місця лежить у конусі виклику моделі (обробник мосту чи клієнт сервера)
    в_конусах = set().union(*конуси.values()) if конуси else set()
    for (файл, рядок, пункт), з in list(м.д.items()):
        if not файл.endswith(".py") or "/показ/" in файл:
            continue
        ім_мод = os.path.basename(файл)[:-3]
        мод = а.м.get(ім_мод)
        власна = [ім for ім, ф in (мод.функції.items() if мод else ()) if ф.lineno <= рядок <= getattr(ф, "end_lineno", ф.lineno)]
        if any((ім_мод, ім) in в_конусах for ім in власна):
            з["шляхи"].add("А")

    # Виняток класу (рішення менеджера 05.11, паспорт, аудит/ПРОДУКТ.md п.1): руки 3–4
    шлях_винятку = os.path.join(КОРІНЬ, ВИНЯТОК_ФАЙЛ)
    межі = межі_винятку_рук(прочитати_файл(шлях_винятку)) if os.path.exists(шлях_винятку) else {}
    for файл_js, функції_js in ВИНЯТОК_JS.items():
        межі.setdefault(файл_js, []).extend((д["рядок"], д["рядок"] + д["тіло"].count("\n")) for ім, д in js.ф.items()
                                            if д["файл"] == файл_js and ім in функції_js)
    м_лічені = Місця()
    м_виняток = Місця()
    for (файл, рядок, пункт), з in м.д.items():
        ціль = м_виняток if у_винятку_рук(файл, рядок, межі) else м_лічені
        for чому in з["чому"]:
            for шлях in з["шляхи"]:
                ціль.додати(файл, рядок, пункт, чому, шлях)
    return м_лічені, м_виняток, інфо, а, конуси, js, ендп, клієнти


def a_події_відсортовані(а):
    return sorted(а.події.values(), key=lambda п: (п["модуль"], п["рядок"], п["вид"], п["дія"]))


def розбіжності(а, конуси, js, ендп, клієнти):
    """Різниця шляхів на рівні меж: ендпойнти, до яких веде JS-виклик моделі (А), і ендпойнти, у конусі яких Python
    читає текст моделі (Б); Python-клієнти сервера моделі (А) і функції з читанням `choices` (Б)."""
    вих = []
    а_ендп = set()
    for функція, _, _, _ in js.сайти():
        а_ендп |= set(js.ендпойнти(js.власники(функція)))
    приймальники = {(п["модуль"], п["функція"]) for п in а.події.values() if п["вид"] in {"парс", "реєстр", "читання"}
                    and п["модуль"] not in РЕЄСТР_МОД}
    б_ендп = {е for е in ендп if конуси["ендпойнт " + е] & приймальники}
    for е in sorted(а_ендп - б_ендп):
        вих.append("А без Б: ендпойнт `%s` — JS шле моделі запит, а Python не читає текст її відповіді в конусі "
                   "(відповідь не текст або читає лише JS)" % е)
    for е in sorted(б_ендп - а_ендп):
        вих.append("Б без А: ендпойнт `%s` — Python читає текст моделі в конусі, а JS-виклику моделі з цим ендпойнтом нема" % е)
    читають_choices = {(п["модуль"], п["функція"]) for п in а.події.values() if М in п["мітки"]
                       and п["модуль"] not in РЕЄСТР_МОД and (п["модуль"], п["функція"]) in set(клієнти)}
    for к in клієнти:
        if к not in читають_choices:
            вих.append("А без Б: клієнт сервера `%s.%s` не читає текст відповіді подією (повертає сирий конверт)" % к)
    поза = sorted({(п["модуль"], п["функція"]) for п in а.події.values() if п["вид"] in {"парс", "реєстр"}
                   and п["модуль"] not in РЕЄСТР_МОД and not any((п["модуль"], п["функція"]) in к for к in конуси.values())})
    for х in поза:
        вих.append("Б без А: читач `%s.%s` поза конусами обробників мосту й клієнтів" % х)
    return вих


def розбіжності_місць(м):
    """Місця, знайдені лише одним шляхом: Б — читач у функції поза конусами мосту й клієнтів; А — виклик моделі в JS і дріт."""
    вих = []
    for (ф, р, п), з in sorted(м.д.items(), key=lambda к: (к[0][0], к[0][1], к[0][2])):
        if len(з["шляхи"]) == 1 and з["шляхи"] != {"В"}:
            # шлях В (дріт без виду) іде від входу моделі, а не від її відповіді: А і Б його не бачать за побудовою
            ш = next(iter(з["шляхи"]))
            вих.append("%s:%d п.%d — лише %s: %s" % (ф, р, п, ш, "функція поза конусами обробників мосту й клієнтів (читач без виклику моделі в досяжному коді)" if ш == "Б"
                                                    else "нема читача відповіді в досяжному коді (JS-виклик чи дріт входу)"))
    return вих


def вивести(м, м_виняток, інфо, а, конуси, js, ендп, клієнти):
    ключі = sorted(м.д, key=lambda к: (к[0], к[1], к[2]))
    різних = {(ф, р) for ф, р, _ in ключі}
    поштучно = {п: len({(ф, р) for ф, р, п_ in ключі if п_ == п}) for п in ПУНКТИ}
    виняток_різних = {(ф, р) for ф, р, _ in м_виняток.д}
    if "--json" in sys.argv:
        print(json.dumps(dict(місць=len(різних), виняток=len(виняток_різних), за_пунктами=поштучно, інфо={к: (v if not isinstance(v, list) else [list(x) for x in v]) for к, v in інфо.items()},
                              місця=[dict(файл=ф, рядок=р, пункт=п, чому=м.д[(ф, р, п)]["чому"], шлях="+".join(sorted(м.д[(ф, р, п)]["шляхи"])))
                                     for ф, р, п in ключі]), ensure_ascii=False, indent=1))
        return len(різних)
    if "--тихо" not in sys.argv:
        print("## Місця: файл:рядок · пункт класу · чому [шлях]\n")
        for ф, р, п in ключі:
            з = м.д[(ф, р, п)]
            print("%s:%d · п.%d · %s [%s]" % (ф, р, п, "; ".join(з["чому"]), "+".join(sorted(з["шляхи"]))))
        print("\n## Виклики моделі в JS (кожен — місце; порушення п.3 лічаться вище)\n")
        зі_збоєм = {(ф, р) for ф, р, п in ключі if п == 3}
        for функція, файл, рядок, виклик in js.сайти():
            print("%s:%d · %s (%s) · %s" % (файл, рядок, виклик, функція, "є порушення п.3" if (файл, рядок) in зі_збоєм
                                            else "збою без звіту нема"))
        print("\n## Місця, знайдені одним шляхом (А — від викликів, Б — від читачів): %d\n" % len(розбіжності_місць(м)))
        for р in розбіжності_місць(м):
            print("- " + р)
        print("\n## Розбіжності шляхів А і Б\n")
        for р in розбіжності(а, конуси, js, ендп, клієнти):
            print("- " + р)
    print("\n## Підсумки за пунктами\n")
    for п in ПУНКТИ:
        print("п.%d (%s): %d" % (п, ПУНКТИ[п], поштучно[п]))
    print("модулів Python в області: %d · ендпойнтів моста: %d · клієнтів сервера моделі: %d · JS-функцій: %d" %
          (інфо["модулів"], інфо["ендпойнтів"], len(інфо["клієнтів"]), інфо["js_функцій"]))
    if "--проби" in sys.argv:
        print("проби (поза `місць`): %s" % проби_із_моделлю())
    print("виняток класу: руки 3–4 — %d місць (рішення менеджера 05.11; аудит/ПРОДУКТ.md, п.1)" % len(виняток_різних))
    print("місць: %d" % len(різних))
    return len(різних)


def проби_із_моделлю():
    """Скільки файлів `проби/` самі шлють запит моделі чи читають `choices` (довідка, у `місць` не входить)."""
    к, всього = 0, 0
    тека = os.path.join(ДЖЕРЕЛА, "проби")
    for ім in os.listdir(тека) if os.path.isdir(тека) else []:
        if ім.endswith(".py"):
            всього += 1
            if re.search(r'"choices"|chat/completions|міст_http|urlopen', прочитати_файл(os.path.join(тека, ім))):
                к += 1
    return "%d з %d файлів" % (к, всього)


def main():
    if "--тест" in sys.argv:
        _тест_винятку()
        _тест_перетворення_ід()
        _тест_запасного_ходу_у_викликачах()
        _тест_п3_зупинки()
        print("тест винятку: ОК")
        print("тест перетворення ід: ОК")
        print("тест запасного ходу у викликачах: ОК")
        print("тест п.3 зупинки (д, е, є): ОК")
        return 0
    _тест_винятку()
    _тест_перетворення_ід()
    _тест_запасного_ходу_у_викликачах()
    _тест_п3_зупинки()
    м, м_виняток, інфо, а, конуси, js, ендп, клієнти = зібрати()
    вивести(м, м_виняток, інфо, а, конуси, js, ендп, клієнти)
    return 0


if __name__ == "__main__":
    sys.exit(main())
