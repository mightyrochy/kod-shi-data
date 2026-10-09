# -*- coding: utf-8 -*-
"""КОЛІР-Р3 (рядок 2696): пакетний вимір кольору жнивами v2 для речей без виміру — v1 і «нові» (без запису чи з помилкою).
Кадр — перший кадр картки (`фід_фото.кадри_речі`), маска ATR→SAM, k-means у Lab з поправкою тла (`жнива_колір.виміряти_фото`).
Запис результату — `виміри.jsonl` поруч (по рядку на річ, обрив не губить зроблене); `--злити` кладе виміри в каталог.
Запуск із джерела/: python ../аудит/колір_р3/виміряти.py --група v1 --ліміт 20 | --злити"""
import argparse, gzip, hashlib, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ТУТ, "..", "..", "джерела"))
import feed as F
from фід_фото import кадри_речі, _спільні_фото, _хости_крамниць, _файл_фото
from жнива_фото import _скачати_фото, збільшити_url
from жнива_реєстр import КЕШ
from жнива_колір import виміряти_фото, звести_колір
from звірка_збагачення import сім_я_слова
from жнива_промпти import тип_речі
from звірка_збагачення import слова_крамниці
ЖУРНАЛ = os.path.join(ТУТ, "виміри.jsonl")
ЗБ = os.path.join(ТУТ, "..", "..", "джерела", "каталог_збагачення.json.gz")


def група(z):
    return "нові" if (z is None or "помилка" in z) else "v1" if z.get("версія") is None else "v2"


def зроблені():
    if not os.path.exists(ЖУРНАЛ):
        return {}
    return {j["id"]: j for j in (json.loads(р) for р in open(ЖУРНАЛ, encoding="utf-8") if р.strip())}


def згода(частка_маски, основний, слова):
    """`жнива_колір.впевненість` без свідків, яких тут не питали: слово моделі (v1-слово хибне вже в кожному
    третьому з вибірки очима — його проти виміру не ставимо) і друге фото мовчать, ваги не мають."""
    ваги, бали = [0.35], [min(1.0, (частка_маски or 0) / 0.25)]
    if слова:
        ваги.append(0.20)
        бали.append(1.0 if сім_я_слова(основний["слово"]) in {сім_я_слова(с) for с in слова} else 0.0)
    if not основний.get("у_вікні", True):
        бали = [б * 0.8 for б in бали]
    return round(sum(в * б for в, б in zip(ваги, бали)) / sum(ваги), 2)


def скачати(u, ід):
    return _скачати_фото(u, збільшити_url(u), "r3-%s-" % hashlib.md5(ід.encode("utf-8")).hexdigest()[:10])


def вимір_речі(o, z, адреси, фото):
    """Перший придатний кадр → запис журналу (ok, поля колір_основний/другий/впевненість)."""
    ід, т0 = o["id"], time.time()
    тип, слот = тип_речі(o)
    слова = слова_крамниці(o.get("колір_сирий") or o.get("колір_назва") or "")
    спроби = []
    for u, ф in zip(адреси, фото):
        if ф.get("помилка") or not ф.get("шлях"):
            спроби.append((u, "не скачалось: %s" % (ф.get("помилка") or "шляху нема"))); continue
        if ф.get("мала") or ф.get("майже_біла"):
            спроби.append((u, "заглушка: %s" % ("менша за 6 КБ" if ф.get("мала") else "майже біла"))); continue
        частка, кластери, чому, джерело, _ = виміряти_фото(ф["шлях"], слот)
        if not кластери:
            спроби.append((u, "без виміру: %s [%s]" % (str(чому)[:100], джерело))); continue
        основний, другий, спір = звести_колір(кластери, None, слова)
        впев = згода(частка, основний, слова)
        return dict(id=ід, ok=True, url=u, слот=слот, маска=джерело, частка_маски=частка, чому=str(чому)[:160],
                    кластери=[[к["слово"], к["частка"], к["hex"]] for к in кластери[:4]],
                    основний=dict(слово=основний["слово"], hex=основний["hex"], частка=основний["частка"]),
                    другий=(dict(слово=другий["слово"], hex=другий["hex"], частка=другий["частка"]) if другий else None),
                    спір=спір, впевненість=впев, слово_було=((z or {}).get("колір_основний") or {}).get("слово"), група=група(z),
                    спроб=len(спроби) + 1, с=round(time.time() - т0, 1))
    return dict(id=ід, ok=False, група=група(z), спроби=спроби, адрес=len(адреси), с=round(time.time() - т0, 1))


