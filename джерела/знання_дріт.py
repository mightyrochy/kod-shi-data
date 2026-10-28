"""Безвтратний словник нового знання для фактичних речей одного промпту.

К-3, 7503: повторені статуси на кожному рядку скоротили пул 575→379.
Факти, словник і join оплачуються чинним cap; старі поля речей не змінюються.
Кожний рядок явно посилається на факти, їхнє походження і застосовність.
"""
import json as _json

from знання_речі import ВЛАСТИВОСТІ
from colorspace import hx
import колір_річ as _КР_ТИП

ОПИС = (
    "knowledge_legend joins knowledge to the actual items in this request. sections keys are JSON Pointer "
    "paths from this request root (~0 means ~, ~1 means /). A section with rows has one knowledge vector "
    "per row of that list/table, in the exact same order; a table's cols/rows represent logical item rows. "
    "A section with item gives the vector for that single item. null means no knowledge supplied. "
    "Vector indices refer to facts in property order. defaults is the explicit complete three-index vector: "
    "append its trailing indices to a shorter vector; a scalar is a one-index vector. Only explicitly "
    "listed items use defaults. Each fact is [descriptor index, value]; each descriptor is "
    "[status, source, applicability index]. applicability records give applicability and its source. "
    "Applicability is independent of status; unknown never proves NA. "
    "measured: known value from that source; range: only that window/alternatives; unknown: no supported "
    "fact; not_applicable: explicit inapplicability. Only status=measured with literal value=\"absent\" "
    "states explicit absence; a missing value or field never does. "
    "Color range value is [L0,L1,C0,C1,hue arc or null], never a measured hex centre. "
    "Composition_raw means unparsed shop text, never coded composition. Metal unknown never proves no metal. "
    "A value {field, conversion} references that same item's existing field: lab is the exact Lab value; "
    "hex uses colorspace.hx (sRGB to CIELab D65); hx_round2 uses the existing feed producer's two-decimal "
    "representation after hx. A reference is emitted only when it reconstructs the original value exactly."
)


