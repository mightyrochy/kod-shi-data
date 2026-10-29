# -*- coding: utf-8 -*-
"""спільні_вимоги.py — вимоги до моделі, спільні для кількох промптів: кожна написана тут раз.

ЧОМУ. Поле входу `case`, `case.goal_zones`, `she_refuses`, `item_keys`… стояло копіями у п'яти модулях промптів
(складання, вердикт, вибір, повнота, рука без коду, розбір): копії розходились («with goal conceal» проти «with any
goal» про ті самі зони) і росли кожна своїм абзацом. Тепер опис поля — `ПОЛЯ[шлях]` тут; промпт бере поле через
`поле(шлях, як=…)` і міняє лише «як» — що з ним робити в ЦІЙ задачі. Новий промпт про ту саму річ не пише опису
вдруге. Мірило — `прилади/промпти_одне_джерело.py` (поля з одним шляхом, написані у ≥ 2 місцях: ПІСЛЯ 0).

Опис поля — англійською дротом (аудит/ПРОДУКТ.md п.12); «що» — що це, «як» за замовчуванням — що з ним робити всюди."""
import збирач_промптів as _ЗП

# значення `goal_extra` — слова кодів, одні для довідника кодів (мовний_шар) і поля входу `case.goal_extra`
КОДИ_GOAL_EXTRA = "taller — a longer line, to look taller; comfort — moving comfortably all day; strict — strictly by the occasion"
ПРОТИ_ВІДМОВ = "do not take an item that goes against her refusals or her words"  # як до `case` складання й руки
ЦИТАТА_ГОВОРИТЬ_БІЛЬШЕ = "they say more than the code: the outfit answers them"  # як до цитат наміру й мети
РОЛЬ_ЗАСТОСУНКУ = "You are the stylist of the Lyusterko styling app."  # початок ролі помічниці, питання й вибору палітри

# шлях → (що, як за замовчуванням). `як` задачі замінює типове; «» вимикає його.
ПОЛЯ = {
    "case": ("her case: the occasion, her words, wishes, mood and refusals", ""),
    "case.goal_quote": ("her own words behind «goal»", ЦИТАТА_ГОВОРИТЬ_БІЛЬШЕ),
    "case.intent_quote": ("her own words behind «intent»", ЦИТАТА_ГОВОРИТЬ_БІЛЬШЕ),
    "case.goal_zones": ("the body zones she wants to draw the eye away from, with any goal",
                        "keep these zones quiet; the rest of the look follows goal"),
    "case.her_words": ("what she asked for in her own words", ""),
    "case.her_other_words": ("the rest of what she said, which no field of «case» carries", "it is part of her case"),
    "case.language_model_note": ("the language model's note on her words about the event, when they are hard to "
                                 "read without context",
                                 "it explains her words and does not replace them: where they differ, her words win"),
    "day": ("her day as facts", ""),
    "person": ("her coloring, palette and body", ""),
    "she_refuses": ("what she refused", ""),
    "style_rules": ("what the code measured about her and this case, her own answers and wishes: each entry is "
                    "{code, values, …}; codes are defined in \"statement_codes\"", ""),
    "outfits_wanted": ("how many outfits to return: exactly this many", ""),
    "item_keys": ("what the keys in «candidates» mean, and defaults for omitted values",
                  "read every item by these keys; restore every absent key that has an `absent =` default"),
    "set": ("the check of the whole set: variety, hero, coordination", ""),
    "register": ("her style: the leading register and the ones next to it", ""),
    "showcase": ("item numbers that can fill what is missing", ""),
    "question": ("her question, in her words", ""),
    "her_new_message": ("her new message", ""),
    "profile": ("her profile in codes: colouring, palette choice, height, what is missing", ""),
    "passport": ("her case passport in codes after the previous turns", ""),
    "chosen": ("what she chose with the tiles on the screen, in codes", ""),
}


def поле(шлях, як=None, **вл):
    """Спільне поле входу: опис — з `ПОЛЯ`, `як` — задачі (`None` — типове, «» — без), `треба` й `без` — як у `Поле`."""
    що, як_типове = ПОЛЯ[шлях]
    return _ЗП.Поле(шлях, що, як=як_типове if як is None else як, **вл)


def поле_помилки(як, до_чого="this same message", коди=None, бачила=True):
    """Поле `format_error` повтору після відмови формату: причина кодом, а не словами (`як` — що писати вдруге); є лише на
    повторі, тож сталий початок промпта (кеш) той самий. `до_чого` — про яку відповідь; `коди` — {код: що він означає},
    коли їх у задачі більше за «not_json_object»; `бачила` False — повтор іде іншим промптом, ніж перша відповідь
    (оцінка/турнір): модель попередньої відповіді не бачила."""
    опис = ("why your previous answer to %s could not be used" % до_чого if бачила
            else "why this request is sent again")
    if коди:
        опис += ": " + "; ".join("%s — %s" % пара for пара in коди.items())
    return _ЗП.Поле("format_error", опис, як=як)
