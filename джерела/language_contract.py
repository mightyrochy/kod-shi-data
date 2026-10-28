# -*- coding: utf-8 -*-
"""Договір мовного шару: пояснення втрат розбору й збереження названої події."""
import copy
import json
import re
import внутрішня_мова as М
import формальність as Ф


def пояснити_повтор(промпт, причина, маркер=""):
    """Додати розбіжність, зберігши структурований вхід промпта придатним до розбору."""
    if not причина:
        return промпт
    if not маркер:
        об = json.loads(промпт)
        об["format_error"] = "Correct the previous answer: " + str(причина)
        return json.dumps(об, ensure_ascii=False)
    чому = {"no_text_field": "немає непорожнього рядка text",
             "only_questions": "текст не передає прийнятих фактів або ставить недозволені питання"}.get(
                 str(причина), str(причина))
    return промпт.replace(маркер, "Розбіжність попередньої відповіді: " + чому + ".\n\n" + маркер, 1)


def відсутні_поля(значення, схема, шлях=""):
    """Знайти обов’язкові поля вкладених об’єктів за тим самим словником розбору."""
    if "$ref" in схема:
        схема = М.схема()["$defs"][схема["$ref"].rsplit("/", 1)[-1]]
    if isinstance(значення, dict):
        бракує = [шлях + "." + к + ": required value is missing"
                  for к in схема.get("required", []) if к not in значення]
        return бракує + [п for к, в in значення.items() if к in схема.get("properties", {})
                         for п in відсутні_поля(в, схема["properties"][к], шлях + "." + к)]
    if isinstance(значення, list):
        return [п for і, в in enumerate(значення)
                for п in відсутні_поля(в, схема.get("items", {}), "%s[%d]" % (шлях, і))]
    return []


def доповнити(було, нове):
    """Доповнити прийняте значення без заміни вже відомих фактів.

    Речі зі списку зіставляються лише за ідентичністю або їхнім уривком,
    тому переставлений повтор не змінює речі місцями.
    """
    if isinstance(було, dict) and isinstance(нове, dict):
        return {к: доповнити(в, нове[к]) if к in нове else copy.deepcopy(в) for к, в in було.items()} | {
            к: copy.deepcopy(в) for к, в in нове.items() if к not in було}
    if isinstance(було, list) and isinstance(нове, list):
        вих = []
        for в in було:
            пара = next((н for н in нове if isinstance(в, dict) and isinstance(н, dict)
                         and any(в.get(к) and в.get(к) == н.get(к) for к in ("id", "item", "quote"))), None)
            вих.append(доповнити(в, пара) if пара is not None else copy.deepcopy(в))
        вих += [copy.deepcopy(н) for н in нове if isinstance(н, dict) and (н.get("id") or н.get("item") or н.get("quote"))
                and not any(isinstance(в, dict) and any(н.get(к) and н.get(к) == в.get(к)
                            for к in ("id", "item", "quote")) for в in було)]
        return вих
    return copy.deepcopy(було)


def розбіжності(результат, сирий, поля, обовʼязкові=()):
    """Додати один запит виправлення для відкинутих значень і відсутніх полів.

    Розбір уже перевіряє коди й форми за своїм словником. Тут ті самі відхилення
    стають входом повтору; прийняті значення лишаються доступні запасному ходу.
    """
    р = dict(результат)
    об = сирий if isinstance(сирий, dict) else {}
    вади = list(dict.fromkeys(str(x) for x in р.get("незнайомі") or []))
    for поле, значення in (р.get("внутрішня") or {}).items():
        if поле in поля:
            вади += відсутні_поля(значення, поля[поле], поле)
    for поле in обовʼязкові:
        if поле not in (р.get("внутрішня") or {}):
            вади.append(поле + ": required value is missing")
    if not вади:
        return р
    описи = []
    for вада in dict.fromkeys(вади):
        поле = re.split(r"[.\[=:]", вада, 1)[0]
        if поле not in поля and поле not in об:
            continue
        форма = поля.get(поле)
        if поле == "formality":
            форма = {"enum": [щ["код"] for щ in Ф.ДРАБИНА]}
        опис = ("Field %s: %s. Previous value: %s." % (
            поле, вада, json.dumps(об.get(поле), ensure_ascii=False)))
        опис += (" Use this field schema: %s." % json.dumps(форма, ensure_ascii=False)
                 if форма else " This key is not a field; use the matching declared field.")
        описи.append(опис)
    if описи:
        р["повтор"] = "contract: " + " ".join(описи) + " Return the corrected answer once; keep all known facts."
    return р


def зберегти_подію(результат, сирий):
    """Після невдалого повтору зберегти її назву події без вигадування коду нагоди.

    Невідомий код не стає відомим. Його процитована нагода лишається подією,
    яку вміє читати паспорт; сирі значення й причина залишаються в журналі.
    """
    р = copy.deepcopy(результат)
    об = сирий if isinstance(сирий, dict) else {}
    в = р.setdefault("внутрішня", {})
    нагода = об.get("occasion")
    if not в.get("occasion") and not в.get("event") and isinstance(нагода, dict):
        цитата = нагода.get("quote")
        if isinstance(цитата, str) and цитата.strip():
            в["event"] = {"free_text": цитата.strip(), "lang": "uk"}
            в.setdefault("quotes", {})["event"] = цитата.strip()
    if р.get("повтор"):
        р["запасний"] = р.pop("повтор")
    if р.get("причина") and в:
        р["запасний"] = р["причина"]
        р["причина"] = None
    return р


def контекст_репліки(репліка, паспорт, коди, запрошення=""):
    """Додати відомі факти й дані коду до обох шляхів перекладу репліки."""
    п = паспорт if isinstance(паспорт, dict) else {}
    р = dict(репліка or {})
    р["passport"] = {к: в for к, в in коди.items() if not к.startswith("formality")}
    р["advice"] = запрошення or п.get("порада_людині") or ""
    р["code_data"] = {"advice_topics": п.get("поради_дані") or [],
                       "not_recorded": п.get("не_взято_кодом") or [],
                       "required": р.get("required") or []}
    return р
