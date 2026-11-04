"""Переміряти старі кадри галерей справжнім записувачем; зберегти вхід і дельту."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import feed as Ф
import жнива_кадри as Ж
import фід_кадр_колір as К
from фід_фото import хости_крамниць


def записати(шлях, дані):
    """Зберегти відновлюваний стан атомарною заміною."""
    тимч = шлях.with_suffix(шлях.suffix + ".tmp")
    with gzip.open(тимч, "wt", encoding="utf-8") as файл:
        json.dump(дані, файл, ensure_ascii=False)
    тимч.replace(шлях)


def головна():
    """Переміряти частину черги без мовної моделі й без публікації неперевірених даних."""
    парсер = argparse.ArgumentParser()
    парсер.add_argument("--ліміт", type=int, default=40)
    арг = парсер.parse_args()
    база = КОРІНЬ / "джерела" / "каталог_кадри.json.gz"
    до = ТЕКА / "кадри_ДО.json.gz"
    if not до.exists():
        shutil.copyfile(база, до)
    with gzip.open(до, "rt", encoding="utf-8") as файл:
        старі = json.load(файл)["записи"]
    офери = Ф.читати_yml(Ф.каталог_на_диску())[0]
    зб = Ф.читати_збагачення()
    цілі, спільні = Ж.цілі(офери, зб)
    хости = хости_крамниць(офери)
    черга = Ж.черга_галерей(офери, зб, старі, спільні, хости,
                            {о["id"] for о, _ in цілі}, Ж.читати_чергу_woo())
    Ж.писати_чергу(черга, str(ТЕКА / "черга_ДО.tsv"))
    # Лише відомі старі кадри: класи плиток зберігаються за тотожними URL і файлом.
    частина = [(о, з, {ф for ф, причина in треба.items() if причина == "без_поверхні"})
               for о, з, треба, _ in черга if "без_поверхні" in треба.values()][:арг.ліміт]
    шлях = ТЕКА / "дельта.json.gz"
    дані = {"мета": {"голова": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=КОРІНЬ, text=True).strip(),
        "почато_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "модель_класів": "наявні класи тотожних кадрів; модель не викликали"}, "записи": {}, "маніфест": []}
    if шлях.exists():
        with gzip.open(шлях, "rt", encoding="utf-8") as файл:
            дані = json.load(файл)
    дані["мета"].setdefault("прогони", []).append(dict(
        команда=[sys.executable, *sys.argv], utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    (ТЕКА / "вибірка.json").write_text(json.dumps([
        dict(id=о["id"], файли=sorted(ф)) for о, _, ф in частина],
        ensure_ascii=False, indent=2), encoding="utf-8")
    (ТЕКА / "фото").mkdir(exist_ok=True)
    print("ЧЕРГА: речей %d, старих для цього кроку %d, кадрів %d" %
          (len(черга), len(частина), sum(len(ф) for _, _, ф in частина)), flush=True)
    for номер, (офер, збагачення, файли) in enumerate(частина, 1):
        ід = офер["id"]
        if ід in дані["записи"]:
            continue
        початок = time.monotonic()
        нові = Ж.виміряти_річ(офер, збагачення, спільні, хости, None, False, 4,
                             None, кеш=True, тайм_кадру=0, лише=файли)
        попередні = {в["файл"]: в for в in старі[ід]}
        for запис in нові:
            попередній = попередні.get(запис["файл"], {})
            if запис["url"] == попередній.get("url") and попередній.get("клас"):
                запис["клас"] = попередній["клас"]
            ключ = hashlib.md5(запис["url"].encode()).hexdigest()
            кеш = Ж._індекс.get(ключ, {})
            фото = кеш.get("шлях")
            if фото and Path(фото).is_file():
                ціль = ТЕКА / "фото" / (ключ + ".jpg")
                shutil.copyfile(фото, ціль)
                дані["маніфест"].append(dict(id=ід, файл=запис["файл"], url=запис["url"],
                    фото=ціль.relative_to(ТЕКА).as_posix(),
                    sha256=hashlib.sha256(ціль.read_bytes()).hexdigest(),
                    розмір=кеш.get("розмір"), url_великий=кеш.get("url_великий")))
            elif запис.get("вимір"):
                raise RuntimeError("Вимір без збереженого кадру: " + запис["url"])
        дані["записи"][ід] = нові
        дані.setdefault("час_секунд", {})[ід] = round(time.monotonic() - початок, 1)
        дані["мета"]["оновлено_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        записати(шлях, дані)
        print("[%d/%d] %s: кадрів %d, придатних %d, %.1f с" %
              (номер, len(частина), ід, len(нові), sum(bool(К.вимір_кадру(в)) for в in нові),
               time.monotonic() - початок), flush=True)
    усі = [в for записи in дані["записи"].values() for в in записи]
    print("ПІДСУМОК: " + json.dumps(dict(речей=len(дані["записи"]), кадрів=len(усі),
          придатних=sum(bool(К.вимір_кадру(в)) for в in усі),
          маски=dict(collections.Counter(в.get("маска", "не_міряли") for в in усі)),
          маніфест=len(дані["маніфест"])), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    головна()
