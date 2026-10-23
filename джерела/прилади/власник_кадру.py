# -*- coding: utf-8 -*-
"""прилади/власник_кадру.py — ФАКТИ ВЛАСНОСТІ КАДРУ ВИМІРУ з маніфесту кадрів → `каталог_власник_кадру.json.gz`
поруч із `feed.py` (наряд 5.2).

Маніфест (`каталог_маніфест_кадрів.json.gz` у корені, 80 910 адрес: sha256 вмісту кожної) лежить лише в
збирача й у вантаж сторінки не їде — 7 МБ. Тому прилад зводить його до того, що питає код
(`фід_власник_кадру.запис`): для кожного запису збагачення — відбиток адреси кадру виміру, sha256 його вмісту
(12 знаків), чи ті самі байти є в галереї цього товару і на яких ІНШИХ товарах фіду вони стоять. Рішення
(«свій» / «спільний» / «невідомо») приймає модуль, тут лише байти. Слів, сімей тону й імен файлів тут нема.

Запуск: cd джерела && python3 прилади/власник_кадру.py [--писати]
  без ключа — лічба; `--писати` — ще й файл (відсортовано, без mtime: ті самі дані — ті самі байти).
Перезапуск — разом із маніфестом кадрів (`zhnyvarka/кадри_маніфест.py`) чи новими жнивами: факт, знятий з
іншої адреси кадру, код не застосовує (відбиток не збігся — «невідомо»), тож застарілий файл не бреше.
"""
import collections, gzip, json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ)
import feed
import фід_власник_кадру as ВК

МАНІФЕСТ = os.path.join(os.path.dirname(ТУТ), "каталог_маніфест_кадрів.json.gz")


def факти(offers, збагачення, кадри):
    """{ід: [crc адреси, sha256[:12] | None, байти в галереї товару, [інші ід]]} для записів збагачення з кадром."""
    sha = lambda u: (кадри.get(u) or [None] * 5)[4] if (кадри.get(u) or [None])[0] == 200 else None  # noqa: E731
    галерея, де = {}, collections.defaultdict(set)
    for o in offers:
        галерея[o["id"]] = {sha(u) for u in o.get("фото") or () if u} - {None}
        for с in галерея[o["id"]]:
            де[с].add(o["id"])
    вихід = {}
    for ід, зб in збагачення.items():
        url, _ = ВК.адреса_кадру(зб)
        if not url or ід not in галерея:
            continue
        с = sha(url)
        вихід[ід] = [ВК.crc_адреси(url), с[:12] if с else None, bool(с and с in галерея[ід]),
                     sorted(де.get(с, set()) - {ід}) if с else []]
    return вихід


def main():
    offers = feed.читати_yml(feed.каталог_на_диску())[0]
    збагачення = feed.читати_збагачення()
    with gzip.open(МАНІФЕСТ, "rt", encoding="utf-8") as f:
        кадри = json.load(f)["кадри"]
    ф = факти(offers, збагачення, кадри)
    стани = collections.Counter("поза маніфестом" if not в[1] else "спільний" if в[3] else
                                "свій" if в[2] else "поза галереєю" for в in ф.values())
    print("записів із кадром у фіді: %d · %s" % (len(ф), " · ".join("%s %d" % кв for кв in стани.most_common())))
    if "--писати" in sys.argv:
        шлях = os.path.join(ТУТ, ВК.ВЛАСНИК_ІМ + ".gz")
        тіло = json.dumps({"мета": {"маніфест": os.path.basename(МАНІФЕСТ), "адрес": len(кадри)},
                           "записи": ф}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with open(шлях + ".tmp", "wb") as сирий, gzip.GzipFile(fileobj=сирий, mode="wb", compresslevel=9, mtime=0) as g:
            g.write(тіло)
        os.replace(шлях + ".tmp", шлях)
        print("записано %s (%d КБ)" % (шлях, os.path.getsize(шлях) // 1024))


if __name__ == "__main__":
    main()
