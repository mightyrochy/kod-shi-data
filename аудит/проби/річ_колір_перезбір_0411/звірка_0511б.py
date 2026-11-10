"""Галереї 61–70 (05.11): відокремити нову частину й звірити збереження попередньої."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import фід_кадр_колір as К


def головна():
    """Звірити старі записи, повноту нових і SHA-256 усіх збережених входів."""
    база = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=КОРІНЬ, text=True).strip()
    відносний = (ТЕКА / "дельта.json.gz").relative_to(КОРІНЬ).as_posix()
    попередня = json.loads(gzip.decompress(subprocess.check_output(
        ["git", "show", база + ":" + відносний], cwd=КОРІНЬ)))
    після = json.loads(gzip.decompress((ТЕКА / "дельта.json.gz").read_bytes()))
    до = json.loads(gzip.decompress((ТЕКА / "кадри_ДО.json.gz").read_bytes()))["записи"]
    вибірка = {р["id"]: set(р["файли"]) for р in
               json.loads((ТЕКА / "вибірка.json").read_text(encoding="utf-8"))}
    assert set(після["записи"]) == set(вибірка), "Неповна вибірка"
    for ід, записи in попередня["записи"].items():
        assert після["записи"][ід] == записи, ід
    for ід, час in попередня["час_секунд"].items():
        assert після["час_секунд"][ід] == час, ід
    assert після["маніфест"][:len(попередня["маніфест"])] == попередня["маніфест"]
    маніфест = {}
    for м in після["маніфест"]:
        assert hashlib.sha256((ТЕКА / м["фото"]).read_bytes()).hexdigest() == м["sha256"]
        ключ = (м["id"], м["файл"], м["url"])
        assert ключ not in маніфест, ключ
        маніфест[ключ] = м
    нові = set(після["записи"]) - set(попередня["записи"])
    рядки = []
    змінені_url = []
    for ід in sorted(нові):
        записи = після["записи"][ід]
        assert {в["файл"] for в in записи} == вибірка[ід], ід
        старі = {в["файл"]: в for в in до[ід]}
        for в in записи:
            с = старі[в["файл"]]
            if в["url"] != с["url"]:
                змінені_url.append((ід, в["файл"], с["url"], в["url"]))
            elif в.get("клас") != с.get("клас"):
                raise AssertionError((ід, в["файл"]))
            assert (ід, в["файл"], в["url"]) in маніфест, (ід, в["файл"])
            if not К.вимір_кадру(в):
                assert not в.get("lab") and not в.get("hex"), (ід, в["файл"])
            рядки.append((с, в))
    числа = dict(база=база, попередніх_галерей=len(попередня["записи"]),
        попередніх_кадрів=sum(map(len, попередня["записи"].values())),
        нових_галерей=len(нові), нових_кадрів=len(рядки),
        вимірів_до=sum(bool(К.вимір_кадру(с)) for с, _ in рядки),
        вимірів_після=sum(bool(К.вимір_кадру(в)) for _, в in рядки),
        невідомих=sum(not К.вимір_кадру(в) for _, в in рядки),
        змінили_hex=sum(с.get("hex") != в.get("hex") for с, в in рядки),
        змінили_hex_придатних=sum(bool(К.вимір_кадру(в)) and с.get("hex") != в.get("hex")
                                   for с, в in рядки),
        змінили_слово=sum(с.get("слово") != в.get("слово") for с, в in рядки),
        маски=dict(collections.Counter(в.get("маска") for _, в in рядки)),
        час_секунд=round(sum(після["час_секунд"][ід] for ід in нові), 1),
        змінених_url=len(змінені_url), нові_id=sorted(нові), перевірених_фото=len(маніфест))
    (ТЕКА / "числа_0511б.json").write_text(
        json.dumps(числа, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(числа, ensure_ascii=False))


if __name__ == "__main__":
    головна()
