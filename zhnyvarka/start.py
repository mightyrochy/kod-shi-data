# -*- coding: utf-8 -*-
"""Запускач жниварки для ноутбука. Дві дії людини: подвійний клік увечері, надіслати zip зранку
(або й це не треба — якщо поруч лежить github_token.txt, результат викладається сам).

Що робить сам, без питань:
 1. Оновлює жниварка.py, магазини.tsv і себе з GitHub (тека zhnyvarka/ у repo kod-shi-data);
    без інтернету/без файлів у repo — працює з тим, що лежить поруч.
 2. Якщо попередній прогін обірвано (закрите вікно, вимкнений ноутбук) — пакує його в zip
    «…_незавершений.zip», щоб нічого не пропало. Та сама версія → продовжує; нова версія → заново.
 3. Проба (3 картки з магазину, ~5 хв) → якщо жоден магазин не дав речей, зупиняється.
 4. Повний прогін зі стелею 10 годин → zip → виклад у GitHub, якщо є токен.
"""
import base64, datetime, glob, hashlib, io, json, os, shutil, subprocess, sys, zipfile
from urllib.parse import quote

ВЕРСІЯ_ЗАПУСКАЧА = "start 3.3 · 2026-09-06"
REPO = "mightyrochy/kod-shi-data"
ТЕКА_У_REPO = "zhnyvarka"                       # ASCII: цю адресу читає і .bat через curl
RAW = "https://raw.githubusercontent.com/%s/main/%s/" % (REPO, ТЕКА_У_REPO)
ФАЙЛИ_ОНОВЛЕННЯ = ("жниварка.py", "магазини.tsv", "start.py")
МАРКЕР = "прогін_іде.txt"
ТУТ = os.path.dirname(os.path.abspath(__file__))
ТИХО = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def лог(*x):
    print(*x, flush=True)
    try:
        with io.open(os.path.join(ТУТ, "лог_жнив.txt"), "a", encoding="utf-8") as f:
            f.write(" ".join(str(y) for y in x) + "\n")
    except OSError:
        pass


def md5(шлях):
    try:
        return hashlib.md5(open(os.path.join(ТУТ, шлях), "rb").read()).hexdigest()[:12]
    except OSError:
        return "—"


def є(модуль):
    try:
        __import__(модуль); return True
    except ImportError:
        return False


def pip(*пакети):
    for додатково in (["--user"], [], ["--break-system-packages"]):
        if subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", *додатково, *пакети], **ТИХО).returncode == 0:
            return True
    return False


def бібліотеки():
    бракує = [пакет for модуль, пакет in (("requests", "requests"), ("bs4", "beautifulsoup4")) if not є(модуль)]
    if бракує or not є("lxml"):
        if subprocess.run([sys.executable, "-m", "pip", "--version"], **ТИХО).returncode != 0:
            subprocess.run([sys.executable, "-m", "ensurepip", "--user"], **ТИХО)
        лог("Ставлю бібліотеки:", ", ".join(бракує + ([] if є("lxml") else ["lxml"])), "…")
    if бракує and not pip(*бракує):
        лог("!! Не вдалося поставити %s — перевірте інтернет і запустіть ще раз." % ", ".join(бракує))
        input("Enter для виходу"); sys.exit(1)
    if not є("lxml") and not pip("lxml"):
        лог("lxml не став — жниварка піде на вбудованому парсері: повільніше, але працює.")


