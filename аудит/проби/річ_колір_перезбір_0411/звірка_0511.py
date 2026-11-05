"""Звірити наступні десять галерей із незміненою дельтою п'ятдесяти."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
БАЗА = "c253d7bebc52371bba8aef0a5c81d47131083a3e"
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import фід_кадр_колір as К
import жнива_кадри as Ж


def головна():
    """Звірити повноту кадрів, спадкоємність дельти й SHA-256 кожного фото."""
    шлях = (ТЕКА / "дельта.json.gz").relative_to(КОРІНЬ).as_posix()
    попередня = json.loads(gzip.decompress(subprocess.check_output(
        ["git", "show", БАЗА + ":" + шлях], cwd=КОРІНЬ)))
    після = json.loads(gzip.decompress((ТЕКА / "дельта.json.gz").read_bytes()))
    до = json.loads(gzip.decompress((ТЕКА / "кадри_ДО.json.gz").read_bytes()))["записи"]
    вхід = (ТЕКА / "кадри_ДО.json.gz").relative_to(КОРІНЬ).as_posix()
    assert (ТЕКА / "кадри_ДО.json.gz").read_bytes() == subprocess.check_output(
        ["git", "show", БАЗА + ":" + вхід], cwd=КОРІНЬ), "Змінився вхід"
    вибірка = {р["id"]: set(р["файли"]) for р in json.loads(
        (ТЕКА / "вибірка.json").read_text(encoding="utf-8"))}
    assert set(після["записи"]) == set(вибірка), "Неповна вибірка"
    assert len(вибірка) == 60 and len(попередня["записи"]) == 50
    for ід, записи in попередня["записи"].items():
        assert після["записи"][ід] == записи, ід
    for ід, час in попередня["час_секунд"].items():
        assert після["час_секунд"][ід] == час, ід
    assert після["маніфест"][:len(попередня["маніфест"])] == попередня["маніфест"]
    маніфест = {}
    for м in після["маніфест"]:
        фото = ТЕКА / м["фото"]
        assert hashlib.sha256(фото.read_bytes()).hexdigest() == м["sha256"], м
        ключ = (м["id"], м["файл"], м["url"])
        assert ключ not in маніфест, ключ
        маніфест[ключ] = м
    нові = set(після["записи"]) - set(попередня["записи"])
    рядки, адреси = [], []
    for ід, записи in після["записи"].items():
        assert len(записи) == len(вибірка[ід]), ід
        assert {в["файл"] for в in записи} == вибірка[ід], ід
        старі = {в["файл"]: в for в in до[ід]}
        for в in записи:
            с = старі[в["файл"]]
            assert (ід, в["файл"], в["url"]) in маніфест, (ід, в["файл"])
            if not К.вимір_кадру(в):
                assert not в.get("lab") and not в.get("hex"), (ід, в["файл"])
            if ід in нові:
                assert Ж._файл_фото(в["url"]) == Ж._файл_фото(с["url"]) == в["файл"]
                if в["url"] == с["url"]:
                    assert в.get("клас") == с.get("клас"), (ід, в["файл"])
                else:
                    # Записувач свідомо не переносить клас за іншою адресою.
                    assert not в.get("клас"), (ід, в["файл"])
                    адреси.append(dict(id=ід, файл=в["файл"], до=с["url"], після=в["url"],
                                       клас_до=с.get("клас"), клас_після=в.get("клас")))
                рядки.append((с, в))
    усі = [в for записи in після["записи"].values() for в in записи]
    assert len(усі) == len(маніфест)
    числа = dict(база=БАЗА, попередніх_галерей=50,
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
        нові_id=sorted(нові), перевірених_фото=len(маніфест),
        фото_байтів=sum((ТЕКА / м["фото"]).stat().st_size for м in маніфест.values()),
        разом_галерей=len(після["записи"]), разом_кадрів=len(усі),
        разом_придатних=sum(bool(К.вимір_кадру(в)) for в in усі),
        разом_утримань=sum(not К.вимір_кадру(в) for в in усі))
    числа.update(змінили_url=len(адреси), зняли_клас=sum(bool(а["клас_до"]) for а in адреси),
                  відмінності_url=адреси)
    (ТЕКА / "числа_0511.json").write_text(
        json.dumps(числа, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(числа, ensure_ascii=False))


if __name__ == "__main__":
    головна()
