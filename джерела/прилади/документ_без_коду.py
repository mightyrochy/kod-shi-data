# -*- coding: utf-8 -*-
"""Клас «документ без коду» (ядро, «Документ без коду зливається сам») і рішення кроку CI самозлиття.

python3 джерела/прилади/документ_без_коду.py --файли ФАЙЛ   # JSON файлів PR з API чи рядки `git diff --name-status`
python3 джерела/прилади/документ_без_коду.py --коміт SHA    # дифф коміту проти першого батька (історія злитих PR)
python3 джерела/прилади/документ_без_коду.py --самоперевірка
python3 джерела/прилади/документ_без_коду.py --рішення      # CI: відкриті PR → кандидати в $GITHUB_OUTPUT
python3 джерела/прилади/документ_без_коду.py --злити        # CI: кандидати з $KANDYDATY → squash з sha голови

Клас (правило — ядро; точний перелік — тут, і лише тут). PR — «документ», коли КОЖЕН змінений шлях (у
перейменуванні — обидва імені, у видаленні — старе) лежить у дозволеному місці:
  стан      — `аудит/СТАН.md`;
  дошка     — `аудит/БЕКЛОГ.md`, `аудит/дошка/**.md`;
  журнал    — `аудит/РІШЕННЯ_ВЛАСНИКА.md` (журнал власника; ядро, «Пам'ять»);
  наряди    — `аудит/наряди/<файл>.md`, крім нарядів, які читає код (`ІМЕНА_КОДУ`);
  передачі  — `аудит/передачі/<файл>.md|.txt`;
  звіт      — `аудит/<тека звітів>/<звіт>/**` (теки звітів — `ТЕКИ_ЗВІТІВ`): дані й скрипти проби — лише в теці
              звіту; файл просто в теці звітів — лише не скрипт, а в `аудит/проби/` — жоден (там скрипти CI, стенди
              обгортки, `живі_сцени.txt`, `живі_порядок.md`); тека чи файл, які код називає явно (`ІМЕНА_КОДУ`), — «ні».
Усе інше — «ні», зокрема: файли правил (ядро, адаптери, договори ролей, решта `аудит/*.md` верхнього рівня, додатки
`проби/живі_порядок.md`), паспорт кореня `аудит/корені/` (його `прилад:` і `база:` читає храповик у CI), обгортка й
адаптери `аудит/адаптери/`, усе, що виконують продукт, CI чи хук (`джерела/`, `.github/`, `.claude/`, `index.html`,
`build.txt`, каталог, `zhnyvarka/`, …), будь-яка прихована частина шляху (`.x/`), `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`
на будь-якій глибині (їх підхоплюють сесії), невідомий шлях. `ІМЕНА_КОДУ` звіряє тест з кодом репозиторію
(`тест_документ_без_коду.py`): нове ім'я в коді — тест червоний, доки його не внесено сюди.

Рішення CI (`рішення_pr`): PR відкритий, не чернетка, автор `mightyrochy`, голова й база — цей репозиторій, база
`main`, список файлів повний (API віддає до 3000), прилад — «документ», а перевірки голови завершені: останній запуск
кожного робочого процесу на події `pull_request` — `success` чи `skipped`, обов'язкові (`ОБОВ'ЯЗКОВІ`) є, кожен
check run (`filter=latest`) і кожен статус — так само. Злиття — squash з `sha` голови: змінилась голова — GitHub
відмовляє (409), конфлікт — 405; тоді нічого, лише причина в підсумку.

Код виходу: `--файли`/`--коміт` — 0 «документ», 1 «ні»; 2 — помилка приладу.
"""
import argparse
import fnmatch
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

РЕПОЗИТОРІЙ = "mightyrochy/kod-shi-data"
АВТОР = "mightyrochy"
БАЗА = "main"

ПРАВИЛА_БУДЬ_ДЕ = {"AGENTS.md", "CLAUDE.md", "CLAUDE.local.md", "GEMINI.md"}
ОКРЕМІ = {
    "аудит/СТАН.md": "стан",
    "аудит/БЕКЛОГ.md": "дошка",
    "аудит/РІШЕННЯ_ВЛАСНИКА.md": "журнал",
}
# Теки звітів: тека звіту — під ними; у `проби` файли верхнього рівня — код і додатки, тож лише теки.
ТЕКИ_ЗВІТІВ = ("проби", "перевірка", "перевірки", "виміри", "звіти", "витрати")
СКРИПТИ = (".py", ".pyw", ".js", ".mjs", ".cjs", ".ts", ".sh", ".bash", ".ps1", ".psm1", ".bat", ".cmd", ".rb",
           ".pl", ".php", ".lua", ".exe", ".dll", ".so", ".jar", ".wasm")
