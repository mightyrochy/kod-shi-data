# -*- coding: utf-8 -*-
"""міст_стилістка.py — ендпойнт `стилістка`: відповідь на ЇЇ ПИТАННЯ ПРО ОБРАЗ (М-1, 8/8).

ЩО БУЛО. З мовним шаром (а він увімкнений типово — модель шару = модель продукту) питання
жінки з розмови йшло `помічникП` — моделі-довідці про застосунок: без фото, без її речей,
без вердикту коду й сценарію. На «чи підійде ця спідниця?» вона чесно відповідала «я не
бачу фото» (розбір 8/8, PR #345). ЩО ТЕПЕР. Перекладач називає, про що питання
(`question_about`: app | look); про застосунок — довідці, як доти; про образ — сюди:
функціональна модель зі збирача промптів бачить питання, її речі з фото (слова моделі з
зором і вердикт коду, `річ_з_фото.для_моделі`), рядок випадку і самі фото її речей
(показ чіпляє їх блоками в межах стелі моста). Відповідь — вільний текст у полі `answer`;
до жінки її доносить перекладач репліки (`мовний_шар`, поле `answer`).

ДВА КРОКИ, ЯК `мова`: {питання, речі?, випадок?, фото_речей?} → {промпт};
{відповідь_моделі} → {відповідь, причина}. Python між кроками стану не тримає."""
import json as _json

import протокол as _ПР
import збирач_промптів as _ЗП
import річ_з_фото as _РФ

ЗОВНІШНІ_ВХОДИ = {
    "питання": "вхід із показу (`стилісткаП`): її питання про образ — вільний текст від перекладача "
               "(`question.free_text`)",
    "речі": "вхід із показу: її речі з паспорта (`ПАСПОРТ_П.речі_з_фото`) — як їх бачить код",
    "випадок": "вхід із показу: рядок випадку для моделей (`ВИПАДОК_ПАСПОРТА_П`)",
    "фото_речей": "вхід із показу: ід фото, які показ чіпляє до виклику блоками, у тому самому порядку",
    "відповідь_моделі": "вхід із показу: сира відповідь моделі на промпт першого кроку",
}

# ОГОЛОШЕННЯ ЗАДАЧІ — англійською (CLAUDE.md п.12: промпти функціональної моделі — англійською,
# на збирачі). Відповідь для неї пише ця модель, а природною мовою її доносить перекладач репліки.
ПИТАННЯ = _ЗП.Оголошення(
    задача="питання_образу",
    роль="You are the stylist of the Lyusterko styling app. She has asked you a question about her "
         "look; you answer it.",
    вхід=(
        _ЗП.Поле("question", "her question, in her own words", треба=True),
        _ЗП.Поле("items", "her own items from this conversation, as the code sees them: name, slot, "
                          "colour, formality 1–10; «вердикт_коду» is the code's verdict on the item "
                          "for her palette and this occasion",
                 "do not contradict «вердикт_коду»",
                 без="She has not shown or described any item yet."),
        _ЗП.Поле("photos", "which attached image (in order) shows which item: [{photo, item}]",
                 без="No image is attached: judge only by the item descriptions."),
        _ЗП.Поле("case", "the occasion as the code knows it", без="The occasion is not known yet."),
    ),
    правила=(
        "Answer exactly what she asked about her look: whether the item suits her and this "
        "occasion, and what to wear it with.",
        "Rely on the attached images and the item descriptions.",
        "Name no shops, brands, prices or links: you do not see the catalogue.",
        "Two to four sentences.",
    ),
    вихід="питання_образу",
    скелет={"answer": "<text>"},
    поля_виходу={"answer": "your answer to her question"},
    межі=("лише_вхід", "для_неї", "без_чисел_тіла"),
)


def промпт(питання, речі=None, випадок="", фото_речей=None):
    """Промпт моделі: її питання, її речі (слова коду й вердикт), рядок випадку, які фото
    прикріплено до яких речей. Фото без речі в паспорті не згадується."""
    речі = [р for р in речі or [] if isinstance(р, dict) and р.get("ід")]
    за_фото = {р.get("фото"): р.get("ід") for р in речі if р.get("фото")}
    дані = dict(question=str(питання or "").strip(),
                items=[_РФ.для_моделі(р) for р in речі],
                photos=[dict(photo=ф, item=за_фото[ф]) for ф in фото_речей or [] if ф in за_фото],
                case=str(випадок or "").strip())
    return _json.dumps(_ЗП.зібрати(ПИТАННЯ, дані), ensure_ascii=False)


def прийняти(відповідь):
    """Сира відповідь моделі → dict(відповідь, причина): текст лише з поля `answer`."""
    об, чому_не = _ПР.розбір(str(відповідь or ""))
    т = об.get("answer") if isinstance(об, dict) else None
    if isinstance(т, str) and т.strip():
        return dict(відповідь=т.strip(), причина=None)
    return dict(відповідь="", причина=("нема поля answer" if isinstance(об, dict)
                                        else "відповідь не JSON-об'єкт (%s)" % чому_не))


def стилістка(вхід):
    """Ендпойнт моста `стилістка` (два кроки, див. шапку модуля)."""
    d = _json.loads(вхід) if isinstance(вхід, str) else (вхід or {})
    if d.get("відповідь_моделі") is not None:
        return _json.dumps(прийняти(d["відповідь_моделі"]), ensure_ascii=False)
    if not str(d.get("питання") or "").strip():
        return _json.dumps(dict(помилка="нема питання"), ensure_ascii=False)
    return _json.dumps(dict(промпт=промпт(d["питання"], d.get("речі"), d.get("випадок") or "",
                                          d.get("фото_речей"))), ensure_ascii=False)
