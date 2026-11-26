"""Запис речі нового виду — одне визначення міток (`дані/мітки_речі.json`) для промпту запису (К3) і для Ч2.

Запис — дві частини: вільний опис (усе, що модель бачить; читає стилістка й суддя-модель) і мітки — відповіді лише на
питання, які ставить код. Мітка — поле `ПОЛЯ_РЕЧІ` (`поняття.py`) з кодами названого реєстру; поза своїми слотами
мітки нема; без відповіді — «невідомо», вимір без певності — «не_певний» з межами, типового нема (корінь
`Річ-запис-речі`, рішення менеджера 21.11 і 26.11). Модуль моделей не кличе: промпт складає, відповідь перевіряє.
"""
import importlib
import json
from functools import lru_cache
from pathlib import Path

from .поняття import НЕВІДОМО, НЕ_ПЕВНИЙ, Факт

with Path(__file__).with_name("дані").joinpath("мітки_речі.json").open(encoding="utf-8") as _файл:
    _СИРЕ = json.load(_файл)
with Path(__file__).with_name("дані").joinpath("правила.json").open(encoding="utf-8") as _файл:
    _ПРАВИЛА = json.load(_файл)

МІТКИ = {к: в for к, в in _СИРЕ.items() if not к.startswith("_")}
ВИВЕДЕНІ = {к for к, в in МІТКИ.items() if "виведено" in в}
ЗАПИТАНІ = tuple(к for к in МІТКИ if к not in ВИВЕДЕНІ and к != "опис")
_ДЖЕРЕЛА_МОДЕЛІ = {"крамниця": "крамниця", "фото": "фото", "shop": "крамниця", "photo": "фото"}
_СЛУЖБОВІ = ("not_applicable", "unknown", "невідомо", "не_певний")


def _слоти(де):
    return tuple(_СИРЕ[де]) if isinstance(де, str) else tuple(де)


def застосовна(поле, слот):
    """Чи стосується мітка речі цього слоту; поле без визначення стосується всіх."""
    опис = МІТКИ.get(поле)
    if опис is None:
        return True
    if "де" in опис and слот not in _слоти(опис["де"]):
        return False
    return not ("не_для" in опис and слот in _слоти(опис["не_для"]))


def правила_читачі(поле):
    """Правила знань, що оголошують поле своїм входом (ключ «річ» `правила.json`)."""
    return tuple(к for к, п in _ПРАВИЛА.items() if поле in п.get("річ", ()))


def читачі(поле):
    return (*МІТКИ[поле].get("читачі", ()), *правила_читачі(поле))


def _реєстр(шлях):
    модуль, *ключі = шлях.split(".")
    if модуль == "запит":
        from .пул import СЛОТИ
        return tuple(СЛОТИ)
    значення = importlib.import_module(модуль)
    for ключ in ключі:
        значення = значення[ключ] if isinstance(значення, dict) else getattr(значення, ключ)
    return tuple(значення)


@lru_cache(maxsize=None)
def коди(поле):
    """Закриті значення мітки: коди реєстру без службових і без вилучених («без»); None — число чи текст."""
    опис = МІТКИ[поле]
    if "реєстр" in опис:
        шляхи = опис["реєстр"] if isinstance(опис["реєстр"], list) else [опис["реєстр"]]
        вихід = []
        for шлях in шляхи:
            вихід.extend(к for к in _реєстр(шлях) if к not in вихід and к not in _СЛУЖБОВІ)
        return tuple(к for к in вихід if к not in опис.get("без", ()))
    if isinstance(опис.get("значення"), list):
        return tuple(опис["значення"])
    return None


def промпт(слова_крамниці, фото_шт, таблиця=None):
    """Системний і користувацький текст запису речі з того самого визначення міток."""
    системний = ("You write the record of one clothing or accessory item from a Ukrainian online shop for a styling app. "
                 "The user message holds the shop's own words, maybe a size table, and photos of the item. "
                 "Answer with raw JSON only, no code fence, no commentary.")
    т = ["Shop words" + (", size table" if таблиця else "") + f" and {фото_шт} photo(s) of one item follow.",
         "", "=== SHOP WORDS ===", слова_крамниці]
    if таблиця:
        т += ["", "=== SIZE TABLE (from the shop; rows separated by ';') ===", таблиця]
    т += ["", "=== TASK ===",
          'Return {"опис": <text>, "мітки": {<key>: {"в": <value>, "дж": "крамниця" | "фото", "межі": <only for uncertain>}}}.',
          f'"опис": {МІТКИ["опис"]["питання"]}',
          "Labels answer only the questions below. Skip a label whose «only for» does not include the item's slot.",
          'No answer in the shop words or on the photos -> {"в": "невідомо"}. Do not pick a typical or middle value.',
          'A measure you can only bound -> {"в": "не_певний", "межі": [low, high], "дж": ...}.',
          '"дж" is where the answer comes from: "крамниця" (the shop\'s words) or "фото"; allowed sources are listed per label.']
    for поле in ЗАПИТАНІ:
        опис = МІТКИ[поле]
        рядок = f'- "{поле}": {опис["питання"]}'
        к = коди(поле)
        if к is not None:
            рядок += (" One or more of: " if опис.get("кілька") else " One of: ") + ", ".join(к) + "."
        elif опис.get("значення") == "число_см":
            рядок += " A number of centimetres."
        if "де" in опис:
            рядок += " Only for: " + ", ".join(_слоти(опис["де"])) + "."
        if "не_для" in опис:
            рядок += " Not for: " + ", ".join(_слоти(опис["не_для"])) + "."
        рядок += " Sources: " + ", ".join(опис["джерела"]) + "."
        т.append(рядок)
    return системний, "\n".join(т)


