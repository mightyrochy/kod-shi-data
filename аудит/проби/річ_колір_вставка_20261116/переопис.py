"""Продовжує повний переопис вставок, пропускаючи записи без достовірного кадру."""
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ПОПЕРЕДНЯ = ТЕКА.parent / "річ_колір_вставка_20261115"
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import жнива_промпти as П
import жнива_розбір as Р

СПЕЦ = importlib.util.spec_from_file_location("попередній_переопис", ПОПЕРЕДНЯ / "переопис.py")
ПОПЕРЕДНІЙ = importlib.util.module_from_spec(СПЕЦ)
СПЕЦ.loader.exec_module(ПОПЕРЕДНІЙ)
записати = ПОПЕРЕДНІЙ.записати
кадр = ПОПЕРЕДНІЙ.кадр
МОДЕЛЬ = ПОПЕРЕДНІЙ.МОДЕЛЬ


def main():
    """Зберігає кожну відповідь, а каталог оновлює після повного обходу всіх доступних кадрів."""
    бази = {ш: subprocess.check_output(["git", "rev-parse", "HEAD:" + ш], cwd=КОРІНЬ).decode().strip()
            for ш in ("каталог_повний.xml.gz", "джерела/каталог_збагачення.json.gz")}
    for ш, sha in бази.items():
        попередній = subprocess.check_output(["git", "rev-parse", "9c38154a:" + ш], cwd=КОРІНЬ).decode().strip()
        assert sha == попередній, (ш, "каталог змінився: потрібен новий повний перелік")
    записати(ТЕКА / "бази.json", бази)
    до = json.loads((ПОПЕРЕДНЯ / "прикраси_до.json").read_text(encoding="utf-8"))
    додаткові = json.loads((ПОПЕРЕДНЯ / "додаткові_фото.json").read_text(encoding="utf-8"))
    шлях = ТЕКА / "відповіді.json"
    відповіді = json.loads(шлях.read_text(encoding="utf-8")) if шлях.exists() else {}
    пропуски = {}
    шлях_відмов = ТЕКА / "відмови_моделі.json"
    відмови = json.loads(шлях_відмов.read_text(encoding="utf-8")) if шлях_відмов.exists() else {}
    for ід in [і for і, з in відповіді.items() if "помилка" in з]:
        відмови[ід] = відповіді.pop(ід)
    записати(шлях, відповіді)
    записати(шлях_відмов, відмови)
    кеш = КОРІНЬ.parent / "tmp/вставки_кадри"
    кеш.mkdir(exist_ok=True)
    промпт = П._підставити(П.ПРОМПТ_ПРИКРАСА, "прикраса")
    assert промпт == (ПОПЕРЕДНЯ / "промпт.txt").read_text(encoding="utf-8"), "промпт змінився"
    (ТЕКА / "промпт.txt").write_text(промпт, encoding="utf-8")
    попередні = json.loads((ПОПЕРЕДНЯ / "відповіді.json").read_text(encoding="utf-8"))
    for номер, річ in enumerate(до["прикраси"], 1):
        ід = річ["id"]
        старе = до["збагачення"].get(ід) or {}
        адреса = старе.get("фото") or next(iter(річ.get("фото") or []), None)
        if not адреса and ід.endswith("@jecomestudio.com"):
            адреса = next(iter(додаткові.get(ід, {}).get("фото") or []), None)
            if адреса:
                адреса = адреса.replace("http://", "https://", 1)
        if not адреса:
            пропуски[ід] = {"причина": "немає достовірного кадру у фіді й збагаченні"}
            записати(ТЕКА / "без_кадру.json", пропуски)
            print(f"{номер}/394 {ід}: без кадру", flush=True)
            continue
        if ід in відмови:
            print(f"{номер}/394 {ід}: відмова моделі збережена, не запитуємо вдруге", flush=True)
            continue
        запис = {"фото": адреса, "модель": МОДЕЛЬ, "час_utc": datetime.now(timezone.utc).isoformat()}
        фото = кеш / (ід + ".jpg")
        давнє = попередні.get(ід) or {}
        if давнє.get("фото") == адреса and "помилка" not in давнє and (ПОПЕРЕДНЯ / "фото" / фото.name).exists():
            shutil.copyfile(ПОПЕРЕДНЯ / "фото" / фото.name, фото)
        try:
            байти = кадр(адреса, фото)
        except Exception as помилка:
            пропуски[ід] = {"фото": адреса, "причина": str(помилка)}
            записати(ТЕКА / "без_кадру.json", пропуски)
            print(f"{номер}/394 {ід}: кадр недоступний: {помилка}", flush=True)
            continue
        запис["sha256_jpeg"] = hashlib.sha256(байти).hexdigest()
        збережене = відповіді.get(ід) or давнє
        if (збережене.get("фото") == адреса and збережене.get("sha256_jpeg") == запис["sha256_jpeg"]
                and "помилка" not in збережене):
            assert Р.нормалізувати(збережене["відповідь"], "прикраса")["вставка"] == збережене["вставка"]
            відповіді[ід] = збережене
            записати(шлях, відповіді)
            print(f"{номер}/394 {ід}: збережена відповідь", flush=True)
            continue
        try:
            сире, ужиток = П._запит(МОДЕЛЬ, промпт, [base64.b64encode(байти).decode("ascii")], з_ужитком=True)
        except Exception as помилка:
            raise SystemExit(f"ЗАБЛОКОВАНО: {ід}, {адреса}: запит до моделі: {помилка}")
        запис.update(відповідь=сире, usage=ужиток)
        try:
            if "вставка" not in сире:
                raise ValueError("модель пропустила обов'язкове поле вставка")
            запис["вставка"] = Р.нормалізувати(сире, "прикраса")["вставка"]
        except Exception as помилка:
            запис["помилка"] = str(помилка)
            відмови[ід] = запис
            записати(шлях_відмов, відмови)
            print(f"{номер}/394 {ід}: ВІДМОВА МОДЕЛІ: {помилка}", flush=True)
            continue
        відповіді[ід] = запис
        записати(шлях, відповіді)
        print(f"{номер}/394 {ід}: {запис['вставка']}", flush=True)
    очікувані = {р["id"] for р in до["прикраси"]}
    assert set(відповіді).isdisjoint(пропуски) and set(відповіді).isdisjoint(відмови)
    assert set(відповіді) | set(пропуски) | set(відмови) == очікувані
    assert not any("помилка" in з for з in відповіді.values())
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
        "каталог_записів": до["каталог"], "прикраси_до": len(очікувані), "прикраси_після": len(очікувані),
        "збагачено_до": sum(з is not None for з in до["збагачення"].values()),
        "збагачено_після": sum(ід in дані for ід in очікувані),
        "поле_до": sum("вставка" in (з or {}) for з in до["збагачення"].values()),
        "поле_після": len(відповіді),
        "зі_вставкою": sum(з["вставка"] is not None for з in відповіді.values()),
        "null": sum(з["вставка"] is None for з in відповіді.values()), "відмов": len(відмови),
        "відмови": {ід: {"відповідь": з["відповідь"], "причина": з["помилка"]} for ід, з in відмови.items()},
        "без_кадру": пропуски, "каталог_sha256": hashlib.sha256(каталог.read_bytes()).hexdigest()})


if __name__ == "__main__":
    main()
