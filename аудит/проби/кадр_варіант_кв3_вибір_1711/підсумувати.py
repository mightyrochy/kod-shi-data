"""Порівняння повних повторів і дві відтворювані вибірки для незалежної перевірки."""
import argparse
import collections
import csv
import gzip
import hashlib
import json
from pathlib import Path
import random
from urllib.parse import urlsplit

ТЕКА = Path(__file__).resolve().parent
ЗЕРНО = 20261117
КРАМНИЦІ = {"25union.com.ua", "emmeliedelage.com", "fromus.ua", "giardini-shoes.com", "maryline.ua",
            "ricamare.com.ua", "rito.ua", "sezone.ua", "vilni.store", "welfare.ua", "yulashop.com.ua"}


def читати(шлях):
    """Читає повний архів результатів за ідентифікатором запису."""
    with gzip.open(шлях, "rt", encoding="utf-8") as потік:
        рядки = [json.loads(р) for р in потік]
    вихід = {р["ід"]: р for р in рядки}
    assert len(вихід) == len(рядки) == 13882
    return вихід


def таблиця(шлях, поля, рядки):
    """Зберігає TSV з точними адресами та незаповненими вердиктами."""
    with шлях.open("w", encoding="utf-8", newline="") as потік:
        писач = csv.DictWriter(потік, поля, delimiter="\t", lineterminator="\n")
        писач.writeheader()
        писач.writerows(рядки)


def вибірка(групи, мінімум, загалом):
    """Зерном бере мінімум з кожної крамниці, решту — з об'єднаного залишку."""
    генератор = random.Random(ЗЕРНО)
    взято, решта = [], []
    for д, група in sorted(групи.items()):
        група = sorted(група, key=lambda р: р["ід"])
        assert len(група) >= мінімум, (д, len(група))
        генератор.shuffle(група)
        взято.extend(група[:мінімум])
        решта.extend(група[мінімум:])
    генератор.shuffle(решта)
    взято.extend(решта[:загалом - len(взято)])
    assert len(взято) == загалом
    return sorted(взято, key=lambda р: (urlsplit(р["адреса"]).netloc, р["ід"]))


def зберегти_вибірку(шлях, рядки, сховище):
    """Зберігає походження HTML, усі кадри та окремі питання перевірці."""
    вихід = []
    for н, р in enumerate(рядки, 1):
        файл = сховище / "відповіді" / (р["ід"] + ".json.gz")
        вихід.append(dict(номер=н, зерно=ЗЕРНО, крамниця=urlsplit(р["адреса"]).netloc,
                          ід=р["ід"], адреса=р["адреса"], HTML="відповіді/" + файл.name,
                          HTML_gzip_sha256=hashlib.sha256(файл.read_bytes()).hexdigest(),
                          фото=json.dumps(р.get("запис", {}).get("фото", []), ensure_ascii=False),
                          власник=р.get("запис", {}).get("параметри", {}).get("власник_кадру", ""),
                          один_колір="не перевірено", кадри_цієї_речі="не перевірено", кадр_цього_варіанта="не перевірено"))
    таблиця(шлях, list(вихід[0]), вихід)


def main():
    """Звіряє незмінність вибірки та пише числа, переходи й матеріали перевірці."""
    п = argparse.ArgumentParser(description=__doc__)
    п.add_argument("--до", type=Path, required=True)
    п.add_argument("--після", type=Path, required=True)
    п.add_argument("--сховище", type=Path, required=True)
    п.add_argument("--вихід", type=Path, default=ТЕКА)
    а = п.parse_args()
    а.вихід.mkdir(parents=True, exist_ok=True)
    до, після = читати(а.до), читати(а.після)
    assert до.keys() == після.keys() and all(р["адреса"] == після[і]["адреса"] for і, р in до.items())
    звіт = {"записів": len(до), "зерно": ЗЕРНО}
    for ім, дані in (("до", до), ("після", після)):
        звіт[ім] = dict(стани=dict(collections.Counter(р["стан"] for р in дані.values())),
                       первинні=dict(collections.Counter(р.get("причина") for р in дані.values() if р["стан"] == "невідомо")),
                       усі_причини=dict(collections.Counter(п for р in дані.values() for п in р.get("причини", []))))
    втрачені = [і for і, р in до.items() if р["стан"] == "доведено" and після[і]["стан"] != "доведено"]
    змінені_кадри = [і for і, р in до.items() if р["стан"] == "доведено" and р["запис"]["фото"] != після[і]["запис"]["фото"]]
    звіт.update(втрачено=втрачені, змінені_доведені_галереї=змінені_кадри)
    assert not втрачені and not змінені_кадри, звіт
    переходи = collections.defaultdict(collections.Counter)
    частина1, частина2 = collections.defaultdict(list), collections.defaultdict(list)
    свотчі_кв2 = collections.Counter()
    for і, р in до.items():
        д = urlsplit(р["адреса"]).netloc
        н = після[і]
        переходи[д]["до_доведено"] += р["стан"] == "доведено"
        переходи[д]["після_доведено"] += н["стан"] == "доведено"
        if р.get("причина") == "кілька_свотчів":
            свотчі_кв2[д] += 1
        if д in КРАМНИЦІ and р.get("причина") == "нема_свідчення_одного_кольору":
            частина1[д].append(н)
        ф = н.get("факти", {})
        if н["стан"] == "доведено" and р["стан"] != "доведено" and (ф.get("свотчі") or ф.get("кольори_вибору")):
            частина2[д].append(н)
    звіт["кілька_свотчів_кв2_за_крамницями"] = dict(свотчі_кв2)
    звіт["кандидати_частини1"] = {д: len(р) for д, р in sorted(частина1.items())}
    звіт["доведено_відсотків"] = 100 * звіт["після"]["стани"].get("доведено", 0) / len(після)
    таблиця(а.вихід / "крамниці.tsv", ["крамниця", "до_доведено", "після_доведено"],
            [dict(крамниця=д, **л) for д, л in sorted(переходи.items())])
    зберегти_вибірку(а.вихід / "вибірка_без_вибору.tsv", вибірка(частина1, 3, 40), а.сховище)
    зберегти_вибірку(а.вихід / "вибірка_з_вибором.tsv", вибірка(частина2, 0, 40), а.сховище)
    таблиця(а.вихід / "кандидати_один_колір.tsv", ["домен", "записів_без_свідчення", "вибірка", "рішення"],
            [dict(домен=д, записів_без_свідчення=len(р), вибірка="вибірка_без_вибору.tsv", рішення="чекає незалежних очей")
             for д, р in sorted(частина1.items())])
    (а.вихід / "порівняння.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(звіт, ensure_ascii=False))


if __name__ == "__main__":
    main()
