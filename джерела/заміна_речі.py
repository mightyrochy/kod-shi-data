# -*- coding: utf-8 -*-
"""Заміна одного слота: той самий пул і модель добору, неторканий решта образу (4945)."""
import copy as _copy
import dataclasses as _dc
import json as _json

import пакет_моделі as _ПМ
import дріт_моделі as _Д
import протокол as _ПР
import збирач_промптів as _ЗП
import внутрішня_мова as _ВМ
import уважний_вибір as _УВ
import руки_без_коду as _РБ

ЗОВНІШНІ_ВХОДИ = {
    "заміна": "показ: один слот і речі одного образу, спосіб добору та відповіді його викликів",
    "рука": "показ: рука картки, що змінюється",
}
_ПОЛЕ = _ЗП.Поле("replacement", "one rejected item and the unchanged items of her outfit",
    як="replace only the rejected item in its slot; fit the choice to every unchanged item; "
       "leave all other items unchanged; do not return the rejected item")
_ПРАВИЛА = ("Choose exactly one different item for replacement.slot, considering the entire fixed outfit. "
            "Return only that item, never a rebuilt outfit. If no eligible different item exists, "
            "return an empty item list. Do not invent a catalogue item or reuse an item already worn.",)
# Роль заміни — одна на її складання й уважний вибір (`уважний_вибір._запит`).
РОЛЬ = "You are the stylist choosing a replacement for one item of her current outfit."
# ЗАМІНА — НЕ СКЛАДАННЯ ДЕСЯТИ ОБРАЗІВ (рядок 6209): доти промпт брав роль і весь вхід `СКЛАДАННЯ` — «You put
# together outfits for her…», задуми набору («each outfit follows its own idea…»), недосяжні задуми, число
# образів, ноти всіх видів і скелет `ОБРАЗИ_V1` з підписом, задумом, «day», «deliberate» і «needed» (2 тис.
# переліків кодів), а правило — «Return only that item». Задуми й число — питання набору, а не однієї речі;
# відповідь — лише номер речі слота.
_НЕ_ДЛЯ_ЗАМІНИ = ("poles", "poles_unavailable", "outfits_wanted")
_СКЕЛЕТ = {"outfits": [{"items": ["<n>"]}]}


def контекст(з):
    """Контекст слота й образу англійським дротом, без читання назв речей."""
    речі = з.get("речі") or []
    ід = str(з.get("ід") or "")
    старі = [р for р in речі if str(р.get("id") or "") == ід]
    слот = з.get("слот")
    if len(старі) != 1 or not слот or старі[0].get("слот") != слот or старі[0].get("власна"):
        raise ValueError("replacement_unknown_item_or_slot")
    return dict(slot=_ВМ.код("slot", слот), rejected=_Д.річ(старі[0]),
                fixed_outfit=[_Д.річ(р) for р in речі if р is not старі[0]])


def промпт_складання(пакет):
    """Складання на один слот: роль заміни, вхід складання без полів набору, ноти лише виду слота, відповідь —
    один номер речі (рядок 6209)."""
    з = пакет.get("заміна")
    дані = {к: v for к, v in _Д.пакет(пакет).items() if к not in _НЕ_ДЛЯ_ЗАМІНИ}
    дані["replacement"] = контекст(з)
    вид = дані["replacement"]["slot"]
    if isinstance(дані.get("kind_notes"), dict):
        дані["kind_notes"] = {к: v for к, v in дані["kind_notes"].items() if к == вид}
    о = _dc.replace(_ПМ.СКЛАДАННЯ, роль=РОЛЬ,
        вхід=tuple(п for п in _ПМ.СКЛАДАННЯ.вхід if п.шлях not in _НЕ_ДЛЯ_ЗАМІНИ) + (_ПОЛЕ,),
        правила=_ПРАВИЛА + (_ПМ.РЯДОК_ЛИШЕ_НОМЕР,), скелет=_СКЕЛЕТ,
        поля_виходу={"outfits[].items": "exactly one eligible «n» of «pool», or []"})
    return _json.dumps(_ЗП.зібрати(о, дані,
        мова_тексту=(пакет.get("завдання") or {}).get("мова_тексту")), ensure_ascii=False, separators=(",", ":"))