# ── 1. оновлення з GitHub ────────────────────────────────────────────────────────
def оновити_з_github(файли=ФАЙЛИ_ОНОВЛЕННЯ):
    """→ True, якщо start.py змінився (тоді перезапуск). Без мережі — тихо працюємо з локальними."""
    try:
        import requests
    except ImportError:
        return False
    змінився_start = False
    for ім in файли:
        try:
            r = requests.get(RAW + quote(ім), timeout=(10, 30))
        except Exception as e:                       # noqa
            лог("GitHub недоступний (%s) — працюю з локальними файлами" % type(e).__name__); return False
        if r.status_code != 200 or not r.content or len(r.content) < 200:
            лог("GitHub: %s не викладено (HTTP %s) — лишаю локальний" % (ім, r.status_code)); continue
        шлях = os.path.join(ТУТ, ім)
        новий = r.content
        if os.path.exists(шлях) and open(шлях, "rb").read() == новий:
            continue
        if ім == "start.py" and "ВЕРСІЯ_ЗАПУСКАЧА" not in новий.decode("utf-8", "replace"):
            лог("GitHub: start.py виглядає не як запускач — пропускаю"); continue
        if ім == "жниварка.py" and "def зібрати_магазин" not in новий.decode("utf-8", "replace"):
            лог("GitHub: жниварка.py виглядає не як жниварка — пропускаю"); continue
        with open(шлях + ".new", "wb") as f:
            f.write(новий)
        os.replace(шлях + ".new", шлях)
        лог("оновлено з GitHub: %s (%s)" % (ім, md5(ім)))
        if ім == "start.py":
            змінився_start = True
    return змінився_start


# ── 2. попередній прогін ─────────────────────────────────────────────────────────
def версія_жниварки():
    try:
        т = io.open(os.path.join(ТУТ, "жниварка.py"), encoding="utf-8").read()
        i = т.index("ВЕРСІЯ = "); return т[i:i + 80].split('"')[1]
    except Exception:                                # noqa
        return "?"


def версія_сирих(тека):
    import gzip
    for ім in sorted(glob.glob(os.path.join(тека, "*.json.gz")))[:3]:
        try:
            д = json.load(gzip.open(ім, "rt", encoding="utf-8"))
            return д.get("діаг", {}).get("версія") or "стара (до 3.2)"
        except Exception:                            # noqa
            continue
    return None


def запакувати(назва, теки, файли):
    шлях = os.path.join(ТУТ, назва)
    with zipfile.ZipFile(шлях, "w", zipfile.ZIP_DEFLATED) as z:
        for тека in теки:
            for корінь, _, фф in os.walk(os.path.join(ТУТ, тека)):
                for ф in фф:
                    повний = os.path.join(корінь, ф)
                    z.write(повний, os.path.relpath(повний, ТУТ))
        for ф in файли:
            if os.path.exists(os.path.join(ТУТ, ф)):
                z.write(os.path.join(ТУТ, ф), ф)
    return шлях


def прибрати_попередній():
    """Обірваний прогін → zip «…_незавершений»; «продовжити / заново» — без питань. → аргумент або None."""
    сирі = os.path.join(ТУТ, "жнива_сирі")
    є_сирі = bool(glob.glob(os.path.join(сирі, "*.json.gz")))
    обірвано = os.path.exists(os.path.join(ТУТ, МАРКЕР))
    if not є_сирі:
        return None
    if обірвано:
        ім = "жнива_%s_незавершений.zip" % datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        запакувати(ім, ("жнива", "жнива_сирі", "жнива_проба"), ("лог_жнив.txt",))
        лог("Попередній прогін було обірвано — спаковано в %s (надішліть і його)." % ім)
    v_сирих, v_тепер = версія_сирих(сирі), версія_жниварки()
    if v_сирих == v_тепер and обірвано:
        лог("Та сама версія жниварки (%s) — продовжую з місця зупинки." % v_тепер)
        return "--продовжити"
    старе = os.path.join(ТУТ, "старі_жнива", datetime.datetime.now().strftime("%Y-%m-%d_%H%M"))
    os.makedirs(старе, exist_ok=True)
    for тека in ("жнива_сирі", "жнива", "жнива_проба"):
        if os.path.isdir(os.path.join(ТУТ, тека)):
            shutil.move(os.path.join(ТУТ, тека), os.path.join(старе, тека))
    лог("Версія жниварки інша (%s → %s) або прогін був завершений — починаю заново; старе лежить у %s"
        % (v_сирих, v_тепер, os.path.relpath(старе, ТУТ)))
    return None