# Імена під дозволеними теками, які код (джерела/, .github/, .claude/, zhnyvarka/, обгортка, скрипти аудит/проби/)
# називає явно поза рядком коментаря — вхід продукту, CI, обгортки чи проби (коментар, що цитує звіт як доказ, —
# не читання). Звіряє тест; глоб — fnmatch.
ІМЕНА_КОДУ = {
    "проби": {
        "Е1-нічний-живий-20261107", "Е2-ремонт-шар", "автоживий-4411f70673afbfb20e780bd4f3764e830c51a582",
        "автоживий-bd628bb29a90637ae18833c92eceb8230bd9b995", "автоживий-проба", "архів", "б1", "жінки", "знімки",
        "знімок_входи", "нічні", "поверхня_212", "пс5_кадри", "річ-ознаки-прилад-поріг-0711",
        "річ_запис_каталог_2026_10_30",
    },
    "перевірка": {
        "2.1-Б", "4920", "5293", "935", "доробка_2028_2", "кольори_9858",
        "похибка_вимірів_тіла", "річ_колір_межі_крок26", "річ_колір_межі_крок27", "річ_колір_межі_сім_ї_20261105",
        "хук_фонові_завдання.md",
    },
    "перевірки": {
        "fokus_2", "per_492", "rozbir_0210", "typove_1", "vyb1", "vyrva_968", "доробка-1886", "доробка-53Б-журнал",
        "доробка-53Б-обрив",
    },
    "витрати": {"аналіз_1518.md", "аналіз_2910.md"},
    "передачі": {"2026-10-29_ранок_уроки.md"},
    "наряди": {
        "CI-храповик-кореня.md", "Приховані-розвідка.md", "автоживий.md", "автоперевірка.md", "код-у-хмарі.md",
        "крок.md", "стенд.md", "х.md",
    },
}
# Робочі процеси на `pull_request` без фільтра шляхів: їхній запуск на голові обов'язковий (тест звіряє з .github/).
ОБОВЯЗКОВІ = (".github/workflows/khrapovyk.yml", ".github/workflows/zbirka.yml",
              ".github/workflows/zhyvyi-ryadok.yml")
ДОБРІ = {"success", "skipped"}
МАКС_ФАЙЛІВ = 3000


def _ім_я_коду(тека, ім_я):
    return any(fnmatch.fnmatchcase(ім_я, з) for з in ІМЕНА_КОДУ.get(тека, ()))


def шлях(п):
    """(True, клас) чи (False, причина) для одного шляху від кореня репозиторію."""
    if not п or п.startswith("/") or "\\" in п or "\0" in п:
        return False, "невідомий шлях"
    ч = п.split("/")
    if any(not к or к in (".", "..") or к.startswith(".") for к in ч):
        return False, "прихована чи порожня частина шляху"
    if ч[-1] in ПРАВИЛА_БУДЬ_ДЕ:
        return False, "файл правил сесій"
    if п in ОКРЕМІ:
        return True, ОКРЕМІ[п]
    if ч[0] != "аудит" or len(ч) < 3:
        return False, "код, файл правил чи невідомий шлях"
    тека, ім_я = ч[1], ч[2]
    if тека == "дошка":
        return (True, "дошка") if п.endswith(".md") else (False, "не .md у дошці")
    if тека == "наряди":
        if len(ч) != 3 or not п.endswith(".md"):
            return False, "не наряд .md"
        return (False, "наряд, який читає код") if _ім_я_коду(тека, ім_я) else (True, "наряд")
    if тека == "передачі":
        if len(ч) != 3 or not п.endswith((".md", ".txt")):
            return False, "не передача .md чи .txt"
        return (False, "передача, яку читає код") if _ім_я_коду(тека, ім_я) else (True, "передачі")
    if тека in ТЕКИ_ЗВІТІВ:
        if _ім_я_коду(тека, ім_я):
            return False, "тека чи файл, які читає код"
        if len(ч) == 3:
            if тека == "проби":
                return False, "файл верхнього рівня аудит/проби (скрипти CI, стенди, додатки)"
            if п.lower().endswith(СКРИПТИ):
                return False, "скрипт поза текою звіту"
        return True, "звіт"
    return False, "тека аудит/ поза класом (корені, адаптери, історія, …)"


def вердикт(зміни):
    """зміни — [(статус, шлях, старий_шлях | None)] → (документ?, перший шлях-причина, причина)."""
    if not зміни:
        return False, "", "порожній список змін"
    for статус, п, старий in зміни:
        for к in (п, старий):
            if к is None:
                continue
            так, чому = шлях(к)
            if not так:
                return False, к, f"{чому} ({статус})"
    return True, "", "документ"


