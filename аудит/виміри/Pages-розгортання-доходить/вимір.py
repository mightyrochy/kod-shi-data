# -*- coding: utf-8 -*-
"""Мірило 1 наряду «Pages-розгортання-доходить»: чи доходить `main` до сайта (рядки дошки 16652–16654).

python3 аудит/виміри/Pages-розгортання-доходить/вимір.py --від 2026-11-17T19:00:00Z --до 2026-11-18T19:50:00Z \
    [--json вихід.json] [--ревізія HEAD]

Читає через API GitHub (токен — `GH_TOKEN`/`GITHUB_TOKEN`, коли є; запуск — з кореня репозиторію):
- запуски процесів розгортання за вікно: вбудованого «pages build and deployment» (id 345307674) і власного
  `pages.yml` — скільки дійшло до кінця (success), скасовано, впало;
- розгортання середовища `github-pages` (їх створює job розгортання обох процесів) і час, коли кожне стало «success»
  — тоді коміт розгортання на сайті; частка розгортань, що дійшли до кінця;
- коміти `main` за вікно і їхні файли; коміт «міняє сайт», коли хоч один його файл — сайт за
  `джерела/прилади/сайт_pages.py` на `--ревізія` (історія лінійна: розгортання коміту D несе всі коміти до D);
- проміжок «коміт, що міняє сайт, у `main` → він на сайті»: від часу коміту (у `main` він потрапляє злиттям чи push
  тієї ж хвилини) до першого успішного розгортання цього чи новішого коміту; найдовший — мірило; ще не на сайті —
  проміжок до моменту виміру з позначкою;
- найдовші проміжки між успішними розгортаннями за вікно.
"""
import argparse
import datetime as dt
import json
import os
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "джерела", "прилади"))
import сайт_pages  # noqa: E402

РЕПО = "mightyrochy/kod-shi-data"
API = "https://api.github.com"
ВБУДОВАНИЙ = "345307674"
ВЛАСНИЙ = "pages.yml"


def час(р):
    return dt.datetime.fromisoformat(р.replace("Z", "+00:00"))


def хв(дельта):
    return round(дельта.total_seconds() / 60, 1)


def запит(шлях, параметри=None):
    адреса = шлях if шлях.startswith("http") else f"{API}/repos/{РЕПО}/{шлях}"
    if параметри:
        адреса += ("&" if "?" in адреса else "?") + urllib.parse.urlencode(параметри)
    заголовки = {"Accept": "application/vnd.github+json", "User-Agent": "vymir-pages"}
    токен = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if токен:
        заголовки["Authorization"] = f"Bearer {токен}"
    for спроба in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(адреса, headers=заголовки), timeout=60) as в:
                return json.load(в), в.headers.get("Link", "")
        except urllib.error.HTTPError as п:
            if п.code == 404:
                return None, ""
            if спроба == 3 or п.code not in (500, 502, 503, 504):
                raise
        except urllib.error.URLError:
            if спроба == 3:
                raise


def сторінки(шлях, параметри, ключ=None, стоп=None):
    параметри = dict(параметри, per_page=100)
    адреса = шлях
    while адреса:
        дані, link = запит(адреса, параметри)
        параметри = None
        if дані is None:
            return
        елементи = дані[ключ] if ключ else дані
        for е in елементи:
            if стоп and стоп(е):
                return
            yield е
        адреса = None
        for частина in link.split(","):
            if 'rel="next"' in частина:
                адреса = частина.split(";")[0].strip()[1:-1]


def запуски(процес, від, до):
    діапазон = f"{від:%Y-%m-%dT%H:%M:%SZ}..{до:%Y-%m-%dT%H:%M:%SZ}"
    вихід = []
    for р in сторінки(f"actions/workflows/{процес}/runs", {"created": діапазон}, "workflow_runs"):
        вихід.append({
            "id": р["id"], "подія": р["event"], "sha": р["head_sha"], "створено": р["created_at"],
            "почато": р.get("run_started_at"), "кінець": р["updated_at"], "стан": р["status"],
            "висновок": р["conclusion"],
        })
    return вихід


def розгортання(від):
    межа = від - dt.timedelta(days=2)
    вихід = []
    for д in сторінки("deployments", {"environment": "github-pages"},
                      стоп=lambda д: час(д["created_at"]) < межа):
        статуси = list(сторінки(f"deployments/{д['id']}/statuses", {}))
        успіх = [с["created_at"] for с in статуси if с["state"] == "success"]
        кінцеві = [с["state"] for с in статуси if с["state"] in ("success", "failure", "error")]
        вихід.append({
            "id": д["id"], "sha": д["sha"], "створено": д["created_at"], "хто": д["creator"]["login"],
            "на_сайті": min(успіх) if успіх else None, "кінець": кінцеві[0] if кінцеві else None,
        })
    return вихід


def коміти(від, до, одн):
    вихід = []
    for к in сторінки("commits", {"sha": "main", "since": f"{від:%Y-%m-%dT%H:%M:%SZ}",
                                  "until": f"{до:%Y-%m-%dT%H:%M:%SZ}"}):
        файли = []
        for ф in сторінки(f"commits/{к['sha']}", {}, "files"):
            файли.append(ф["filename"])
            if ф.get("previous_filename"):
                файли.append(ф["previous_filename"])
        вихід.append({
            "sha": к["sha"], "час": к["commit"]["committer"]["date"], "хто": к["commit"]["author"]["name"],
            "назва": к["commit"]["message"].split("\n", 1)[0][:100], "файлів": len(файли),
            "сайт": any(сайт_pages.у_сайті(ф, одн) for ф in файли),
        })
    вихід.reverse()
    return вихід


