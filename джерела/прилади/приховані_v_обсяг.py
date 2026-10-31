# -*- coding: utf-8 -*-
"""Приховані-розвідка, частина (в): кожне правило стилю в коді й реєстрах проти бази знань.

Наряд `аудит/наряди/Приховані-розвідка.md` (слово власника 31.10 14:26, 14:51): прихована вада — місце, де система
робить не те, що записано в її правилах, хоч симптому ще нема. Мірка частини (в) — база знань: теми корпусу
(`корпус.файли()`: `джерела/тема-*.md` і `topic-7-…`). Прилад не судить змісту — він лічить знаменник (кожну одиницю
з детермінованим ід) і ставить кожній механічні ознаки розбіжності з корпусом; змістовий вердикт — рядок переліку
`аудит/корені/Приховані-перелік-в.md`, покриття яким лічить `--перелік`.

Одиниці (ід — перша колонка виводу):
  Р  константа реєстру: значення словника рівня модуля, чий запис має тір (`t`/`тир`) і значення (`val`/`значення`)
     — `в:Р:<модуль>:<словник>:<ключ>`;
  П  запис реєстру правил за ід: словник рівня модуля з ≥3 ключами-ід правил (політика регістру, «без входу»,
     «гейт заявою», описи кодів, …) — `в:П:<модуль>:<словник>:<ід>`;
  І  ід правила (база) у виконуваному рядку коду продукту (`.py` без докстрінгів і коментарів, `показ/*.js` без
     `//`-коментарів) — `в:І:<ід>`;
  Л  голий поріг: порівняння `< <= > >=` з числовим літералом поза БЕЗПЕЧНІ у функції модуля, що виконує правила —
     `в:Л:<модуль>:<рядок>:<число>`.

Ознаки (колонка 4, через «;»; змісту не судять, лише кажуть, де корпус і код розходяться за формою):
  корпус:поза | корпус:без_означення     ід, на який посилається одиниця, корпус не має чи не означає;
  прав:нема                              константа стилю (не `службова`, тір не T4) без правила-джерела;
  число:нема_в_корпусі                   у означенні правила й поряд з ід у корпусі (±600 знаків) числа нема — число
                                         знає лише код;
  число:інше                             у означенні правила числа є, жодне не збігається з константою (±3 %);
  число:поряд                            збіг лише поряд з ід у корпусі, не в означенні (корпус часто сам описує код —
                                         такий збіг коловий, доказом правила не є);
  джерело:сесія                          опис константи називає число власним («моє», «мої») — його поставила сесія;
  джерело:код                            опис посилається лише на код, стенд чи наряд (не на корпус) — провенанс коловий;
  тір:вищий_за_доказ                     тір T1/T2 при словах «фольклор», «не мір», «не калібр», «оцінка» в описі;
  сила:понад_корпус                      стеля тіру (T1 hard, T2 strong) сильніша за силу (FORCE) правила в корпусі, а
                                         `ПОЛІТИКА_РЕГІСТРУ` стелі корпусу для нього не має;
  політика:сила≠корпус                   `сила_корпусу` політики не та, що FORCE у означенні правила;
  політика:гейт_на_мʼякому               регістр «гейт» на правилі, якому корпус дає `soft`/`hint`/`default`;
  мертва                                 ключ константи ніде в коді продукту, крім свого рядка, не прочитано;
  де:нема:<ім'я>                         функція з поля `де` реєстру в коді не існує;
  без_входу_але_виконується              ід у «без входу», а в виконуваному коді продукту стоїть;
  поза_корпусом_застаріло                ід у `ПОЗА_КОРПУСОМ`, а корпус його має;
  рід:не_код                             `rule_genus.рід` каже «не виконуваний», а ід у виконуваному коді;
  двійник:<модуль>:<ключ>                голий поріг дорівнює значенню константи реєстру, хоч рядок її не читає;
  поріг:без_правила                      голий поріг у функції, де ід правила не стоїть і реєстру не читано.

Запуск з кореня репозиторію:
  python3 джерела/прилади/приховані_v_обсяг.py                       лічба одиниць і ознак за частинами
  python3 джерела/прилади/приховані_v_обсяг.py --частина Р            одиниці: ід ⇥ місце ⇥ опис ⇥ ознаки
  python3 джерела/прилади/приховані_v_обсяг.py --перелік аудит/корені/Приховані-перелік-в.md
      змістовий вердикт: «своїм рядком» — ід одиниці стоїть першою клітинкою рядка таблиці переліку (`| ід | … |`);
      «класом» — ознака одиниці стоїть першою клітинкою як `клас:<ознака>` (вердикт класу за вибіркою, одиницю
      окремо не прочитано). Механічні ознаки прилад ставить усім одиницям.
Останній рядок — `місць: <N>` (одиниць з будь-якою ознакою).
"""
import argparse
import ast
import glob
import io
import contextlib
import os
import re
import sys
import warnings

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ДЖ = os.path.join(КОРІНЬ, "джерела")
sys.path.insert(0, ДЖ)
warnings.simplefilter("ignore")