def з_api(файли):
    """Файли PR з `GET /pulls/N/files` → зміни."""
    return [(ф.get("status", "?"), ф["filename"], ф.get("previous_filename")) for ф in файли]


def з_name_status(текст):
    """Рядки `git diff --name-status` (R100\\tстарий\\tновий) → зміни."""
    зміни = []
    for р in текст.splitlines():
        if not р.strip():
            continue
        ч = р.split("\t")
        if ч[0][:1] in "RC" and len(ч) == 3:
            зміни.append((ч[0], ч[2], ч[1]))
        else:
            зміни.append((ч[0], ч[1], None))
    return зміни


def зміни_коміту(sha, корінь="."):
    вивід = subprocess.run(["git", "-c", "core.quotepath=off", "diff", "--name-status", "-M", f"{sha}^1", sha],
                           cwd=корінь, capture_output=True, text=True, check=True).stdout
    return з_name_status(вивід)


# ---------- рішення CI ----------

def _останні(запуски):
    """Останній запуск на кожен робочий процес (за id; скасовані старші конкурентністю не рахуються)."""
    за_шляхом = {}
    for з in запуски:
        шл = (з.get("path") or "").split("@")[0]
        if шл not in за_шляхом or з["id"] > за_шляхом[шл]["id"]:
            за_шляхом[шл] = з
    return за_шляхом


def перевірки_голови(голова, запуски, check_runs, статуси):
    """(усе зелене?, причина) для голови PR."""
    запуски = [з for з in запуски if з.get("head_sha") == голова and з.get("event") == "pull_request"]
    за_шляхом = _останні(запуски)
    for шл in ОБОВЯЗКОВІ:
        if шл not in за_шляхом:
            return False, f"нема запуску {шл} на голові"
    for шл, з in sorted(за_шляхом.items()):
        if з.get("status") != "completed":
            return False, f"запуск {шл} ще йде ({з.get('status')})"
        if з.get("conclusion") not in ДОБРІ:
            return False, f"запуск {шл}: {з.get('conclusion')}"
    for к in check_runs:
        if к.get("status") != "completed":
            return False, f"перевірка «{к.get('name')}» ще йде"
        if к.get("conclusion") not in ДОБРІ:
            return False, f"перевірка «{к.get('name')}»: {к.get('conclusion')}"
    останні_статуси = {}
    for с in статуси:  # API віддає новіші першими
        останні_статуси.setdefault(с.get("context"), с)
    for контекст, с in sorted(останні_статуси.items()):
        if с.get("state") != "success":
            return False, f"статус «{контекст}»: {с.get('state')}"
    return True, "перевірки голови зелені"


def рішення_pr(pr, файли, запуски, check_runs, статуси):
    """(злити?, причина) для одного PR за записаними відповідями API."""
    if pr.get("state") != "open":
        return False, "PR не відкритий"
    if pr.get("draft"):
        return False, "чернетка"
    if (pr.get("user") or {}).get("login") != АВТОР:
        return False, f"автор {(pr.get('user') or {}).get('login')}, не {АВТОР}"
    голова, база = pr.get("head") or {}, pr.get("base") or {}
    if ((голова.get("repo") or {}).get("full_name") != РЕПОЗИТОРІЙ
            or (база.get("repo") or {}).get("full_name") != РЕПОЗИТОРІЙ):
        return False, "голова чи база не з цього репозиторію (форк)"
    if база.get("ref") != БАЗА:
        return False, f"база {база.get('ref')}, не {БАЗА}"
    if pr.get("changed_files") is None or len(файли) != pr["changed_files"] or len(файли) >= МАКС_ФАЙЛІВ:
        return False, f"список файлів неповний ({len(файли)} з {pr.get('changed_files')})"
    так, перший, чому = вердикт(з_api(файли))
    if not так:
        return False, f"прилад: ні — {перший}: {чому}"
    return перевірки_голови(голова.get("sha"), запуски, check_runs, статуси)


