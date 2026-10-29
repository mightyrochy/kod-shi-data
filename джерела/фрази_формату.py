# -*- coding: utf-8 -*-
"""фрази_формату.py — нижній шар реєстру форми відповіді: УСІ слова про те, якою відповідь має бути.

Вимога до форми відповіді (один JSON-обʼєкт, без пояснень, де кінець, як повторити) існує в одному місці — тут;
`схема_відповіді.фраза_формату` складає з цих фраз рядок промпту за схемою, а промпти й повтори беруть решту звідси.
Модуль без імпортів: його читають і `протокол` (нижче за `схема_відповіді` в графі), і збирач, і мовний шар.
Прилад `прилади/промпти_одне_джерело.py` лічить фрази формату поза `схема_відповіді` й цим модулем (ПІСЛЯ — 0)."""

ФОРМА_JSON = "Відповідь — лише один JSON-обʼєкт за «схема_відповіді», без пояснень і без ```."
ОДИН_ОБЄКТ_ЗА_СХЕМОЮ_EN = "one JSON object following \"answer_schema\""  # корінь усіх англійських фраз формату нижче
ФОРМА_JSON_EN = "The answer is %s, without explanations and without ```." % ОДИН_ОБЄКТ_ЗА_СХЕМОЮ_EN
ФОРМИ_EN = {
    "текст": "The answer is plain text laid out as the rules say, not JSON.",
    "картинка": "The answer is one image and no text.",
}

# Український промпт (перекладачка, репліка): те саме правило однією фразою замість трьох переписів.
ВІДПОВІДЬ_ОДИН_ОБЄКТ_UK = ("Відповідь — рівно ОДИН JSON-об'єкт і нічого після нього: другої, виправленої версії, "
                           "приміток і пояснень не пиши — помилку виправ у тому самому об'єкті.")
ВІДПОВІДЬ_UK = "Відповідь — JSON-об'єкт"  # + продовження задачі: «{key: текст}: …», «з одним ключем text — …»
ВІДПОВІДЬ_ЛИШЕ_UK = "Відповідь — лише JSON-об'єкт"
ВІДПОВІДЬ_ТІЛЬКИ_ЦЕЙ_UK = "Відповідь — тільки цей JSON-об'єкт"


def кінець_відповіді_en(після=None):
    """Правило кінця відповіді промпту, що несе схему ключами «task»: початок і кінець — місцем, а не переліком
    ключів, яких не писати (ехо ключів, 17 з 28 відповідей ремонту). `після` — ключ, після якого дужка закриває."""
    return ("Write the answer object itself: it begins with {\"version\" and ends with the brace that closes it"
            + (", right after «%s»" % після if після else "")
            + ". Do not wrap it in another object; after that brace the answer is over"
            + ("." if після else " — write nothing more."))


def наприкінці_en(після=None):
    """Останній рядок промпту, коли схема відповіді стоїть останньою (`скелет_наприкінці`)."""
    return ("Now write your answer: one object of the form above, from {\"version\" to the brace that closes it"
            + (" right after «%s»" % після if після else "")
            + ", not wrapped in another object. The answer is over at that brace.")


def відповідь_за_схемою_en(початок, лише=None):
    """Останній рядок промпту ходу мовного шару: «<початок>: one JSON object following "answer_schema" in "task"»."""
    return ("%s: %s in \"task\"%s." % (початок, ОДИН_ОБЄКТ_ЗА_СХЕМОЮ_EN, ", only with " + лише if лише else ""))


# Повтор після відмови формату: вказівка моделі, що надсилається ПОЛЕМ `format_error` або `instead` (англійською).
ПОВТОР_JSON_EN = "answer again: one JSON object, every string a valid JSON string"
ПОВТОР_ЛИШЕ_JSON_EN = "Return ONLY %s, without explanations and without ```." % ОДИН_ОБЄКТ_ЗА_СХЕМОЮ_EN
ТОЙ_САМИЙ_ОБЄКТ_EN = "return the same JSON object"  # кінець повтору, що просить переписати відповідь


def повтор_за_схемою_en(рівно):
    """`як` поля `format_error` повтору: той самий вибір, але рівно <що>."""
    return "answer again: %s with exactly %s" % (ОДИН_ОБЄКТ_ЗА_СХЕМОЮ_EN, рівно)


def повтор_назвою_схеми_en(назва=None):
    """Вказівка `натомість` обʼєкта помилки формату: з назвою схеми — коли її знає код, інакше без неї."""
    if назва:
        return "Return ONLY one JSON object following schema «%s», without explanations and without ```." % назва
    return "Return ONLY one JSON object, without explanations and without ```."