# ── 3–4. проба, повний прогін, виклад ────────────────────────────────────────────
def підсумок_проби(шлях_journal):
    магазинів = відповіли = речей = 0
    try:
        рядки = open(шлях_journal, encoding="utf-8").read().splitlines()[1:]
    except OSError:
        return 0, 0, 0
    for р in рядки:
        к = р.split("\t")
        if len(к) < 8:
            continue
        магазинів += 1
        try:
            n = int(к[6])
        except ValueError:
            n = 0
        речей += n; відповіли += 1 if n > 0 else 0
    return магазинів, відповіли, речей


def викласти_у_github(дата, сесія=None):
    """Опційно: github_token.txt поруч → результат у repo, тека zhnyvarka/жнива_<дата>/. Без токена — нічого."""
    токен_шлях = os.path.join(ТУТ, "github_token.txt")
    if not os.path.exists(токен_шлях):
        return False
    токен = open(токен_шлях, encoding="utf-8").read().strip()
    if len(токен) < 20:
        return False
    import gzip, requests
    s = сесія or requests
    заг = {"Authorization": "Bearer " + токен, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    r = s.get("https://api.github.com/repos/%s" % REPO, headers=заг, timeout=30)
    if r.status_code != 200:
        лог("GitHub-токен не приймається (HTTP %s) — результат надішліть вручну." % r.status_code); return False

    def покласти(шлях_у_repo, байти):
        url = "https://api.github.com/repos/%s/contents/%s" % (REPO, quote(шлях_у_repo))
        sha = None
        g = s.get(url, headers=заг, timeout=30)
        if g.status_code == 200:
            sha = g.json().get("sha")
        тіло = {"message": "жнива %s: %s" % (дата, os.path.basename(шлях_у_repo)), "content": base64.b64encode(байти).decode("ascii")}
        if sha:
            тіло["sha"] = sha
        p = s.put(url, headers=заг, json=тіло, timeout=180)
        return 1 if p.status_code in (200, 201) else 0
    ок = зб = 0
    тека_repo = "%s/жнива_%s" % (ТЕКА_У_REPO, дата)
    for ім in ("звіт_жнив.md", "journal_жнив.tsv"):
        ф = os.path.join(ТУТ, "жнива", ім)
        if os.path.exists(ф):
            зб += 1; ок += покласти("%s/%s" % (тека_repo, ім), open(ф, "rb").read())
    for ім in ("каталог_повний.xml", "каталог_чоловічий.xml", "карантин.xml"):
        ф = os.path.join(ТУТ, "жнива", ім)
        if os.path.exists(ф):
            зб += 1; ок += покласти("%s/%s.gz" % (тека_repo, ім), gzip.compress(open(ф, "rb").read()))
    for ф in sorted(glob.glob(os.path.join(ТУТ, "жнива_сирі", "*.json.gz"))):
        зб += 1; ок += покласти("%s/сирі/%s" % (тека_repo, os.path.basename(ф)), open(ф, "rb").read())
    ф = os.path.join(ТУТ, "лог_жнив.txt")
    if os.path.exists(ф):
        зб += 1; ок += покласти("%s/лог_жнив.txt" % тека_repo, open(ф, "rb").read())
    лог("Викладено в GitHub: %d із %d файлів → %s" % (ок, зб, тека_repo))
    return ок == зб and зб > 0


def main(без_мережі=False):
    os.chdir(ТУТ)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                # noqa
        pass
    лог("=== %s · Python %s · %s ===" % (ВЕРСІЯ_ЗАПУСКАЧА, sys.version.split()[0], datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    if sys.version_info < (3, 9):
        лог("!! Потрібен Python 3.9 або новіший."); return 1
    бібліотеки()
    if not без_мережі and os.environ.get("ЖНИВАРКА_БЕЗ_ОНОВЛЕННЯ") != "1" and оновити_з_github():
        лог("start.py оновлено — перезапускаюсь.")
        os.environ["ЖНИВАРКА_БЕЗ_ОНОВЛЕННЯ"] = "1"
        return subprocess.run([sys.executable, os.path.join(ТУТ, "start.py")]).returncode
    лог("жниварка: %s (%s) · магазини.tsv %s" % (версія_жниварки(), md5("жниварка.py"), md5("магазини.tsv")))
    продовжити = прибрати_попередній()
    дата = datetime.date.today().isoformat()
    with io.open(os.path.join(ТУТ, МАРКЕР), "w", encoding="utf-8") as f:
        f.write(datetime.datetime.now().isoformat())
    лог("\nЖниварка працює. Не закривайте це вікно. Ноутбук має бути в розетці.\n")
    код = 0
    if not продовжити:
        лог("=== Проба: по 3 картки з кожного магазину, ~5 хвилин ===")
        shutil.rmtree("жнива_сирі_проба", ignore_errors=True)
        subprocess.run([sys.executable, "жниварка.py", "--режим", "проба", "--стеля", "3", "--вихід", "жнива_проба",
                        "--сирі", "жнива_сирі_проба", "--потоки", "4", "--лог", "лог_жнив.txt"])
        магазинів, відповіли, речей = підсумок_проби(os.path.join("жнива_проба", "journal_жнив.tsv"))
        лог("\n=== Проба: магазинів %d, дали речі %d, прийнято %d речей ===" % (магазинів, відповіли, речей))
        if відповіли == 0:
            лог("!! Жоден магазин не дав речей. Повний прогін не запускаю."); код = 3
        else:
            лог("Проба пройшла — запускаю повний прогін (стеля 10 годин, далі добере наступна ніч).\n")
    if код == 0:
        # 05.09: 4,7 с на картку (половина — HEAD фото) → фото у кожної 5-ї, 4 потоки, стеля 10 год
        арг = ["--режим", "повний", "--вихід", "жнива", "--потоки", "4", "--лог", "лог_жнив.txt", "--фото-кожен", "5", "--дедлайн-хвилин", "600"]
        if продовжити:
            арг.append(продовжити)
        try:
            код = subprocess.run([sys.executable, "жниварка.py", *арг]).returncode
        except KeyboardInterrupt:
            лог("\nЗупинено вручну — пакую те, що є.")
            subprocess.run([sys.executable, "жниварка.py", "--зібрати", "--вихід", "жнива"]); код = 4
    if os.path.exists(os.path.join(ТУТ, МАРКЕР)):
        os.remove(os.path.join(ТУТ, МАРКЕР))
    назва_zip = "жнива_%s.zip" % дата
    запакувати(назва_zip, ("жнива", "жнива_сирі", "жнива_проба"), ("лог_жнив.txt",))
    викладено = False
    if not без_мережі:
        try:
            викладено = викласти_у_github(дата)
        except Exception as e:                       # noqa
            лог("Виклад у GitHub не вдався (%s) — надішліть zip вручну." % type(e).__name__)
    стан = {0: "ГОТОВО", 3: "ЗУПИНЕНО ПІСЛЯ ПРОБИ (жоден магазин не дав речей)", 4: "ЗУПИНЕНО ВРУЧНУ"}.get(код, "ЗАВЕРШЕНО З ПОМИЛКОЮ (код %s)" % код)
    лог("\n%s." % стан)
    if викладено:
        лог("Результат уже викладено в GitHub — надсилати нічого не треба.")
    else:
        лог("Надішліть файл %s — він лежить поруч із цим файлом." % назва_zip)
    return код


if __name__ == "__main__":
    код = main()
    try:
        input("Enter, щоб закрити вікно")
    except EOFError:
        pass
    sys.exit(код)
