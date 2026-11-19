"""Набір відкритих портретів: одна команда кладе файли в теку фото сцен (поза репозиторієм) і звіряє контрольні суми.

    TEKA_FOTO_SCENY=<тека> python3 -I збір.py [<тека виходу>]

Файли — з `набір.json` (Wikimedia Commons, студійні офіційні портрети, ліцензія відкрита, автор і сторінка файлу — там
само). Виходять: `<тека>/портрети/<id>.jpg` і `<тека>/портрети/опис.json` ({"<людина>": [{"файл", "шлях", "ліцензія"}]},
формат `аудит/проби/вимір-портрета-1211/вимір.py`). Тека виходу — аргумент, а нема його — `$TEKA_FOTO_SCENY`. Фото в
репозиторій не комітять. Сервер лімітує запити: пауза між файлами, на 429 чекаємо `Retry-After`, а не повторюємо одразу.
Код виходу 1 — контрольна сума файлу не збіглася (сервер віддав інше) або файл не дістали."""
import hashlib, json, os, sys, time, urllib.error, urllib.request
ТУТ = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "PortraitProbe/0.1 (research script)"}
ПАУЗА = 1.5
def дістати(url):
    for спроба in range(12):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as е:
            if е.code not in (429, 500, 502, 503, 504):
                print("  HTTP", е.code, url[-60:], file=sys.stderr); return None
            чекати = int(е.headers.get("Retry-After") or 20) + 2
            print("  %d: чекаю %d с" % (е.code, чекати), file=sys.stderr, flush=True); time.sleep(чекати)
        except OSError as е:
            print("  збій мережі:", str(е)[:60], file=sys.stderr); time.sleep(10)
    return None
def головна():
    набір = json.load(open(os.path.join(ТУТ, "набір.json"), encoding="utf-8"))
    корінь = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TEKA_FOTO_SCENY", "")
    if not корінь:
        sys.exit("потрібна тека: TEKA_FOTO_SCENY=<тека> або аргумент")
    тека = os.path.join(корінь, "портрети"); os.makedirs(тека, exist_ok=True)
    опис, збоїв = {}, 0
    for к in набір["кадри"]:
        шлях = os.path.join(тека, к["id"] + ".jpg")
        суму = lambda: hashlib.sha256(open(шлях, "rb").read()).hexdigest() if os.path.exists(шлях) else None
        if суму() != к["sha256"]:
            time.sleep(ПАУЗА)
            b = дістати(к["url"])
            if b is None:
                збоїв += 1; print("НЕ ДІСТАЛИ", к["id"]); continue
            if hashlib.sha256(b).hexdigest() != к["sha256"]:
                збоїв += 1; print("СУМА НЕ ЗБІГЛАСЬ", к["id"]); continue
            open(шлях, "wb").write(b)
        опис.setdefault(к["людина"], []).append(dict(файл=к["файл"], шлях=шлях, ліцензія=к["ліцензія"]))
    json.dump(опис, open(os.path.join(тека, "опис.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("кадрів %d, людей %d, збоїв %d; опис — %s" % (sum(map(len, опис.values())), len(опис), збоїв, os.path.join(тека, "опис.json")))
    sys.exit(1 if збоїв else 0)
if __name__ == "__main__":
    головна()