def _текст_json(текст):
    текст = (текст or "").strip()
    if текст.startswith("```"):
        текст = текст.strip("`").removeprefix("json").strip()
    return json.JSONDecoder().raw_decode(текст)[0]


def розібрати(текст):
    """Відповідь моделі → запис речі {опис, мітки: {поле: {значення, джерело[, межі]}}, збої}.

    Мітка поза визначенням, значення поза кодами чи джерело, якого мітка не дозволяє, — збій з назвою поля і
    «невідомо» в мітці, а не мовчазне прийняття: запис не вгадує за модель."""
    try:
        сире = _текст_json(текст)
    except (ValueError, TypeError) as помилка:
        return {"опис": НЕВІДОМО, "мітки": {}, "збої": [{"поле": "*", "що": f"не JSON: {помилка}"}]}
    if not isinstance(сире, dict):
        return {"опис": НЕВІДОМО, "мітки": {}, "збої": [{"поле": "*", "що": "не об'єкт"}]}
    опис = сире.get("опис")
    вихід = {"опис": опис.strip() if isinstance(опис, str) and опис.strip() else НЕВІДОМО, "мітки": {}, "збої": []}
    мітки = сире.get("мітки") if isinstance(сире.get("мітки"), dict) else {}
    for поле, відп in мітки.items():
        if поле not in ЗАПИТАНІ:
            вихід["збої"].append({"поле": поле, "що": "мітки нема у визначенні"})
            continue
        факт, збій = мітка(поле, відп)
        if збій:
            вихід["збої"].append({"поле": поле, "що": збій, "сире": відп})
        if факт is not None:
            вихід["мітки"][поле] = факт
    return вихід


def мітка(поле, відп):
    """Одна відповідь моделі → (значення мітки або None, збій або None) за визначенням поля."""
    опис = МІТКИ[поле]
    if not isinstance(відп, dict):
        return None, "очікувано об'єкт {в, дж}"
    в = відп.get("в")
    if в in (None, "", НЕВІДОМО, "unknown", "не видно"):
        return None, None
    дж = _ДЖЕРЕЛА_МОДЕЛІ.get(відп.get("дж"))
    if дж not in опис["джерела"]:
        return None, f"джерело {відп.get('дж')!r} не дозволене для мітки"
    if в == НЕ_ПЕВНИЙ:
        межі = відп.get("межі")
        if not межі:
            return None, "«не_певний» без меж"
        return {"значення": НЕ_ПЕВНИЙ, "джерело": дж, "межі": межі}, None
    к = коди(поле)
    if опис.get("значення") == "число_см":
        if isinstance(в, bool) or not isinstance(в, (int, float)) or в < 0:
            return None, f"очікувано число см, а не {в!r}"
        return {"значення": в, "джерело": дж}, None
    if опис.get("кілька"):
        в = [в] if isinstance(в, str) else в
        if not isinstance(в, list) or not в or any(х not in к for х in в):
            return None, f"значення {в!r} поза кодами"
        return {"значення": в, "джерело": дж}, None
    if к is not None and в not in к:
        return None, f"значення {в!r} поза кодами"
    if к is None and not isinstance(в, str):
        return None, "очікувано текст"
    return {"значення": в, "джерело": дж}, None


def факт_мітки(поле, сире, слот):
    """Мітка запису → Факт ядра; поза слотом чи з битим значенням — None (читач лишає старе джерело)."""
    if not застосовна(поле, слот) or not isinstance(сире, dict):
        return None
    перевірене, збій = мітка(поле, {"в": сире.get("значення"), "дж": сире.get("джерело"), "межі": сире.get("межі")})
    if збій or перевірене is None:
        return None
    значення = перевірене["значення"]
    if значення == НЕ_ПЕВНИЙ:
        return Факт(НЕ_ПЕВНИЙ, перевірене["джерело"], межі=tuple(перевірене["межі"]))
    if поле == "ошатність":
        from формальність import ЩАБЕЛЬ
        значення = tuple(ЩАБЕЛЬ[значення]["смуга"])
    elif isinstance(значення, list):
        значення = tuple(значення)
    return Факт(значення, перевірене["джерело"])


def тепло_шару(слот, тканина, утеплення):
    """Тепло шару виводить код із тканини й утеплення (`мітки_речі.json`, «тепло_шару»); модель його не оцінює.

    Утеплення лише додає тепла; синтетика без утеплення тепла не визначає; поза слотами шару мітки нема."""
    опис = МІТКИ["тепло_шару"]
    if not застосовна("тепло_шару", слот):
        return Факт()
    з_тканини = next((клас for клас, тк in опис["тканина"].items() if тканина.значення in тк), None)
    з_утеплення = опис["утеплення"].get(утеплення.значення)
    порядок = опис["значення"]
    відомі = [к for к in (з_тканини, з_утеплення) if к]
    if not відомі:
        return Факт()
    if з_утеплення is None and утеплення.значення != "none" and застосовна("утеплення", слот) and з_тканини != "warm":
        return Факт()
    тепло = max(відомі, key=порядок.index)
    з_чого = tuple(п for п, к in (("тканина", з_тканини), ("утеплення", з_утеплення)) if к) or ("тканина",)
    return Факт(тепло, "код", з_чого=з_чого)
