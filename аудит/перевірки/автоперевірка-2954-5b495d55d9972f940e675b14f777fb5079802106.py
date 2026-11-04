"""Незалежна звірка збереженої дельти #2954; запуск з кореня дерева голови PR."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

ГОЛОВА = "5b495d55d9972f940e675b14f777fb5079802106"
ВХІД = "1fc4ed8547643cf9642c9104098e3b8abc3bbf27"
assert subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == ГОЛОВА
ТЕКА = Path("аудит/проби/річ_колір_перезбір_0411")
sys.path.insert(0, "джерела")
from фід_кадр_колір import вимір_кадру


def прочитати(назва):
    """Прочитати архів без перезапису доказів."""
    return json.loads(gzip.decompress((ТЕКА / назва).read_bytes()))


до = прочитати("кадри_ДО.json.gz")["записи"]
після = прочитати("дельта.json.gz")
вибірка = {р["id"]: set(р["файли"]) for р in
           json.loads((ТЕКА / "вибірка.json").read_text("utf-8"))}
assert set(вибірка) == set(після["записи"]) and len(вибірка) == 40
маніфест = {(р["id"], р["файл"], р["url"]): р for р in після["маніфест"]}
assert len(маніфест) == len(після["маніфест"]) == 147
числа, бачені = collections.Counter(), set()
змінені_url = без_класу = 0
for ід, кадри in після["записи"].items():
    старі = {р["файл"]: р for р in до[ід]}
    assert len(кадри) == len({р["файл"] for р in кадри})
    assert {р["файл"] for р in кадри} == вибірка[ід]
    for кадр in кадри:
        ключ = ід, кадр["файл"], кадр["url"]
        assert ключ in маніфест
        бачені.add(ключ)
        м = маніфест[ключ]
        фото = ТЕКА / м["фото"]
        байти = фото.read_bytes()
        assert hashlib.sha256(байти).hexdigest() == м["sha256"]
        with Image.open(фото) as зображення:
            assert list(зображення.size) == м["розмір"]
            зображення.verify()
        старий = старі[кадр["файл"]]
        if старий["url"] == кадр["url"]:
            assert старий.get("клас") == кадр.get("клас")
        else:
            змінені_url += 1
        без_класу += not bool(кадр.get("клас"))
        assert not вимір_кадру(старий)
        придатний = bool(вимір_кадру(кадр))
        числа["valid" if придатний else "unknown"] += 1
        assert придатний == (кадр["колір_тип"] == "вимір") == кадр["придатна"]
        if not придатний:
            assert not кадр.get("lab") and not кадр.get("hex") and not кадр.get("слово")
        числа[кадр["маска"]] += 1
        числа["hex_changed"] += старий.get("hex") != кадр.get("hex")
        числа["word_changed"] += старий.get("слово") != кадр.get("слово")
        числа["bytes"] += len(байти)
assert бачені == set(маніфест)
assert set(ТЕКА.glob("фото/*.jpg")) == {ТЕКА / р["фото"] for р in маніфест.values()}
assert (ТЕКА / "кадри_ДО.json.gz").read_bytes() == subprocess.check_output(
    ["git", "show", ВХІД + ":джерела/каталог_кадри.json.gz"])
сирий = gzip.decompress((ТЕКА / "перезбір_сирий.log.gz").read_bytes()).decode("utf-8")
читаний = (ТЕКА / "перезбір.log").read_text("utf-8")
assert [р for р in сирий.splitlines() if р.strip()] == [р for р in читаний.splitlines() if р.strip()]
print("INDEPENDENT", json.dumps(dict(числа), ensure_ascii=False))
print("URL змінено:", змінені_url, "; класу немає:", без_класу)
print("Вхід ДО побайтово тотожний; непорожні рядки сирого й читаного журналів тотожні")
for ід in ("ж-01872@vmma.com.ua", "ж-02051@vmma.com.ua", "ж-01203@stolyarchuk.com.ua"):
    print(ід, json.dumps([(р["файл"], bool(вимір_кадру(р)),
                          (р.get("вимір") or {}).get("візерунок"))
                         for р in після["записи"][ід]], ensure_ascii=False))