def позиція(sha, порядок, від, до, кеш):
    if sha in порядок:
        return порядок[sha]
    if sha not in кеш:
        дані, _ = запит(f"commits/{sha}")
        кеш[sha] = час(дані["commit"]["committer"]["date"]) if дані else від
    return -1 if кеш[sha] < від else float("inf")


def main():
    п = argparse.ArgumentParser()
    п.add_argument("--від", required=True)
    п.add_argument("--до", required=True)
    п.add_argument("--json")
    п.add_argument("--ревізія", default="HEAD")
    а = п.parse_args()
    від, до = час(а.від), час(а.до)
    тепер = dt.datetime.now(dt.timezone.utc)
    одн = сайт_pages.одиниці(а.ревізія)

    звіт = {"вікно": [а.від, а.до], "виміряно": f"{тепер:%Y-%m-%dT%H:%M:%SZ}", "одиниці_сайта": одн, "процеси": {}}
    for назва, процес in (("вбудований", ВБУДОВАНИЙ), ("власний", ВЛАСНИЙ)):
        зап = запуски(процес, від, до)
        лічба = {}
        for з in зап:
            ключ = з["висновок"] or з["стан"]
            лічба[ключ] = лічба.get(ключ, 0) + 1
        тривалості = [хв(час(з["кінець"]) - час(з["почато"])) for з in зап
                      if з["висновок"] == "success" and з["почато"]]
        звіт["процеси"][назва] = {
            "запусків": len(зап), "висновки": лічба,
            "частка_success": round(100 * лічба.get("success", 0) / len(зап), 1) if зап else None,
            "тривалість_success_хв": [min(тривалості), statistics.median(тривалості), max(тривалості)]
            if тривалості else None,
            "запуски": зап,
        }

    розг = розгортання(від)
    у_вікні = [р for р in розг if від <= час(р["створено"]) <= до]
    лічба = {}
    for р in у_вікні:
        лічба[р["кінець"] or "не скінчилось"] = лічба.get(р["кінець"] or "не скінчилось", 0) + 1
    звіт["розгортання"] = {"у_вікні": len(у_вікні), "кінець": лічба, "усі": розг}

    ком = коміти(від, до, одн)
    порядок = {к["sha"]: і for і, к in enumerate(ком)}
    кеш = {}
    успішні = sorted((час(р["на_сайті"]), позиція(р["sha"], порядок, від, до, кеш), р["sha"])
                     for р in розг if р["на_сайті"])
    проміжки = []
    for і, к in enumerate(ком):
        if not к["сайт"]:
            continue
        тк = час(к["час"])
        дійшло = next(((т, sha) for т, поз, sha in успішні if поз >= і and т >= тк), None)
        проміжки.append({
            "sha": к["sha"], "час": к["час"], "назва": к["назва"],
            "на_сайті": f"{дійшло[0]:%Y-%m-%dT%H:%M:%SZ}" if дійшло else None,
            "розгортання": дійшло[1] if дійшло else None,
            "хв": хв((дійшло[0] if дійшло else тепер) - тк), "ще_не_на_сайті": not дійшло,
        })
    моменти = [від] + [т for т, _, _ in успішні if від <= т <= до] + [до]
    паузи = sorted(((хв(б - а_), f"{а_:%d.%m %H:%M}", f"{б:%d.%m %H:%M}") for а_, б in zip(моменти, моменти[1:])),
                   reverse=True)
    звіт["коміти"] = {"усього": len(ком), "міняють_сайт": len(проміжки), "перелік": ком}
    звіт["коміт_на_сайті"] = проміжки
    найдовший = max(проміжки, key=lambda п_: п_["хв"]) if проміжки else None
    звіт["найдовший_хв"] = найдовший["хв"] if найдовший else None
    звіт["паузи_між_розгортаннями"] = паузи[:5]

    print(f"вікно {а.від} – {а.до} (виміряно {звіт['виміряно']}), сайт на {а.ревізія}: {len(одн)} одиниць")
    for назва, д in звіт["процеси"].items():
        print(f"процес {назва}: запусків {д['запусків']}, висновки {д['висновки']}, success {д['частка_success']} %, "
              f"тривалість success (мін/медіана/макс, хв) {д['тривалість_success_хв']}")
    print(f"розгортань github-pages за вікно: {len(у_вікні)}, кінець {лічба}")
    print(f"комітів у main: {len(ком)}, з них міняють сайт: {len(проміжки)}")
    if найдовший:
        print(f"найдовший проміжок коміт → сайт: {найдовший['хв']} хв ({найдовший['sha'][:8]} {найдовший['час']}"
              f"{', ще не на сайті' if найдовший['ще_не_на_сайті'] else ''}: {найдовший['назва']})")
        понад = [п_ for п_ in проміжки if п_["хв"] > 20]
        print(f"комітів сайта довше 20 хв до сайта: {len(понад)} з {len(проміжки)}; "
              f"медіана {statistics.median(п_['хв'] for п_ in проміжки)} хв")
    print("найдовші паузи між успішними розгортаннями: "
          + "; ".join(f"{а_}→{б} ({т} хв)" for т, а_, б in звіт["паузи_між_розгортаннями"]))
    if а.json:
        with open(а.json, "w", encoding="utf-8") as ф:
            json.dump(звіт, ф, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
