"""Звірка повноти, старої межі й результатів; без мережі та продуктових записів."""
import argparse
import collections
import csv
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

ТЕКА = Path(__file__).resolve().parent


def прочитати(шлях):
    with gzip.open(шлях, "rt", encoding="utf-8") as потік:
        return [json.loads(рядок) for рядок in потік]


def main():
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument("--знімок", required=True, type=Path)
    парсер.add_argument("--дерево", required=True, type=Path)
    а = парсер.parse_args()
    assert subprocess.check_output(["git", "-C", str(а.дерево), "rev-parse", "HEAD"], text=True).strip() == \
        "f03db4bbc2fb5a175f98ea373be4624421492cb9"
    assert hashlib.sha256(а.знімок.read_bytes()).hexdigest() == \
        "463268ea374a2d61192f6aee87b2f7513111ff37fd73614b9aa5fd555c0e28cc"
    sys.path.insert(0, str(а.дерево / "джерела"))
    import фід_власник_кадру as читач
    записи = [з for з in прочитати(а.знімок) if
              {п[0]: п[1] for п in з.get("параметри", [])}.get("канал") == "картка"]
    результати = прочитати(ТЕКА / "результати.jsonl.gz")
    assert len(записи) == len(результати) == 13882
    assert {з["ід"] for з in записи} == {р["ід"] for р in результати}
    assert len({р["ід"] for р in результати}) == 13882
    результати = {р["ід"]: р for р in результати}
    межа = collections.Counter()
    матриця = collections.defaultdict(collections.Counter)
    причини = collections.Counter()
    відхилені = []
    до = після = кадрів = 0
    for з in записи:
        п = {п[0]: п[1] for п in з["параметри"]}
        група = ("свотч_у_старому_записі" if п.get("свотч_hex") or п.get("свотч_фото") else
                 "стара_межа_7530" if п.get("id_магазину") and з.get("кадри") else "без_id_1868")
        межа[група] += 1
        старий = dict(id=з["ід"], url=з["адреса"], фото=з["кадри"], параметри=п)
        до += any(читач.доказ_варіанта(старий, к) for к in з["кадри"])
        р = результати[з["ід"]]
        assert р["адреса"] == з["адреса"]
        assert р["голова"] == "f03db4bbc2fb5a175f98ea373be4624421492cb9"
        ключ = р["стан"] + (":" + р["причина"] if р["стан"] == "невідомо" else "")
        матриця[група][ключ] += 1
        причини.update(р.get("причини") or [])
        if р["стан"] in ("доведено", "невідомо"):
            докази = [читач.доказ_варіанта(р["запис"], к) for к in р["запис"]["фото"]]
            assert докази == р["докази"]
            відомий = bool(докази) and all(докази)
            assert відомий == (р["стан"] == "доведено")
            після += відомий
            кадрів += sum(bool(д) for д in докази)
            if р.get("причина") == "читач_відхилив_доказ":
                о = р["запис"]
                власник = json.loads(о["параметри"]["власник_кадру"])
                відхилені.append(dict(ід=з["ід"], адреса=о["url"],
                    параметри_адреси=urlsplit(о["url"]).query, джерело=власник["джерело"],
                    вибір_адреси="прийнято" if читач._вибір_адреси(власник, о["url"]) else "відхилено",
                    товар_збігається=власник["товар"] == о["параметри"]["id_магазину"]))
    assert межа == {"стара_межа_7530": 7530, "свотч_у_старому_записі": 4484, "без_id_1868": 1868}, межа
    assert до == 0
    with (ТЕКА / "лічба.tsv").open(encoding="utf-8", newline="") as потік:
        рядки = list(csv.DictReader(потік, delimiter="\t"))
    assert рядки[-1]["крамниця"] == "РАЗОМ"
    assert sum(int(р["записів"]) for р in рядки[:-1]) == 13882
    assert sum(int(р["оброблено"]) for р in рядки[:-1]) == 13882
    assert sum(int(р["не_виміряно"]) for р in рядки[:-1]) == 0
    колонки = sorted({к for л in матриця.values() for к in л})
    with (ТЕКА / "порівняння.tsv").open("w", encoding="utf-8", newline="") as потік:
        писач = csv.writer(потік, delimiter="\t", lineterminator="\n")
        писач.writerow(["стара_група", "записів"] + колонки)
        for група, лічба in sorted(матриця.items()):
            писач.writerow([група, sum(лічба.values())] + [лічба[к] for к in колонки])
    with (ТЕКА / "відхилено_читачем.tsv").open("w", encoding="utf-8", newline="") as потік:
        писач = csv.DictWriter(потік, fieldnames=["ід", "адреса", "параметри_адреси", "джерело",
                                                "вибір_адреси", "товар_збігається"],
                               delimiter="\t", lineterminator="\n")
        писач.writeheader()
        писач.writerows(відхилені)
    звіт = dict(записів=13882, крамниць=len(рядки) - 1, доведено_до=до, доведено_після=після,
                кадрів_із_доказом=кадрів, стара_межа=межа, причини_з_перетинами=причини,
                відхилення_читача=collections.Counter(р["вибір_адреси"] for р in відхилені),
                знімок_sha256=hashlib.sha256(а.знімок.read_bytes()).hexdigest(),
                відбитки={ім: hashlib.sha256((ТЕКА / ім).read_bytes()).hexdigest()
                           for ім in ("лічба.tsv", "результати.jsonl.gz", "порівняння.tsv", "відхилено_читачем.tsv")})
    (ТЕКА / "звірка.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(звіт, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
