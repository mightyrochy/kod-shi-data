"""Зберігає одноразовий публічний знімок ідентичності PR, CI та рецензій голови."""
from concurrent.futures import ThreadPoolExecutor
import datetime
import json
from pathlib import Path
import urllib.request

ГОЛОВА = "6d36c9f12b845cd8d67fe0aab9e1eaee6b01e38c"


def main():
    """Читає лише публічний API без токена й не виконує жодних записів у GitHub."""
    основа = "https://api.github.com/repos/mightyrochy/kod-shi-data/"
    адреси = ["pulls/2085", f"commits/{ГОЛОВА}/check-runs?per_page=100",
              f"commits/{ГОЛОВА}/status", "pulls/2085/reviews?per_page=100"]
    def отримати(адреса):
        """Читає JSON офіційного API з кінцевою межею часу."""
        запит = urllib.request.Request(основа + адреса, headers={"User-Agent": "review-2085", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(запит, timeout=30) as відповідь:
            return json.load(відповідь)
    with ThreadPoolExecutor(max_workers=4) as пул:
        пр, перевірки, статус, рецензії = list(пул.map(отримати, адреси))
    дані = dict(час_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), адреси=адреси,
        pr=dict(номер=пр["number"], автор=пр["user"]["login"], стан=пр["state"],
                база=пр["base"]["ref"], репо_бази=пр["base"]["repo"]["full_name"], sha_бази=пр["base"]["sha"],
                репо_голови=пр["head"]["repo"]["full_name"], sha_голови=пр["head"]["sha"]),
        ci=[dict(назва=к["name"], sha=к["head_sha"], стан=к["status"], висновок=к["conclusion"],
                 url=к["html_url"]) for к in перевірки["check_runs"]],
        commit_status=dict(стан=статус["state"], кількість=статус["total_count"]),
        рецензії=[dict(автор=р["user"]["login"], sha=р["commit_id"], стан=р["state"], url=р["html_url"]) for р in рецензії])
    Path(__file__).with_name("стан_github.json").write_text(json.dumps(дані, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(дані, ensure_ascii=False, indent=2))
    assert дані["pr"]["автор"] == "mightyrochy"
    assert дані["pr"]["репо_бази"] == дані["pr"]["репо_голови"] == "mightyrochy/kod-shi-data"
    assert дані["pr"]["база"] == "main" and дані["pr"]["sha_голови"] == ГОЛОВА


if __name__ == "__main__":
    main()
