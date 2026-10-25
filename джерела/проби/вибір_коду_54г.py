# -*- coding: utf-8 -*-
# 5.4-Г ВИБІР КОДУ: крок над ЗБЕРЕЖЕНИМ розбором V5-цитата (без перерозбору). Та сама модель одним викликом на річ для кожного пункту
# «поле=код=цитата» обирає з переліку цього поля (або unknown) код, який стверджує САМА цитата; ширша чи інша цитата за код розбору
# («В'язана шапка» → не `knitwear`, а те, що вона каже) дає інший код чи unknown. Граматика на пункт — enum переліку поля + unknown.
# Результат — копія теки з виправленими кодами (далі звичайні `--зібрати` і суд `еталон_частки.py`). Словника й слів-запасу нема.
#   python3 проби/вибір_коду_54г.py <тека розбору> <НОВА тека> --модель <ід> [--паралельно 2]
import argparse, concurrent.futures, json, os, shutil, sys, time
ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ТУТ))
import каталог_розбір as КР                    # noqa: E402
import каталог_розбір_прогін as П              # noqa: E402

ПРОМПТ = """You choose the right code for coded fields of one online-shop item. The shop text is Ukrainian.
ITEM TEXT (JSON): %s

Each claim below has a field, the code chosen earlier and the quote cited as its proof. For every claim answer with the
code from the field's list that the QUOTE ITSELF states. Keep the earlier code when the quote states exactly that. When the
quote states something broader, narrower or different, answer the code it really states; when no code of the list is stated
by the quote, answer "unknown". Do not use the rest of the text to add facts the quote does not say.
A code is stated only when a word of the quote names it or is its direct synonym: a model number, an article, a colour word
for a non-colour field, a width or a name of a collection state nothing; a word that suggests a code without naming it
(a general "shorter" for a length code, "yellow" for a gold metal) is also not enough for the specific code: take the broader
code of the list that the quote really names, or "unknown".
CLAIMS:
%s
Return JSON {"p1":<code>, ...} with one answer for every claim."""

ПЕРЕЛІК = {КР._ключ_коду(ш): к for ш, к, _ in КР._листки() if not isinstance(к, КР.Мірка)}


def пункти(рядок):
    вих = []
    for сирий in рядок.split(";"):
        ч = сирий.split("=", 2)
        вих.append((ч[0], ч[1] if len(ч) > 1 else "", ч[2] if len(ч) > 2 else "", сирий))
    return вих


def схема(поля):
    return {"type": "object", "additionalProperties": False,
            "required": ["p%d" % (i + 1) for i in range(len(поля))],
            "properties": {"p%d" % (i + 1): {"enum": [к for к in ПЕРЕЛІК[п] if к != КР.НЕ_СТОСУЄТЬСЯ] + ([КР.UNKNOWN] if КР.UNKNOWN not in ПЕРЕЛІК[п] else [])}
                           for i, п in enumerate(поля)}}


def одна(файл, звідки, куди, модель, годинник):
    текст = open(os.path.join(звідки, файл), encoding="utf-8").read()
    дані, відп = П.розділити(текст)
    try:
        об = json.loads(відп)
        усі = пункти(об["codes"])
    except (ValueError, KeyError):
        shutil.copy(os.path.join(звідки, файл), os.path.join(куди, файл))
        return файл, 0, 0.0
    суд = [(і, п) for і, п in enumerate(усі) if п[2] and п[0] in ПЕРЕЛІК]
    if not суд:
        shutil.copy(os.path.join(звідки, файл), os.path.join(куди, файл))
        return файл, 0, 0.0
    рядки = "\n".join("p%d: field=%s (%s); earlier code=%s; quote=%s; list=%s" % (
        к, п[0], (КР.ОПИСИ.get(п[0]) or "")[:120], п[1], json.dumps(п[2], ensure_ascii=False),
        "|".join(x for x in ПЕРЕЛІК[п[0]] if x != КР.НЕ_СТОСУЄТЬСЯ))
        for к, (і, п) in enumerate(суд, 1))
    тіло = dict(model=модель, stream=False, max_tokens=500, temperature=0,
                messages=[dict(role="user", content=ПРОМПТ % (json.dumps(дані, ensure_ascii=False)[:9000], рядки))],
                response_format={"type": "json_schema", "json_schema": {
                    "name": "code_choice", "strict": True, "schema": схема([п[0] for _, (_, п) in enumerate(суд, 1)])}})
    відповідь, сек = П.надіслати(тіло, годинник, стадія="вибір")
    в = json.loads(відповідь)
    зміни, нові = [], list(п[3] for п in усі)
    for к, (і, п) in enumerate(суд, 1):
        код = в.get("p%d" % к)
        if код == п[1]:
            continue
        зміни.append((п[0], п[1], код, п[2]))
        нові[і] = None if код == КР.UNKNOWN else "%s=%s=%s" % (п[0], код, п[2])
    лишилось = [x for x in нові if x]
    if нові[0] is None or not лишилось or not лишилось[0].startswith("item_type"):
        лишилось = ["item_type=unknown"] + [x for x in лишилось if not x.startswith("item_type")]
    об["codes"] = ";".join(лишилось)
    нове = текст[:текст.rfind("── ВІДПОВІДЬ")] + "── ВІДПОВІДЬ\n" + json.dumps(об, ensure_ascii=False, indent=2) + "\n"
    open(os.path.join(куди, файл), "w", encoding="utf-8").write(нове)
    open(os.path.join(куди, файл + ".вибір.json"), "w", encoding="utf-8").write(json.dumps(
        dict(пунктів=len(суд), зміни=зміни, секунд=сек), ensure_ascii=False))
    return файл, len(зміни), сек


def main():
    р = argparse.ArgumentParser()
    р.add_argument("звідки"); р.add_argument("куди")
    р.add_argument("--модель", required=True); р.add_argument("--паралельно", type=int, default=2)
    а = р.parse_args()
    os.makedirs(а.куди, exist_ok=True)
    for ф in os.listdir(а.звідки):
        if not ф.endswith(".txt"):
            shutil.copy(os.path.join(а.звідки, ф), os.path.join(а.куди, ф))
    файли = sorted(ф for ф in os.listdir(а.звідки) if ф.endswith(".txt"))
    годинник = П.Годинник(а.паралельно)
    т0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(а.паралельно) as пул:
        рез = list(пул.map(lambda ф: одна(ф, а.звідки, а.куди, а.модель, годинник), файли))
    стіна = time.time() - т0
    print("вибір коду: речей %d · викликів %d · змін %d · стіною %.1f с (%.1f с/річ) · %s" % (
        len(файли), sum(1 for _, _, с in рез if с), sum(к for _, к, _ in рез), стіна, стіна / max(1, len(файли)),
        json.dumps(годинник.зведення()["дія"], ensure_ascii=False)[:220]))


if __name__ == "__main__":
    main()