import ід_правил as ІП  # noqa: E402

НЕ_ПРОДУКТ = ("тест", "стенд", "проба", "батарея", "audit", "gate", "measure", "мутанти", "жнива", "pair_test",
              "лабораторія", "гейти", "verify", "аудит_", "поломки", "траса", "звірка", "status", "trace",
              "build_", "покроковик", "зведення", "досяжність", "відбиток", "лічба", "rule_genus", "правила",
              "корпус", "ід_правил")
БЕЗПЕЧНІ = {0, 1, 2, -1, 0.0, 1.0, 2.0, 0.5, 100, 100.0, 10, 10.0, 3, 4, 60, 360, 180}
СИЛИ = ["hard", "strong", "default", "soft", "hint"]
СТЕЛЯ_ТІРУ = {"T1": "hard", "T2": "strong", "T3": "soft"}


def _продукт():
    return sorted(ф for ф in glob.glob(os.path.join(ДЖ, "*.py"))
                  if not os.path.basename(ф).startswith(НЕ_ПРОДУКТ))


def _js():
    return sorted(glob.glob(os.path.join(ДЖ, "показ", "*.js")))


def _відн(ф):
    return os.path.relpath(ф, КОРІНЬ)


def _мод(ф):
    return os.path.basename(ф).rsplit(".", 1)[0]


_ДЕРЕВА = {}


def _ast(ф):
    if ф not in _ДЕРЕВА:
        _ДЕРЕВА[ф] = ast.parse(open(ф, encoding="utf-8").read())
    return _ДЕРЕВА[ф]


def _число(x):
    if isinstance(x, ast.Constant) and isinstance(x.value, (int, float)) and not isinstance(x.value, bool):
        return x.value
    if isinstance(x, ast.UnaryOp) and isinstance(x.op, ast.USub) and _число(x.operand) is not None:
        return -_число(x.operand)
    return None


def _числа_вузла(в):
    """Усі числові літерали виразу (значення константи може бути кортежем, словником, `float(…)`)."""
    out, мінус = [], set()
    for д in ast.walk(в):
        if isinstance(д, ast.UnaryOp) and isinstance(д.op, ast.USub) and _число(д.operand) is not None:
            мінус.add(id(д.operand))
            out.append(-_число(д.operand))
        elif id(д) not in мінус and _число(д) is not None:
            out.append(_число(д))
    return out


