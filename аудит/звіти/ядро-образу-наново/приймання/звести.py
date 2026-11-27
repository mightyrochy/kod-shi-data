"""Зводить секунди, виклики, токени й речення про невідоме з тек проходу Н6."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re


РЕЧЕННЯ = re.compile(r"[^.!?…\n]+(?:[.!?…]+|$)", re.MULTILINE)
НЕВІДОМЕ = re.compile(
    r"\b(?:не\s+(?:знаю|бачу|стверджую|впевнена|можу\s+(?:визначити|сказати|оцінити|перевірити|підтвердити))"
    r"|бракує\s+(?:даних|відомостей)|невідомо|cannot\s+(?:tell|verify|confirm)|do not know)\b", re.I
)
ПОЛЯ = (
    ("підошва", r"підошв\w*|зчеплен\w*|sole|tread|grip", ("sole", "tread")),
    ("водостійкість", r"водостійк\w*|водонепроникн\w*|waterproof", ("waterproof",)),
    ("каблук", r"підбор\w*|каблук\w*|heel", ("heel",)),
    ("посадка", r"посадк\w*|fit", ("fit",)),
    ("крій", r"кро[йюї]\w*|крій|cut", ("cut",)),
    ("довжина", r"довжин\w*|поділ\w*|length|hem", ("length",)),
    ("блиск", r"блиск\w*|shine|gloss", ("shine", "gloss")),
    ("розмір", r"розмір\w*|size", ("size",)),
    ("ширина", r"ширин\w*|width", ("width",)),
    ("підкладка", r"підклад\w*|lining", ("lining",)),
    ("ошатність", r"ошатн\w*|formality", ("formality",)),
    ("матеріал", r"матеріал\w*|тканин\w*|fabric|material", ("fabric", "material")),
    ("колір", r"кол[іь]ор\w*|колір|відтін\w*|colour|color", ("color", "colour")),
    ("портрет", r"портрет\w*|обличч\w*|portrait", ("портрет", "profile")),
    ("дорога", r"дорог\w*|скільки\s+йтим\w*|пішки|walk", ("walk_min", "movement")),
    ("погода", r"погод\w*|опад\w*|weather|precipitation", ("weather", "precipitation")),
)
БРАКУЄ = (None, "", "unknown", "невідомо", "не_певний", [], {})


def прочитати(файл):
    """Читає один збережений документ JSON."""
    return json.loads(файл.read_text(encoding="utf-8"))


def рядки(файл):
    """Читає JSONL, зберігаючи порядок запису."""
    return [json.loads(р) for р in файл.read_text(encoding="utf-8").splitlines() if р.strip()]


def токени(обміни):
    """Рахує токени, які повернув рушій; клітинка без лічильника має None."""
    вхід, вихід = [], []
    for запис in обміни:
        відповідь = запис["відповідь"]
        try:
            usage = json.loads(відповідь).get("usage") or {}
        except (json.JSONDecodeError, AttributeError):
            continue
        if type(usage.get("input_tokens")) is int:
            вхід.append(usage["input_tokens"] + sum(usage.get(к) or 0 for к in (
                "cache_read_input_tokens", "cache_creation_input_tokens")))
        elif type(usage.get("prompt_tokens")) is int:
            вхід.append(usage["prompt_tokens"])
        if type(usage.get("output_tokens")) is int:
            вихід.append(usage["output_tokens"])
        elif type(usage.get("completion_tokens")) is int:
            вихід.append(usage["completion_tokens"])
    return dict(вхід=sum(вхід) if вхід else None, вихід=sum(вихід) if вихід else None,
                без_входу=len(обміни) - len(вхід), без_виходу=len(обміни) - len(вихід))


def ключі(об):
    """Збирає однойменні поля структурованого входу з їхніми значеннями."""
    if isinstance(об, dict):
        for ключ, значення in об.items():
            yield ключ, значення
            yield from ключі(значення)
    if isinstance(об, list):
        for значення in об:
            yield from ключі(значення)


def розклад(руки):
    """Рахує тексти кожного показаного складу й дає цитату для звірки входу."""
    описи = set()
    скільки, порожніх = 0, 0
    невідомі = []
    for крок in руки:
        if крок.get("режим") != "образи":
            continue
        for картка in крок["картки"]:
            текст = (картка.get("опис") or "").strip()
            речі = картка.get("речі") or []
            ід = (крок["прогін"], картка["рука"], tuple(р.get("id") for р in речі), текст)
            if ід in описи:
                continue
            описи.add(ід)
            if not текст or re.search(r"пояснення\s+не\s+(?:вийшло|завантажилось)", текст, re.I):
                порожніх += 1
                continue
            опори = [р.get("опора_опису") or {} for р in речі]
            for речення in (з.strip() for з in РЕЧЕННЯ.findall(текст) if з.strip()):
                скільки += 1
                if not НЕВІДОМЕ.search(речення):
                    continue
                свідки = []
                for поле, вираз, назви in ПОЛЯ:
                    if not re.search(rf"\b(?:{вираз})\b", речення, re.I):
                        continue
                    значення = [в for к, в in ключі(опори) if к in назви]
                    свідки.append({"поле": поле, "значення_в_опорі": значення,
                                   "знаних": sum(в not in БРАКУЄ for в in значення)})
                невідомі.append(dict(рука=картка["рука"], прогін=крок["прогін"],
                                     речення=речення, поля=свідки, знімок=крок["знімок"]))
    поля = Counter(поле["поле"] for з in невідомі for поле in (з["поля"] or [{"поле": "потрібна звірка"}]))
    return dict(речень=скільки, невідомих=len(невідомі), порожніх=порожніх,
                частка=len(невідомі) / скільки if скільки else None, за_полем=dict(поля), цитати=невідомі)


def звести(тека):
    """Рахує кожен каталог проходу й групує старий і новий записи тієї самої ситуації."""
    звіт = []
    for файл in sorted(тека.glob("*/*/*/числа.json")):
        план = прочитати(файл)
        if файл.parent.name != план["ситуація"]:
            continue
        папка = файл.parent
        обміни = рядки(папка / "обміни.jsonl")
        руки = рядки(папка / "руки.jsonl")
        звіт.append(dict(план, токени=токени(обміни), описи=розклад(руки) if план["шлях"] == "ядро" else None,
                         тека=str(папка.relative_to(тека))))
    return звіт


def main():
    """Пише числа й цитати поряд із записом для судді."""
    п = argparse.ArgumentParser(description=__doc__)
    п.add_argument("тека", type=Path)
    а = п.parse_args()
    звіт = звести(а.тека)
    if not звіт:
        п.error("у теці немає проходів із числами")
    (а.тека / "зведення.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("| Ситуація | Шлях | Прохід | До карток, с | До кінця, с | Викликів | Токени вхід / вихід | «Не знаю» / речень |")
    print("|---|---|---:|---:|---:|---:|---:|---:|")
    для_показу = lambda в: "—" if в is None else str(round(в, 2))
    for з in звіт:
        т, о = з["токени"], з["описи"]
        print(f"| {з['ситуація']} | {з['шлях']} | {з['прохід']} | {для_показу(з.get('до_карток_с'))} | "
              f"{для_показу(з.get('до_кінця_с'))} | {з['викликів']} | "
              f"{для_показу(т['вхід'])} / {для_показу(т['вихід'])} | "
              f"{str(о['невідомих']) + ' / ' + str(о['речень']) if о else '—'} |")


if __name__ == "__main__":
    main()
