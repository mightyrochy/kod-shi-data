# -*- coding: utf-8 -*-
"""Інструменти розмови: одне джерело переліку й договір виклику (корінь Е2-усе-з-розмови, етап Е3).

Інструмент — функція продукту, яку мовна модель розмови кличе за тим, чого людина хоче. Запис переліку несе ім'я
(код), що робить, коли кликати, вхід (JSON Schema аргументів), вихід (поля результату) і як показати результат у
розмові. З цього переліку беруть усі: промпт ходу (`мовний_шар`: коди, правило, скелет), форма відповіді ходу
(`схема_відповіді.форма_мовного_шару`, частина `tool`), перевірка виклику (`прийняти_виклик`) і показ, який кличе ту саму
функцію, що й кнопка вікна (`показ/мовний_шар.js`, `інструментомП`).

Договір виклику: модель кладе в хід `tool: {name, args}`; код перевіряє його схемою звідси. Розбіжність повертається
моделі словами на один повтор тим самим каналом, що й решта ходу (`language_contract.розбіжності`); після повтору —
запасний хід коду без зупинки: виконується прийнята частина (ім'я з переліку й аргументи, що пройшли схему), решта —
у записі ходу. Рідного виклику інструментів рушія договір не потребує: співрозмовницею може бути будь-яка модель.

Посилання на дані продукту (`переліки` запису): аргумент — ід запису з переліку цього ходу, який код дає моделі в
промпті (`переліки_промпту`: збережені сценарії — `saved_cases`). Стала схема лишається одна (рядок); допустимі значення
— ід переліку, з яким модель бачила хід, і звіряє їх той самий договір (`звірити_переліки`): ід поза переліком —
розбіжність на один повтор, як і решта вад виклику.
"""
import copy
import re

ІНСТРУМЕНТИ = {
    "save_scenario": {
        "робить": "зберегти сценарій цієї розмови в збережені сценарії: новим або оновити відкритий",
        "для_моделі": "saves this case (the passport and this conversation) to her saved cases",
        "коли": "her new message asks to save or keep this case for later",
        # Назви аргументом нема: назва сценарію — її ввід у полі форми, а слова з відповіді моделі на екрані — не її
        # доведені слова (корінь Е2-текст-жінці); без назви оновлення лишає назву відкритого сценарію.
        "вхід": {"type": "object", "additionalProperties": False, "properties": {
            "as_new": {"type": "boolean",
                       "description": "true — keep it as one more saved case; otherwise the open saved case is "
                                      "updated (a new one when none is open)"}}},
        "вихід": {"type": "object", "additionalProperties": False, "required": ["done"], "properties": {
            "done": {"type": "boolean", "description": "чи збережено"},
            "as_new": {"type": "boolean", "description": "збережено новим, а не оновлено відкритий"},
            "name": {"type": "string", "description": "назва збереженого сценарію — її ввід у формі; без назви — порожньо"}}},
        "показ": "картка під реплікою: збережено чи ні й під якою назвою — тим самим підписом, що в кнопки «Зберегти»",
        "функція": "зберегтиСценарій",
    },
    "list_scenarios": {
        "робить": "показати її збережені сценарії переліком у розмові: назва, про що, дата; відкрити — дотиком",
        "для_моделі": "shows the list of her saved cases under your reply",
        "коли": "her new message asks to see or choose among her saved cases",
        "вхід": {"type": "object", "additionalProperties": False, "properties": {}},
        "вихід": {"type": "object", "additionalProperties": False, "required": ["done"], "properties": {
            "done": {"type": "boolean", "description": "чи прочитано збережені"},
            "scenarios": {"type": "array", "description": "збережені: ід, назва — її ввід, про що, час, чи відкритий"}}},
        "показ": "картка під реплікою: перелік збережених тими самими рядками, що в «Збережених», дотик відкриває",
        "функція": "оновитиСценарії",
    },
    "open_scenario": {
        "робить": "відкрити збережений сценарій: його паспорт і розмову замість поточних",
        "для_моделі": "opens one of her saved cases instead of the current one (what is not saved is lost)",
        "коли": "her new message asks to open or go back to one of her saved cases",
        "вхід": {"type": "object", "additionalProperties": False, "required": ["id"], "properties": {
            "id": {"type": "string", "minLength": 1, "description": "the \"id\" of one of saved_cases"}}},
        "переліки": {"id": "saved_cases"},
        "вихід": {"type": "object", "additionalProperties": False, "required": ["done"], "properties": {
            "done": {"type": "boolean", "description": "чи відкрито"},
            "name": {"type": "string", "description": "назва відкритого — її ввід; без назви — порожньо"}}},
        "показ": "картка в розмові відкритого сценарію: який відкрито — її назвою чи підписом без назви",
        "функція": "відкритиСценарій",
        "заміна_сценарію": True,
    },
    "delete_scenario": {
        "робить": "видалити збережений сценарій",
        "для_моделі": "deletes one of her saved cases for good",
        "коли": "her new message asks to delete or remove one of her saved cases",
        "вхід": {"type": "object", "additionalProperties": False, "required": ["id"], "properties": {
            "id": {"type": "string", "minLength": 1, "description": "the \"id\" of one of saved_cases"}}},
        "переліки": {"id": "saved_cases"},
        "вихід": {"type": "object", "additionalProperties": False, "required": ["done"], "properties": {
            "done": {"type": "boolean", "description": "чи видалено"},
            "name": {"type": "string", "description": "назва видаленого — її ввід; без назви — порожньо"}}},
        "показ": "картка під реплікою: який сценарій видалено — її назвою чи підписом без назви",
        "функція": "видалитиСценарій",
    },
    "new_scenario": {
        "робить": "почати новий сценарій: порожній паспорт і нова розмова",
        "для_моделі": "starts a new empty case with a new conversation (what is not saved is lost)",
        "коли": "her new message asks to start a new case from scratch",
        "вхід": {"type": "object", "additionalProperties": False, "properties": {}},
        "вихід": {"type": "object", "additionalProperties": False, "required": ["done"], "properties": {
            "done": {"type": "boolean", "description": "чи почато"}}},
        "показ": "картка в розмові нового сценарію: почато новий",
        "функція": "новийСценарій",
        "заміна_сценарію": True,
    },
    "confirm_case": {
        "робить": "підтвердити, що паспорт нагоди зрозуміто правильно: зняти питання «Усе правильно?»",
        "для_моделі": "marks the passport of this case as confirmed by her",
        "коли": "her new message says the passport you read from her is right (\"yes\", \"that is right\")",
        "вхід": {"type": "object", "additionalProperties": False, "properties": {}},
        "вихід": {"type": "object", "additionalProperties": False, "required": ["done"], "properties": {
            "done": {"type": "boolean", "description": "чи підтверджено"}}},
        "показ": "картка під реплікою: розуміння підтверджено — тим самим підписом, що в кнопки «так»",
        "функція": "підтвердитиРозумінняП",
    },
    "set_weather_feel": {
        "робить": "обрати відчуття погоди плиткою «Коли й погода» без градусів; уже обране лишається",
        "для_моделі": "sets how the weather feels for this case, without degrees (the same as her tapping the tile)",
        "коли": "her new message says how the weather feels by a word, not by a number, and asks to set it",
        # Коди відчуттів — ті самі, що `ВІДЧУТТЯ_П` у показі (`внутрішня_мова`: weather_feel).
        "вхід": {"type": "object", "additionalProperties": False, "required": ["feel"], "properties": {
            "feel": {"type": "string", "enum": ["deep_frost", "frost", "cold", "cool", "mild", "warm", "hot"],
                     "description": "how the weather feels, from the coldest to the hottest"}}},
        "вихід": {"type": "object", "additionalProperties": False, "required": ["done"], "properties": {
            "done": {"type": "boolean", "description": "чи обрано"},
            "feel": {"type": "string", "description": "обране відчуття; порожньо, коли вибір знято"}}},
        "показ": "картка під реплікою: яке відчуття погоди обрано — тим самим підписом, що на плитці",
        "функція": "обратиВідчуттяП",
    },
}

