# -*- coding: utf-8 -*-
"""приміряння.py — промпт картинки «вона в цьому образі» на збирачі, англійською (П-1).

ЩО БУЛО. Промпт приміряння складав JS показу (`примірка_за_фото`, `примірка_за_описом`,
`ПРИМІРКА_СПІЛЬНЕ(_МАКІЯЖ)`, `перелік_речей_П`, `рядокМакіяжуП`, `ПРИМІРКА_ОДИН_КАДР`) — поза
збирачем і поза Python (розбір 5/8, #349). Тепер JS лише збирає зображення (її фото на повний
зріст, фото речей крамниць адресами, фото її речей байтами) і кличе міст `приміряння`: той
віддає текст із ОГОЛОШЕННЯ задачі (`збирач_промптів`, відповідь — картинка), англійською
(CLAUDE.md п.12), без фраз-прикладів.

ЩО ЗБЕРЕЖЕНО — КОЖНЕ ПРАВИЛО З ТІЄЇ САМОЇ ПРИЧИНИ, ЩО ДОТИ (показ.html, коментарі над
старими константами):
  · «змінити лише одяг, решта точно як на фото 1» — переліком того, що лишається, а не
    забороною: промпт, що вимагав «денне світло, нейтральне тло», перемальовував людину;
  · макіяж, коли вона його обрала, — ДРУГИЙ стан тієї самої команди (рядок 128 дошки):
    дописати помаду до «обличчя точно як на фото 1» дало б дві вимоги, з яких одна програє;
    «невідомо» не шле нічого (K-IO-02) — коду нема чого назвати;
  · «з фото речі бери лише названу річ» — фото крамниць зняті на моделях у повних образах;
  · річ без фото — словами, з усім, що код про неї знає (Т-11, Т-15): доти модель картинки
    не бачила її жодним входом, а підпис під кадром її називав; ОДИН перелік на промпт і на
    підпис (показ шле сюди ті самі речі, з яких пише `к.примірка.без_фото`);
  · її власна річ — «саме ця» (рядок 152);
  · один кадр у пропорціях фото 1 (рядок 125: триптих); повтор — той самий промпт із полем
    «previous_picture», а не другий абзац поверх першого.
Прозу опису образу сюди не шлють (як доти в режимі «за фото»): вона писалась для жінки й
конкурує з речами; речі рук 3–4 тепер мають назву й деталі з переліку кодами (П-1).
"""
import json as _json

import збирач_промптів as _ЗП
import внутрішня_мова as _ВМ
import річ_з_фото as _РФ

ЗОВНІШНІ_ВХОДИ = {
    "з_фото": "вхід із показу (`приміряти`): речі, чиї фото йдуть у виклик, у порядку зображень "
              "після її фото: {слот, назва, власна}",
    "без_фото": "вхід із показу: речі образу без фото в запиті — {слот, назва, колір, hex, крій, "
                "довжина_рівень, матеріал, деталі, власна}; ті самі, що в підписі кадру",
    "макіяж": "вхід із показу: макіяж паспорта {рівень, губи}, коли вона його обрала",
    "як_носити": "вхід із показу: «Як це носити» картки",
    "повтор": "вхід із показу: попередня картинка вийшла ширша за фото 1 (кілька кадрів поруч)",
}


def _довжина(рівень):
    """Рівень довжини картки («литка») → код внутрішньої мови або None."""
    import пакет_моделі as _ПМ
    return _ВМ.код("length", _ПМ.ДОВЖИНА_СЛОВОМ.get(рівень)) if рівень else None


def опис_речі(р):
    """Річ картки → повний опис кодами для промпта: усе, що код про неї знає, і нічого понад."""
    о = {"slot": _ВМ.код("slot", р.get("слот")) or р.get("слот") or _ВМ.UNKNOWN,
         "name": р.get("назва") or _ВМ.UNKNOWN}
    if р.get("колір"):
        о["color"] = _ВМ.код("color_name", р["колір"]) or р["колір"]
    if р.get("hex"):
        о["color_hex"] = р["hex"]
    for ключ, v in (("cut", р.get("крій") if р.get("крій") in _РФ.КРОЇ else None),
                    ("length", _довжина(р.get("довжина_рівень"))),
                    ("fabric", _РФ.код_поля("fabric", р.get("матеріал"))),
                    ("details", р.get("деталі"))):
        if v:
            о[ключ] = v
    if р.get("власна"):
        о["hers"] = True
    return о