def _рядки_докстрінгів(дерево):
    р = set()
    for в in ast.walk(дерево):
        if isinstance(в, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and в.body \
                and isinstance(в.body[0], ast.Expr) and isinstance(в.body[0].value, ast.Constant) \
                and isinstance(в.body[0].value.value, str):
            д = в.body[0]
            р.update(range(д.lineno, д.end_lineno + 1))
    return р


# ───────────────────────────── корпус ─────────────────────────────
_К = {}


def корпус():
    """{"ід": множина ід корпусу, "озн": {ід: блок означення}, "текст": {тема: текст}, "без": названі без означення}."""
    if _К:
        return _К
    import корпус as КР
    import правила
    with contextlib.redirect_stdout(io.StringIO()):
        _К["ід"] = set(КР.ід())
        _К["озн"] = {к: в[1] for к, в in правила.формулювання(максимум=2500).items()}
        _К["текст"] = КР.текст()
    _К["без"] = _К["ід"] - set(_К["озн"])
    return _К


_СИЛА = re.compile(r"FORCE\W{0,6}(?:\*\*)?\s*`?\[?(" + "|".join(СИЛИ) + r")\b|`\[?(" + "|".join(СИЛИ) + r")\]?`"
                   r"|\[(" + "|".join(СИЛИ) + r")\b")


def сила_корпусу(ід):
    """Перша названа сила в означенні правила (FORCE: `x`, `[x]`, `x`) — чи None."""
    б = корпус()["озн"].get(ід)
    if not б:
        return None
    м = _СИЛА.search(б)
    return next(г for г in м.groups() if г) if м else None


_ЧИСЛО = re.compile(r"(?<![\w.\-])[−\-–]?\d+(?:[.,]\d+)?")


def _числа_тексту(т, ід=None):
    if ід:
        т = т.replace(ід, " ")
    т = re.sub(r"\b[KRPE]-[A-ZА-Я0-9]{2,5}-\d{2}[a-zа-я]?\b", " ", т)          # чужі ід
    т = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\.\d{2}\.\d{4}\b", " ", т)      # дати
    т = re.sub(r"тема-\d+|topic-\d+|:\d{2,5}\b", " ", т)                       # посилання на тему й рядок
    out = []
    for м in _ЧИСЛО.finditer(т):
        с = м.group(0).replace("−", "-").replace("–", "-").replace(",", ".")
        try:
            out.append(float(с))
        except ValueError:
            pass
    return out


def _збіг(а, б):
    for x in а:
        for y in б:
            if x == y or (y and abs(x - y) <= 0.03 * abs(y)) or (abs(x) <= 1 and abs(x * 100 - y) <= 0.5) \
                    or (abs(y) <= 1 and abs(y * 100 - x) <= 0.5):
                return True
    return False


def _поряд(ід, радіус=600):
    out = []
    for т in корпус()["текст"].values():
        for м in re.finditer(re.escape(ід) + r"(?![\w-])", т):
            out.append(т[max(0, м.start() - радіус):м.end() + радіус])
    return " ".join(out)


def _ознаки_ід(ід):
    К = корпус()
    б = ІП.база(ід) or ід
    if б not in К["ід"] and ід not in К["ід"]:
        return ["корпус:поза"]
    if б in К["без"] and ід not in К["озн"]:
        return ["корпус:без_означення"]
    return []


# ───────────────────────────── код продукту: ід у виконуваних рядках ─────────────────────────────
_ВИК = {}


def виконувані_ід():
    """{база ід: [файл:рядок]} — ід у виконуваному рядку коду продукту."""
    if _ВИК:
        return _ВИК
    for ф in _продукт():
        док = _рядки_докстрінгів(_ast(ф))
        for н, р in enumerate(open(ф, encoding="utf-8"), 1):
            if н in док:
                continue
            гол = р.split("#")[0]
            for б in ІП.бази_в_тексті(гол):
                _ВИК.setdefault(б, []).append("%s:%d" % (_відн(ф), н))
    for ф in _js():
        for н, р in enumerate(open(ф, encoding="utf-8"), 1):
            гол = р.split("//")[0]
            if гол.strip().startswith(("*", "/*")):
                continue
            for б in ІП.бази_в_тексті(гол):
                _ВИК.setdefault(б, []).append("%s:%d" % (_відн(ф), н))
    return _ВИК


_ТЕКСТ_КОДУ = {}


def _текст_коду():
    if not _ТЕКСТ_КОДУ:
        for ф in _продукт() + _js():
            _ТЕКСТ_КОДУ[ф] = open(ф, encoding="utf-8").read()
    return _ТЕКСТ_КОДУ


_ІМЕНА = set()


def _імена_коду():
    if not _ІМЕНА:
        for ф in _продукт():
            for в in ast.walk(_ast(ф)):
                if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    _ІМЕНА.add(в.name)
        for т in (open(ф, encoding="utf-8").read() for ф in _js()):
            _ІМЕНА.update(re.findall(r"function\s+([\wА-яЇїІіЄєҐґʼ']+)", т))
            _ІМЕНА.update(re.findall(r"([\wА-яЇїІіЄєҐґʼ']+)\s*[:=]\s*(?:async\s*)?(?:function|\()", т))
    return _ІМЕНА


# ───────────────────────────── Р: константи реєстрів ─────────────────────────────
def _поля_запису(в):
    """dict(поле → вузол) для запису `{…}` чи `dict(…)`; інакше None."""
    if isinstance(в, ast.Dict):
        return {к.value: з for к, з in zip(в.keys, в.values) if isinstance(к, ast.Constant)}
    if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "dict":
        return {к.arg: к.value for к in в.keywords if к.arg}
    return None


def _рядок(в):
    if в is None:
        return ""
    if isinstance(в, ast.Constant):
        return str(в.value)
    if isinstance(в, (ast.List, ast.Tuple)):
        return " ".join(_рядок(е) for е in в.elts)
    if isinstance(в, ast.JoinedStr):
        return "".join(_рядок(е) for е in в.values)
    return ast.unparse(в)


def константи():
    """[(ід, файл:рядок, мод, словник, ключ, поля{t,val,прав,опис,де,службова}, вузол_val)]"""
    out = []
    for ф in _продукт():
        for в in _ast(ф).body:
            ціль = в.targets[0] if isinstance(в, ast.Assign) else (в.target if isinstance(в, ast.AnnAssign) else None)
            словник = getattr(в, "value", None)
            if isinstance(в, ast.Expr) and isinstance(в.value, ast.Call) and isinstance(в.value.func, ast.Attribute) \
                    and в.value.func.attr == "update" and isinstance(в.value.func.value, ast.Name) and в.value.args:
                ціль, словник = в.value.func.value, в.value.args[0]           # `РЕЄСТР.update({…})`
            if not isinstance(ціль, ast.Name) or not isinstance(словник, ast.Dict):
                continue
            for к, з in zip(словник.keys, словник.values):
                п = _поля_запису(з)
                if not isinstance(к, ast.Constant) or not п:
                    continue
                тір = п.get("t", п.get("тир"))
                if тір is None or not ({"val", "значення"} & set(п)
                                      or isinstance(тір, ast.Constant) and str(тір.value).startswith("T")):
                    continue
                val = п.get("val", п.get("значення", ast.Constant(None)))
                прав = [ід for ід in ІП.усі_в_тексті(_рядок(п.get("прав", п.get("правило"))))]
                out.append(dict(
                    ід="в:Р:%s:%s:%s" % (_мод(ф), ціль.id, к.value), місце="%s:%d" % (_відн(ф), к.lineno),
                    мод=_мод(ф), файл=ф, словник=ціль.id, ключ=к.value, рядок=к.lineno,
                    t=_рядок(п.get("t", п.get("тир"))), val=val, прав=прав,
                    опис=" ".join(_рядок(п.get(х)) for х in ("суть", "джерело", "src", "що_вирішує", "згода", "калібр", "оптика")),
                    де=_рядок(п.get("де", п.get("де_в_коді"))),
                    службова=isinstance(п.get("службова"), ast.Constant) and п["службова"].value is True))
    return out


_СЛАБКИЙ_ДОКАЗ = re.compile(r"фольклор|не мір|не калібр|некалібр|оцінк|на око|навмання|не перевір", re.I)


_САМА_СЕСІЯ = re.compile(r"(?<!\w)(?:мо[єїя]|мій|моїм|моєю)(?!\w)|моя оцінка|я вибра|обрано навмання", re.I)
_ДЖЕРЕЛО_КОРПУС = re.compile(r"тем[аи]-?\d|topic-|корпус|\b[KR]-[A-Z]{2,5}-\d{2}|\(\d{4}\)|et al|ASTM|CIE|ISO|дослідж|study", re.I)
_ДЖЕРЕЛО_КОД = re.compile(r"[\wʼ]+\.py|[A-ZА-ЯІЇЄ]{3,}_[A-ZА-ЯІЇЄ_]+|чинн|відсів|стенд|П-\d|Н-\d")


def ознаки_Р(к, політика):
    о = []
    for ід in к["прав"]:
        о += _ознаки_ід(ід)
    стильова = not к["службова"] and к["t"] != "T4"
    if not к["прав"] and стильова:
        о.append("прав:нема")
    числа = _числа_вузла(к["val"])
    if числа and к["прав"] and стильова:
        озн = " ".join(корпус()["озн"].get(ІП.база(ід) or ід, "") for ід in к["прав"])
        поряд = " ".join(_поряд(ІП.база(ід) or ід) for ід in к["прав"])
        чо = [ч for ід in к["прав"] for ч in _числа_тексту(корпус()["озн"].get(ІП.база(ід) or ід, ""), ід)]
        чп = [ч for ід in к["прав"] for ч in _числа_тексту(_поряд(ІП.база(ід) or ід), ід)]
        if _збіг(числа, чо):
            pass
        elif _збіг(числа, чп):
            о.append("число:поряд")
        elif чо:
            о.append("число:інше")
        else:
            о.append("число:нема_в_корпусі")
        del озн, поряд
    if стильова and _САМА_СЕСІЯ.search(к["опис"]):
        о.append("джерело:сесія")
    elif стильова and к["прав"] and not _ДЖЕРЕЛО_КОРПУС.search(к["опис"]) and _ДЖЕРЕЛО_КОД.search(к["опис"]):
        о.append("джерело:код")
    if к["t"] in ("T1", "T2") and _СЛАБКИЙ_ДОКАЗ.search(к["опис"]):
        о.append("тір:вищий_за_доказ")
    стеля = СТЕЛЯ_ТІРУ.get(к["t"])
    if стеля and стеля != "soft":
        for ід in к["прав"]:
            с = сила_корпусу(ІП.база(ід) or ід)
            if с and СИЛИ.index(стеля) < СИЛИ.index(с) and not (політика.get(ід) or {}).get("сила_корпусу"):
                о.append("сила:понад_корпус:%s=%s" % (ід, с))
    # мертва: ключ рядком ніде в коді продукту, крім рядка означення
    ключ = str(к["ключ"])
    взір = re.compile(r"[\"']" + re.escape(ключ) + r"[\"']")
    ужито = 0
    for ф, т in _текст_коду().items():
        for м in взір.finditer(т):
            н = т.count("\n", 0, м.start()) + 1
            if not (ф == к["файл"] and н == к["рядок"]):
                ужито += 1
    if not ужито:
        о.append("мертва")
    for ім in re.findall(r"([\wʼ']+)\(\)", к["де"]):
        if ім.split(".")[-1] not in _імена_коду():
            о.append("де:нема:" + ім)
    return о


# ───────────────────────────── П: реєстри правил за ід ─────────────────────────────
def записи_П():
    out = []
    for ф in _продукт():
        for в in _ast(ф).body:
            ціль = в.targets[0] if isinstance(в, ast.Assign) else (в.target if isinstance(в, ast.AnnAssign) else None)
            if not isinstance(ціль, ast.Name) or not isinstance(getattr(в, "value", None), ast.Dict):
                continue
            ключі = [к for к in в.value.keys if isinstance(к, ast.Constant) and isinstance(к.value, str)]
            if sum(1 for к in ключі if ІП.цілий(к.value)) < 3:
                continue
            for к, з in zip(в.value.keys, в.value.values):
                if isinstance(к, ast.Constant) and isinstance(к.value, str) and ІП.цілий(к.value):
                    out.append(dict(ід="в:П:%s:%s:%s" % (_мод(ф), ціль.id, к.value),
                                    місце="%s:%d" % (_відн(ф), к.lineno), мод=_мод(ф), словник=ціль.id,
                                    правило=к.value, вузол=з))
    return out


_ЕМ = {}


def емісії():
    """{ід: [(файл:рядок, сила)]} — виклики конструктора знахідки (`_зн`, `зн`, `_зн_акс`, `_зн_верх`) з ід першим
    аргументом і силою-рядком другим."""
    if not _ЕМ:
        for ф in _продукт():
            for в in ast.walk(_ast(ф)):
                if isinstance(в, ast.Call) and len(в.args) >= 2 and isinstance(в.args[0], ast.Constant) \
                        and isinstance(в.args[0].value, str) and ІП.цілий(в.args[0].value) \
                        and ast.unparse(в.func).split(".")[-1] in ("_зн", "зн", "_зн_акс", "_зн_верх"):
                    с = в.args[1].value if isinstance(в.args[1], ast.Constant) else "?"
                    _ЕМ.setdefault(в.args[0].value, []).append(("%s:%d" % (_відн(ф), в.lineno), с))
    return _ЕМ


def _політика():
    import реєстр_політика
    return реєстр_політика.ПОЛІТИКА_РЕГІСТРУ


def ознаки_П(з):
    о = []
    ід = з["правило"]
    if з["словник"] == "ПОЗА_КОРПУСОМ":
        if ід in корпус()["ід"]:
            о.append("поза_корпусом_застаріло")
        return о
    о += _ознаки_ід(ід)
    if з["словник"] == "ПОЛІТИКА_РЕГІСТРУ":
        п = _політика().get(ід) or {}
        к = сила_корпусу(ІП.база(ід) or ід)
        if п.get("сила_корпусу") and к and п["сила_корпусу"] != к:
            о.append("політика:сила≠корпус:%s≠%s" % (п["сила_корпусу"], к))
        if п.get("регістр") == "гейт" and к in ("soft", "hint", "default"):
            о.append("політика:гейт_на_мʼякому:%s" % к)
    if з["словник"] == "БЕЗ_ВХОДУ":
        вироки = [м for м in емісії().get(ід, []) if м[1] in СИЛИ]
        if вироки:
            о.append("без_входу_але_виконується:%s=%s" % вироки[0])
    return о


# ───────────────────────────── І: ід у виконуваному коді ─────────────────────────────
def ознаки_І(ід):
    о = list(_ознаки_ід(ід))
    try:
        import rule_genus
        р = rule_genus.рід(ід)
        if str(р.get("виконуваний")) in ("ні", "False", "no"):
            о.append("рід:не_код:%s" % р.get("рід"))
    except Exception:
        pass
    return о


# ───────────────────────────── Л: голі пороги ─────────────────────────────
def пороги(константи_р):
    значення = {}
    for к in константи_р:
        for ч in _числа_вузла(к["val"]):
            if ч not in БЕЗПЕЧНІ:
                значення.setdefault(ч, []).append("%s:%s" % (к["мод"], к["ключ"]))
    модулі_правил = {м.split(":")[0] for мм in виконувані_ід().values() for м in мм}
    out = []
    for ф in _продукт():
        if _відн(ф) not in модулі_правил:
            continue
        дерево = _ast(ф)
        рядки = open(ф, encoding="utf-8").read().splitlines()

        def обхід(в, функція):
            for д in ast.iter_child_nodes(в):
                if isinstance(д, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    обхід(д, д)
                    continue
                if функція is not None and isinstance(д, ast.Compare) and any(
                        isinstance(о, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for о in д.ops):
                    бачені = set()
                    for x in [д.left] + д.comparators:
                        ч = _число(x)
                        if ч is None or ч in БЕЗПЕЧНІ or ч in бачені:
                            continue
                        бачені.add(ч)
                        тіло = "\n".join(рядки[функція.lineno - 1:функція.end_lineno])
                        о = []
                        свої = [з for з in значення.get(ч, []) if з.split(":")[0] == _мод(ф)
                                or re.search(r"\b(?:import|from)\s+" + re.escape(з.split(":")[0]) + r"\b", "\n".join(рядки))]
                        if свої and not re.search(r"РЕЄСТР|REGISTRY|\bC\[|\bC\.", рядки[д.lineno - 1]):
                            о.append("двійник:" + свої[0])
                        if not ІП.бази_в_тексті(тіло) and not re.search(r"РЕЄСТР|REGISTRY|\bC\[", тіло):
                            о.append("поріг:без_правила")
                        out.append(dict(ід="в:Л:%s:%d:%s" % (_мод(ф), д.lineno, ч), місце="%s:%d" % (_відн(ф), д.lineno),
                                        опис="%s · %s" % (функція.name, ast.unparse(д)[:70]), ознаки=о))
                обхід(д, функція)
        обхід(дерево, None)
    return out


# ───────────────────────────── збирання ─────────────────────────────
def усі():
    політика = _політика()
    рк = константи()
    out = {"Р": [], "П": [], "І": [], "Л": []}
    for к in рк:
        out["Р"].append((к["ід"], к["місце"], "%s=%s · %s" % (к["t"], ast.unparse(к["val"])[:50], ",".join(к["прав"]) or "—"),
                         ознаки_Р(к, політика)))
    for з in записи_П():
        out["П"].append((з["ід"], з["місце"], ast.unparse(з["вузол"])[:90], ознаки_П(з)))
    for ід, місця in sorted(виконувані_ід().items()):
        out["І"].append(("в:І:" + ід, місця[0], "місць %d · %s" % (len(місця), " ".join(місця[:4])), ознаки_І(ід)))
    for п in пороги(рк):
        out["Л"].append((п["ід"], п["місце"], п["опис"], п["ознаки"]))
    return out


КЛАСИ = ("корпус:поза", "корпус:без_означення", "прав:нема", "число:нема_в_корпусі", "число:інше", "число:поряд",
         "тір:вищий_за_доказ", "сила:понад_корпус", "джерело:сесія", "джерело:код", "політика:сила≠корпус", "політика:гейт_на_мʼякому", "мертва",
         "де:нема", "без_входу_але_виконується", "поза_корпусом_застаріло", "рід:не_код", "двійник",
         "поріг:без_правила")


def _клас(ознака):
    return next((к for к in КЛАСИ if ознака == к or ознака.startswith(к + ":")), ознака)


def main():
    ап = argparse.ArgumentParser()
    ап.add_argument("--частина", choices=list("РПІЛ"))
    ап.add_argument("--перелік")
    а = ап.parse_args()
    д = усі()
    if а.частина:
        for р in д[а.частина]:
            print("\t".join([р[0], р[1], р[2], ";".join(р[3])]))
        return
    from collections import Counter
    з_ознакою = 0
    for ч, рр in д.items():
        кл = Counter()
        for р in рр:
            for о in set(_клас(о) for о in р[3]):
                кл[о] += 1
        мічені = sum(1 for р in рр if р[3])
        з_ознакою += мічені
        print("%s: одиниць %d, з ознакою %d · %s" % (ч, len(рр), мічені,
              ", ".join("%s %d" % (к, н) for к, н in sorted(кл.items(), key=lambda x: -x[1]))))
    if а.перелік:
        т = open(а.перелік, encoding="utf-8").read()
        перші = {м.group(1).strip().strip("`") for м in re.finditer(r"^\|\s*([^|]+?)\s*\|", т, re.M)}
        класи = {п[len("клас:"):] for п in перші if п.startswith("клас:")}
        всього = своїм = класом = 0
        for ч, рр in д.items():
            сч = кч = 0
            for р in рр:
                if р[0] in перші:
                    сч += 1
                elif any(_клас(о) in класи for о in р[3]):
                    кч += 1
            всього += len(рр)
            своїм += сч
            класом += кч
            print("вердикт %s: своїм рядком %d, класом %d, без вердикту %d з %d" % (ч, сч, кч, len(рр) - сч - кч, len(рр)))
        print("змістовий вердикт: своїм рядком %d, класом %d з %d; механічні ознаки — %d з %d (100 %%)"
              % (своїм, класом, всього, всього, всього))
    print("місць: %d" % з_ознакою)


if __name__ == "__main__":
    main()