def без_каталогу(d):
    """Руки 3–4 обирають одну вигадану річ тим самим модельним контекстом, без каталогу."""
    з = d["заміна"]
    к = контекст(з)
    if "текст" in з:
        речі = _РБ.речі_переліку(з["текст"])
        if not речі or len(речі) != 1 or not речі[0].get("носить"):
            return dict(готово=True, чому="replacement_not_one_item")
        р = речі[0]
        if р.get("слот") != з["слот"] or р.get("own"):
            return dict(готово=True, чому="replacement_wrong_slot_or_owned")
        стара = next(р for р in з["речі"] if str(р.get("id")) == str(з["ід"]))
        # Тотожність — дані, не семантика слів: повтор усіх полів не є заміною.
        if all(р.get(п) == стара.get(п) for п in ("назва", "деталі", "hex")):
            return dict(готово=True, чому="replacement_same_item")
        return dict(готово=True, річ=dict(р, id="м-заміна-" + str(з["запит"]), вигадана=True))
    from міст_вхід import _збірка
    F, T, зріст, _ = _збірка(d)
    випадок = (_РБ.випадок_кодами(d.get("паспорт"), d.get("випадок"), d.get("сценарій"), d.get("вимоги"))
               or d.get("випадок"))
    базовий = _json.loads(_РБ.промпт_руки(str(d["рука"]), випадок,
        вимоги=d.get("вимоги"), вибір=d.get("вибір_кольору"),
        речі_паспорта=(d.get("паспорт") or {}).get("речі"),
        факти=_РБ.особа(d.get("шкіра"), d.get("волосся"), d.get("очі"), зріст, d.get("обхвати"), d.get("намір")),
        мова_тексту=d.get("мова_тексту")))
    базовий.pop("task", None)
    базовий["replacement"] = к
    о = _dc.replace(_РБ.ОБРАЗ, вхід=_РБ.ОБРАЗ.вхід + (_ПОЛЕ,), правила=_ПРАВИЛА,
        вихід=_РБ.ПЕРЕЛІК.вихід, скелет=_РБ.ПЕРЕЛІК.скелет,
        відповідь_як="json", поля_виходу=_РБ.ПЕРЕЛІК.поля_виходу)
    return dict(готово=False, запити=[dict(ключ="replace", чого="replace_item",
        текст=_json.dumps(_ЗП.зібрати(о, базовий, мова_тексту=d.get("мова_тексту")), ensure_ascii=False))])


def крок(d, пак, сцен, сід):
    """Звужує спільний пул до слота, переносить оцінку/турнір і приймає лише одну нову річ."""
    з = d["заміна"]
    контекст(з)
    слот = з["слот"]
    зайняті = {str(р.get("id")) for р in з["речі"]}
    джерело = next((р for р in пак.get("_каталог") or [] if str(р.get("id")) == str(з["ід"])), None)
    if джерело is None:
        return dict(готово=True, чому="replacement_source_not_found")
    каталог = {str(р.get("id")): р for р in пак.get("_каталог") or []}
    п = _copy.deepcopy(пак)
    ном, _ = _ПМ.номери_речей(пак.get("кандидати") or {})
    дозволені = {"#%d·%s" % ном[р["id"]]: р for р in (пак.get("кандидати") or {}).get(слот, [])
                 if str(р.get("id")) not in зайняті and р.get("id") in ном and not _УВ._свої(р)
                 and not any(джерело.get(п) and джерело.get(п) == каталог.get(str(р.get("id")), {}).get(п)
                             for п in ("group_id", "фото_ключ"))}
    пакет = п["пакет"]
    пакет["пул"] = {слот: [р for р in пакет.get("пул", {}).get(слот, []) if р.get("н") in дозволені]}
    п["слот_заміни"] = слот
    пакет["заміна"] = з
    пакет["завдання"]["образів"] = 1
    пакет["обмеження"] = dict(пакет.get("обмеження") or {}, **{"обов'язкові_слоти": [слот], "закріплені": []})
    if not пакет["пул"][слот]:
        return dict(готово=True, чому="replacement_no_eligible_item")
    if "текст" not in з:
        if _УВ.спосіб(з.get("спосіб")) != "list":
            в = _УВ.крок(з, п, сцен, сід, межі=d.get("межі"))
            if в.get("текст_складання"):
                return крок(dict(d, заміна=dict(з, текст=в["текст_складання"])), пак, сцен, сід)
            if в.get("промпт_фіналу"):
                return dict(в, готово=False, запити=[dict(ключ="replace", чого="replace_item", текст=в["промпт_фіналу"])])
            return в
        return dict(готово=False, запити=[dict(ключ="replace", чого="replace_item", текст=промпт_складання(пакет))])
    об, причина, _ = _ПР.розбір_за_схемою(з["текст"], "ОБРАЗИ_V1")
    образи = (об or {}).get("образи") or []
    if len(образи) != 1 or len(образи[0].get("речі") or []) != 1:
        return dict(готово=True, чому=причина or "replacement_not_one_item")
    н = _УВ.ключ_н(образи[0]["речі"][0])
    р = дозволені.get(н)
    if р is None:
        return dict(готово=True, чому="replacement_outside_pool_or_same_item")
    return dict(готово=True, річ=dict(р, слот=слот), номер=н)
