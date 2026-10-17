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
ПОВТОР = "повтор_форми"
ВІДМОВА = "replacement_model_found_none"  # модель чесно відповіла «підходящої речі нема»: не помилка форми


def _поле_помилки(як, бачила=True):
    """Поле повтору: код, чому відповідь на це саме повідомлення не прочитано; є лише на повторі, тож сталий початок
    промпта (кеш) той самий, що на першому виклику (як `format_error` ходу розмови). `бачила` False — повтор іде
    іншим промптом, ніж перша відповідь (оцінка/турнір): модель попередньої відповіді не бачила."""
    опис = ("the code of why your previous answer to this same message could not be used" if бачила
            else "the code of why this request is sent again")
    return _ЗП.Поле("format_error", опис, як=як)


_ПОМИЛКА_ПУЛУ = _поле_помилки("answer again: one JSON object following \"answer_schema\" with exactly one «n» of "
                             "«pool»")
_ПОМИЛКА_ПЕРЕЛІКУ = _поле_помилки("answer again: one JSON object following \"answer_schema\" with exactly one "
                                  "item, its \"worn\" true")


_ПОМИЛКА_ПУЛУ_ІНШИЙ = _поле_помилки(_ПОМИЛКА_ПУЛУ.як, бачила=False)


def _відповідь(з):
    """→ (текст відповіді моделі | None, чи це відповідь на повтор форми). Показ повертає відповідь першого
    виклику як `текст`, а повтору (`ключ` не «replace») — як `відповіді` разом зі `стан`, який віддав код."""
    if isinstance(з.get("стан"), dict) and ПОВТОР in з["стан"]:
        return str(((з.get("відповіді") or [{}])[0] or {}).get("текст") or ""), True
    return (з["текст"], False) if "текст" in з else (None, False)


def _повтор_форми(вже, причина, промпт):
    """Відповідь не тієї форми: ОДИН повтор того самого промпта з причиною кодом; повтор, що теж не той, —
    відмова з тією самою причиною. `промпт` — виклик, що збирає текст, лише коли повтор потрібен."""
    код = str(причина).split("(")[0]
    if вже:
        return dict(готово=True, чому=причина)
    return dict(готово=False, стан={ПОВТОР: код},
                запити=[dict(ключ="replace_retry", чого="replace_item_retry", текст=промпт(код))])


def _номер_відповіді(текст, відомі):
    """→ (номер «n» | None, причина | None) відповіді за схемою `ОБРАЗИ_V1` з одним образом і однією річчю.
    Відповідь-список з одного номера пулу (`["#2·18"]`) — теж ця річ: модель назвала її однозначно, а код читає
    номер, не слова (п.12); рядок поза пулом форми не рятує."""
    об, причина, _ = _ПР.розбір_за_схемою(текст, "ОБРАЗИ_V1")
    образи = (об or {}).get("образи") or []
    if not причина and (not образи or all(not (о.get("речі") or []) for о in образи)):
        return None, ВІДМОВА
    if len(образи) == 1 and len(образи[0].get("речі") or []) == 1:
        return _УВ.ключ_н(образи[0]["речі"][0]), None
    try:
        список = _json.loads("\n".join(р for р in str(текст or "").splitlines() if not р.startswith("```")))
    except ValueError:
        список = None
    if isinstance(список, list) and not список:
        return None, ВІДМОВА
    if isinstance(список, list) and len(список) == 1 and _УВ.ключ_н(список[0]) in відомі:
        return _УВ.ключ_н(список[0]), None
    return None, причина or "replacement_not_one_item"


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


def промпт_складання(пакет, помилка=None, бачила=True):
    """Складання на один слот: роль заміни, вхід складання без полів набору, ноти лише виду слота, відповідь —
    один номер речі (рядок 6209). `помилка` — код, чому попередню відповідь не прийнято (повтор, один)."""
    з = пакет.get("заміна")
    дані = {к: v for к, v in _Д.пакет(пакет).items() if к not in _НЕ_ДЛЯ_ЗАМІНИ}
    дані["replacement"] = контекст(з)
    дані["format_error"] = помилка
    вид = дані["replacement"]["slot"]
    if isinstance(дані.get("kind_notes"), dict):
        дані["kind_notes"] = {к: v for к, v in дані["kind_notes"].items() if к == вид}
    о = _dc.replace(_ПМ.СКЛАДАННЯ, роль=РОЛЬ,
        вхід=tuple(п for п in _ПМ.СКЛАДАННЯ.вхід if п.шлях not in _НЕ_ДЛЯ_ЗАМІНИ) + (_ПОЛЕ, _ПОМИЛКА_ПУЛУ if бачила else _ПОМИЛКА_ПУЛУ_ІНШИЙ),
        правила=_ПРАВИЛА + (_ПМ.РЯДОК_ЛИШЕ_НОМЕР,), скелет=_СКЕЛЕТ,
        поля_виходу={"outfits[].items": "exactly one eligible «n» of «pool», or []"})
    return _json.dumps(_ЗП.зібрати(о, дані,
        мова_тексту=(пакет.get("завдання") or {}).get("мова_тексту")), ensure_ascii=False, separators=(",", ":"))


