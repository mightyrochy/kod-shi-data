# -*- coding: utf-8 -*-
"""Сайт GitHub Pages: які файли дерева він віддає і відбиток їхнього вмісту — одне визначення.

python3 джерела/прилади/сайт_pages.py --одиниці [РЕВІЗІЯ]   # одиниці сайта: тека зі скісною в кінці чи файл
python3 джерела/прилади/сайт_pages.py --шаблони [РЕВІЗІЯ]   # те саме шаблонами `git sparse-checkout set --no-cone`
python3 джерела/прилади/сайт_pages.py --відбиток [РЕВІЗІЯ]  # sha256 вмісту сайта (ідентифікатори git одиниць)

Читачі: `.github/workflows/pages.yml` (що кладе в артефакт розгортання і чи сайт уже віддає цей вміст) і скрипти
виміру наряду «Pages-розгортання-доходить» у теці його звіту (чи коміт міняє сайт). Рядки дошки 16652–16654.

Сайт — це (до перемикання на власний процес його віддавав Jekyll усім деревом, 75 тис. файлів):
1. усе з кореня дерева, крім `аудит/`, `джерела/`, `open-source-stylist/`, назв із крапкою (`.github/`, …) і файлів
   правил сесій (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`): продукт (`index.html`, `build.txt`, `шрифти/`, файли
   каталогу), `ohliad-koloru/`, `zhnyvarka/`, `показ_зонд.html`, `README.md`;
2. з `аудит/` — тека, у якій прямо лежить сторінка `.html`/`.htm`, цілком (з підтеками): сторінки власника
   (`аудит/айдентика/`), інструкція тестувальниць, звіти-сторінки перевірки;
3. замикання посилань: файл дерева, на який відносною адресою посилається сторінка, стиль чи малюнок сайта (`src=`,
   `href=`, `url(…)`, `@import`, `fetch("…")` літералом), — теж сайт, і далі по сторінках, що додались (сторінки
   айдентики посилаються на дослідження в `аудит/дослідження_research/`).
Решта `аудит/` (стан, дошка, наряди, звіти, записи прогонів — 5,7 ГБ) і `джерела/` сайтом не є: жодна адреса сайта в
дереві на них не веде (вимір у PR цього файла).
"""
import hashlib
import posixpath
import re
import subprocess
import sys
import urllib.parse

ПОЗА_САЙТОМ = {"аудит", "джерела", "open-source-stylist", "AGENTS.md", "CLAUDE.md", "GEMINI.md"}
ТЕКИ_СТОРІНОК = "аудит"
СТОРІНКИ = (".html", ".htm")
З_ПОСИЛАННЯМИ = (".html", ".htm", ".css", ".svg")
НАЗВА_САЙТА = "kod-shi-data"

ПОСИЛАННЯ = re.compile(
    r"""(?:\b(?:src|href|poster)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'<>`]+)))"""
    r"""|(?:url\(\s*(?:"([^"]*)"|'([^']*)'|([^)"'\s]+))\s*\))"""
    r"""|(?:@import\s+(?:"([^"]*)"|'([^']*)'))"""
    r"""|(?:\bfetch\(\s*(?:"([^"]*)"|'([^']*)'|`([^`$]*)`)\s*[,)])""",
    re.IGNORECASE,
)
НЕ_ФАЙЛ = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#|\?)", re.IGNORECASE)


def _git(*арг, вхід=None):
    return subprocess.run(["git", *арг], input=вхід, capture_output=True, check=True).stdout


def дерево(ревізія="HEAD"):
    """{шлях файла: (режим, тип, ідентифікатор)} усього дерева ревізії (лише дерева git, без вмісту файлів)."""
    вихід = {}
    for запис in _git("ls-tree", "-r", "-z", "--full-tree", ревізія).split(b"\0"):
        if not запис:
            continue
        мета, шлях = запис.split(b"\t", 1)
        режим, тип, ід = мета.decode().split()
        вихід[шлях.decode("utf-8", "surrogateescape")] = (режим, тип, ід)
    return вихід


def вміст(ревізія, шляхи):
    """{шлях: байти} для файлів ревізії; у частковому клоні git докачує бракуючі об'єкти сам."""
    if not шляхи:
        return {}
    запит = "".join(f"{ревізія}:{ш}\n" for ш in шляхи).encode("utf-8", "surrogateescape")
    сире = _git("cat-file", "--batch", вхід=запит)
    вихід, поз = {}, 0
    for ш in шляхи:
        кінець = сире.index(b"\n", поз)
        голова = сире[поз:кінець].split()
        поз = кінець + 1
        if len(голова) < 3 or голова[1] == b"missing":
            continue
        розмір = int(голова[2])
        вихід[ш] = сире[поз:поз + розмір]
        поз += розмір + 1
    return вихід