def злити(тільки_ok=True):
    зб = json.load(gzip.open(ЗБ, "rt", encoding="utf-8"))
    дата, n = time.strftime("%Y-%m-%d"), 0
    for ід, j in зроблені().items():
        if not j.get("ok") or ід not in зб and j["група"] != "нові":
            continue
        z = зб.get(ід) or {}
        з = {k: v for k, v in z.items() if k != "помилка"} if "помилка" in z else dict(z)
        з.update(колір_основний=j["основний"], колір_другий=j["другий"], впевненість=j["впевненість"],
                 фото=j["url"], версія=2, знято=дата)
        з.setdefault("модель", "маска ATR→SAM (колір-р3)")
        зб[ід] = з
        n += 1
    сирі = json.dumps(зб, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    тимч = ЗБ + ".tmp"
    with gzip.open(тимч, "wb", compresslevel=9) as f:
        f.write(сирі)
    os.replace(тимч, ЗБ)
    print("злито в каталог: %d записів, файл %d КБ" % (n, os.path.getsize(ЗБ) // 1024))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--група", default="v1", help="v1 | нові | всі")
    ap.add_argument("--ліміт", type=int, default=None)
    ap.add_argument("--пропустити", type=int, default=0, help="пропустити перші N речей черги (після відбору)")
    ap.add_argument("--качалок", type=int, default=8)
    ap.add_argument("--вікно", type=int, default=12, help="скільком наступним речам качати кадр наперед")
    ap.add_argument("--злити", action="store_true")
    а = ap.parse_args()
    if а.злити:
        return злити()
    offers = F.читати_yml(F.каталог_на_диску())[0]
    зб = json.load(gzip.open(ЗБ, "rt", encoding="utf-8"))
    сп, хости, готові = _спільні_фото(offers), _хости_крамниць(offers), зроблені()
    черга = []
    for o in offers:
        z = зб.get(o["id"])
        if група(z) == "v2" or (а.група != "всі" and група(z) != а.група) or o["id"] in готові:
            continue
        мг = o.get("магазин") or o["id"].split("@")[-1]
        адреси = кадри_речі(o, сп.get(мг) or {}, хости, (z or {}).get("фото") if група(z) == "v1" else None)[:3]
        черга.append((o, z, адреси))
    черга = черга[а.пропустити:][:а.ліміт]
    print("у черзі: %d (група %s), уже в журналі: %d" % (len(черга), а.група, len(готові)), flush=True)
    os.makedirs(КЕШ, exist_ok=True)
    пул, т0, ok, зайнято = ThreadPoolExecutor(а.качалок), time.time(), 0, 0.0
    заявки = {}

    def замовити(i):
        if i < len(черга) and i not in заявки:
            o, _, адреси = черга[i]
            заявки[i] = [пул.submit(скачати, u, o["id"]) for u in адреси]
    for i in range(min(а.вікно, len(черга))):
        замовити(i)
    with open(ЖУРНАЛ, "a", encoding="utf-8") as вих:
        for i, (o, z, адреси) in enumerate(черга):
            замовити(i + а.вікно)
            фото = [ф.result() for ф in заявки.pop(i)]
            т = time.time()
            j = вимір_речі(o, z, адреси, фото)
            зайнято += time.time() - т
            for ф in фото:
                if ф.get("шлях") and os.path.exists(ф["шлях"]):
                    try:
                        os.remove(ф["шлях"])
                    except OSError:
                        pass
            ok += bool(j["ok"])
            вих.write(json.dumps(j, ensure_ascii=False) + "\n"); вих.flush()
            print("[%d/%d] %s %s %s %.1f с" % (i + 1, len(черга), o["id"], "ok" if j["ok"] else "збій",
                  (j["основний"]["слово"] + " " + str(j["впевненість"])) if j["ok"] else str(j["спроби"])[:90], j["с"]), flush=True)
    print("готово за %.0f с (вимір %.0f с): ok %d з %d" % (time.time() - т0, зайнято, ok, len(черга)))


if __name__ == "__main__":
    main()