def _канон(р):
    """Ключ інтернування з точним JSON-значенням, без округлення кольору."""
    return _json.dumps(р, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _повне(річ):
    """Розпізнати тільки наш договір, а не довільне поле з назвою knowledge."""
    з = річ.get("knowledge") if isinstance(річ, dict) else None
    return (isinstance(з, dict) and set(з) == set(ВЛАСТИВОСТІ) and all(
        isinstance(з[в], dict) and set(з[в]) == {"status", "value", "source", "applicability"}
        for в in ВЛАСТИВОСТІ))


def _шлях(шлях, ключ):
    """Дописати ключ чи індекс до однозначного JSON Pointer."""
    return шлях + "/" + str(ключ).replace("~", "~0").replace("/", "~1")


def додаток_бюджету(промпт):
    """Уся винесена ціна нового знання лишається всередині чинного cap пулу."""
    ключі = {поле: {к: р for к, р in (промпт.get(поле) or {}).items()
                    if к in ("knowledge", "color_range")}
             for поле in ("pool_keys", "item_keys")}
    return dict(knowledge_legend=промпт["knowledge_legend"], join=ОПИС,
                key_descriptions={к: р for к, р in ключі.items() if р})


def _типові(секції):
    """Вкоротити лише хвости однакових фактів із явним правилом читачу."""
    from collections import Counter
    вектори = [р for с in секції.values() for р in с.get("rows", [с.get("item")]) if р is not None]
    типові = [Counter(р[і] for р in вектори).most_common(1)[0][0] for і in range(3)]

    def коротко(вектор):
        """Пропустити тільки явно оголошений однаковий кінець вектора."""
        if вектор is None:
            return None
        вектор = list(вектор)
        while вектор and вектор[-1] == типові[len(вектор) - 1]:
            вектор.pop()
        return вектор[0] if len(вектор) == 1 else вектор

    for с in секції.values():
        if "rows" in с:
            с["rows"] = [коротко(р) for р in с["rows"]]
        else:
            с["item"] = коротко(с["item"])
    return типові


def _точка_посиланням(річ, факт):
    """Послатися на старе поле лише за точного відновлення чисельного факту.

    hx_round2 — вже чинна форма фід_збагачення.колір_збагачення, не округлення
    Lab договору. Якщо hex не відтворює його буквально, значення лишається повним.
    """
    if факт["status"] != "measured":
        return факт["value"]
    if _канон(_КР_ТИП.точка_кольору(річ)) == _канон(факт["value"]):
        return dict(field="lab", conversion="identity")
    if річ.get("hex"):
        try:
            точка = hx(річ["hex"])
        except ValueError:
            return факт["value"]
        for спосіб, значення in (("hx", точка), ("hx_round2", tuple(round(ч, 2) for ч in точка))):
            if _канон(значення) == _канон(факт["value"]):
                return dict(field="hex", conversion=спосіб)
    return факт["value"]


# ── ПЕРЕЛІК ОДНАКОВИХ ЗАПИСІВ — ТАБЛИЦЕЮ ──────────────────────────────────────────────────
# Пул складання переліком обʼєктів платив би ім'я кожного ключа на кожній речі:
# 38 % токенів пулу руки 1 (Qwen 3.5, офіс, 463 речі) — імена ключів, а не факти про речі.
# Ключ, що стоїть хоча б у чверті записів, — колонка, названа раз (`cols`); запис —
# рядок значень у порядку колонок (`rows`), `null` — такого ключа в записі нема; решта ключів
# запису — обʼєктом у кінці рядка. Факти й порядок записів ті самі, назад читається однозначно
# (`рядки_таблиці`). Поріг чверті виміряно: колонка коштує `null` на рядку без ключа, рідкий
# ключ — своє ім'я на кожному записі, де він є.
ЧАСТКА_КОЛОНКИ = 0.25


def таблиця(перелік):
    """Перелік обʼєктів → {"cols": [ключ…], "rows": [[значення…], …]} без втрати жодного ключа."""
    лік, порядок = {}, []
    for о in перелік:
        for к in о:
            if к not in лік:
                порядок.append(к)
                лік[к] = 0
            лік[к] += 1
    кол = [к for к in порядок if лік[к] >= ЧАСТКА_КОЛОНКИ * len(перелік)]
    рядки = []
    for о in перелік:
        решта = {к: в for к, в in о.items() if к not in кол}
        рядки.append([о.get(к) for к in кол] + ([решта] if решта else []))
    return {"cols": кол, "rows": рядки}


# Остання розгорнута таблиця: збирач питає ту саму таблицю пулу за кожним полем «pool[].…»
# (~7 разів на промпт, промпт — на кожен крок пошуку бюджету), а дані виклику він не міняє.
_ОСТАННЯ = (None, None)


def рядки_таблиці(т):
    """Таблиця (`таблиця`) → перелік обʼєктів; що не таблиця — як є."""
    global _ОСТАННЯ
    if not (isinstance(т, dict) and isinstance(т.get("cols"), list) and isinstance(т.get("rows"), list)):
        return т
    if _ОСТАННЯ[0] is т:
        return _ОСТАННЯ[1]
    вих = []
    for р in т["rows"]:
        о = {к: в for к, в in zip(т["cols"], р) if в is not None}
        if len(р) > len(т["cols"]) and isinstance(р[-1], dict):
            о.update(р[-1])
        вих.append(о)
    _ОСТАННЯ = (т, вих)
    return вих


def ущільнити(промпт, завдання="task", вхід="input"):
    """Один спільний словник до всіх живих читачів, включно з replacement."""
    описи, факти, застосовність, секції, індекси = [], [], [], {}, ({}, {}, {})

    def інтернувати(значення, таблиця_, індекс):
        """Дати однаковим JSON-фактам один індекс у цьому виклику."""
        ключ = _канон(значення)
        if ключ not in індекс:
            індекс[ключ] = len(таблиця_)
            таблиця_.append(значення)
        return індекс[ключ]

    def річ(в):
        """Винести повний договір, лишивши старі поля речі незмінними."""
        коди = []
        for назва in ВЛАСТИВОСТІ:
            факт = в["knowledge"][назва]
            застос = інтернувати(факт["applicability"], застосовність, індекси[2])
            опис = [факт["status"], факт["source"], застос]
            код = інтернувати(опис, описи, індекси[0])
            значення = _точка_посиланням(в, факт) if назва == "color" else факт["value"]
            коди.append(інтернувати([код, значення], факти, індекси[1]))
        вих = {к: р for к, р in в.items() if к != "knowledge"}
        for ключ, назва in (("color_range", "color"), ("metal", "metal")):
            if ключ in вих and _канон(вих[ключ]) == _канон(в["knowledge"][назва]["value"]):
                вих.pop(ключ)
        return вих, коди

    def пройти(в, шлях=""):
        """Скопіювати дані й назвати точний шлях кожної фактичної секції."""
        if isinstance(в, list):
            рядки, коди = [], []
            for і, р in enumerate(в):
                запис, код = річ(р) if _повне(р) else (р, None)
                рядки.append(пройти(запис, _шлях(шлях, і)))
                коди.append(код)
            if any(к is not None for к in коди):
                секції[шлях] = dict(rows=коди)
            return рядки
        if not isinstance(в, dict):
            return в
        if set(в) == {"cols", "rows"}:
            return таблиця(пройти(рядки_таблиці(в), шлях))
        if _повне(в):
            в, коди = річ(в)
            секції[шлях] = dict(item=коди)
        return {к: пройти(р, _шлях(шлях, к)) for к, р in в.items()}

    вих = пройти(промпт)
    if not факти:
        return вих
    типові = _типові(секції)
    вих[завдання][вхід] = [*вих[завдання][вхід], ОПИС]
    словник = dict(properties=list(ВЛАСТИВОСТІ), applicability=застосовність,
                  descriptors=описи, facts=факти, defaults=типові, sections=секції)
    # Т-7: словник перед схемою і кінцевою вказівкою, які лишаються останніми.
    місце = next((к for к in вих if к in ("answer_schema", "схема_відповіді")), None)
    хвіст = list(вих)[list(вих).index(місце):] if місце else []
    кінець = {к: вих.pop(к) for к in хвіст}
    вих["knowledge_legend"] = словник
    вих.update(кінець)
    return вих


def відновити(промпт):
    """Зворотний договір для проб: повні факти і перенесені нові значення."""
    словник = промпт["knowledge_legend"]

    def доповнити(річ, коди):
        """Відновити повний договір саме цього рядка, без припущення про n."""
        if коди is None:
            return річ
        коди = [коди] if isinstance(коди, int) else коди
        коди = коди + словник["defaults"][len(коди):]
        знання = {}
        for назва, код in zip(словник["properties"], коди):
            індекс, значення = словник["facts"][код]
            стан, джерело, застос = словник["descriptors"][індекс]
            if назва == "color" and isinstance(значення, dict) and "field" in значення:
                поле, спосіб = значення["field"], значення["conversion"]
                значення = річ[поле]
                if спосіб != "identity":
                    значення = hx(значення)
                    if спосіб == "hx_round2":
                        значення = tuple(round(ч, 2) for ч in значення)
            знання[назва] = dict(status=стан, source=джерело, value=значення,
                                 applicability=словник["applicability"][застос])
        вих = dict(річ, knowledge=знання)
        if знання["color"]["status"] == "range":
            вих["color_range"] = знання["color"]["value"]
        if знання["metal"]["status"] in ("measured", "range"):
            вих["metal"] = знання["metal"]["value"]
        return вих

    def пройти(в, шлях=""):
        """Приєднати факти за явним шляхом та індексом фактичного рядка."""
        секція = словник["sections"].get(шлях) or {}
        if isinstance(в, list):
            рядки = [пройти(р, _шлях(шлях, і)) for і, р in enumerate(в)]
            return [доповнити(р, к) for р, к in zip(рядки, секція["rows"])] if "rows" in секція else рядки
        if not isinstance(в, dict):
            return в
        if set(в) == {"cols", "rows"}:
            return таблиця(пройти(рядки_таблиці(в), шлях))
        вих = {к: пройти(р, _шлях(шлях, к)) for к, р in в.items()}
        return доповнити(вих, секція["item"]) if "item" in секція else вих

    return {к: пройти(р, _шлях("", к)) for к, р in промпт.items() if к != "knowledge_legend"}