class API:
    def __init__(self, токен, репозиторій, адреса="https://api.github.com"):
        self.токен, self.р, self.адреса = токен, репозиторій, адреса.rstrip("/")

    def запит(self, метод, шлях, тіло=None):
        дані = None if тіло is None else json.dumps(тіло).encode()
        з = urllib.request.Request(self.адреса + шлях, data=дані, method=метод, headers={
            "Authorization": f"Bearer {self.токен}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "samozlyttia-dokumenta"})
        try:
            with urllib.request.urlopen(з, timeout=60) as в:
                return в.status, json.loads(в.read() or b"null"), в.headers.get("Link", "")
        except urllib.error.HTTPError as п:
            try:
                return п.code, json.loads(п.read() or b"null"), ""
            except ValueError:
                return п.code, None, ""

    def усі(self, шлях, ключ=None, межа=30):
        """GET зі сторінками (per_page=100) до `межа` сторінок."""
        роздільник = "&" if "?" in шлях else "?"
        усе, сторінка = [], 1
        while сторінка <= межа:
            код, дані, link = self.запит("GET", f"{шлях}{роздільник}per_page=100&page={сторінка}")
            if код != 200:
                raise RuntimeError(f"GET {шлях}: {код} {дані}")
            частина = дані[ключ] if ключ else дані
            усе.extend(частина)
            if 'rel="next"' not in link:
                break
            сторінка += 1
        return усе


def обійти(api):
    """Відкриті PR → [(номер, голова, злити?, причина)]."""
    р = f"/repos/{api.р}"
    підсумок = []
    for коротко in api.усі(f"{р}/pulls?state=open&base={БАЗА}"):
        if коротко.get("draft") or (коротко.get("user") or {}).get("login") != АВТОР:
            continue
        if ((коротко.get("head") or {}).get("repo") or {}).get("full_name") != РЕПОЗИТОРІЙ:
            continue
        н = коротко["number"]
        код, pr, _ = api.запит("GET", f"{р}/pulls/{н}")
        if код != 200:
            підсумок.append((н, "", False, f"GET PR: {код}"))
            continue
        голова = pr["head"]["sha"]
        файли = api.усі(f"{р}/pulls/{н}/files")
        if not вердикт(з_api(файли))[0] or len(файли) != pr.get("changed_files"):
            так, чому = рішення_pr(pr, файли, [], [], [])
            підсумок.append((н, голова, так, чому))
            continue
        запуски = api.усі(f"{р}/actions/runs?head_sha={голова}&event=pull_request", "workflow_runs", 3)
        check_runs = api.усі(f"{р}/commits/{голова}/check-runs?filter=latest", "check_runs", 5)
        статуси = api.усі(f"{р}/commits/{голова}/statuses", None, 3)
        так, чому = рішення_pr(pr, файли, запуски, check_runs, статуси)
        підсумок.append((н, голова, так, чому))
    return підсумок


def злити(api, кандидати):
    """Кандидати [{номер, голова}] → (злито [(номер, sha злиття)], перед, рядки підсумку)."""
    р = f"/repos/{api.р}"
    код, реф, _ = api.запит("GET", f"{р}/git/ref/heads/{БАЗА}")
    перед = (реф or {}).get("object", {}).get("sha", "") if код == 200 else ""
    злито, рядки = [], []
    for к in кандидати:
        н, голова = int(к["номер"]), к["голова"]
        код, pr, _ = api.запит("GET", f"{р}/pulls/{н}")
        if код != 200 or pr.get("state") != "open" or pr.get("draft") or pr["head"]["sha"] != голова:
            рядки.append(f"#{н}: не злито — PR змінився після рішення (стан, чернетка чи голова)")
            continue
        код, відповідь, _ = api.запит("PUT", f"{р}/pulls/{н}/merge", {
            "sha": голова, "merge_method": "squash", "commit_title": f"{pr['title']} (#{н})"})
        if код == 200 and (відповідь or {}).get("merged"):
            злито.append((н, відповідь["sha"]))
            рядки.append(f"#{н}: злито squash з голови {голова} → {відповідь['sha']}")
        else:
            рядки.append(f"#{н}: не злито — {код} {(відповідь or {}).get('message', '')}")
    return злито, перед, рядки


def _вихід(**пари):
    шлях_виходу = os.environ.get("GITHUB_OUTPUT")
    if шлях_виходу:
        with open(шлях_виходу, "a", encoding="utf-8") as ф:
            for к, з in пари.items():
                ф.write(f"{к}={з}\n")


def _підсумок(рядки):
    шлях_підсумку = os.environ.get("GITHUB_STEP_SUMMARY")
    текст = "\n".join(рядки) + "\n"
    print(текст, end="")
    if шлях_підсумку:
        with open(шлях_підсумку, "a", encoding="utf-8") as ф:
            ф.write(текст)


def _api_з_середовища():
    return API(os.environ["GH_TOKEN"], os.environ.get("GITHUB_REPOSITORY", РЕПОЗИТОРІЙ),
               os.environ.get("GITHUB_API_URL", "https://api.github.com"))


# ---------- самоперевірка ----------

САМО = [
    ("аудит/СТАН.md", True), ("аудит/БЕКЛОГ.md", True), ("аудит/РІШЕННЯ_ВЛАСНИКА.md", True),
    ("аудит/дошка/claude/x.md", True), ("аудит/дошка/x.txt", False), ("аудит/наряди/Е2-крок.md", True),
    ("аудит/наряди/автоживий.md", False), ("аудит/наряди/x/y.md", False), ("аудит/передачі/2026-11-12.md", True),
    ("аудит/проби/звіт-1211/ЗВІТ.md", True), ("аудит/проби/звіт-1211/проба.py", True),
    ("аудит/проби/живий_після_CI.js", False), ("аудит/проби/живі_сцени.txt", False),
    ("аудит/проби/живі_порядок.md", False), ("аудит/проби/нічні/x.json", False), ("аудит/проби/жінки/ж.json", False),
    ("аудит/перевірки/перевірка-1211-8.md", True), ("аудит/перевірки/проба.py", False),
    ("аудит/перевірка/звіт/a.py", True), ("аудит/виміри/x/y.json", True), ("аудит/корені/Е2.md", False),
    ("аудит/адаптери/gemini/ЧЕРГА.md", False), ("аудит/ДИСПЕТЧЕР.md", False), ("аудит/КАРТИНА.md", False),
    ("аудит/ПРОДУКТ.md", False), ("аудит/дошка_звірка.py", False), ("AGENTS.md", False), ("CLAUDE.md", False),
    ("README.md", False), ("index.html", False), ("build.txt", False), ("джерела/x.py", False),
    (".github/workflows/x.yml", False), (".claude/settings.json", False), ("каталог_повний.xml.gz", False),
    ("аудит/проби/звіт/CLAUDE.md", False), ("аудит/проби/звіт/.claude/settings.json", False),
    ("аудит/проби/звіт/../../джерела/x.py", False), ("аудит/живі_12/x.md", False), ("", False),
]


def самоперевірка():
    вади = [(п, о) for п, о in САМО if шлях(п)[0] != о]
    вади += [("вердикт R", None)] if вердикт([("R100", "аудит/СТАН.md", "аудит/КАРТИНА.md")])[0] else []
    вади += [("вердикт D", None)] if вердикт([("D", "джерела/x.py", None)])[0] else []
    вади += [("вердикт A", None)] if not вердикт([("A", "аудит/наряди/x.md", None)])[0] else []
    for п, о in вади:
        print(f"ВАДА самоперевірки: {п} — очікувано {о}")
    print(f"самоперевірка: випадків {len(САМО) + 3}, вад {len(вади)}")
    return 1 if вади else 0


def main(argv=None):
    а = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    г = а.add_mutually_exclusive_group(required=True)
    г.add_argument("--файли")
    г.add_argument("--коміт")
    г.add_argument("--самоперевірка", action="store_true")
    г.add_argument("--рішення", action="store_true")
    г.add_argument("--злити", action="store_true")
    п = а.parse_args(argv)
    if п.самоперевірка:
        return самоперевірка()
    if п.файли or п.коміт:
        if п.коміт:
            зміни = зміни_коміту(п.коміт)
        else:
            текст = sys.stdin.read() if п.файли == "-" else open(п.файли, encoding="utf-8").read()
            зміни = з_api(json.loads(текст)) if текст.lstrip().startswith("[") else з_name_status(текст)
        так, перший, чому = вердикт(зміни)
        print("документ" if так else f"ні: {перший} — {чому}")
        return 0 if так else 1
    api = _api_з_середовища()
    if п.рішення:
        if самоперевірка():
            _вихід(kandydaty="[]")
            return 2
        підсумок = обійти(api)
        кандидати = [{"номер": н, "голова": г} for н, г, так, _ in підсумок if так]
        _підсумок(["### Самозлиття документа: рішення", ""] +
                  [f"- #{н} `{г[:8]}`: {'ЗЛИТИ' if так else 'не зливати'} — {чому}" for н, г, так, чому in підсумок]
                  + ([] if підсумок else ["- відкритих PR-кандидатів нема"]))
        _вихід(kandydaty=json.dumps(кандидати, ensure_ascii=False))
        return 0
    кандидати = json.loads(os.environ.get("KANDYDATY") or "[]")
    злито, перед, рядки = злити(api, кандидати)
    _підсумок(["### Самозлиття документа: злиття", ""] + [f"- {р}" for р in рядки])
    _вихід(zlyto="true" if злито else "false", pered=перед, pislia=злито[-1][1] if злито else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