# ЧОМУ ЦІ РЯДКИ — у шапці модуля. «лише_вхід» — не додавати речей, яких в образі нема.
_ЛИШАЄТЬСЯ = ("Change only the clothes on photo 1: her face, body, pose, hands, hair, light, background, "
              "framing and angle stay exactly as on photo 1 — it is the same photo.")
_ЛИШАЄТЬСЯ_З_МАКІЯЖЕМ = ("Change the clothes and the makeup on photo 1: her facial features, face shape, "
                         "expression and angle stay exactly as on photo 1 — it is the same person — and so "
                         "do her body, pose, hands, hair, light, background and framing.")
ПРИМІРЯННЯ = _ЗП.Оголошення(
    задача="приміряння",
    роль="Photo 1 is a woman. Dress her in the outfit below.",
    вхід=(
        _ЗП.Поле("item_photos", "the items on the attached photos after photo 1, with their photo numbers",
                 як="take from each photo only the item named for it: the photo may show a whole outfit on "
                    "a model; draw its color, cut, length and texture as on the photo"),
        _ЗП.Поле("items_without_photo", "the outfit items that have no photo, with all that is known about them",
                 як="she wears them too: draw them from this description"),
        _ЗП.Поле("makeup", "the makeup she chose for this outfit: level and lip color",
                 як="paint exactly this makeup on her face"),
        _ЗП.Поле("how_to_wear", "how the items are worn", як="follow it"),
        _ЗП.Поле("previous_picture", "what was wrong with the previous picture", як="draw it again"),
        # рядок 152: її власна річ — «саме ця»; рядок іде лише тоді, коли така річ у списку є
        _ЗП.Поле("item_photos[].hers", "her own item", як="draw exactly this one"),
        _ЗП.Поле("items_without_photo[].hers", "her own item", як="draw exactly this one"),
    ),
    правила=(
        _ЛИШАЄТЬСЯ,
        "One image with one frame: the same single woman filling the frame, in the proportions of photo 1.",
    ),
    вихід="TRY_ON_IMAGE",
    межі=("лише_вхід",),
    мова_промпту="en",
    відповідь_як="картинка",
)
# Рівні, які показ малює плиткою (`МАКІЯЖ`): «невідомо» й «хай обере стилістка» — не рівень.
_РІВНІ = tuple(_ВМ.ТАБЛИЦЯ["makeup_level"].values())


def промпт(з_фото=(), без_фото=(), макіяж=None, як_носити=(), повтор=False):
    """Промпт приміряння рядком JSON. `з_фото` — у порядку зображень після її фото (№ 2…)."""
    import dataclasses as _dc
    мк = None
    if isinstance(макіяж, dict) and макіяж.get("рівень") in _РІВНІ:
        мк = {"level": _ВМ.код("makeup_level", макіяж["рівень"])}
        губи = str(макіяж.get("губи") or "").strip().lower()
        if макіяж["рівень"] != "нюд" and len(губи) == 7 and губи.startswith("#"):
            мк["lips_hex"] = губи
    дані = dict(item_photos=[dict({"photo": н}, **опис_речі(р)) for н, р in enumerate(з_фото or (), 2)],
                items_without_photo=[опис_речі(р) for р in (без_фото or ())],
                makeup=мк, how_to_wear=[str(х) for х in (як_носити or ()) if str(х or "").strip()],
                previous_picture=("wider than photo 1: several frames side by side" if повтор else None))
    о = ПРИМІРЯННЯ if not мк else _dc.replace(
        ПРИМІРЯННЯ, правила=(_ЛИШАЄТЬСЯ_З_МАКІЯЖЕМ,) + ПРИМІРЯННЯ.правила[1:])
    return _json.dumps(_ЗП.зібрати(о, дані), ensure_ascii=False)


def приміряння(вхід):
    """Ендпойнт мосту: {з_фото, без_фото, макіяж?, як_носити?, повтор?} → {промпт}."""
    d = _json.loads(вхід) if isinstance(вхід, str) else (вхід or {})
    return _json.dumps(dict(промпт=промпт(d.get("з_фото"), d.get("без_фото"), d.get("макіяж"),
                                          d.get("як_носити"), bool(d.get("повтор")))), ensure_ascii=False)
