# -*- coding: utf-8 -*-
"""Інструменти розмови: одне джерело переліку й договір виклику (корінь Е2-усе-з-розмови, етап Е3).

Інструмент — функція продукту, яку мовна модель розмови кличе за тим, чого людина хоче. Запис переліку несе ім'я
(код), що робить, коли кликати, вхід (JSON Schema аргументів), вихід (поля результату) і як показати результат у
розмові. З цього переліку беруть усі: промпт ходу (`мовний_шар`: коди, правило, скелет), форма відповіді ходу
(`схема_відповіді.форма_мовного_шару`, частина `tool`), перевірка виклику (`перевірити`) і показ, який кличе ту саму
функцію, що й кнопка вікна (`показ/мовний_шар.js`, `інструментомП`).

Договір виклику: модель кладе в хід `tool: {name, args}`; код перевіряє його схемою звідси. Розбіжність повертається
моделі словами на один повтор тим самим каналом, що й решта ходу (`language_contract.розбіжності`); після повтору —
запасний хід коду без зупинки: виконується прийнята частина (ім'я з переліку й аргументи, що пройшли схему), решта —
у записі ходу. Рідного виклику інструментів рушія договір не потребує: співрозмовницею може бути будь-яка модель.
"""
import copy

import паспорт_поля as _ПП

# Ключ схеми аргументу: рядок мусить стояти дослівно в її словах розмови. Так тримається назва, яку дає лише вона
# (назва сценарію — її ввід, корінь Е2-текст-жінці): модель її не складає, код її не пише.
ЇЇ_СЛОВА = "x-her_words"

ІНСТРУМЕНТИ = {
    "save_scenario": {
        "робить": "зберегти сценарій цієї розмови в збережені сценарії: новим або оновити відкритий",
        "для_моделі": "saves this case (the passport and this conversation) to her saved cases",
        "коли": "her new message asks to save or keep this case for later",
        "вхід": {"type": "object", "additionalProperties": False, "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 80, ЇЇ_СЛОВА: True,
                     "description": "the name she gives it, copied from her words; only when she names it"},
            "as_new": {"type": "boolean",
                       "description": "true — keep it as one more saved case; otherwise the open saved case is "
                                      "updated (a new one when none is open)"}}},
        "вихід": {"type": "object", "additionalProperties": False, "required": ["done"], "properties": {
            "done": {"type": "boolean", "description": "чи збережено"},
            "as_new": {"type": "boolean", "description": "збережено новим, а не оновлено відкритий"},
            "name": {"type": "string", "description": "назва збереженого сценарію — її слова; без назви — порожньо"}}},
        "показ": "картка під реплікою: збережено чи ні, новим чи оновлено, назва її словами",
        "функція": "зберегтиСценарій",
    },
}


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
                              for к, с in о["вхід"]["properties"].items())
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


def перевірити(виклик, слова=""):
    """Виклик моделі → (прийнятий виклик чи None, розбіжності рядками `tool…: що не так`).

    Прийнятий — ім'я з переліку й лише ті аргументи, що пройшли схему; без обов'язкового аргументу виклику нема.
    Розбіжності — вхід одного повтору моделі й запис ходу; аргумент із її слів (`ЇЇ_СЛОВА`) мусить дослівно стояти
    в `слова` — у її репліках розмови."""
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
        if not в and схема.get(ЇЇ_СЛОВА) and not _ПП.цитата_тримає(з, слова):
            в = ["tool.args.%s: not her exact words" % к]
        if в:
            вади += в
        else:
            прийняті[к] = з.strip() if isinstance(з, str) else з
    бракує = [к for к in вхід.get("required", ()) if к not in прийняті]
    вади += ["tool.args.%s: required value is missing" % к for к in бракує]
    return (None if бракує else {"name": ім, "args": прийняті}), вади
