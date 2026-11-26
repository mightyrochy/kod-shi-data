"""К3: промпт запису речі нового виду й розбір відповіді моделі — з одного визначення міток ядра (`ядро/мітки.py`,
`ядро/дані/мітки_речі.json`). Поза живим шляхом: модель кличе прохід К3 (`аудит/проби/запис-речі-вибірка-300/скрипти/
прохід_новий.py`), результат — ключ `мітки_речі` рядка каталогу (не `запис_речі`: так старий шлях зве розбір офера), який читає Ч2 (`ядро/річ.py`)."""
import json

from ядро import мітки
from ядро.поняття import НЕВІДОМО

СИСТЕМНИЙ = ("You write the record of one clothing or accessory item from a Ukrainian online shop for a styling app. "
             "The user message holds the shop's own words, maybe a size table, and photos of the item. "
             "Answer with raw JSON only, no code fence, no commentary.")


def промпт(слова_крамниці, фото_шт, таблиця=None):
    """Системний і користувацький текст запису речі з визначення міток."""
    т = ["Shop words" + (", size table" if таблиця else "") + f" and {фото_шт} photo(s) of one item follow.",
         "", "=== SHOP WORDS ===", слова_крамниці]
    if таблиця:
        т += ["", "=== SIZE TABLE (from the shop; rows separated by ';') ===", таблиця]
    т += ["", "=== TASK ===",
          'Return {"опис": <text>, "мітки": {<key>: {"в": <value>, "дж": "крамниця" | "фото", "межі": <only for uncertain>}}}.',
          f'"опис": {мітки.МІТКИ["опис"]["питання"]}',
          "Labels answer only the questions below. Skip a label whose «only for» does not include the item's slot.",
          'No answer in the shop words or on the photos -> {"в": "невідомо"}. Do not pick a typical or middle value.',
          'A measure you can only bound -> {"в": "не_певний", "межі": [low, high], "дж": ...}.',
          '"дж" is where the answer comes from: "крамниця" (the shop\'s words) or "фото"; allowed sources are listed per label.']
    for поле in мітки.ЗАПИТАНІ:
        опис = мітки.МІТКИ[поле]
        рядок = f'- "{поле}": {опис["питання"]}'
        к = мітки.коди(поле)
        if к is not None:
            рядок += (" One or more of: " if опис.get("кілька") else " One of: ") + ", ".join(к) + "."
        elif опис.get("значення") == "число_см":
            рядок += " A number of centimetres."
        if "де" in опис:
            рядок += " Only for: " + ", ".join(мітки.слоти(опис["де"])) + "."
        if "не_для" in опис:
            рядок += " Not for: " + ", ".join(мітки.слоти(опис["не_для"])) + "."
        рядок += " Sources: " + ", ".join(опис["джерела"]) + "."
        т.append(рядок)
    return СИСТЕМНИЙ, "\n".join(т)


def розібрати(текст):
    """Відповідь моделі → запис речі {опис, мітки: {поле: {значення, джерело[, межі]}}, збої}.

    Мітка поза визначенням, значення поза кодами чи джерело, якого мітка не дозволяє, — збій з назвою поля, а мітки в
    записі нема («невідомо»): запис не вгадує за модель."""
    текст = (текст or "").strip()
    if текст.startswith("```"):
        текст = текст.strip("`").removeprefix("json").strip()
    try:
        сире = json.JSONDecoder().raw_decode(текст)[0]
    except (ValueError, TypeError) as помилка:
        return {"опис": НЕВІДОМО, "мітки": {}, "збої": [{"поле": "*", "що": f"не JSON: {помилка}"}]}
    if not isinstance(сире, dict):
        return {"опис": НЕВІДОМО, "мітки": {}, "збої": [{"поле": "*", "що": "не об'єкт"}]}
    опис = сире.get("опис")
    вихід = {"опис": опис.strip() if isinstance(опис, str) and опис.strip() else НЕВІДОМО, "мітки": {}, "збої": []}
    for поле, відп in (сире.get("мітки") if isinstance(сире.get("мітки"), dict) else {}).items():
        if поле not in мітки.ЗАПИТАНІ:
            вихід["збої"].append({"поле": поле, "що": "мітки нема у визначенні"})
            continue
        значення, збій = мітки.мітка(поле, відп)
        if збій:
            вихід["збої"].append({"поле": поле, "що": збій, "сире": відп})
        if значення is not None:
            вихід["мітки"][поле] = значення
    return вихід
