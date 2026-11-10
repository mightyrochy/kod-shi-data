"""Мірило запису перезбору в продуктові файли (корінь Річ-кадр-варіант): читає ЛИШЕ продуктові файли дерева —
`каталог_повний.xml.gz` (чистим читачем фіду, як продукт), `джерела/каталог_власник_кадру.json.gz`,
`джерела/каталог_збагачення.json.gz`, `zhnyvarka/черга_ноутбука_5697.tsv`. Нічого не пише, крім розпакованого каталогу.
Запуск з кореня: python3 аудит/жнива_5_3/2026-11-06_запис/вимір_запису.py"""
import collections, gzip, json, os, sys
КОРІНЬ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(КОРІНЬ, "джерела"))
os.chdir(os.path.join(КОРІНЬ, "джерела"))
import feed, фід_власник_кадру as в

КРАМНИЦІ = ("attico.ua", "feelyou.com.ua", "likeangel.com.ua", "maxa.ua", "morandi.ua", "sunwin-store.com",
            "honchstudio.com", "jecomestudio.com", "nyni.shop", "wearme.ua")


def main():
    оф = feed.читати_yml(feed.каталог_на_диску())[0]
    зб = feed.читати_збагачення()
    with gzip.open(os.path.join(КОРІНЬ, "джерела", в.ВЛАСНИК_ІМ + ".gz"), "rt", encoding="utf-8") as f:
        факти = json.load(f)["записи"]
    поля = collections.Counter(len(ф) for ф in факти.values())
    відомих = sum(1 for ф in факти.values() if len(ф) > 6 and ф[6] != "невідомо")
    print("факти: записів %d, полів %s, з відомим варіантом %d" % (len(факти), dict(sorted(поля.items())), відомих))
    л = collections.defaultdict(collections.Counter)
    for о in оф:
        м = о.get("магазин") if о.get("магазин") in КРАМНИЦІ else "решта"
        с = л[м]
        с["записів"] += 1
        с["кадрів"] += len(о.get("фото") or ())
        с["з_параметром"] += "власник_кадру" in (о.get("параметри") or {})
        с["кадрів_з_доказом"] += sum(в.доказ_варіанта(о, к) is not None for к in о.get("фото") or ())
        р = в.запис(о, зб.get(о["id"]), факти=факти)
        if not р:
            continue
        с["вимірів"] += 1
        с["вимірів_з_варіантом"] += р["варіант"] != "невідомо"
        с["своїх_з_варіантом"] += р["варіант"] != "невідомо" and р["стан"] == "свій"
    for м in КРАМНИЦІ + ("решта",):
        print("%-18s %s" % (м, json.dumps(dict(sorted(л[м].items())), ensure_ascii=False)))
    разом = sum(л.values(), collections.Counter())
    print("разом %s" % json.dumps(dict(sorted(разом.items())), ensure_ascii=False))
    черга = open(os.path.join(КОРІНЬ, "zhnyvarka", "черга_ноутбука_5697.tsv"), encoding="utf-8").read().splitlines()[1:]
    print("черга ноутбука: %d · %s" % (len(черга), dict(sorted(collections.Counter(р.split("\t")[1] for р in черга).items()))))


if __name__ == "__main__":
    main()