def _промпт_без_каталогу(d, помилка=None):
    """Промпт руки 3–4 на один слот; `помилка` — код повтору форми (один)."""
    з = d["заміна"]
    к = контекст(з)
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
    базовий["format_error"] = помилка
    о = _dc.replace(_РБ.ОБРАЗ, вхід=_РБ.ОБРАЗ.вхід + (_ПОЛЕ, _ПОМИЛКА_ПЕРЕЛІКУ), правила=_ПРАВИЛА,
        вихід=_РБ.ПЕРЕЛІК.вихід, скелет=_РБ.ПЕРЕЛІК.скелет,
        відповідь_як="json", поля_виходу=_РБ.ПЕРЕЛІК.поля_виходу)
    return _json.dumps(_ЗП.зібрати(о, базовий, мова_тексту=d.get("мова_тексту")), ensure_ascii=False)


def _порожній_перелік(текст):
    """Відповідь рук 3–4 — JSON з порожнім переліком речей (`items` — `[]`) або порожній список."""
    try:
        об = _json.loads("\n".join(р for р in str(текст or "").splitlines() if not р.startswith("```")))
    except ValueError:
        return False
    items = об.get("items") if isinstance(об, dict) else об
    return items == []


def без_каталогу(d):
    """Руки 3–4 обирають одну вигадану річ тим самим модельним контекстом, без каталогу. Відповідь, що не одна річ
    (`worn` false, кілька, не обʼєкт), — один повтор із причиною кодом."""
    з = d["заміна"]
    контекст(з)
    текст, повтор = _відповідь(з)
    if текст is not None:
        речі = _РБ.речі_переліку(текст)
        if речі == [] or _порожній_перелік(текст):
            return dict(готово=True, чому=ВІДМОВА)
        if not речі or len(речі) != 1 or not речі[0].get("носить"):
            return _повтор_форми(повтор, "replacement_not_one_item", lambda код: _промпт_без_каталогу(d, код))
        р = речі[0]
        if р.get("слот") != з["слот"] or р.get("own"):
            return dict(готово=True, чому="replacement_wrong_slot_or_owned")
        стара = next(р for р in з["речі"] if str(р.get("id")) == str(з["ід"]))
        # Тотожність — дані, не семантика слів: повтор усіх полів не є заміною.
        if all(р.get(п) == стара.get(п) for п in ("назва", "деталі", "hex")):
            return dict(готово=True, чому="replacement_same_item")
        return dict(готово=True, річ=dict(р, id="м-заміна-" + str(з["запит"]), вигадана=True))
    return dict(готово=False, запити=[dict(ключ="replace", чого="replace_item", текст=_промпт_без_каталогу(d))])


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
    текст, повтор = _відповідь(з)
    if текст is None:
        if _УВ.спосіб(з.get("спосіб")) != "list":
            в = _УВ.крок(з, п, сцен, сід, межі=d.get("межі"))
            if в.get("текст_складання"):
                return крок(dict(d, заміна=dict(з, текст=в["текст_складання"])), пак, сцен, сід)
            if в.get("промпт_фіналу"):
                return dict(в, готово=False, запити=[dict(ключ="replace", чого="replace_item", текст=в["промпт_фіналу"])])
            return в
        return dict(готово=False, запити=[dict(ключ="replace", чого="replace_item", текст=промпт_складання(пакет))])
    н, причина = _номер_відповіді(текст, дозволені)
    if причина == ВІДМОВА:
        return dict(готово=True, чому=ВІДМОВА)
    if н is None:
        # Повтор іде промптом «списку» над пулом слота: стан «оцінки»/«турніру» до повтору не доходить — показ
        # повертає коду лише відповідь, а не промпт, на який вона була.
        return _повтор_форми(повтор, причина, lambda код: промпт_складання(пакет, код, бачила=_УВ.спосіб(з.get("спосіб")) == "list"))
    р = дозволені.get(н)
    if р is None:
        return dict(готово=True, чому="replacement_outside_pool_or_same_item")
    return dict(готово=True, річ=dict(р, слот=слот), номер=н)
