"""Переописує вставки всіх прикрас спільним промптом жнив і зберігає прямі відповіді."""
import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request

from PIL import Image

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
# Фасад жнива_v2 завантажує також ATR/SAM; цей переопис не міряє масок і кольору.
import жнива_промпти as П
import жнива_розбір as Р

МОДЕЛЬ = "qwen3-vl-8b-instruct"


def записати(шлях, дані):
    """Пише JSON атомарно, щоб результат переживав обрив."""
    тимчасовий = шлях.with_suffix(шлях.suffix + ".tmp")
    тимчасовий.write_text(json.dumps(дані, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    тимчасовий.replace(шлях)


def кадр(адреса, кеш):
    """Зберігає саме JPEG, який бачить модель, і повертає його байти."""
    if кеш.exists():
        return кеш.read_bytes()
    запит = urllib.request.Request(адреса, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(запит, timeout=30) as відповідь:
        сирі = відповідь.read()
    фото = Image.open(io.BytesIO(сирі)).convert("RGBA")
    тло = Image.new("RGB", фото.size, "white")
    тло.paste(фото, mask=фото.getchannel("A"))
    тло.thumbnail((1024, 1024))
    тло.save(кеш, "JPEG", quality=85)
    return кеш.read_bytes()


def main():
    """Обходить повний перелік; каталог міняє лише після повного успішного переопису."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument("--ліміт", type=int, default=0)
    арг = парсер.parse_args()
    до = json.loads((ТЕКА / "прикраси_до.json").read_text(encoding="utf-8"))
    шлях = ТЕКА / "відповіді.json"
    відповіді = json.loads(шлях.read_text(encoding="utf-8")) if шлях.exists() else {}
    кеш = КОРІНЬ.parent / "tmp/вставки_кадри"
    кеш.mkdir(exist_ok=True)
    промпт = П._підставити(П.ПРОМПТ_ПРИКРАСА, "прикраса")
    (ТЕКА / "промпт.txt").write_text(промпт, encoding="utf-8")
    перелік = до["прикраси"][:арг.ліміт or None]
    for номер, річ in enumerate(перелік, 1):
        ід = річ["id"]
        if ід in відповіді and "помилка" not in відповіді[ід]:
            continue
        старе = до["збагачення"].get(ід) or {}
        адреса = старе.get("фото") or next(iter(річ.get("фото") or []), None)
        запис = {"фото": адреса, "модель": МОДЕЛЬ,
                 "час_utc": datetime.now(timezone.utc).isoformat()}
        try:
            if not адреса:
                raise ValueError("немає фото прикраси")
            байти = кадр(адреса, кеш / (ід + ".jpg"))
            запис["sha256_jpeg"] = hashlib.sha256(байти).hexdigest()
            сире, ужиток = П._запит(МОДЕЛЬ, промпт, [base64.b64encode(байти).decode("ascii")], з_ужитком=True)
            запис.update(відповідь=сире, usage=ужиток)
            if "вставка" not in сире:
                raise ValueError("модель пропустила обов'язкове поле вставка")
            поля = Р.нормалізувати(сире, "прикраса")
            запис["вставка"] = поля["вставка"]
        except Exception as помилка:
            запис["помилка"] = str(помилка)
            відповіді[ід] = запис
            записати(шлях, відповіді)
            raise SystemExit(f"ЗАБЛОКОВАНО: {ід}, {адреса}: {помилка}")
        відповіді[ід] = запис
        записати(шлях, відповіді)
        print(f"{номер}/{len(перелік)} {ід}: {запис['вставка']}", flush=True)
    if арг.ліміт:
        return
    очікувані = {р["id"] for р in перелік}
    assert set(відповіді) == очікувані and not any("помилка" in з for з in відповіді.values())
    каталог = КОРІНЬ / "джерела/каталог_збагачення.json.gz"
    дані = json.loads(gzip.decompress(каталог.read_bytes()))
    for ід, з in відповіді.items():
        запис = дані.setdefault(ід, {})
        запис["вставка"] = з["вставка"]
        запис["вставка_джерело"] = {к: з[к] for к in ("фото", "модель", "час_utc", "sha256_jpeg")}
    байти = json.dumps(дані, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    тимчасовий = каталог.with_suffix(".gz.tmp")
    тимчасовий.write_bytes(gzip.compress(байти, mtime=0))
    тимчасовий.replace(каталог)
    записати(ТЕКА / "підсумок.json", {
        "каталог_записів": до["каталог"], "прикраси_до": len(перелік), "прикраси_після": len(перелік),
        "збагачено_до": sum(з is not None for з in до["збагачення"].values()),
        "збагачено_після": len(перелік), "поле_до": sum("вставка" in (з or {}) for з in до["збагачення"].values()),
        "зі_вставкою": sum(з["вставка"] is not None for з in відповіді.values()),
        "null": sum(з["вставка"] is None for з in відповіді.values()), "відмов": 0,
        "каталог_sha256": hashlib.sha256(каталог.read_bytes()).hexdigest()})


if __name__ == "__main__":
    main()