# Переліки цього ходу: ім'я в промпті → ключ входу ендпойнта `мова`, який дає показ (`ходомРозмовиП`), і поля запису.
ПЕРЕЛІКИ = {"saved_cases": {"вхід": "збережені", "поля": {"id": "ід", "name": "назва", "case": "випадок",
                                                         "date": "час", "open": "відкрито"}}}
ПЕРЕЛІК_МАКС = 30


def схема_виклику():
    """JSON Schema частини `tool` відповіді ходу: один виклик інструмента з переліку з його аргументами."""
    return {"type": "object", "additionalProperties": False, "required": ["name"],
            "description": "one call of a tool listed under Tools in codes, only when her new message asks the app to do it",
            "oneOf": [{"properties": {"name": {"const": ім}, "args": copy.deepcopy(о["вхід"])}}
                      for ім, о in ІНСТРУМЕНТИ.items()],
            "properties": {"name": {"enum": list(ІНСТРУМЕНТИ)}, "args": {"type": "object"}}}


def скелет():
    """Частина `tool` у скелеті відповіді ходу — форма, а не значення."""
    return {"name": "a tool from codes", "args": {"<argument>": "its value"}}


def коди_для_промпту():
    """Рядки переліку для сталого словника кодів ходу: ім'я, що робить, коли кликати, аргументи з їхніх описів."""
    р = ["Tools (\"tool\": {\"name\", \"args\"}; the app does it and shows the result under your reply):"]
    for ім, о in ІНСТРУМЕНТИ.items():
        аргументи = "; ".join("%s (%s) — %s" % (к, с["type"], с["description"])
                              for к, с in о["вхід"]["properties"].items()) or "none"
        р.append("- %s: %s; when %s. args: %s" % (ім, о["для_моделі"], о["коли"], аргументи))
    return tuple(р)


_ТИПИ = {"object": dict, "string": str, "boolean": bool, "array": list}