def _ціль(звідки, адреса, файли, теки):
    """Шлях дерева, на який веде відносна адреса зі сторінки `звідки`, чи None."""
    адреса = адреса.strip()
    if not адреса or НЕ_ФАЙЛ.match(адреса) or "${" in адреса or "{{" in адреса:
        return None
    адреса = urllib.parse.unquote(адреса.split("#", 1)[0].split("?", 1)[0])
    if not адреса:
        return None
    if адреса.startswith("/"):
        префікс = f"/{НАЗВА_САЙТА}/"
        if not адреса.startswith(префікс):
            return None
        шлях = адреса[len(префікс):]
    else:
        шлях = posixpath.join(posixpath.dirname(звідки), адреса)
    шлях = posixpath.normpath(шлях) if шлях else "."
    if шлях == ".." or шлях.startswith("../"):
        return None
    if шлях in файли:
        return шлях
    if шлях == ".":
        return "index.html" if "index.html" in файли else None
    індекс = шлях + "/index.html"
    return індекс if шлях in теки and індекс in файли else None


def _посилання(текст):
    for зб in ПОСИЛАННЯ.finditer(текст):
        for група in зб.groups():
            if група is not None:
                yield група
                break


def одиниці(ревізія="HEAD", файли=None, читати=None):
    """Відсортовані одиниці сайта: тека — `шлях/`, файл — `шлях`. `файли`/`читати` — для тестів."""
    if файли is None:
        файли = set(дерево(ревізія))
    if читати is None:
        def читати(шляхи):
            return вміст(ревізія, шляхи)
    теки = set()
    for ф in файли:
        ч = ф.split("/")
        for і in range(1, len(ч)):
            теки.add("/".join(ч[:і]))

    def у_теці(ф, тека):
        return ф.startswith(тека + "/")

    одн_теки, одн_файли = set(), set()
    for ф in файли:
        верх = ф.split("/", 1)[0]
        if верх.startswith(".") or верх in ПОЗА_САЙТОМ:
            continue
        if "/" in ф:
            одн_теки.add(верх)
        else:
            одн_файли.add(ф)
    for ф in файли:
        if ф.startswith(ТЕКИ_СТОРІНОК + "/") and ф.lower().endswith(СТОРІНКИ):
            тека = posixpath.dirname(ф)
            if тека == ТЕКИ_СТОРІНОК:
                одн_файли.add(ф)
            else:
                одн_теки.add(тека)
    одн_теки = {т for т in одн_теки if not any(т != в and у_теці(т, в) for в in одн_теки)}

    def в_сайті(ф):
        return ф in одн_файли or any(у_теці(ф, т) for т in одн_теки)

    черга = sorted(ф for ф in файли if в_сайті(ф) and ф.lower().endswith(З_ПОСИЛАННЯМИ))
    переглянуті = set()
    while черга:
        партія = [ф for ф in черга if ф not in переглянуті]
        переглянуті.update(партія)
        черга = []
        for ф, сире in читати(партія).items():
            текст = сире.decode("utf-8", "replace")
            for адреса in _посилання(текст):
                ціль = _ціль(ф, адреса, файли, теки)
                if ціль is None or в_сайті(ціль):
                    continue
                одн_файли.add(ціль)
                if ціль.lower().endswith(З_ПОСИЛАННЯМИ):
                    черга.append(ціль)
    одн_файли = {ф for ф in одн_файли if not any(у_теці(ф, т) for т in одн_теки)}
    return sorted([т + "/" for т in одн_теки] + sorted(одн_файли))


def у_сайті(шлях, одн):
    """Чи файл дерева належить сайту з одиницями `одн`."""
    return any(шлях == о or (о.endswith("/") and шлях.startswith(о)) for о in одн)


def шаблон(одиниця):
    """Шаблон no-cone sparse-checkout (синтаксис gitignore), що збігається рівно з одиницею."""
    тіло = re.sub(r"([\\*?\[\]!#])", r"\\\1", одиниця.rstrip("/"))
    if тіло.endswith(" "):
        тіло = тіло[:-1] + "\\ "
    return "/" + тіло + ("/" if одиниця.endswith("/") else "")


def відбиток(ревізія="HEAD", одн=None):
    """sha256 ідентифікаторів git усіх одиниць: той самий вміст сайта — той самий відбиток."""
    if одн is None:
        одн = одиниці(ревізія)
    шляхи = [о.rstrip("/") for о in одн]
    сире = _git("ls-tree", "-z", "--full-tree", ревізія, "--", *шляхи) if шляхи else b""
    рядки = sorted(з for з in сире.split(b"\0") if з)
    return hashlib.sha256(b"\n".join(рядки)).hexdigest()


def main(арг):
    if not арг or арг[0] not in ("--одиниці", "--шаблони", "--відбиток") or len(арг) > 2:
        print(__doc__.split("\n\n", 1)[0], file=sys.stderr)
        return 2
    ревізія = арг[1] if len(арг) > 1 else "HEAD"
    одн = одиниці(ревізія)
    if арг[0] == "--одиниці":
        print("\n".join(одн))
    elif арг[0] == "--шаблони":
        print("\n".join(шаблон(о) for о in одн))
    else:
        print(відбиток(ревізія, одн))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
