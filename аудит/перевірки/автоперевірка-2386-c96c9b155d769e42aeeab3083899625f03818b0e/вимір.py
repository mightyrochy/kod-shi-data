"""Звіряє таблицю обходу та відтворює перенесення неповної картки без запису каталогу."""
import collections
import csv
import json
from pathlib import Path
import sys
import tempfile


def main():
    """Читає призначене дерево PR й друкує факти зі збережених артефактів і контрольного запису."""
    корінь = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(корінь / "zhnyvarka"))
    import жнива_каталог as ж
    import складальник as с
    реєстр = csv.DictReader((р for р in (корінь / "zhnyvarka/магазини.tsv").read_text(encoding="utf-8").splitlines()
                            if not р.startswith("#")), delimiter="\t")
    увімкнені = {р["домен"] for р in реєстр if р["стан"] == "увімкнено"}
    with (корінь / "аудит/жнива_5_3/повний-обхід_стан.tsv").open(encoding="utf-8") as потік:
        стани = list(csv.DictReader(потік, delimiter="\t"))
    вибрані = [р for р in стани if р["домен"] in увімкнені]
    print("увімкнених:", len(увімкнені), "станів:", len(вибрані), "пропущено:", sorted(увімкнені - {р["домен"] for р in стани}))
    print("адрес:", sum(int(р["адрес"]) for р in вибрані), "готово:", sum(int(р["готово"]) for р in вибрані))
    print("стани:", dict(collections.Counter(р["стан_код"] for р in вибрані)))
    print("причини:", dict(collections.Counter(р["причина_код"] for р in вибрані)))
    print("без залишку:", sum(int(р["лишилось"]) == 0 for р in вибрані))
    for рядок in стани:
        if рядок["домен"] == "theoriginals.com.ua":
            print("theoriginals:", рядок)
    шапка, записи = с.читати_записи()
    старий = dict(записи[0], ід="збережений-ід", адреса="https://store.test/ua/p1", опис="Збережений опис",
                 параметри=[["Склад", "100% льон", "к"], ["Колір", "синій", "к"], ["стать", "жіноча", "к"]])
    свіжий = dict(url="https://store.test/ru/p1", назва="Українська назва", фото=["https://store.test/photo.jpg"], ціна=100, склад=None)
    with tempfile.TemporaryDirectory() as тека:
        файл = Path(тека) / "сирі/store.test.jsonl"
        файл.parent.mkdir()
        файл.write_text(json.dumps(dict(url=свіжий["url"], стан="картка", дата="2026-10-30", записи=[свіжий]), ensure_ascii=False) + "\n", encoding="utf-8")
        _, результат, лічби = ж.зібрати(тека, шапка, [старий])
        print("свіжа /ru/ картка:", "вхід", старий["адреса"], "вихід", результат[0]["адреса"], "ід", результат[0]["ід"], "лічби", dict(лічби))
        print("параметри ДО:", старий["параметри"])
        print("параметри ПІСЛЯ:", результат[0]["параметри"])
        print("опис ДО:", старий["опис"], "ПІСЛЯ:", результат[0]["опис"])
    print("дані каталогу:", len(записи), "theoriginals:", sum("theoriginals.com.ua" in р["адреса"] for р in записи))


if __name__ == "__main__":
    main()
