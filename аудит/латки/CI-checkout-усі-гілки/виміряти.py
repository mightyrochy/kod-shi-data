"""Збирає всі спроби запусків zbirka.yml за 31.10–03.11 UTC через GitHub API."""

import concurrent.futures
import collections
import datetime
import gzip
import hashlib
import json
import pathlib
import re
import statistics
import subprocess
import sys

РЕПО = "repos/mightyrochy/kod-shi-data"
ПЕРІОД = "2026-10-31T00:00:00Z..2026-11-03T23:59:59Z"


def апі(шлях):
    """Читає всі сторінки API, зупиняючись на помилці доступу."""
    процес = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", шлях],
        capture_output=True, check=True, encoding="utf-8",
    )
    return json.loads(процес.stdout)


def записати(шлях, дані):
    """Зберігає відтворюваний знімок відповіді API."""
    with gzip.open(шлях, "wt", encoding="utf-8") as файл:
        json.dump(дані, файл, ensure_ascii=False, separators=(",", ":"))


def читати(шлях):
    """Читає вже збережений знімок без повторного запиту."""
    with gzip.open(шлях, "rt", encoding="utf-8") as файл:
        return json.load(файл)


def зібрати(тека):
    """Знімає всі jobs і steps усіх спроб, а не лише останньої."""
    тека.mkdir(parents=True, exist_ok=True)
    шлях = тека / "запуски.json.gz"
    if not шлях.exists():
        сторінки = апі(f"{РЕПО}/actions/workflows/zbirka.yml/runs?created={ПЕРІОД}&per_page=100")
        запуски = [запуск for сторінка in сторінки for запуск in сторінка["workflow_runs"]]
        assert len(запуски) == сторінки[0]["total_count"] < 1000
        assert len({запуск["id"] for запуск in запуски}) == len(запуски)
        записати(шлях, запуски)
    запуски = читати(шлях)
    спроби = [(запуск["id"], номер) for запуск in запуски
              for номер in range(1, запуск["run_attempt"] + 1)]

    def спроба(вхід):
        """Зберігає повні jobs однієї спроби разом із часовими мітками steps."""
        запуск, номер = вхід
        шлях = тека / f"{запуск}-{номер}.json.gz"
        if not шлях.exists():
            сторінки = апі(f"{РЕПО}/actions/runs/{запуск}/attempts/{номер}/jobs?per_page=100")
            роботи = [робота for сторінка in сторінки for робота in сторінка["jobs"]]
            assert len(роботи) == сторінки[0]["total_count"]
            записати(шлях, роботи)
        return len(читати(шлях))

    кількість = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as пул:
        for номер, результат in enumerate(пул.map(спроба, спроби), 1):
            кількість += результат
            if номер % 50 == 0 or номер == len(спроби):
                print(f"Спроб: {номер}/{len(спроби)}; jobs: {кількість}", flush=True)
    print(f"Запусків: {len(запуски)}; спроб: {len(спроби)}; jobs: {кількість}")


def анотації(тека):
    """Читає причини всіх невдалих jobs, щоб відрізнити тайм-аут від concurrency."""
    роботи = []
    for шлях in тека.glob("*-*.json.gz"):
        роботи.extend(читати(шлях))
    кандидати = [робота for робота in роботи
                 if робота["conclusion"] not in {"success", "skipped"}]
    вихід = тека / "annotations"
    вихід.mkdir(exist_ok=True)

    def зняти(робота):
        """Зберігає всі сторінки анотацій одного check-run."""
        шлях = вихід / f"{робота['id']}.json.gz"
        if not шлях.exists():
            сторінки = апі(робота["check_run_url"] + "/annotations?per_page=100")
            записати(шлях, [рядок for сторінка in сторінки for рядок in сторінка])
        return len(читати(шлях))

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as пул:
        for номер, результат in enumerate(пул.map(зняти, кандидати), 1):
            if номер % 50 == 0 or номер == len(кандидати):
                print(f"Анотації jobs: {номер}/{len(кандидати)}", flush=True)