def _вади_значення(значення, схема, шлях):
    """Розбіжності значення зі схемою підмножини JSON Schema, якою записано входи переліку."""
    тип = схема.get("type")
    if тип and not (isinstance(значення, _ТИПИ[тип]) and not (тип != "boolean" and isinstance(значення, bool))):
        return ["%s: must be %s" % (шлях, тип)]
    if "enum" in схема and значення not in схема["enum"]:
        return ["%s: must be one of %s" % (шлях, ", ".join(map(str, схема["enum"])))]
    if тип == "string":
        if len(значення.strip()) < схема.get("minLength", 0):
            return ["%s: must not be empty" % шлях]
        if len(значення) > схема.get("maxLength", len(значення)):
            return ["%s: longer than %d characters" % (шлях, схема["maxLength"])]
    return []


def прийняти_виклик(виклик):
    """Виклик моделі → (прийнятий виклик чи None, розбіжності рядками `tool…: що не так`).

    Прийнятий — ім'я з переліку й лише ті аргументи, що пройшли схему; без обов'язкового аргументу виклику нема.
    Розбіжності — вхід одного повтору моделі й запис ходу."""
    if виклик in (None, "", {}, []) or (isinstance(виклик, str) and виклик.strip().lower() in ("none", "null")):
        return None, []
    if not isinstance(виклик, dict):
        return None, ["tool: must be an object {\"name\", \"args\"}"]
    ім = виклик.get("name")
    if ім not in ІНСТРУМЕНТИ:
        return None, ["tool.name: %s is not a tool; tools: %s" % (ім, ", ".join(ІНСТРУМЕНТИ))]
    вхід = ІНСТРУМЕНТИ[ім]["вхід"]
    аргументи = виклик.get("args") if виклик.get("args") is not None else {}
    вади = ["tool.%s: not a key of the call" % к for к in виклик if к not in ("name", "args")]
    if not isinstance(аргументи, dict):
        return None, вади + ["tool.args: must be an object"]
    прийняті = {}
    for к, з in аргументи.items():
        схема = вхід["properties"].get(к)
        if схема is None:
            вади.append("tool.args.%s: not an argument of %s" % (к, ім))
            continue
        if з is None:
            continue
        в = _вади_значення(з, схема, "tool.args." + к)
        if в:
            вади += в
        else:
            прийняті[к] = з.strip() if isinstance(з, str) else з
    бракує = [к for к in вхід.get("required", ()) if к not in прийняті]
    вади += ["tool.args.%s: required value is missing" % к for к in бракує]
    return (None if бракує else {"name": ім, "args": прийняті}), вади


def _перелік(d, ім):
    """Записи переліку `ім` зі входу ендпойнта: лише словники з непорожнім ід, не більше `ПЕРЕЛІК_МАКС`."""
    о = ПЕРЕЛІКИ[ім]
    сирі = (d or {}).get(о["вхід"]) if isinstance(d, dict) else None
    return [з for з in (сирі if isinstance(сирі, list) else ())
            if isinstance(з, dict) and isinstance(з.get(о["поля"]["id"]), str) and з[о["поля"]["id"]]][:ПЕРЕЛІК_МАКС]


def переліки_промпту(d):
    """Переліки цього ходу для промпту: {ім'я: [{id, name, …}]} — лише непорожні; назва — її ввід як є.

    Перелік, що не прочитався, вхід несе кодом причини (рядок, напр. `saved_cases_unreadable`): він іде в промпт як є,
    щоб модель не сказала «збережених нема»."""
    вих = {}
    for ім, о in ПЕРЕЛІКИ.items():
        сирі = (d or {}).get(о["вхід"]) if isinstance(d, dict) else None
        if isinstance(сирі, str) and re.fullmatch(r"[a-z][a-z0-9_]{2,60}", сирі):
            вих[ім] = сирі
            continue
        записи = [{к: з[п] for к, п in о["поля"].items() if з.get(п) not in (None, "")} for з in _перелік(d, ім)]
        if записи:
            вих[ім] = записи
    return вих


def звірити_переліки(результат, d):
    """Розбір ходу → той самий, де виклик з ід поза переліком цього ходу знято, а вада — у `незнайомі` (повтор).

    Прийнятий виклик (`частини.tool`) уже пройшов сталу схему; тут — лише посилання на дані продукту."""
    виклик = ((результат or {}).get("частини") or {}).get("tool")
    if not isinstance(виклик, dict) or not ІНСТРУМЕНТИ.get(виклик.get("name"), {}).get("переліки"):
        return результат
    вади = []
    for арг, ім in ІНСТРУМЕНТИ[виклик["name"]]["переліки"].items():
        ід = (виклик.get("args") or {}).get(арг)
        є = [з[ПЕРЕЛІКИ[ім]["поля"]["id"]] for з in _перелік(d, ім)]
        if ід is not None and ід not in є:
            вади.append("tool.args.%s: %s is not an id of %s; ids: %s" % (арг, ід, ім, ", ".join(є) or "none"))
    if not вади:
        return результат
    р = dict(результат, частини={к: в for к, в in результат["частини"].items() if к != "tool"})
    р["незнайомі"] = list(результат.get("незнайомі") or []) + вади
    return р
