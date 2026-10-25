# -*- coding: utf-8 -*-
# 5.4-Г ОПОРА, пункт 2: КРОК ОПОРИ ПОЛЯ. Та сама модель одним викликом на річ відповідає лише yes/no на кожен пункт
# «поле=код=цитата» розбору V5: чи САМА цитата говорить значення цього поля для цієї речі (граматика yes|no).
# «no» → пункт викидається з відповіді (код стане unknown). Відповіді речей копіюються у НОВУ теку без «no»-пунктів,
# далі звичайні `--зібрати` і суд `проби/еталон_частки.py`. Ні словника, ні запасного шляху словами.
#   python3 проби/крок_опори_54г.py <тека V5> <НОВА тека> --модель <ід> [--паралельно 2]
import argparse, concurrent.futures, json, os, re, shutil, sys, time
ТУТ = os.path.dirname(os.path.abspath(__file__))
ДЖЕРЕЛА = os.path.dirname(ТУТ)
sys.path.insert(0, ДЖЕРЕЛА)
import каталог_розбір as КР                    # noqa: E402
import каталог_розбір_прогін as П              # noqa: E402

ПРОМПТ = """You check the evidence behind coded fields of one online-shop item. The shop text is Ukrainian.
ITEM TEXT (JSON): %s

Below are numbered claims. Each claim has the field, the code chosen for it and the quote cited as proof.
Answer "yes" only when the quote itself states the value of THAT field for THIS item. A quote that names a different
property (a colour for the fabric field, the item name for the cut field, a size for the sleeve field) is "no"; a quote that
only mentions a related word without saying the value is "no". For item_type a quote that names the item is "yes".
CLAIMS:
%s
Return JSON {"p1":"yes"|"no", ...} with one answer for every claim."""


def пункти(кодирядок):
    """«поле=код=цитата;…» → [(поле, код, цитата, сирий пункт)]."""
    вих = []
    for сирий in кодирядок.split(";"):
        ч = сирий.split("=", 2)
        вих.append((ч[0], ч[1] if len(ч) > 1 else "", ч[2] if len(ч) > 2 else "", сирий))
    return вих


def схема(n):
    return {"type": "object", "additionalProperties": False, "required": ["p%d" % i for i in range(1, n + 1)],
            "properties": {"p%d" % i: {"enum": ["yes", "no"]} for i in range(1, n + 1)}}


def одна(файл, звідки, куди, модель, годинник):
    текст = open(os.path.join(звідки, файл), encoding="utf-8").read()
    дані, відп = П.розділити(текст)
    try:
        об = json.loads(відп)
        усі = пункти(об["codes"])
    except (ValueError, KeyError):
        shutil.copy(os.path.join(звідки, файл), os.path.join(куди, файл))
        return файл, 0, 0.0
    # пункти з кодом і цитатою; голий «item_type=unknown» опори не потребує
    суд = [(і, п) for і, п in enumerate(усі) if п[2]]
    if not суд:
        shutil.copy(os.path.join(звідки, файл), os.path.join(куди, файл))
        return файл, 0, 0.0
    рядки = "\n".join("p%d: field=%s (%s); code=%s; quote=%s" % (
        к, п[0], (КР.ОПИСИ.get(п[0].replace("[]", "")) or "")[:140], п[1], json.dumps(п[2], ensure_ascii=False))
        for к, (і, п) in enumerate(суд, 1))
    тіло = dict(model=модель, stream=False, max_tokens=300, temperature=0,
                messages=[dict(role="user", content=ПРОМПТ % (json.dumps(дані, ensure_ascii=False)[:9000], рядки))],
                response_format={"type": "json_schema", "json_schema": {
                    "name": "evidence_check", "strict": True, "schema": схема(len(суд))}})
    відповідь, сек = П.надіслати(тіло, годинник, стадія="опора")
    вердикт = json.loads(відповідь)
    викинути = {і for к, (і, п) in enumerate(суд, 1) if вердикт.get("p%d" % к) == "no"}
    лишилось = [п[3] for і, п in enumerate(усі) if і not in викинути]
    # перший пункт — завжди item_type: якщо його викинуто, замінюємо на голе «item_type=unknown»
    if 0 in викинути:
        лишилось = ["item_type=unknown"] + лишилось
    об["codes"] = ";".join(лишилось)
    нове = текст[:текст.rfind("── ВІДПОВІДЬ")] + "── ВІДПОВІДЬ\n" + json.dumps(об, ensure_ascii=False, indent=2) + "\n"
    open(os.path.join(куди, файл), "w", encoding="utf-8").write(нове)
    журнал = [(усі[і][0], усі[і][1], усі[і][2]) for і in sorted(викинути)]
    open(os.path.join(куди, файл + ".опора.json"), "w", encoding="utf-8").write(json.dumps(
        dict(пунктів=len(суд), викинуто=журнал, секунд=сек), ensure_ascii=False))
    return файл, len(викинути), сек


def main():
    р = argparse.ArgumentParser()
    р.add_argument("звідки"); р.add_argument("куди")
    р.add_argument("--модель", required=True); р.add_argument("--паралельно", type=int, default=2)
    а = р.parse_args()
    os.makedirs(а.куди, exist_ok=True)
    for ф in os.listdir(а.звідки):                      # мірка прогону й решта — як є
        if not ф.endswith(".txt"):
            shutil.copy(os.path.join(а.звідки, ф), os.path.join(а.куди, ф))
    файли = sorted(ф for ф in os.listdir(а.звідки) if ф.endswith(".txt"))
    годинник = П.Годинник(а.паралельно)
    т0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(а.паралельно) as пул:
        рез = list(пул.map(lambda ф: одна(ф, а.звідки, а.куди, а.модель, годинник), файли))
    стіна = time.time() - т0
    print("крок опори: речей %d · викликів %d · пунктів викинуто %d · стіною %.1f с (%.1f с/річ) · токени %s" % (
        len(файли), sum(1 for _, _, с in рез if с), sum(к for _, к, _ in рез), стіна, стіна / max(1, len(файли)),
        json.dumps(годинник.зведення()["дія"], ensure_ascii=False)[:200]))


if __name__ == "__main__":
    main()