def підсумувати(тека):
    """Зберігає повний знімок API й числа з однозначними знаменниками."""
    вихід = pathlib.Path(__file__).resolve().parent
    if тека.is_file():
        знімок = читати(тека)
        запуски, спроби, пояснення = знімок["запуски"], знімок["спроби"], знімок["анотації"]
    else:
        запуски = читати(тека / "запуски.json.gz")
        спроби = []
        for шлях in sorted(тека.glob("*-*.json.gz")):
            запуск, номер = шлях.name.removesuffix(".json.gz").split("-")
            спроби.append({"run_id": int(запуск), "attempt": int(номер), "jobs": читати(шлях)})
        роботи = [робота for спроба in спроби for робота in спроба["jobs"]]
        пояснення = {str(робота["id"]): читати(тека / "annotations" / f"{робота['id']}.json.gz")
                     for робота in роботи if робота["conclusion"] not in {"success", "skipped"}}
        знімок = {"період_UTC": ПЕРІОД, "запуски": запуски, "спроби": спроби, "анотації": пояснення}
        записати(вихід / "api.json.gz", знімок)
    assert len(спроби) == sum(запуск["run_attempt"] for запуск in запуски)
    роботи = [робота for спроба in спроби for робота in спроба["jobs"]]
    assert len({робота["id"] for робота in роботи}) == len(роботи)

    def секунд(початок, кінець):
        """Віднімає часові мітки GitHub API в UTC."""
        return (datetime.datetime.fromisoformat(кінець) - datetime.datetime.fromisoformat(початок)).total_seconds()

    def статистика(кроки):
        """Підсумовує фактичний час, включно з перерваними checkout."""
        часи = [крок["секунд"] for крок in кроки]
        return {"кількість": len(часи), "медіана_с": statistics.median(часи) if часи else None,
                "максимум_с": max(часи, default=None), "понад_180_с": sum(час > 180 for час in часи)}

    таймаути = []
    checkout = []
    пропущено = 0
    for робота in роботи:
        повідомлення = [рядок["message"] for рядок in пояснення.get(str(робота["id"]), [])]
        if any(re.search(r"job.*(?:exceeded.*maximum execution time|timed out)", рядок, re.I)
               for рядок in повідомлення):
            таймаути.append(робота["id"])
        for крок in робота.get("steps", []):
            if "actions/checkout@" not in крок["name"] or крок["name"].startswith("Post "):
                continue
            if крок["conclusion"] == "skipped":
                пропущено += 1
                continue
            assert крок["started_at"] and крок["completed_at"]
            checkout.append({"job_id": робота["id"], "run_id": робота["run_id"],
                             "name": робота["name"], "conclusion": крок["conclusion"],
                             "started_at": крок["started_at"], "completed_at": крок["completed_at"],
                             "секунд": секунд(крок["started_at"], крок["completed_at"])})
    групи = collections.defaultdict(list)
    дати = collections.defaultdict(list)
    дата_запуску = {запуск["id"]: запуск["created_at"][:10] for запуск in запуски}
    for крок in checkout:
        групи[re.sub(r" \(\d+\)$", "", крок["name"])].append(крок)
        дати[дата_запуску[крок["run_id"]]].append(крок)
    фази_таймаутів = collections.Counter()
    for робота in роботи:
        if робота["id"] in таймаути:
            for крок in робота.get("steps", []):
                if крок["conclusion"] == "cancelled" and not крок["name"].startswith("Post "):
                    фази_таймаутів[крок["name"]] += 1
    розпочаті = sum(робота["conclusion"] != "skipped" for робота in роботи)
    числа = {"період_UTC": ПЕРІОД, "запусків": len(запуски), "спроб": len(спроби), "jobs": len(роботи),
             "стани_jobs": dict(collections.Counter(робота["conclusion"] for робота in роботи)),
             "checkout": статистика(checkout),
             "checkout_успішні": статистика([крок for крок in checkout if крок["conclusion"] == "success"]),
             "checkout_стани": dict(collections.Counter(крок["conclusion"] for крок in checkout)),
             "checkout_пропущені": пропущено, "таймаути_jobs": len(таймаути),
             "частка_таймаутів_усі_jobs": len(таймаути) / len(роботи),
             "розпочаті_jobs": розпочаті, "частка_таймаутів_розпочаті_jobs": len(таймаути) / розпочаті,
             "таймаути_під_час_checkout": sum(крок["job_id"] in таймаути and крок["conclusion"] != "success"
                                               for крок in checkout),
             "фази_таймаутів": dict(фази_таймаутів),
             "за_job": {група: статистика(кроки) for група, кроки in sorted(групи.items())},
             "за_датою": {дата: статистика(кроки) for дата, кроки in sorted(дати.items())},
             "найдовші": sorted(checkout, key=lambda крок: крок["секунд"], reverse=True)[:10],
             "таймаути_job_ids": таймаути,
             "api_sha256": hashlib.sha256((вихід / "api.json.gz").read_bytes()).hexdigest()}
    (вихід / "числа.json").write_text(json.dumps(числа, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(числа, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "annotations":
        анотації(pathlib.Path(sys.argv[1]))
    elif len(sys.argv) > 2 and sys.argv[2] == "summary":
        підсумувати(pathlib.Path(sys.argv[1]))
    else:
        зібрати(pathlib.Path(sys.argv[1]))
