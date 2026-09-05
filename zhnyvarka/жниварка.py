# -*- coding: utf-8 -*-
"""ЖНИВАРКА v3 — збирає речі українських магазинів у каталог, який читає feed.py.

Одна річ у світі, яку вона міняє: що ЛЕЖИТЬ у пулі композитора. Кожне поле нижче
або міняє рішення про образ (слот, стать, колір, розмір, склад, фото, наявність),
або є провенансом, без якого дефект не знайти. Іншого тут нема.

ЗАПУСК
  python3 жниварка.py --режим проба --магазини gepur.com --стеля 25
  python3 жниварка.py --режим повний --група 2/6            # так її кличе GitHub Actions
  python3 жниварка.py --зібрати                             # жнива/*.json → каталоги + звіт
Вихід: жнива/<домен>.json (сире, для перезапуску одного магазину),
       каталог_повний.xml (жіноче + унісекс), каталог_чоловічий.xml (чоловіче + унісекс),
       карантин.xml (відхилене, з причиною на кожній речі), звіт_жнив.md, journal_жнив.tsv.

ПРОБЛЕМИ ПОПЕРЕДНІХ ЖНИВ (23.08–04.09.2026) → ПРАВИЛО ТУТ. Кожне — з фейл-кейсу, не з міркувань.
 П1  Транспорт r.jina.ai (проксі, markdown). Наслідки: «![Image 10: …», «Картинка Валіза»,
     «— фото 1 — Miraton» у назвах (2 558 назв полагоджено 27.08); ціни-склейки
     «899199» = 899 стара + 199 нова (696 знято); одне фото на річ (7 035 із 7 434);
     JSON-канали Shopify/Woo мовчали, бо JSON.parse бився об шапку проксі; темп 3 с/запит,
     коліно сховища на 15 000 речей, вкладка засинала.
     → пряме HTTP з сервера (GitHub Actions), рідні парсери HTML/JSON/XML. Markdown не існує.
 П2  Перше фото — сусіднього товару (gepur 394/414), mainLoader.svg (md-fashion 281/392),
     cart.svg (vovk 221/231), lazy.svg (tm-beart 62/66), стікер sold-out (diadia), фото іншого
     кольорового варіанта (md-fashion 86/100). Тестувальниця бачила червону сукню під сережками.
     → фото беруться лише з КАРТКИ речі (JSON-LD image / og:image / галерея картки), блоки
       «схожі/рекомендовані» вирізаються, заглушки за адресою випадають, перше фото
       ПЕРЕВІРЯЄТЬСЯ запитом (тип image/*, байти картинки), кольоровий варіант несе свої фото.
 П3  Слот із розділу, а розділ збірний: «Сумка Maybelle» у «верх», сукні в «низ» (275 → ще 188
     правок 01.09), «Топсайдери» у «верх» через ключ «топ», «Жакет з бахромою» у «сумка».
     → слот: хлібні крихти картки → назва → слаг URL; ключі — ті самі, що у feed.py
       (імпортується, якщо лежить поруч); підрядкові пастки ті самі; слот не визначено → карантин.
 П4  Чоловіче різалось і в товарах, і в розділах (v2 інваріант); 46 чоловічих речей потім
     спіймано в жіночих образах. Замовник 04.09: чоловіче НЕ обрізати, покриття широке.
     → стать визначається (крихти / URL / назва / теги / типове для магазину) і ПИШЕТЬСЯ
       (`стать`); чоловіче йде в каталог_чоловічий.xml, жіноче+унісекс — у каталог_повний.xml.
       Дитяче не збирається — це не наш каталог.
 П5  ID не унікальний між магазинами («ж-00237» = жакет gepur і капелюх otaje, 1 230 пар).
     → id = <код магазину>-<номер>; group_id = ключ дизайну магазину (варіанти кольору ділять його).
 П6  Наявності жниварка не читала взагалі (94 розпроданих у каталозі; available не писався за фактом).
     → available з JSON-LD/варіантів/тексту картки; розміри в наявності — окремо.
 П7  Склад 83/7 597 (1 %), заміри 68, параметри моделі 66, розмірів 0, опису 0 — фаза карток
     була вимкнена (кожна картка = запит крізь проксі). Замовник: у картках Є заміри й параметри моделі.
     → картка читається для КОЖНОЇ речі: таблиця характеристик, склад (регекс %), розміри
       (кнопки/опції/варіанти), заміри, параметри моделі, опис ≤ 1 500 симв.
 П8  Колір 56 %, переважно зі слага; англійські слаги ставали «Скірт вітг руффлес».
     → колір: характеристика картки / опція варіанта → слово в назві → слаг (транслітерований
       словник, лише основи); джерело пишеться; латиниця в назву не транслітерується ніколи.
 П9  Російська: фід Ager 23.08 (одноразовий виняток, «ніколи знову»); 200 назв російською
     на одному магазині; JS `\\b` не бачить кирилиці.
     → детектор той самий, що в language_gate.py (літери ы/э/ъ/ё, закінчення, словник);
       російська назва → шукається UA-версія картки (hreflang=uk), інакше карантин; магазин,
       де російських > 30 % — виключається цілком; опис російською — викидається, річ лишається.
 П10 Подвійне екранування «&amp;quot;» (336 назв) — ручна склейка XML.
     → лише ElementTree; текст перед записом розекрановується до нерухомої точки (≤ 3 проходи).
 П11 Хорошоп/Bitrix: розділи домальовуються JS → 1 КБ і нуль речей; Хорошоп обмежено головною.
     → універсальний канал — карта сайту (robots.txt → sitemap → URL карток), яка не залежить
       від рендера розділів; розділи з пагінацією — лише запасний шлях.
 П12 Відбиток платформи був ВОРОТАРЕМ: хибний «OpenCart» вимикав products.json.
     → дешеві bulk-проби (Shopify /products.json, Woo wc/store, типові YML-шляхи) ідуть ЗАВЖДИ;
       відбиток лише впорядковує. Адреса YML шукається і в HTML головної (Хорошоп ставить хеш).
 П13 Не одяг у слотах: валіза за 10 600 грн в офісному образі; білизна/купальники/домашнє.
     → НЕ_ОДЯГ feed.py + білизна/купальники/піжами/рукавички/домашній текстиль → карантин.
 П14 Магазин цілком у карантині через частку сміття, хоча 5 664 з 9 213 речей були справні.
     → гейти на рівні РЕЧІ з поіменною причиною; магазин виключається лише за мову чи блок.
 П15 «Перевірено» було невідрізненним від «не запускалось».
     → кожен канал, кожен гейт, кожна відмова лишає число у звіті; розділ «НЕ ЗІБРАНО» рахується.
 П16 Мережеві мережі (Zara, Reserved, Mango, Next, Mohito, Modivo, Wittchen, Answear) каталог не
     віддають; Cloudflare «Just a moment» (skripka), HTTP 422 (maxa).
     → у магазини.tsv стан «вимкнено» з причиною; блок розпізнається й називається у звіті.

 П17 Комплекти (костюм = дві речі в одному SKU) не мають слота; рішення власника 01.09 — не чіпати.
     → збираються зі слотом «комплект»; feed.слот() його не знає → у пул не йдуть, дані лежать.
 П18 Стеля речей на магазин різала ХВІСТ списку: перші N url ager — самі сукні.
     → стеля береться порівну з груп (категорія / префікс шляху), щоб широта покриття не залежала від порядку мапи.
 П19 Розділи 1–3 сторінки × 8 розділів — стеля ~300 речей на магазин і жодного «колготи/шкарпетки».
     → мапа сайту дає всі картки; слоти колготи/шкарпетки/комплект пишуться, не відсікаються.

ЧОГО ЖНИВАРКА НЕ РОБИТЬ (навмисно): не міряє колір з фото (це feed.колір_з_фото), не виводить
тип речі/формальність (feed.тип_речі), не судить образ. Вона віддає факти з провенансом.
"""
import argparse, collections, concurrent.futures, datetime, gzip, html, io, json, os, re, sys, threading, time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode

try:
    import requests
except ImportError:                                   # noqa
    requests = None
try:
    from bs4 import BeautifulSoup
    import warnings
    try:
        from bs4 import XMLParsedAsHTMLWarning, MarkupResemblesLocatorWarning
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
    except ImportError:                               # noqa
        pass
except ImportError:                                   # noqa
    BeautifulSoup = None
try:
    import lxml                                        # noqa
    ПАРСЕР_HTML = "lxml"
except ImportError:                                   # noqa
    ПАРСЕР_HTML = "html.parser"                        # повільніше, але картки читаються; звіт це назве

ВЕРСІЯ = "жниварка v3.2 · 2026-09-06"
# ЛИШЕ ASCII: HTTP-заголовки кодуються latin-1; кирилиця тут поклала 62/62 магазини 05.09
# (UnicodeEncodeError до першого байта в мережу). Гейт: assert нижче + мережевий тест.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0 Safari/537.36 Lyusterko-zhnyvarka/3.0 (+catalog for a styling test stand)")
assert UA.isascii(), "User-Agent має бути ASCII"
СЬОГОДНІ = datetime.date.today().isoformat()
ТЕКА_ЖНИВ = "жнива_сирі"          # <домен>.json.gz — сире, щоб перезбирати один магазин і зливати з рештою

# ═══════════════ 0. СЛОВНИКИ, СПІЛЬНІ З feed.py ═══════════════
# Якщо feed.py лежить поруч (у теці джерел), ключі беруться з нього — тоді жниварка й
# читач не розходяться. Інакше — копія станом на 04.09.2026 (feed.СЛОТ_КЛЮЧІ / НЕ_ОДЯГ /
# ПАСТКИ_ПІДРЯДКА). Розходження копії з оригіналом — це і є фейл-кейс П3.
_СЛОТ_КЛЮЧІ_КОПІЯ = [
 ("верхній_шар", ("пальт", "тренч", "пуховик", "куртк", "парк", "шуб", "плащ", "жилет утепл",
                  "вітровк", "ветровк", "бомбер", "дощовик", "дублянк", "дубленк",
                  "кожух", "анорак", "пуффер", "півпальт", "полупальт",
                  "верхній одяг", "верхняя одежда", "пончо", "накидк")),
 ("сукня",       ("сукн", "плать", "платт", "сарафан", "комбінезон", "комбинезон")),
 ("верх",        ("блуз", "сорочк", "рубашк", "футболк", "лонгслів", "світшот", "свитшот",
                  "худі", "худи", "джемпер", "светр", "свитер", "топ", "боді", "жакет",
                  "піджак", "пиджак", "кардиган", "водолазк", "гольф", "жилет", "болеро",
                  "поло", "туніка", "туник")),
 ("низ",         ("штан", "брюк", "джинс", "спідниц", "юбк", "шорт", "легінс", "леггинс", "бриджі")),
 ("взуття",      ("взутт", "обув", "черевик", "ботинк", "чобот", "сапог", "кросівк", "кроссовк",
                  "туфл", "босоніжк", "босонож", "лофер", "мокасин", "кед", "сандал",
                  "топсайдер", "мюл", "сабо", "слінгбек", "балетк", "еспадриль", "ботильйон",
                  "броги", "оксфорд", "шльопанц", "сліпон", "угг", "в'єтнамк", "в’єтнамк", "дербі")),
 ("сумка",       ("сумк", "рюкзак", "клатч", "шопер", "портфел")),
 ("шарф",        ("шарф", "хустк", "платок", "снуд", "палантин")),
 ("прикраси",    ("прикрас", "украшен", "сереж", "серьг", "кольє", "колье", "браслет",
                  "каблучк", "кільц", "кольц", "підвіск", "кулон", "намист", "брош", "чокер")),
 ("головний_убір",("шапк", "кепк", "капелюх", "шляп", "берет", "панам", "бейсболк")),
 ("пояс",        ("пояс", "ремін", "ремен")),
 ("колготи",     ("колгот", "чулк", "панчох")),
 ("шкарпетки",   ("шкарпет", "носк")),
]
_НЕ_ОДЯГ_КОПІЯ = ("валіз", "чемодан", "гаманц", "гаманец", "кошел", "косметичк", "чохол", "чехол",
                  "ключниц", "органайзер", "парасол", "зонт")
_ПАСТКИ_КОПІЯ = {"боді": ("кросбоді", "crossbody", "кроссбоди"),
                 "топ": ("шопер", "стоп", "лептоп", "топсайдер"),
                 "кед": ("кедр",), "поло": ("полотн", "поломан"), "парк": ("парковк",)}
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import feed as _feed                                   # noqa
    СЛОТ_КЛЮЧІ = list(_feed.СЛОТ_КЛЮЧІ); ПАСТКИ_ПІДРЯДКА = dict(_feed.ПАСТКИ_ПІДРЯДКА)
    НЕ_ОДЯГ = tuple(x for x in _feed.НЕ_ОДЯГ
                    if not any(k in x for k in ("чолов", "мужск", "дитяч", "хлопчик", "дівчинк")))
    СЛОВНИКИ_ЗВІДКИ = "feed.py"
except Exception:                                          # noqa
    СЛОТ_КЛЮЧІ, ПАСТКИ_ПІДРЯДКА, НЕ_ОДЯГ = _СЛОТ_КЛЮЧІ_КОПІЯ, _ПАСТКИ_КОПІЯ, _НЕ_ОДЯГ_КОПІЯ
    СЛОВНИКИ_ЗВІДКИ = "копія у жниварці (feed.py не поруч)"
ІМЕНА_СЛОТІВ = frozenset(с for с, _ in СЛОТ_КЛЮЧІ)

# П13: поза слотами — річ не може стати частиною образу, і слот розділу її не рятує.
ПОЗА_СЛОТАМИ = ("білизн", "бюстгальтер", "трус", "купальник", "купальн", "плавк", "піжам", "пижам", "халат",
                "рукавичк", "перчатк", "рукавиц", "постіл", "рушник", "подушк", "ковдр", "свічк",
                "парфум", "аромат", "косметик", "сертифікат", "подарунков", "пакет", "брелок",
                "окуляр", "годинник", "термос", "чашк", "іграшк", "книг", "ланцюжок для окуляр",
                "догляд", "аерозол", "крем для взуття", "спрей", "щітк", "устілк", "шнурк", "ложк", "просочен", "дезодорант",
                "готовий образ",
                "нижня білизна", "боксери", "бюст", "спортивний топ бра")
# П4: стать — з тексту крихт/URL/назви. Порядок: дитяче → чоловіче/жіноче → унісекс.
_СТАТЬ = [
 ("дитяче",   re.compile(r"дитяч|дівчинк|хлопчик|\bkids?\b|\bchildren\b|\bbaby\b|\bgirls?\b|\bboys?\b|немовля|підлітк|для дітей", re.I)),
 ("чоловіче", re.compile(r"чоловіч|чоловік|для чоловіків|мужск|мужчин|\bmen'?s?\b|\bman\b|\bmale\b|/men/|/cholovik|/choloviky|/muzhsk|\bhim\b", re.I)),
 ("жіноче",   re.compile(r"жіноч|жінк|жінок|для жінок|женск|женщин|\bwomen'?s?\b|\bwoman\b|\bfemale\b|\bladies\b|/women/|/zhinoch|/zhink|/zhinky|/zhenskiy|\bher\b", re.I)),
 ("унісекс",  re.compile(r"унісекс|унисекс|unisex", re.I)),
]

# П9: детектор — той самий, що language_gate.російське (копія логіки 04.09.2026).
_РОС_ЛІТЕРИ = re.compile(r"[ыэъёЫЭЪЁ]")
_РОС_ЗАКІНЧЕННЯ = re.compile(r"\b[а-яіїєґ]{3,}(ое|ые|ая|яя)\b", re.I)
_РОС_СЛОВА = ("платье", "платья", "юбка", "юбку", "юбки", "обувь", "обуви", "туфли", "туфель",
              "рубашка", "рубашку", "кофта", "свитер", "пиджак", "пиджака", "украшения",
              "украшений", "серьги", "цвет", "цвета", "цветом", "оттенок", "оттенка", "ткань",
              "ткани", "кожа", "кожи", "кожаная", "кожаный", "шелк", "шелка", "хлопок", "хлопка",
              "шерсть", "шерсти", "одежда", "одежды", "носить", "надеть", "сочетание",
              "который", "которая", "которые", "очень", "тоже", "также", "если", "чтобы",
              "этот", "эта", "это", "здесь", "сейчас", "сегодня", "женская", "женские", "мужская",
              "мужские", "размер", "размера", "состав", "брюки", "сумка", "пальто женское")
_РОС_ЛИШЕ_ЗІ_СВІДКОМ = {"образ", "носить", "сумка", "шарф", "браслет", "ресторан", "пальто женское"}


def російське(текст):
    """Список підозрілих фрагментів; порожній — текст чистий (як language_gate.російське)."""
    т = str(текст or "")
    знайдені = []
    for м in _РОС_ЛІТЕРИ.finditer(т):
        знайдені.append(м.group(0))
    for м in _РОС_ЗАКІНЧЕННЯ.finditer(т):
        знайдені.append(м.group(0))
    низ = т.lower(); свідок = bool(знайдені)
    for сл in _РОС_СЛОВА:
        if сл in _РОС_ЛИШЕ_ЗІ_СВІДКОМ and not свідок:
            continue
        if re.search(r"\b" + re.escape(сл) + r"\b", низ):
            знайдені.append(сл)
    return sorted(set(знайдені))


def розекранувати(т):
    """П10: до нерухомої точки, не більше трьох проходів (`&amp;amp;quot;` → `"`)."""
    т = str(т or "")
    for _ in range(3):
        н = html.unescape(т)
        if н == т:
            break
        т = н
    return " ".join(т.split())


# ═══════════════ 1. ТРАНСПОРТ ═══════════════
_ЗАСЛОН = re.compile(r"just a moment|attention required|cf-browser-verification|checking your browser|"
                     r"enable javascript and cookies|access denied|ddos-guard|captcha", re.I)


class Транспорт:
    """Пряме HTTP. Темп — на домен, не глобальний; 429/503 — відпочинок, не смерть черги (П1)."""

    def __init__(self, пауза=0.8, ігнорувати_robots=False, лог=None):
        self.пауза, self.ігнорувати_robots, self.лог = пауза, ігнорувати_robots, лог or (lambda *a: None)
        self._останній = {}; self._замок = threading.Lock()
        self.статистика = collections.defaultdict(collections.Counter)   # домен → код → n
        self.поспіль_помилок = collections.Counter()                     # домен → невдач підряд (429/5xx/мережа)
        self.robots = {}                                                  # домен → dict(disallow, sitemaps, delay)
        self.сесія = requests.Session() if requests else None
        if self.сесія:
            self.сесія.headers.update({"User-Agent": UA, "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.5",
                                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                                                 "application/json;q=0.9,*/*;q=0.8"})
        self.підміна = None   # для тестів: url → (код, тіло, content-type)

    def _зачекати(self, домен):
        with self._замок:
            затримка = max(self.пауза, self.robots.get(домен, {}).get("delay", 0))
            минуло = time.time() - self._останній.get(домен, 0)
            if минуло < затримка:
                time.sleep(затримка - минуло)
            self._останній[домен] = time.time()

    def дозволено(self, url):
        if self.ігнорувати_robots:
            return True
        д = urlparse(url).netloc
        р = self.robots.get(д)
        if not р:
            return True
        шлях = urlparse(url).path or "/"
        return not any(шлях.startswith(x) for x in р["disallow"] if x)

    def get(self, url, тип="text", ліміт=6_000_000, повтори=3, заголовки=None):
        """→ dict(код, тіло, url, ctype, заслон, помилка). Тіло — str для text, bytes для bytes."""
        домен = urlparse(url).netloc
        if self.підміна is not None:
            відп = self.підміна(url)
            код, тіло, ctype = відп[:3]; кінцевий = відп[3] if len(відп) > 3 else url
            self.статистика[домен][код] += 1
            if тип == "bytes" and isinstance(тіло, str):
                тіло = тіло.encode("utf-8")
            текст = тіло.decode("utf-8", "replace") if isinstance(тіло, bytes) and тип == "text" else тіло
            return dict(код=код, тіло=текст, url=кінцевий, ctype=ctype,
                        заслон=bool(код in (403, 503) and isinstance(текст, str) and _ЗАСЛОН.search(текст or "")),
                        помилка=None)
        if not self.дозволено(url):
            self.статистика[домен]["robots"] += 1
            return dict(код=0, тіло=None, url=url, ctype="", заслон=False, помилка="robots.txt забороняє")
        помилка = None
        for спроба in range(повтори):
            self._зачекати(домен)
            try:
                r = self.сесія.get(url, timeout=(10, 30), stream=True, allow_redirects=True,
                                   headers=заголовки or {})
                код = r.status_code
                ctype = (r.headers.get("Content-Type") or "").lower()
                шматки, обсяг = [], 0
                for ш in r.iter_content(65536):
                    шматки.append(ш); обсяг += len(ш)
                    if обсяг > ліміт:
                        break
                r.close()
                тіло = b"".join(шматки)
                self.статистика[домен][код] += 1
                if код in (429, 503, 502, 520, 521, 522, 524):
                    self.поспіль_помилок[домен] += 1
                    if спроба < повтори - 1 and self.поспіль_помилок[домен] < 6:
                        self.лог("  ⏸ %s → %s, відпочинок %d с" % (url[:70], код, 15 * (спроба + 1)))
                        time.sleep(15 * (спроба + 1)); continue
                    return dict(код=код, тіло=None, url=r.url, ctype=ctype, заслон=False, помилка="HTTP %s" % код)
                if код < 400:
                    self.поспіль_помилок[домен] = 0
                текст = None
                if тип == "text":
                    кодування = r.encoding if r.encoding and r.encoding.lower() != "iso-8859-1" else None
                    for k in (кодування, "utf-8", "cp1251"):
                        if not k:
                            continue
                        try:
                            текст = тіло.decode(k); break
                        except Exception:
                            continue
                    if текст is None:
                        текст = тіло.decode("utf-8", "replace")
                заслон = код in (403, 503, 429) and bool(_ЗАСЛОН.search((текст or тіло.decode("utf-8", "replace"))[:5000]))
                return dict(код=код, тіло=(текст if тип == "text" else тіло), url=r.url, ctype=ctype,
                            заслон=заслон, помилка=None)
            except Exception as e:                                 # noqa
                помилка = "%s: %s" % (type(e).__name__, str(e)[:120])
                self.статистика[домен]["помилка"] += 1; self.поспіль_помилок[домен] += 1
                if self.поспіль_помилок[домен] >= 6:
                    break                                          # сервер/мережа мовчать підряд — не чекати далі
                time.sleep(2 * (спроба + 1))
        return dict(код=0, тіло=None, url=url, ctype="", заслон=False, помилка=помилка)

    def head_фото(self, url, referer=None):
        """П2: чи за адресою справді картинка. HEAD → при 405/403 GET перших 2 КБ і магічні байти.
        Accept: image/* і Referer картки — CDN без них іноді віддає 403 (гіпотеза з проби 05.09)."""
        домен = urlparse(url).netloc
        if self.підміна is not None:
            відп = self.підміна(url); код, тіло, ctype = відп[:3]
            return код == 200 and (ctype.startswith("image/") or _магія_картинки(тіло))
        з = {"Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"}
        if referer:
            з["Referer"] = referer
        try:
            self._зачекати(домен)
            r = self.сесія.head(url, timeout=(10, 15), allow_redirects=True, headers=з)
            if r.status_code == 200 and (r.headers.get("Content-Type") or "").lower().startswith("image/"):
                довж = r.headers.get("Content-Length")
                return not (довж and довж.isdigit() and int(довж) < 3000)
            if r.status_code in (405, 403, 404) or r.status_code == 200:
                self._зачекати(домен)
                r = self.сесія.get(url, timeout=(10, 15), stream=True, headers=dict(з, Range="bytes=0-2047"))
                шматок = next(r.iter_content(2048), b""); r.close()
                return r.status_code in (200, 206) and _магія_картинки(шматок)
        except Exception:                                          # noqa
            return False
        return False


def _магія_картинки(б):
    if not isinstance(б, (bytes, bytearray)) or len(б) < 12:
        return False
    return (б[:3] == b"\xff\xd8\xff" or б[:8] == b"\x89PNG\r\n\x1a\n" or
            (б[:4] == b"RIFF" and б[8:12] == b"WEBP") or б[4:12] in (b"ftypavif", b"ftypheic") or
            б[:6] in (b"GIF87a", b"GIF89a") or б[:2] == b"BM")


# ═══════════════ 2. АДРЕСИ, JSON-LD, РОЗПІЗНАВАННЯ ═══════════════
_UTM = ("utm_", "fbclid", "gclid", "yclid", "_ga", "ref", "from")


def канонічна(url, база=None):
    """Без UTM і хеша, без завершального слеша (крім кореня). Одна річ — одна адреса."""
    if not url:
        return ""
    u = urlparse(urljoin(база or "", url.strip()))
    q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
         if not k.lower().startswith(_UTM)]
    шлях = re.sub(r"/{2,}", "/", u.path or "/")
    if len(шлях) > 1:
        шлях = шлях.rstrip("/")
    return urlunparse((u.scheme or "https", u.netloc.lower(), шлях, "", urlencode(q), ""))


def домен_із(url):
    return urlparse(url).netloc.lower().replace("www.", "")


def код_магазину(домен):
    """П5: `gepur.com` → `gepur`, `25union.com.ua` → `25union`, `md-fashion.ua` → `md-fashion`."""
    return re.sub(r"[^a-z0-9-]", "", домен.replace("www.", "").split(".")[0])


def json_ld(html_текст):
    """Усі JSON-LD вузли (розгорнуті з @graph і списків). Пошкоджений JSON — пропускається."""
    вих = []
    for м in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         html_текст or "", re.S | re.I):
        сирий = м.group(1).strip()
        сирий = re.sub(r"^\s*<!--|-->\s*$", "", сирий)
        try:
            д = json.loads(сирий)
        except Exception:
            try:
                д = json.loads(re.sub(r",\s*([}\]])", r"\1", сирий))
            except Exception:
                continue
        черга = collections.deque([д])
        while черга:                                  # BFS: зовнішній Product раніше за його варіанти
            x = черга.popleft()
            if isinstance(x, list):
                черга.extend(x)
            elif isinstance(x, dict):
                if x.get("@type"):
                    вих.append(x)
                for k, v in x.items():                # mainEntity, @graph, hasVariant, offers …
                    if isinstance(v, (dict, list)):
                        if k == "itemListElement":    # товари зі списку розділу — позначити, вони не роблять сторінку карткою
                            for e in (v if isinstance(v, list) else [v]):
                                if isinstance(e, dict):
                                    e["_у_списку"] = True
                                    if isinstance(e.get("item"), dict):
                                        e["item"]["_у_списку"] = True
                        черга.append(v)
    return вих


def _тип_ld(в):
    t = в.get("@type") if isinstance(в, dict) else None
    if isinstance(t, list):
        return [str(x) for x in t]
    return [str(t)] if t else []


def відбиток_платформи(html_текст, заголовки=None):
    т = (html_текст or "")[:400000]
    ознаки = [
        ("Shopify", r"cdn\.shopify\.com|Shopify\.theme|shopify-section|myshopify\.com"),
        ("WordPress/Woo", r"wp-content/|woocommerce|wc-block|wp-json"),
        ("Хорошоп", r"horoshop|/hs-|data-hs-|__hs_|horoshop\.ua"),
        ("Bitrix", r"/bitrix/|bx\.|BX\.|bitrix"),
        ("OpenCart", r"index\.php\?route=|catalog/view/theme|opencart"),
        ("PrestaShop", r"prestashop|/modules/ps_|id_product="),
        ("Tilda", r"tilda|tildacdn"),
        ("Magento", r"Magento_|/static/version\d|\bMagento\b"),
        ("Wix", r"wix\.com|wixstatic"),
        ("Prom", r"prom\.ua|uaprom"),
        ("Webflow", r"webflow"),
        ("Squarespace", r"squarespace"),
    ]
    знайдено = [ім for ім, р in ознаки if re.search(р, т, re.I)]
    м = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', т, re.I)
    if м:
        знайдено.insert(0, "generator:" + м.group(1)[:30])
    return "+".join(dict.fromkeys(знайдено)) or "невідомо"


def адреси_фідів_у_html(html_текст, база):
    """П12: адреса YML часто лежить у самій сторінці (Хорошоп ставить хеш — вгадати не можна)."""
    вих = []
    for м in re.finditer(r'href=["\']([^"\']+)["\']|["\'](https?://[^"\'\s<>]+)["\']', html_текст or "", re.I):
        u = м.group(1) or м.group(2)
        if re.search(r"\.(xml|yml)(\?|$)|export/(yml|products)|price[_-]?list|feed", u, re.I) and \
           not re.search(r"sitemap|rss|atom|\.xsl|manifest|opensearch", u, re.I):
            вих.append(канонічна(u, база))
    return list(dict.fromkeys(вих))[:6]


def розібрати_robots(текст):
    р = dict(disallow=[], sitemaps=[], delay=0.0)
    if not текст:
        return р
    для_нас = False
    for рядок in текст.splitlines():
        рядок = рядок.split("#")[0].strip()
        if not рядок or ":" not in рядок:
            continue
        k, v = [x.strip() for x in рядок.split(":", 1)]
        k = k.lower()
        if k == "user-agent":
            для_нас = v.strip() == "*"
        elif k == "sitemap":
            р["sitemaps"].append(v)
        elif для_нас and k == "disallow" and v == "/":
            р["заборона_всього"] = True          # виконувати не будемо (як і попередні жнива), але звіт скаже
        elif для_нас and k == "disallow" and v:
            # `Disallow: /*?sort=` → префікс «/» заборонив би ВСЕ; шаблони з * читаються лише за літеральним
            # початком, і лише коли він довший за «/» (github.com/robots.txt має десятки таких рядків)
            префікс = v.split("*")[0].split("$")[0]
            if len(префікс) >= 2:
                р["disallow"].append(префікс)
        elif для_нас and k == "crawl-delay":
            try:
                р["delay"] = min(float(v.replace(",", ".")), 5.0)
            except ValueError:
                pass
    return р


# ═══════════════ 3. КАНАЛИ ПЕРЕЛІКУ ═══════════════
_ШЛЯХИ_YML = ("/download/prom_yml_catalog.xml", "/index.php?route=extension/feed/yandex_yml",
              "/index.php?route=feed/yandex_yml", "/index.php?route=extension/feed/google_base",
              "/hotline.xml", "/prom.xml", "/rozetka.xml", "/yml.xml", "/export/yml", "/products.xml",
              "/bitrix/catalog_export/yandex.xml", "/export/products.yml")
_МОВНІ_ПРЕФІКСИ = ("/ru/", "/ru", "/en/", "/pl/", "/de/")
_КАРТКОПОДІБНИЙ = re.compile(r"/(product|products|tovar|tovary|goods|item|catalog|katalog|shop|p)/[^/]+|"
                             r"product_id=\d+|/[a-z0-9-]+-\d{3,}(?:/|\.html|$)|/[a-z0-9-]{8,}\.html$", re.I)
# розділ /catalog/spidnytsi — не картка; картка — те, що закінчується номером/.html або лежить у /product(s)/, /tovar/, /p/
_ЯВНО_КАРТКА = re.compile(r"/(product|products|tovar|tovary|goods|item|p)/[^/]+|product_id=\d+|-\d{3,}(?:/|\.html|$)|\.html$", re.I)
_НЕ_КАРТКА = re.compile(r"/(blog|news|novyny|article|articles|stat|statti|page|pages|brand|brands|tag|tags|"
                        r"search|cart|checkout|account|login|wishlist|compare|contact|contacts|about|delivery|"
                        r"dostavka|payment|oplata|faq|sitemap|lookbook|reviews|manufacturer|filter|"
                        r"vacancies|kontakty|pro-nas|info)(/|$)", re.I)


def _не_наша_мова(url):
    шлях = urlparse(url).path.lower()
    return any(шлях.startswith(п) for п in _МОВНІ_ПРЕФІКСИ) or "/ru/" in шлях


def мапа_сайту(транспорт, база, robots, лог, стеля_файлів=40):
    """П11: URL карток із карт сайту. Повертає (список url, дiагностика)."""
    старт = list(dict.fromkeys(robots.get("sitemaps") or [])) or \
            [urljoin(база, p) for p in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/sitemap.xml.gz", "/sitemaps.xml")]
    черга, бачено, картки, файлів = list(старт), set(), [], 0
    інші = 0
    while черга and файлів < стеля_файлів:
        u = черга.pop(0)
        if u in бачено:
            continue
        бачено.add(u); файлів += 1
        r = транспорт.get(u, тип="bytes", ліміт=30_000_000)
        if r["код"] != 200 or not r["тіло"]:
            continue
        тіло = r["тіло"]
        if тіло[:2] == b"\x1f\x8b":
            import gzip
            try:
                тіло = gzip.decompress(тіло)
            except Exception:
                continue
        текст = тіло.decode("utf-8", "replace")
        locs = re.findall(r"<(?:\w+:)?loc>\s*(?:<!\[CDATA\[)?\s*([^<\s\]]+)\s*(?:\]\]>)?\s*</(?:\w+:)?loc>", текст)   # і <sm:loc>, і CDATA
        if re.search(r"<(\w+:)?sitemapindex", текст[:5000]) or (re.search(r"<(\w+:)?sitemap>", текст) and not re.search(r"<(\w+:)?urlset", текст[:5000])):
            # є файли, названі як товарні (products/goods/tovary/offers) — беруться ЛИШЕ вони
            товарні = [x for x in locs if re.search(r"product|goods|tovar|offer|item", x, re.I)]
            черга.extend(html.unescape(x) for x in (товарні or locs))
            continue
        for loc in locs:
            loc = канонічна(html.unescape(loc), база)
            if re.search(r"\.xml(\.gz)?$", urlparse(loc).path, re.I):       # вкладена мапа в urlset (musthave 05.09)
                черга.append(loc); continue
            if домен_із(loc) != домен_із(база) or _не_наша_мова(loc):
                continue
            if _НЕ_КАРТКА.search(urlparse(loc).path) and not re.search(r"product_id=|/product/", loc):
                інші += 1; continue
            картки.append(loc)
    картки = list(dict.fromkeys(картки))
    # vittorossi 05.09: у мапі і /shop/x (рос), і /ua/shop/x — беремо лише UA-версію, коли вона є
    з_префіксом = {re.sub(r"^/(ua|uk)(?=/)", "", urlparse(u).path) for u in картки if re.match(r"^/(ua|uk)/", urlparse(u).path)}
    if з_префіксом:
        було = len(картки)
        картки = [u for u in картки if re.match(r"^/(ua|uk)/", urlparse(u).path) or urlparse(u).path not in з_префіксом]
        лог("  мапа: відкинуто %d без-префіксних дублів, бо є /ua/ версія" % (було - len(картки)))
    лог("  мапа сайту: файлів %d, url карток %d, відкинуто як не-картки %d" % (файлів, len(картки), інші))
    return картки, dict(файлів=файлів, карток=len(картки), інших=інші)


def shopify_products_json(транспорт, база, лог, стеля):
    """Shopify: /products.json?limit=250&page=N — публічний за побудовою (П12)."""
    вих, сторінка = [], 1
    шлях = "/products.json"
    while len(вих) < стеля and сторінка <= 40:
        r = транспорт.get(urljoin(база, "%s?limit=250&page=%d" % (шлях, сторінка)))
        if сторінка == 1 and шлях == "/products.json" and (r["код"] != 200 or not (r["тіло"] or "").lstrip().startswith("{")):
            шлях = "/collections/all/products.json"
            r = транспорт.get(urljoin(база, "%s?limit=250&page=%d" % (шлях, сторінка)))
        if r["код"] != 200 or not r["тіло"] or not r["тіло"].lstrip().startswith("{"):
            break
        try:
            д = json.loads(r["тіло"])
        except Exception:
            break
        товари = д.get("products") or []
        if not товари:
            break
        for т in товари:
            if not т.get("published_at") and "published_at" in т:
                continue
            вих.append(dict(канал="shopify:products.json", сирий=т,
                            url=канонічна("/products/%s" % т.get("handle", ""), база)))
        сторінка += 1
    лог("  shopify products.json: %d товарів" % len(вих))
    return вих


def woo_store_api(транспорт, база, лог, стеля):
    """WooCommerce Store API: /wp-json/wc/store/v1/products — публічний без ключа."""
    вих, сторінка = [], 1
    шлях = "/wp-json/wc/store/v1/products"
    while len(вих) < стеля and сторінка <= 60:
        r = транспорт.get(urljoin(база, "%s?per_page=100&page=%d" % (шлях, сторінка)))
        if сторінка == 1 and шлях.endswith("v1/products") and (r["код"] != 200 or not (r["тіло"] or "").lstrip().startswith("[")):
            шлях = "/wp-json/wc/store/products"                      # старіший Woo без v1 (v2 пробувала обидва)
            r = транспорт.get(urljoin(база, "%s?per_page=100&page=%d" % (шлях, сторінка)))
        if r["код"] != 200 or not r["тіло"] or not r["тіло"].lstrip().startswith("["):
            break
        try:
            д = json.loads(r["тіло"])
        except Exception:
            break
        if not д:
            break
        for т in д:
            вих.append(dict(канал="woo:wc/store", сирий=т, url=канонічна(т.get("permalink") or "", база)))
        сторінка += 1
    лог("  woo wc/store: %d товарів" % len(вих))
    return вих


def yml_фід(транспорт, url, лог, стеля):
    """Готовий YML магазину (Prom/Rozetka/Хорошоп-діалекти). Читається діалектно, як feed.py."""
    r = транспорт.get(url, тип="bytes", ліміт=80_000_000)
    if r["код"] != 200 or not r["тіло"] or b"<offer" not in r["тіло"][:200000] and b"<offer" not in r["тіло"]:
        return []
    try:
        корінь = ET.fromstring(r["тіло"])
    except Exception:
        return []
    кат = {c.get("id"): (c.text or "").strip() for c in корінь.iter("category")}
    батько = {c.get("id"): c.get("parentId") for c in корінь.iter("category")}

    def шлях(cid):
        ім, seen = [], set()
        while cid and cid in кат and cid not in seen:
            seen.add(cid); ім.append(кат[cid]); cid = батько.get(cid)
        return " / ".join(reversed(ім))
    вих = []
    for o in корінь.iter("offer"):
        if len(вих) >= стеля:
            break
        params = {}
        for p in o.findall("param"):
            зн = p.findall("value")
            if зн:
                uk = [v for v in зн if (v.get("lang") or "").lower().startswith("uk")]
                текст = "".join((uk or зн)[0].itertext())
            else:
                текст = ", ".join(x for x in ("".join(p.itertext())).split("\n") if x.strip())
            params[(p.get("name") or "").strip()] = " ".join(текст.split())
        назва = (o.findtext("name_ua") or o.findtext("name") or o.findtext("model") or "").strip()
        вих.append(dict(канал="yml:%s" % urlparse(url).path.split("/")[-1][:30],
                        url=канонічна(o.findtext("url") or "", url),
                        сирий=dict(id=o.get("id"), group_id=o.get("group_id") or o.findtext("group_id"),
                                   available=o.get("available"), назва=назва, ціна=o.findtext("price"),
                                   ціна_стара=o.findtext("oldprice"), валюта=o.findtext("currencyId"),
                                   категорія=шлях(o.findtext("categoryId")), vendor=o.findtext("vendor"),
                                   vendorCode=o.findtext("vendorCode") or o.findtext("article"),
                                   фото=[p.text for p in o.findall("picture") if p.text],
                                   опис=" ".join(("".join(o.find("description").itertext()) if o.find("description") is not None else "").split()),
                                   params=params)))
    лог("  yml %s: %d оферів" % (url[:60], len(вих)))
    return вих


def посилання_карток_зі_сторінки(html_текст, база):
    """Запасний канал: JSON-LD ItemList → якорі, схожі на картку (П11: лише коли мапи нема)."""
    вих = []
    for в in json_ld(html_текст):
        if "ItemList" in _тип_ld(в):
            for e in в.get("itemListElement") or []:
                u = (e.get("url") if isinstance(e, dict) else None) or \
                    (e.get("item", {}).get("url") if isinstance(e, dict) and isinstance(e.get("item"), dict) else None)
                if u:
                    вих.append(канонічна(u, база))
    for м in re.finditer(r'href=["\']([^"\'#]+)["\']', html_текст or "", re.I):
        u = канонічна(м.group(1), база)
        if домен_із(u) == домен_із(база) and _КАРТКОПОДІБНИЙ.search(u) and not _НЕ_КАРТКА.search(urlparse(u).path) \
           and not _не_наша_мова(u):
            вих.append(u)
    return list(dict.fromkeys(вих))


_РОЗДІЛ_СЛОВА = re.compile(r"/(catalog|katalog|collections?|category|categories|shop|zhinoch|zhink|women|cholovi|men|"
                           r"odyag|odiag|odezhda|sukni|plattya|vzuttya|sumky|aksesuar|novynky|new|sale|brand)", re.I)


def розділи_зі_сторінки(html_текст, база):
    """Посилання з головної, схожі на розділи: спершу з каталожними словами, потім усі ≤ 3 сегментів
    (проба 05.09: voronin/vmma/twice/friendsoffashion не мали ні мапи, ні «каталожних» слів у шляхах)."""
    ключові, решта = [], []
    for м in re.finditer(r'href=["\']([^"\'#?]+)["\']', html_текст or "", re.I):
        u = канонічна(м.group(1), база)
        if домен_із(u) != домен_із(база) or _не_наша_мова(u):
            continue
        шлях = urlparse(u).path
        if шлях in ("", "/") or шлях.count("/") > 4 or _ЯВНО_КАРТКА.search(u) or _НЕ_КАРТКА.search(шлях) \
           or re.search(r"\.(jpe?g|png|webp|svg|gif|pdf|css|js|xml|ico|zip|mp4)$", шлях, re.I):
            continue
        (ключові if _РОЗДІЛ_СЛОВА.search(шлях) else решта).append(u)
    return list(dict.fromkeys(ключові + решта))


# ═══════════════ 4. РОЗБІР КАРТКИ ═══════════════
# П2: заглушки за адресою (той самий регекс, що feed._НЕ_ФОТО, плюс gif/спінери/іконки).
_НЕ_ФОТО = re.compile(r"\.svg(?:$|\?)|/loader|lazy\.|placeholder|no[-_]?image|empty[-_]?image|default[-_]?image|no[-_]?photo|/cart\.|/stickers?/|mainLoader|"
                      r"\.gif(?:$|\?)|/logo|icon|/flags?/|payment|visa|mastercard|/banner|badge|size[-_]?"
                      r"(chart|table|guide)|tablica|blank\.|spacer|pixel\.|1x1|/social|telegram|viber|"
                      r"instagram|facebook|/thumb(?:nail)?s?/(?:small|xs)|_50x|/50x50|_100x100|data:image", re.I)
# П2: блоки, з яких фото брати не можна — там сусідній товар.
_СУСІДИ = re.compile(r"related|similar|recommend|also|recent|upsell|cross|viewed|carousel-products|"
                     r"product-list|products-list|catalog|listing|footer|header|menu|nav|review|коментар|"
                     r"схож|рекоменд|також|переглянут", re.I)
_РОЗМІР = re.compile(r"^(xxs|xs|s|m|l|xl|xxl|xxxl|3xl|4xl|5xl|6xl|one\s*size|os|onesize|універсальн\w*|"
                     r"\d{2}(?:[.,]5)?(?:\s*[-/–]\s*\d{2})?|\d{2}\s*[-/]\s*\d{2}\s*[-/]\s*\d{2}|"
                     r"\d{2,3}\s*(?:см)?(?:\s*\(\w+\))?|s/m|m/l|l/xl|xs/s|xl/xxl)$", re.I)
_СКЛАД_А = re.compile(r"(\d{1,3})\s*%\s*([а-яіїєґa-z\-']{3,}(?:\s[а-яіїєґa-z\-']{3,})?)", re.I)   # «95% віскоза»
_СКЛАД_Б = re.compile(r"([а-яіїєґa-z\-']{3,})\s*[:\-–]?\s*(\d{1,3})\s*%", re.I)                          # «віскоза 95%»
_НЕ_ВОЛОКНО = re.compile(r"^(склад|состав|матеріал|материал|composition|material|знижк|скидк|акці|off|sale|до|від|поверн|"
                         r"знижка|економ|ціна|price|весь|вся|тканина|fabric)$", re.I)
_ЦІНА = re.compile(r"(\d[\d\s\u00a0]{1,8}(?:[.,]\d{1,2})?)\s*(?:грн|₴|uah)", re.I)
_КЛЮЧІ_ХАРАКТЕРИСТИК = [
 ("колір",   ("колір", "колир", "цвет", "color", "colour", "відтінок")),
 ("склад",   ("склад", "состав", "матеріал", "материал", "material", "тканина", "ткань", "fabric", "composition")),
 ("розмір",  ("розмір", "размер", "size", "розміри", "размеры", "sizes")),
 ("сезон",   ("сезон", "season")),
 ("довжина", ("довжина", "длина", "length")),
 ("рукав",   ("рукав", "sleeve")),
 ("принт",   ("принт", "print", "візерунок", "узор", "малюнок")),
 ("крій",    ("крій", "крой", "силует", "силуэт", "fit", "посадка")),
 ("бренд",   ("бренд", "brand", "виробник", "производитель", "торгова марка", "тм")),
 ("країна",  ("країна", "страна", "country")),
 ("заміри",  ("заміри", "замери", "виміри", "обхват", "measurements", "мірки", "довжина виробу")),
 ("параметри_моделі", ("параметри моделі", "параметры модели", "на моделі", "на модели", "зріст моделі",
                       "рост модели", "модель на фото", "model")),
 ("стать",   ("стать", "пол", "gender", "для кого")),
 ("каблук",  ("каблук", "підбор", "висота каблука", "heel")),
 ("метал",   ("метал", "металл", "покриття", "покрытие", "проба")),
 ("наповнювач", ("наповнювач", "утеплювач", "наполнитель", "утеплитель", "filling")),
 ("підкладка", ("підкладка", "подкладка", "lining")),
 ("догляд",  ("догляд", "уход", "care")),
]


def _ключ_характеристики(назва):
    н = розекранувати(назва).lower().strip(" :·-—")
    for канон, синоніми in _КЛЮЧІ_ХАРАКТЕРИСТИК:
        if any(н == с or н.startswith(с + " ") or н.startswith(с + ":") for с in синоніми):
            return канон
    return None


def _текст(вузол, ліміт=4000):
    if вузол is None:
        return ""
    return розекранувати(вузол.get_text(" ", strip=True))[:ліміт]


def склад_із(текст):
    """«95% бавовна, 5% еластан» → нормалізований рядок; None, коли відсотків нема."""
    if not текст:
        return None
    пари = []
    for м in _СКЛАД_А.finditer(текст):
        n, слово = int(м.group(1)), м.group(2).lower().strip("-'")
        if 0 < n <= 100 and not _НЕ_ВОЛОКНО.match(слово.split()[0]):
            пари.append((n, слово))
    if not пари:
        for м in _СКЛАД_Б.finditer(текст):
            слово, n = м.group(1).lower().strip("-'"), int(м.group(2))
            if 0 < n <= 100 and not _НЕ_ВОЛОКНО.match(слово):
                пари.append((n, слово))
    if not пари:
        return None
    бачено, вих = set(), []
    for n, с in пари:
        if (n, с) not in бачено:
            бачено.add((n, с)); вих.append("%d%% %s" % (n, с))
    return ", ".join(вих)[:200]


def _ціна_число(т):
    if т is None:
        return None
    s = str(т).replace("\u00a0", "").replace(" ", "")
    s = re.sub(r"^(\d{1,3})[,.](\d{3})(?:[.,](\d{1,2}))?$", lambda m: m.group(1) + m.group(2) + ("." + m.group(3) if m.group(3) else ""), s)   # «1,299» / «2.793» / «1,299.00» — тисячі
    s = s.replace(",", ".")
    m = re.search(r"\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        v = float(m.group(0))
    except ValueError:
        return None
    return v if 0 < v < 1_000_000 else None


def _стан_наявності(зн):
    """Три стани (документ 2, 05.09): є / під замовлення / нема; None — не сказано."""
    s = str(зн or "").lower()
    if not s:
        return None
    if any(x in s for x in ("preorder", "pre-order", "backorder", "presale", "під замовлення", "предзаказ", "под заказ")):
        return "під замовлення"
    if any(x in s for x in ("instock", "in_stock", "limitedavailability", "onlineonly", "в наявності", "в наличии")):
        return "є"
    if any(x in s for x in ("outofstock", "out_of_stock", "soldout", "discontinued", "нема", "немає", "нет в наличии", "розпродано")):
        return "нема"
    return None


def оригінал_фото(url):
    """Мініатюра → оригінал: `-388x582.jpg` (WordPress uploads), `_1024x1024.jpg` (Shopify cdn).
    НЕ для `/cache/`: в OpenCart розмір — частина шляху кешу, без нього файла нема
    (05.09: 25union 1 525, diadia 903, welfare 451 «фото не відкривається» — саме через цей зріз)."""
    u = url or ""
    if re.search(r"/cache/|/cachewebp/|/thumb|/resize/|/imgcache/", u, re.I):
        return u
    return re.sub(r"[-_]\d{2,4}x\d{2,4}(?:_crop_[a-z]+)?(?=\.(?:jpe?g|png|webp|avif)(?:\?|$))", "", u, flags=re.I)


def _наявність_ld(зн):
    s = str(зн or "").lower()
    if not s:
        return None
    if any(x in s for x in ("instock", "in_stock", "limitedavailability", "preorder", "onlineonly", "backorder")):
        return True
    if any(x in s for x in ("outofstock", "out_of_stock", "soldout", "discontinued")):
        return False
    return None


def _список(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _ld_картинки(x):
    вих = []
    for e in _список(x):
        if isinstance(e, str):
            вих.append(e)
        elif isinstance(e, dict):
            u = e.get("url") or e.get("contentUrl")
            if u:
                вих.append(u)
    return вих


def факти_з_картки(html_текст, url):
    """Факти з HTML картки, з провенансом. Нічого не судить — лише читає."""
    ф = dict(назва=None, назва_джерело=None, опис=None, ціна=None, ціна_стара=None, валюта=None,
             available=None, наявність=None, фото=[], фото_джерело=None, крихти=[], характеристики={},
             характеристики_сирі=[], розміри=[], розміри_в_наявності=[], розміри_джерело=None, бренд=None,
             артикул=None, id_магазину=None, колір_ld=None, мова_альт=None, group_id=None, варіанти=[],
             свотчі=[], таблиця_мірок=None)
    т = html_текст or ""
    # ── JSON-LD Product / ProductGroup / BreadcrumbList ─────────────────────────
    вузли = json_ld(т)
    продукт = next((в for в in вузли if "ProductGroup" in _тип_ld(в) and not в.get("_у_списку")), None) or \
              next((в for в in вузли if any(x in ("Product", "ProductModel") for x in _тип_ld(в)) and not в.get("_у_списку")), None)
    ф["є_товар"] = продукт is not None
    ф["є_список"] = any(x in ("ItemList", "CollectionPage", "SearchResultsPage") for в in вузли for x in _тип_ld(в))
    for в in вузли:
        типи = _тип_ld(в)
        if "BreadcrumbList" in типи:
            крихти = []
            for e in sorted(_список(в.get("itemListElement")), key=lambda e: (e.get("position") or 0) if isinstance(e, dict) else 0):
                if isinstance(e, dict):
                    ім = e.get("name") or (e.get("item", {}).get("name") if isinstance(e.get("item"), dict) else None)
                    if ім:
                        крихти.append(розекранувати(ім))
            if крихти and not ф["крихти"]:
                ф["крихти"] = крихти
    if продукт:
        p = продукт
        ф["назва"] = розекранувати(p.get("name") or "") or None
        ф["назва_джерело"] = "json-ld"
        ф["опис"] = розекранувати(re.sub(r"<[^>]+>", " ", str(p.get("description") or "")))[:8000] or None
        ф["фото"] = _ld_картинки(p.get("image")); ф["фото_джерело"] = "json-ld" if ф["фото"] else None
        бр = p.get("brand")
        ф["бренд"] = розекранувати(бр.get("name") if isinstance(бр, dict) else бр) if бр else None
        ф["артикул"] = str(p.get("sku") or p.get("mpn") or p.get("productID") or "").strip() or None
        ф["id_магазину"] = str(p.get("productID") or p.get("@id") or p.get("sku") or "").strip()[:80] or None
        ф["group_id"] = str(p.get("productGroupID") or p.get("inProductGroupWithID") or "").strip() or None
        кол = p.get("color")
        ф["колір_ld"] = розекранувати(кол) if isinstance(кол, str) else None
        мат = p.get("material")
        if isinstance(мат, str) and мат.strip():
            ф["характеристики"].setdefault("склад", розекранувати(мат))
        офери = _список(p.get("offers"))
        ціни, наявн = [], []
        for о in офери:
            if not isinstance(о, dict):
                continue
            for ц in (о.get("price"), о.get("lowPrice")):
                v = _ціна_число(ц)
                if v:
                    ціни.append(v)
            if о.get("priceCurrency"):
                ф["валюта"] = str(о["priceCurrency"]).upper()
            н = _наявність_ld(о.get("availability"))
            if н is not None:
                наявн.append(н)
            ст = _стан_наявності(о.get("availability"))
            if ст and not ф["наявність"]:
                ф["наявність"] = ст
            ps = о.get("priceSpecification")
            for спец in _список(ps):
                if isinstance(спец, dict):
                    v = _ціна_число(спец.get("price"))
                    if v:
                        ціни.append(v)
        варіанти = _список(p.get("hasVariant"))
        for в in варіанти:
            if not isinstance(в, dict):
                continue
            вар = dict(назва=розекранувати(в.get("name") or ""), розмір=в.get("size"), колір=в.get("color"),
                       фото=_ld_картинки(в.get("image")), available=None, ціна=None)
            for о in _список(в.get("offers")):
                if isinstance(о, dict):
                    вар["available"] = _наявність_ld(о.get("availability"))
                    вар["ціна"] = _ціна_число(о.get("price")); ф["валюта"] = ф["валюта"] or str(о.get("priceCurrency") or "").upper() or None
                    if вар["ціна"]:
                        ціни.append(вар["ціна"])
                    if вар["available"] is not None:
                        наявн.append(вар["available"])
            if isinstance(вар["розмір"], dict):
                вар["розмір"] = вар["розмір"].get("name")
            ф["варіанти"].append(вар)
        if ціни:
            ф["ціна"] = min(ціни)
        if наявн:
            ф["available"] = any(наявн)
    # ── meta / OpenGraph ───────────────────────────────────────────────────────
    def meta(ім):
        м = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']*)["\']' % re.escape(ім), т, re.I) or \
            re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']%s["\']' % re.escape(ім), т, re.I)
        return розекранувати(м.group(1)) if м else None
    if not ф["назва"]:
        ф["назва"] = meta("og:title"); ф["назва_джерело"] = "og:title" if ф["назва"] else None
    if ф["ціна"] is None:
        ф["ціна"] = _ціна_число(meta("product:price:amount") or meta("og:price:amount"))
        ф["валюта"] = ф["валюта"] or meta("product:price:currency") or meta("og:price:currency")
    if ф["available"] is None:
        ф["available"] = _наявність_ld(meta("product:availability") or meta("og:availability"))
    if not ф["є_товар"]:
        ф["є_товар"] = (meta("og:type") or "").startswith("product") and not ф.get("є_список")
    if re.search(r"/(product-category|category|categories|catalog|katalog|collections?|brand|brands)(/|$)", urlparse(url).path, re.I) \
       and not _ЯВНО_КАРТКА.search(url) and продукт is None:
        ф["є_товар"] = False; ф["є_список"] = True       # розділ за адресою й без Product у розмітці (gepur 154, cher17)
    if not ф["фото"]:
        og = re.findall(r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)["\']', т, re.I)
        if og:
            ф["фото"] = [розекранувати(x) for x in og]; ф["фото_джерело"] = "og:image"
    альт = re.search(r'<link[^>]+hreflang=["\']uk(?:-ua)?["\'][^>]+href=["\']([^"\']+)["\']', т, re.I) or \
           re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+hreflang=["\']uk(?:-ua)?["\']', т, re.I)
    if альт:
        ф["мова_альт"] = канонічна(альт.group(1), url)
    # ── DOM: h1, крихти, характеристики, розміри, галерея, ціна з розмітки ────
    if BeautifulSoup is None:
        return ф
    try:
        суп = BeautifulSoup(т, ПАРСЕР_HTML)
    except Exception as e:                            # noqa
        ф["dom_помилка"] = "%s: %s" % (type(e).__name__, str(e)[:80])   # П15: не мовчати, що DOM не читався
        return ф
    for s in суп(["script", "style", "noscript", "svg"]):
        s.decompose()
    h1 = суп.find("h1")
    h1_текст = _текст(h1, 200) if h1 else ""
    if h1_текст and (not ф["назва"] or російське(ф["назва"]) or re.match(r"^\s*(купити|купить|buy)\b", ф["назва"], re.I)):
        if not російське(h1_текст) and len(h1_текст) >= 3:
            ф["назва"], ф["назва_джерело"] = h1_текст, "h1 (json-ld/og %s)" % ("російською" if ф["назва"] and російське(ф["назва"]) else "«купити…»" if ф["назва"] else "нема")
    if not ф["крихти"]:
        кр = суп.select_one('[class*="breadcrumb"], [id*="breadcrumb"], nav[aria-label*="rumb"], [class*="crumb"]')
        if кр:
            ф["крихти"] = [x for x in (_текст(a, 60) for a in кр.find_all(["a", "li", "span"])) if x and len(x) < 60]
            ф["крихти"] = list(dict.fromkeys(ф["крихти"]))[:8]
    # характеристики: table tr(th|td, td), dl dt/dd, li «ключ: значення», div.label + div.value
    пари = []
    for tr in суп.find_all("tr"):
        кл = tr.find_all(["th", "td"])
        if len(кл) >= 2:
            пари.append((_текст(кл[0], 80), _текст(кл[1], 400)))
    for dl in суп.find_all("dl"):
        dts, dds = dl.find_all("dt"), dl.find_all("dd")
        for a, b in zip(dts, dds):
            пари.append((_текст(a, 80), _текст(b, 400)))
    for li in суп.find_all("li"):
        діти = [x for x in li.find_all(["span", "div", "b", "strong", "p"], recursive=False)]
        if len(діти) == 2:
            пари.append((_текст(діти[0], 80), _текст(діти[1], 400)))
        else:
            tx = _текст(li, 300)
            if ":" in tx and len(tx) < 200:
                a, b = tx.split(":", 1)
                if 2 < len(a) < 40:
                    пари.append((a, b))
    бачені = set()
    for a, b in пари:
        a_, b_ = розекранувати(a).strip(" :·-—")[:60], розекранувати(b)[:400]
        if a_ and b_ and a_.lower() not in бачені and len(ф["характеристики_сирі"]) < 40 and not _РОЗМІР.match(a_.upper()):
            бачені.add(a_.lower()); ф["характеристики_сирі"].append([a_, b_])
        k = _ключ_характеристики(a)
        if k and b and k not in ф["характеристики"]:
            ф["характеристики"][k] = b_
    # таблиця мірок виробу (см по розмірах): ≥ 3 колонки й шапка про розмір/обхват — verbatim
    for tbl in суп.find_all("table"):
        рядки_т = [[_текст(c, 40) for c in tr.find_all(["th", "td"])] for tr in tbl.find_all("tr")]
        рядки_т = [r for r in рядки_т if len(r) >= 3]
        if len(рядки_т) >= 2 and re.search(r"розмір|size|обхват|груд|талі|стегн|довжин|рукав|плеч|\bсм\b", " ".join(рядки_т[0]), re.I):
            ф["таблиця_мірок"] = " ; ".join(" | ".join(r) for r in рядки_т)[:800]; break
    # свотчі кольору: елемент зі стилем background/data-hex або картинкою, підпис з title/alt/тексту
    for ел in суп.select('[class*="swatch"], [class*="color"], [class*="colour"], [class*="kolir"], [class*="colir"], [data-color], [data-hex]'):
        стиль = ел.get("style") or ""
        hex_ = None
        м = re.search(r"#([0-9a-f]{6}|[0-9a-f]{3})\b", стиль + " " + str(ел.get("data-color") or "") + " " + str(ел.get("data-hex") or ""), re.I)
        if м:
            hex_ = м.group(1).lower()
            hex_ = "#" + ("".join(c * 2 for c in hex_) if len(hex_) == 3 else hex_)
        else:
            м = re.search(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", стиль)
            if м:
                hex_ = "#%02x%02x%02x" % tuple(int(x) for x in м.groups())
        img = ел.find("img") if ел.name != "img" else ел
        кар = канонічна(img.get("data-src") or img.get("src") or "", url) if img else None
        if not hex_ and not кар:
            continue
        підпис = розекранувати(ел.get("title") or ел.get("aria-label") or ел.get("data-title") or ел.get("data-value") or
                              (img.get("alt") if img else "") or _текст(ел, 30))[:40]
        активний = bool(re.search(r"active|selected|checked|current", " ".join(ел.get("class") or []) + " " + str(ел.get("aria-checked") or ""), re.I))
        if len(ф["свотчі"]) < 20:
            ф["свотчі"].append(dict(назва=підпис or None, hex=hex_, фото=кар, активний=активний))
    # рядки «Склад: …» у будь-якому тексті сторінки
    if "склад" not in ф["характеристики"]:
        м = re.search(r"(?:склад|состав|матеріал|material)\s*[:\-–]\s*([^\n<]{5,160})", суп.get_text("\n"), re.I)
        if м:
            ф["характеристики"]["склад"] = розекранувати(м.group(1))
    # розміри: контейнери, чиї клас/ім'я/текст мітки кажуть «розмір»
    розміри, в_наявн = [], []
    for конт in суп.select('[class*="size"], [class*="rozmir"], [class*="razmer"], [id*="size"], [data-attribute*="size"],'
                           ' select[name*="size"], select[name*="rozmir"], [class*="variant"], [class*="option"]'):
        for ел in конт.find_all(["option", "button", "label", "a", "li", "span", "input", "div"]):
            текст = (ел.get("value") if ел.name in ("input", "option") and not _текст(ел, 20) else _текст(ел, 20)) or ""
            текст = текст.strip().upper()
            if not текст or not _РОЗМІР.match(текст) or len(текст) > 12:
                continue
            класи = " ".join(ел.get("class") or []) + " " + " ".join(конт.get("class") or []) + " " + str(ел.get("disabled") or "")
            немає = bool(re.search(r"disabled|out|sold|unavail|нема|немає|відсут|inactive|soldout|not-available", класи, re.I)) \
                    or ел.has_attr("disabled")
            if текст not in розміри:
                розміри.append(текст)
                if not немає:
                    в_наявн.append(текст)
    if розміри and not ф["варіанти"]:
        ф["розміри"], ф["розміри_в_наявності"], ф["розміри_джерело"] = розміри[:20], в_наявн[:20], "dom"
    # галерея — лише коли JSON-LD/og дали < 2 фото; блоки сусідів вирізаються
    if len(ф["фото"]) < 2:
        for сус in суп.select('[class*="related"], [class*="similar"], [class*="recommend"], [class*="also"], '
                              '[class*="recent"], [class*="upsell"], [class*="viewed"], footer, header, nav'):
            сус.decompose()
        галерея = суп.select_one('[class*="gallery"], [class*="product-image"], [class*="product__media"], '
                                 '[class*="swiper"], [class*="slider"], [class*="fotorama"], [class*="carousel"], '
                                 '[class*="photos"], [class*="images"], [class*="product-photo"]') or суп
        картинки = []
        for img in галерея.find_all(["img", "source", "a"]):
            for атр in ("data-src", "data-lazy", "data-original", "data-zoom-image", "data-large", "data-full",
                        "data-srcset", "srcset", "src", "href"):
                v = img.get(атр)
                if not v:
                    continue
                if атр in ("srcset", "data-srcset"):
                    кандидати_ = []
                    for частина in v.split(","):
                        ч = частина.strip().split()
                        if ч:
                            шир = int(re.sub(r"\D", "", ч[1]) or 0) if len(ч) > 1 else 0
                            кандидати_.append((шир, ч[0]))
                    v = max(кандидати_)[1] if кандидати_ else ""
                if not v:
                    continue
                if img.name == "a" and not re.search(r"\.(jpe?g|png|webp|avif)(\?|$)", v, re.I):
                    continue
                w = img.get("width")
                if w and str(w).isdigit() and int(w) <= 300:
                    continue
                картинки.append(оригінал_фото(канонічна(v, url)))
                break
        для = [x for x in dict.fromkeys(картинки) if re.search(r"\.(jpe?g|png|webp|avif)(\?|$)|/image|/photo|/img|/media|/upload", x, re.I)]
        if для:
            ф["фото"] = list(dict.fromkeys(ф["фото"] + для)); ф["фото_джерело"] = (ф["фото_джерело"] or "") + "+галерея"
    # ціна з розмітки, якщо структурні джерела мовчали
    if ф["ціна"] is None:
        ел = суп.select_one('[itemprop="price"], [class*="price"] , [id*="price"]')
        if ел and суп.find("h1") and not ф["є_товар"] and not ф.get("є_список"):
            цін = len(суп.select('[itemprop="price"], [class*="price"]'))
            є_кнопка = bool(re.search(r"кошик|корзин|купити|купить|add to cart|add to bag|\bbuy\b|замовити|заказать", суп.get_text(" ")[:200000], re.I))
            ф["є_товар"] = 1 <= цін <= 6 and є_кнопка      # лістинг: десятки цін; картка: одна-дві
        if ел:
            v = _ціна_число(ел.get("content") or ел.get("data-price") or None)
            if v is None:
                м = _ЦІНА.search(_текст(ел, 120))
                v = _ціна_число(м.group(1)) if м else None
            if v:
                ф["ціна"] = v; ф["валюта"] = ф["валюта"] or "UAH"
        if ф["ціна"] is None:
            ф["ціна_діагностика"] = " | ".join(_текст(e, 60) for e in суп.select('[class*="price"], [itemprop="price"]')[:3]) or None
    if ф["available"] is None:
        текст_низ = суп.get_text(" ").lower()
        # лише з тексту сторінки — ПІДКАЗКА: «нема в наявності» може стояти біля одного розміру чи в шаблоні
        # (welfare 05.09: 1 474 живих товари відкинуто). Відмова — тільки зі структурних джерел.
        if re.search(r"під замовлення|предзаказ|pre-?order", текст_низ):
            ф["available"] = True; ф["наявність"] = ф["наявність"] or "під замовлення"
        elif re.search(r"в наявності|є в наявності|in stock|додати (в|до) кошик|купити", текст_низ) and \
             not re.search(r"нема[єе]? в наявності|немає в наявності|розпродано|sold out|out of stock|нет в наличии", текст_низ):
            ф["available"] = True; ф["наявність"] = ф["наявність"] or "є"
        elif re.search(r"нема[єе]? в наявності|немає в наявності|розпродано|sold out|out of stock", текст_низ):
            ф["наявність"] = ф["наявність"] or "невідомо (на сторінці є «нема в наявності»)"
    if not ф["опис"] or російське(ф["опис"]):
        оп = суп.select_one('[itemprop="description"], [class*="description"], [id*="description"], [class*="desc"]')
        if оп:
            т_ = _текст(оп, 8000)
            if т_ and (not ф["опис"] or not російське(т_)):
                ф["опис"] = т_
    return ф


# ═══════════════ 5. ФАКТИ З BULK-КАНАЛІВ ═══════════════
def факти_shopify(т, база):
    """products.json → факти. Кожен колір — окрема річ зі своїми фото (variant_ids у images)."""
    опції = {(о.get("name") or "").strip().lower(): о.get("values") or [] for о in т.get("options") or []}
    ім_кольору = next((n for n in опції if re.search(r"кол[іи]р|цвет|colou?r", n)), None)
    ім_розміру = next((n for n in опції if re.search(r"розм[іи]р|размер|size", n)), None)
    поз = {("option%d" % (i + 1)): (о.get("name") or "").strip().lower() for i, о in enumerate(т.get("options") or [])}
    варіанти = т.get("variants") or []
    групи = collections.OrderedDict()
    for v in варіанти:
        колір = розмір = None
        for k, ім in поз.items():
            if ім == ім_кольору:
                колір = v.get(k)
            if ім == ім_розміру:
                розмір = v.get(k)
        групи.setdefault(колір, []).append((v, розмір))
    картинки = т.get("images") or []
    опис = розекранувати(re.sub(r"<[^>]+>", " ", т.get("body_html") or ""))[:8000] or None
    вих = []
    for колір, вар in групи.items():
        ід = {v.get("id") for v, _ in вар}
        свої = [i.get("src") for i in картинки if set(i.get("variant_ids") or []) & ід]
        фото = свої or [i.get("src") for i in картинки]
        ціни = [_ціна_число(v.get("price")) for v, _ in вар if _ціна_число(v.get("price"))]
        старі = [_ціна_число(v.get("compare_at_price")) for v, _ in вар if _ціна_число(v.get("compare_at_price"))]
        розміри = [str(р).upper() for _, р in вар if р]
        в_наявн = [str(р).upper() for v, р in вар if р and v.get("available")]
        є = any(v.get("available") for v, _ in вар)
        вих.append(dict(назва=розекранувати(т.get("title") or ""), назва_джерело="shopify",
                        опис=опис, ціна=min(ціни) if ціни else None, ціна_стара=max(старі) if старі else None,
                        валюта=None, available=є, наявність=("є" if є else "нема"),
                        id_магазину=str(т.get("id") or ""), характеристики_сирі=([["Тип (магазин)", т.get("product_type")]] if т.get("product_type") else []) +
                        ([["Теги (магазин)", ", ".join(x for x in т.get("tags") or [] if isinstance(x, str))[:400]]] if т.get("tags") else []),
                        свотчі=[], таблиця_мірок=None,
                        фото=[оригінал_фото(канонічна(x, база)) for x in фото if x], фото_джерело="shopify:images",
                        крихти=[x for x in (т.get("product_type") or "",) if x] + [t for t in (т.get("tags") or [])[:10] if isinstance(t, str)],
                        характеристики=({"колір": розекранувати(колір)} if колір else {}),
                        розміри=розміри, розміри_в_наявності=в_наявн, розміри_джерело="shopify:variants" if розміри else None,
                        бренд=розекранувати(т.get("vendor") or "") or None,
                        артикул=next((v.get("sku") for v, _ in вар if v.get("sku")), None),
                        колір_ld=None, мова_альт=None, group_id=str(т.get("id") or ""), варіанти=[],
                        url=канонічна("/products/%s" % т.get("handle", ""), база) + (("?variant=%s" % вар[0][0].get("id")) if колір and len(групи) > 1 else "")))
    return вих


def факти_woo(т, база):
    """Store API → факти. Ціни в дрібних одиницях (currency_minor_unit)."""
    ц = т.get("prices") or {}
    div = 10 ** int(ц.get("currency_minor_unit") or 2)
    def гр(x):
        v = _ціна_число(x)
        return (v / div) if v else None
    атр = {(a.get("name") or "").lower(): [x.get("name") for x in (a.get("terms") or [])] for a in т.get("attributes") or []}
    колір = next((v for k, v in атр.items() if re.search(r"кол[іи]р|цвет|colou?r", k)), [])
    розміри = next((v for k, v in атр.items() if re.search(r"розм[іи]р|размер|size", k)), [])
    хар = {}
    if колір:
        хар["колір"] = ", ".join(x for x in колір if x)
    for a in т.get("attributes") or []:
        k = _ключ_характеристики(a.get("name") or "")
        if k and k not in хар:
            хар[k] = ", ".join(x.get("name") for x in (a.get("terms") or []) if x.get("name"))
    сирі = [[a.get("name") or "", ", ".join(x.get("name") for x in (a.get("terms") or []) if x.get("name"))] for a in т.get("attributes") or []]
    стан = "є" if т.get("is_in_stock") else ("під замовлення" if т.get("is_on_backorder") else "нема")
    return [dict(назва=розекранувати(т.get("name") or ""), назва_джерело="woo",
                 опис=розекранувати(re.sub(r"<[^>]+>", " ", (т.get("description") or т.get("short_description") or "")))[:8000] or None,
                 ціна=гр(ц.get("price")), ціна_стара=(гр(ц.get("regular_price")) if ц.get("sale_price") and ц.get("regular_price") != ц.get("price") else None),
                 валюта=ц.get("currency_code"), available=(стан != "нема"), наявність=стан, id_магазину=str(т.get("id") or ""),
                 характеристики_сирі=[x for x in сирі if x[0] and x[1]], свотчі=[], таблиця_мірок=None,
                 фото=[оригінал_фото(канонічна(i.get("src"), база)) for i in (т.get("images") or []) if i.get("src")], фото_джерело="woo:images",
                 крихти=[c.get("name") for c in (т.get("categories") or []) if c.get("name")],
                 характеристики=хар, розміри=[str(x).upper() for x in розміри if x],
                 розміри_в_наявності=([str(x).upper() for x in розміри if x] if т.get("is_in_stock") else []),
                 розміри_джерело="woo:attributes" if розміри else None,
                 бренд=None, артикул=(т.get("sku") or None), колір_ld=None, мова_альт=None,
                 group_id=str(т.get("parent") or т.get("id") or ""), варіанти=[],
                 url=канонічна(т.get("permalink") or "", база))]


def факти_yml(с, база):
    p = с.get("params") or {}
    хар = {}
    for k, v in p.items():
        kk = _ключ_характеристики(k)
        if kk and v and kk not in хар:
            хар[kk] = v
    розміри = [x.strip().upper() for x in re.split(r"[,;|/]", хар.get("розмір", "")) if x.strip()][:20]
    дост = None
    a = (с.get("available") or "").strip().lower()
    if a in ("true", "1"):
        дост = True
    elif a in ("false", "0", ""):
        дост = False
    return [dict(назва=розекранувати(с.get("назва") or ""), назва_джерело="yml",
                 опис=(с.get("опис") or "")[:8000] or None, ціна=_ціна_число(с.get("ціна")),
                 ціна_стара=_ціна_число(с.get("ціна_стара")), валюта=(с.get("валюта") or "").upper() or None,
                 available=дост, наявність=(None if дост is None else ("є" if дост else "нема")),
                 характеристики_сирі=[[k, v] for k, v in p.items() if k and v][:40], свотчі=[], таблиця_мірок=None,
                 фото=[оригінал_фото(канонічна(x, база)) for x in с.get("фото") or []], фото_джерело="yml:picture",
                 крихти=[x for x in (с.get("категорія") or "").split(" / ") if x], характеристики=хар,
                 розміри=розміри, розміри_в_наявності=(розміри if дост else []), розміри_джерело="yml:param" if розміри else None,
                 бренд=(с.get("vendor") or None), артикул=(с.get("vendorCode") or None), колір_ld=None, мова_альт=None,
                 group_id=(с.get("group_id") or None), варіанти=[], url=с.get("url") or "", id_магазину=с.get("id"))]


# ═══════════════ 6. СУДЖЕННЯ ПОЛІВ (стать, слот, колір) ═══════════════
_СЛАГ_СЛОТ = [   # транслітерації українських іменників у слагах; короткі основи — лише як окреме слово (laptop ≠ top, spring ≠ ring)
 ("верхній_шар", r"palto|(?<!waist)coat|trench|puhov|pukhov|(?:^|[-/])down-|kurtk|jacket|shub|(?:^|[-/])fur-|plash|park[ai]|vitrovk|vetrovk|bomber|dublyank|anorak|puffer|poncho|kozhuh|kozhukh"),
 ("сукня", r"sukn|plat(?:t|ya|ie|te)|dress|sarafan|kombinezon|jumpsuit|overall"),
 ("верх", r"bluz|blouse|shirt|sorochk|(?:^|[-/])top(?:[-/]|$)|sweat|hoodie|hudi|zhaket|pidzhak|blazer|cardigan|kardigan|jumper|sweater|svetr|sviter|svitshot|longsleeve|longsliv|(?:^|[-/])bod[iy](?:[-/]|$)|futbolk|t-shirt|tshirt|(?:^|[-/])polo(?:[-/]|$)|vodolazk|(?:^|[-/])golf|zhylet|zhilet|(?:^|[-/])vest(?:[-/]|$)|tunik|tunic|kofta|koft"),
 ("низ", r"shtan|bryuk|pants|trousers|jeans|dzhins|skirt|spidny|yubk|(?:^|[-/])short|leg[gi]n|kulot|culotte|bridzh"),
 ("взуття", r"vzutt|shoes|boot|cherevyk|chobot|sneaker|krosivk|(?:^|[-/])ked[iy]|tufl|loafer|lofer|sandal|bosonizhk|(?:^|[-/])mule|myuli|slipon|balet|espadr|oxford|brog|derby|(?:^|[-/])sabo|(?:^|[-/])ugg|botil|mokasyn|moccasin|slingback|shlopan|vyetnamk"),
 ("сумка", r"sumk|(?:^|[-/])bags?(?:[-/]|$)|backpack|ryukzak|clutch|klatch|shopper|shoper|(?:^|[-/])tote"),
 ("шарф", r"sharf|scarf|hustk|hustyn|snood|snud|palantyn|stole"),
 ("прикраси", r"prykras|jewel|serezhk|serg|earring|necklace|kolye|bracelet|braslet|(?:^|[-/])rings?(?:[-/]|$)|kabluchk|kilce|kiltse|pidvisk|kulon|namyst|brosh|choker"),
 ("головний_убір", r"shapk|(?:^|[-/])hats?(?:[-/]|$)|kepk|(?:^|[-/])caps?(?:[-/]|$)|kapelyukh|beret|panam|beanie"),
 ("пояс", r"poyas|(?:^|[-/])belt|remin|remen"),
 ("колготи", r"kolgot|tights|stockings|panchoh"),
 ("шкарпетки", r"shkarpet|socks|nosk"),
]
# П8: основа в назві → канонічне слово (чоловічий рід), бо «чорна»/«чорні»/«чорну» — одна кольороназва
# для лексикону. Префікс темно-/світло-/ніжно-/яскраво- переноситься.
_КОЛЬОРИ_КАНОН = {
 "чорн": "чорний", "біл": "білий", "бежев": "бежевий", "беж": "бежевий", "червон": "червоний", "салатов": "салатовий",
 "коричнев": "коричневий", "бордов": "бордовий", "бордо": "бордовий", "сір": "сірий", "син": "синій", "зелен": "зелений",
 "рожев": "рожевий", "золот": "золотий", "срібляст": "сріблястий", "срібл": "сріблястий", "срібн": "срібний",
 "молочн": "молочний", "блакитн": "блакитний", "фіолетов": "фіолетовий", "оливков": "оливковий", "олив": "оливковий",
 "хакі": "хакі", "коралов": "кораловий", "корал": "кораловий", "гірчичн": "гірчичний", "пісочн": "пісочний",
 "кремов": "кремовий", "карамельн": "карамельний", "карамел": "карамельний", "мокко": "мокко", "шоколадн": "шоколадний",
 "шоколад": "шоколадний", "вишнев": "вишневий", "жовт": "жовтий", "оранжев": "помаранчевий", "помаранчев": "помаранчевий",
 "бузков": "бузковий", "лавандов": "лавандовий", "лаванд": "лавандовий", "бірюзов": "бірюзовий", "бірюз": "бірюзовий",
 "м'ятн": "м'ятний", "м’ятн": "м'ятний", "мятн": "м'ятний", "персиков": "персиковий", "пудров": "пудровий",
 "графітов": "графітовий", "графіт": "графітовий", "антрацитов": "антрацитовий", "антрацит": "антрацитовий",
 "смарагдов": "смарагдовий", "смарагд": "смарагдовий", "індиго": "індиго", "марсал": "марсала", "фуксі": "фуксія",
 "лілов": "ліловий", "айворі": "айворі", "капучино": "капучино", "кавов": "кавовий", "малинов": "малиновий",
 "пурпуров": "пурпуровий", "пурпур": "пурпуровий", "нюд": "нюд", "камуфляж": "камуфляж", "мультиколор": "мультиколор",
 "різнокольоров": "різнокольоровий", "какао": "какао", "кемел": "кемел", "верблюж": "верблюжий", "мідн": "мідний",
 "бронзов": "бронзовий", "теракотов": "теракотовий", "теракот": "теракотовий", "охр": "охра", "хвойн": "хвойний",
 "трав'ян": "трав'яний", "небесн": "небесний", "лимонн": "лимонний", "пшеничн": "пшеничний", "перлинн": "перлинний",
 "металік": "металік", "сталев": "сталевий", "димчаст": "димчастий", "чорнильн": "чорнильний", "сливов": "сливовий",
 "баклажанов": "баклажановий", "фісташков": "фісташковий", "гранатов": "гранатовий", "піщан": "пісочний",
 "тауп": "тауп", "екрю": "екрю", "ванільн": "ванільний", "кавуновий": "кавуновий", "лососев": "лососевий",
 "ультрамарин": "ультрамарин", "кобальт": "кобальтовий", "електрик": "електрик", "ментолов": "ментоловий",
}
_КОЛЬОРИ_РЕ = re.compile(r"\b((?:темно|світло|ніжно|яскраво|блідо|насичено|глибоко)[- ])?(%s)[а-яіїєґ'’]*\b"
                         % "|".join(sorted((re.escape(k) for k in _КОЛЬОРИ_КАНОН), key=len, reverse=True)), re.I)
_КОЛЬОРИ_ЛАТ = {"black": "чорний", "white": "білий", "beige": "бежевий", "red": "червоний", "brown": "коричневий",
                "burgundy": "бордовий", "bordo": "бордовий", "grey": "сірий", "gray": "сірий", "blue": "синій", "navy": "темно-синій",
                "green": "зелений", "pink": "рожевий", "gold": "золотий", "silver": "сріблястий", "milk": "молочний",
                "ivory": "айворі", "olive": "оливковий", "khaki": "хакі", "coral": "кораловий", "mustard": "гірчичний",
                "sand": "пісочний", "cream": "кремовий", "caramel": "карамельний", "mocha": "мокко", "chocolate": "шоколадний",
                "cherry": "вишневий", "yellow": "жовтий", "orange": "помаранчевий", "lilac": "бузковий", "lavender": "лавандовий",
                "turquoise": "бірюзовий", "mint": "м'ятний", "peach": "персиковий", "powder": "пудровий", "graphite": "графітовий",
                "emerald": "смарагдовий", "camel": "кемел", "nude": "нюд", "purple": "фіолетовий", "violet": "фіолетовий",
                "chorn": "чорний", "bil": "білий", "bezh": "бежевий", "chervon": "червоний", "korychnev": "коричневий",
                "bordov": "бордовий", "sir": "сірий", "syn": "синій", "zelen": "зелений", "rozhev": "рожевий",
                "zolot": "золотий", "srib": "сріблястий", "moloch": "молочний", "blakytn": "блакитний", "fiolet": "фіолетовий",
                "oliv": "оливковий", "khaki": "хакі", "koral": "кораловий", "hirchych": "гірчичний", "pisoch": "пісочний",
                "kremov": "кремовий", "karamel": "карамельний", "mokko": "мокко", "shokolad": "шоколадний",
                "vyshnev": "вишневий", "zhovt": "жовтий", "oranzh": "помаранчевий", "buzk": "бузковий", "lavand": "лавандовий",
                "biryuz": "бірюзовий", "myatn": "м'ятний", "persyk": "персиковий", "pudrov": "пудровий", "salatov": "салатовий",
                "temno-syn": "темно-синій", "temno": "темний", "svitlo": "світлий"}


def стать_речі(крихти, url, назва, теги=(), типова=None):
    """→ (стать, джерело). Дитяче — окремо, воно не наш каталог (П4)."""
    джерела = [("крихти", " / ".join(крихти or [])), ("url", urlparse(url or "").path),
               ("назва", назва or ""), ("теги", " ".join(теги or []))]
    for ім, текст in джерела:
        if not текст:
            continue
        збіги = [с for с, р in _СТАТЬ if р.search(текст)]
        if "дитяче" in збіги and ("чоловіче" not in збіги and "жіноче" not in збіги):
            return "дитяче", ім
        if "унісекс" in збіги or ("чоловіче" in збіги and "жіноче" in збіги):
            return "унісекс", ім
        if "чоловіче" in збіги:
            return "чоловіче", ім
        if "жіноче" in збіги:
            return "жіноче", ім
    if типова and типова != "невідомо":
        return типова, "типова для магазину"
    return "невідомо", "не названо"


def _слот_у_тексті(текст):
    т = (текст or "").lower()
    for сл, ключі in СЛОТ_КЛЮЧІ:
        for k in ключі:
            if k in т:
                пастки = ПАСТКИ_ПІДРЯДКА.get(k)
                if пастки and any(p in т for p in пастки):
                    continue
                return сл, k
    return None, None


def слот_речі(крихти, назва, url):
    """→ (слот, джерело) або (None, причина). Крихти → назва → слаг (П3)."""
    низ = (назва or "").lower()
    if any(x in низ for x in НЕ_ОДЯГ) or any(x in низ for x in ПОЗА_СЛОТАМИ):
        return None, "поза слотами (не одяг образу)"
    # КОМПЛЕКТ (рішення власника 01.09: не чіпати, бо дві речі в одному SKU): збирається зі слотом
    # «комплект». feed.слот() цього імені не знає → у пул не йде, але дані є, коли композитор навчиться.
    перше = низ.split()[0] if низ.split() else ""
    if re.match(r"^(костюм|комплект|двійка|трійка|набір)", перше) and not перше.startswith("костюмн"):
        return "комплект", "перше слово назви (дві речі в одному SKU)"
    # НАЗВА вирішує родину, коли її іменник однозначний — це те, що людина бачить (П3: «Сумка Maybelle» у «верх»).
    зн, k_н = _слот_у_тексті(назва)
    for кр in reversed(крихти or []):          # найглибша крихта — найточніша
        зк, k_к = _слот_у_тексті(кр)
        if зк:
            if зн and зн != зк and _слот_у_тексті(назва.split()[0] if назва else "")[0] == зн:
                return зн, "назва (перше слово) переважила крихту «%s»" % кр
            return зк, "крихта «%s»" % кр
    if зн:
        return зн, "назва «%s»" % k_н
    слаг = urlparse(url or "").path.lower()
    for сл, р in _СЛАГ_СЛОТ:
        if re.search(р, слаг):
            return сл, "слаг url"
    return None, "слот не визначено"


def колір_речі(характеристики, назва, url, колір_ld=None):
    """→ (колір, акценти, джерело). Характеристика → JSON-LD → назва → слаг (П8)."""
    сирий = (характеристики or {}).get("колір") or колір_ld
    if сирий:
        части = [x.strip() for x in re.split(r"\s*[,|/]\s*|\s+та\s+|\s+і\s+", сирий) if x.strip()]
        if части and not російське(части[0]):
            return части[0].lower(), [x.lower() for x in части[1:3]], "характеристика картки" if (характеристики or {}).get("колір") else "json-ld"
    низ = (назва or "").lower()
    м = _КОЛЬОРИ_РЕ.search(низ)
    if м:
        преф = (м.group(1) or "").replace(" ", "-")
        return преф + _КОЛЬОРИ_КАНОН[м.group(2).lower()], [], "слово в назві"
    слаг = urlparse(url or "").path.lower()
    for лат, укр in sorted(_КОЛЬОРИ_ЛАТ.items(), key=lambda kv: -len(kv[0])):
        if re.search(r"(?:^|[-_/])%s" % лат, слаг):
            return укр, [], "слаг url"
    return None, [], "не названо"


# ═══════════════ 7. ГЕЙТИ РЕЧІ (П14: поіменно, на рівні речі) ═══════════════
_СМІТТЯ_НАЗВИ = re.compile(r"!\[|\]\(|https?://|<[a-z/]|\bImage\s*\d|^\s*(картинка|зображення|фото)\s|"
                          r"додати (в|до) кошик|у кошик|інтернет-магазин|в наявності|детальніше|переглянути|"
                          r"^\s*(sale|new|акція|знижк)\s*$", re.I)
_ГОЛОВА_НАЗВИ = re.compile(r"^\s*(купити|купить|buy|замовити)\s+", re.I)
_ХВІСТ_НАЗВИ = re.compile(r"[\s\-–|·]+(\d[\d\s]*(?:[.,]\d+)?\s*(?:грн|₴|uah)\.?|фото\s*\d*|"
                          r"\|\s*[^|]{0,40}\bфото\b|SS'?\d{2,4}|-\d{1,2}%|new|sale)\s*$", re.I)
ЦІНА_МІН, ЦІНА_МАКС = 30.0, 300_000.0


def чиста_назва(назва):
    н = розекранувати(назва or "")
    н = re.sub(r"\s*[|·]\s*[^|·]{0,60}$", lambda m: "" if re.search(r"магазин|shop|store|купити|інтернет", m.group(0), re.I) else m.group(0), н)
    н = _ГОЛОВА_НАЗВИ.sub("", н)            # «Купити жіночі шкіряні лофери | Welfare» → SEO-заголовок, не назва
    попередня = None
    while н != попередня:
        попередня = н
        н = _ХВІСТ_НАЗВИ.sub("", н).strip(" -–|·,")
    return н[:200]


def гейти_речі(з):
    """→ список причин відхилення; порожній — річ у каталог."""
    причини = []
    н = з.get("назва") or ""
    if len(н) < 3 or _СМІТТЯ_НАЗВИ.search(н):
        причини.append("назва: сміття або порожньо")
    рос = російське(н)
    if рос:
        причини.append("назва російською (%s)" % ", ".join(рос[:3]))
    ц = з.get("ціна")
    if ц is None:
        причини.append("ціни нема")
    elif not (ЦІНА_МІН <= ц <= ЦІНА_МАКС):
        причини.append("ціна поза межами (%s)" % ц)
    if з.get("валюта") and з["валюта"] not in ("UAH", "ГРН", "UA"):
        причини.append("валюта не UAH (%s)" % з["валюта"])
    if not з.get("фото"):
        причини.append("фото нема після чистки")
    if not з.get("слот"):
        причини.append(з.get("слот_джерело") or "слот не визначено")
    if з.get("стать") == "дитяче":
        причини.append("дитяче — не наш каталог")
    if з.get("available") is False and not з.get("розміри_в_наявності"):
        причини.append("нема в наявності")
    if not з.get("url") or not з["url"].startswith("http"):
        причини.append("адреси нема")
    return причини


def чисті_фото(фото, url="", артикул=None, відкинуті=None):
    вих = []
    for ф in фото or []:
        if not ф or _НЕ_ФОТО.search(ф) or not ф.startswith("http"):
            if відкинуті is not None and ф and len(відкинуті) < 3:
                відкинуті.append(ф)
            continue
        ф = оригінал_фото(ф)                       # документ 2: оригінал, не мініатюра
        if ф not in вих:
            вих.append(ф)
    # П2, доказовий фільтр gepur: номер товару з url у шляху картинки — лишаються лише «свої»
    м = re.search(r"-(\d{3,})/?$", url or "")
    номери = [м.group(1)] if м else []
    if артикул and re.fullmatch(r"\d{3,}", str(артикул)):
        номери.append(str(артикул))
    for ном in номери:
        свої = [ф for ф in вих if ("/%s/" % ном) in ф or ("/%s_" % ном) in ф or ("_%s_" % ном) in ф]
        if свої:
            return свої[:8]
    return вих[:8]


# ═══════════════ 8. МАГАЗИН ЦІЛКОМ ═══════════════
def _ім_каналу(каналів):
    return "+".join(dict.fromkeys(каналів)) or "нема"





def nema_str(поля):
    return ", ".join(поля) if поля else None


def канонічний_запис(ф, маг, канал):
    """Факти → запис каталогу (без гейтів). Усе, що судиться, — з провенансом."""
    url = ф.get("url") or ""
    назва = чиста_назва(ф.get("назва"))
    хар = dict(ф.get("характеристики") or {})
    склад = склад_із(хар.get("склад")) or склад_із(ф.get("опис")) or (хар.get("склад") if хар.get("склад") and len(хар["склад"]) < 80 else None)
    колір, акценти, кол_дж = колір_речі(хар, назва, url, ф.get("колір_ld"))
    крихти = [x for x in (ф.get("крихти") or []) if x and not re.match(r"^(головна|home|main|каталог)$", x, re.I)]
    стать, ст_дж = стать_речі(крихти, url, назва, теги=(ф.get("крихти") or [])[-10:], типова=маг.get("стать_типово"))
    if стать == "невідомо" and хар.get("стать"):
        стать, ст_дж = стать_речі([], "", хар["стать"], типова=None)
        ст_дж = "характеристика"
    слот, сл_дж = слот_речі(крихти, назва, url)
    опис, опис_рос, мова_опису = ф.get("опис"), None, None
    if опис and російське(опис):
        опис_рос, опис, мова_опису = опис, None, "рос"      # лишається в сирих жнивах, людині не йде
    # свотч цієї речі: активний → єдиний → за словом кольору
    свотчі = ф.get("свотчі") or []
    свотч = next((x for x in свотчі if x.get("активний")), None) or (свотчі[0] if len(свотчі) == 1 else None) or \
            next((x for x in свотчі if колір and x.get("назва") and колір.split("-")[-1][:4] in x["назва"].lower()), None)
    розміри = ф.get("розміри") or []
    в_наявн = ф.get("розміри_в_наявності") or []
    if ф.get("варіанти") and not розміри:
        розміри = [str(v["розмір"]).upper() for v in ф["варіанти"] if v.get("розмір")]
        в_наявн = [str(v["розмір"]).upper() for v in ф["варіанти"] if v.get("розмір") and v.get("available")]
    сира = розекранувати(ф.get("назва") or "")
    наявн = ф.get("наявність") or (None if ф.get("available") is None else ("є" if ф.get("available") else "нема")) or "невідомо"
    нема = [x for x, v in (("колір", колір), ("склад", склад), ("розміри", розміри), ("опис", опис or опис_рос),
                          ("заміри", хар.get("заміри") or ф.get("таблиця_мірок")), ("свотч", свотч),
                          ("характеристики", ф.get("характеристики_сирі")), ("крихти", крихти)) if not v]
    відкинуті_фото = []
    фото = чисті_фото(ф.get("фото"), url, ф.get("артикул"), відкинуті_фото)
    return dict(
        url=url, назва=назва, назва_сира=(сира if сира != назва else None), назва_джерело=ф.get("назва_джерело"),
        фото_відкинуто=("; ".join(відкинуті_фото) if відкинуті_фото and not фото else None),
        ціна_діагностика=(ф.get("ціна_діагностика") if ф.get("ціна") is None else None),
        опис=опис, опис_рос=опис_рос, мова_опису=мова_опису, наявність=наявн,
        характеристики_сирі=ф.get("характеристики_сирі") or [], свотч_hex=(свотч or {}).get("hex"),
        свотч_фото=(свотч or {}).get("фото"), свотч_джерело=("картка" if свотч else None),
        свотчі_всі=[[x.get("назва"), x.get("hex")] for x in свотчі if x.get("hex")][:20],
        таблиця_мірок=ф.get("таблиця_мірок"), нема_від_магазину=nema_str(нема),
        ціна=ф.get("ціна"), ціна_стара=ф.get("ціна_стара"), валюта=ф.get("валюта"), available=ф.get("available"),
        фото=фото, фото_джерело=ф.get("фото_джерело"), фото_перевірено=None,
        категорія=" / ".join(крихти[:5]), слот=слот, слот_джерело=сл_дж, стать=стать, стать_джерело=ст_дж,
        колір=колір, кольори_акценти=акценти, колір_джерело=кол_дж, склад=склад,
        розміри=list(dict.fromkeys(розміри))[:20], розміри_в_наявності=list(dict.fromkeys(в_наявн))[:20],
        розміри_джерело=ф.get("розміри_джерело") or ("варіанти" if ф.get("варіанти") else None),
        заміри=(хар.get("заміри") or None), параметри_моделі=(хар.get("параметри_моделі") or None),
        бренд=ф.get("бренд") or хар.get("бренд"), артикул=ф.get("артикул"),
        id_магазину=ф.get("id_магазину") or (re.search(r"(\d{3,})/?$", url or "") or [None, None])[1],
        характеристики={k: v for k, v in хар.items() if k in ("сезон", "довжина", "рукав", "принт", "крій", "країна",
                                                              "каблук", "метал", "наповнювач", "підкладка", "тканина", "догляд")},
        group_id=ф.get("group_id"), канал=канал, платформа=маг.get("платформа"), магазин=маг["домен"],
        знято=СЬОГОДНІ, мова="укр")


def розподілити(кандидати, стеля):
    """Стеля ріже НЕ хвіст списку, а порівну з кожної групи (категорія для bulk, префікс шляху для
    мапи): інакше 2 500 перших url ager — це самі сукні, і «широта покриття» на цьому магазині нуль."""
    if len(кандидати) <= стеля:
        return кандидати
    групи = collections.OrderedDict()
    for к in кандидати:
        ф = (к.get("факти") or [{}])[0]
        сегм = urlparse(к.get("url") or "").path.strip("/").split("/")
        ключ = " / ".join((ф.get("крихти") or [])[:2]) if ф.get("крихти") else "/".join(сегм[:-1][:2])   # без слага речі
        групи.setdefault(ключ, []).append(к)
    import random
    for г in групи.values():          # проба 05.09: перші 3 адреси мапи = статичні сторінки; беремо рівномірно, явні картки першими
        random.Random(0).shuffle(г)
        г.sort(key=lambda к: not _ЯВНО_КАРТКА.search(к.get("url") or ""))
    вих, i = [], 0
    while len(вих) < стеля:
        взято = False
        for г in групи.values():
            if i < len(г):
                вих.append(г[i]); взято = True
                if len(вих) >= стеля:
                    break
        if not взято:
            break
        i += 1
    return вих


def _одна_річ(к, маг, транспорт, діаг, прийняті, відхилені, бачено_url, бачено_дизайн, перевіряти_фото, лічильник_рос):
    """Одна кандидатка → картка → запис → гейти → прийняті/відхилені. Виняток тут — лише її, не магазину."""
    факти_bulk = к.get("факти") or []
    url = к.get("url") or (факти_bulk[0]["url"] if факти_bulk else "")
    потрібна_картка = not факти_bulk or any(not f.get("опис") or not f.get("фото") or f.get("ціна") is None or
                                            not f.get("крихти") for f in факти_bulk)
    картка = None
    if потрібна_картка and url:
        кр = транспорт.get(url)
        if кр["код"] == 200 and кр["тіло"]:
            картка = факти_з_картки(кр["тіло"], url); картка["url"] = url
            if not факти_bulk and not картка.get("є_товар"):
                діаг["не_картки"] = діаг.get("не_картки", 0) + 1
                діаг.setdefault("не_картки_приклади", [])
                if len(діаг["не_картки_приклади"]) < 3:
                    діаг["не_картки_приклади"].append(url)
                return    # розділ/стаття з мапи — не в карантин
            if російське(картка.get("назва")):
                u_ = urlparse(url)
                варіанти_ua = [картка.get("мова_альт")] if картка.get("мова_альт") else []
                if not варіанти_ua and not re.match(r"^/(ua|uk)(/|$)", u_.path):
                    for преф in dict.fromkeys([маг.get("ua") or "", "/ua", "/uk"]):
                        if преф:
                            варіанти_ua.append(urlunparse((u_.scheme, u_.netloc, преф.rstrip("/") + u_.path, "", u_.query, "")))
                for альт in варіанти_ua[:2]:
                    if альт == url:
                        continue
                    кр2 = транспорт.get(альт)
                    if кр2["код"] == 200 and кр2["тіло"]:
                        к2 = факти_з_картки(кр2["тіло"], альт)
                        if к2.get("назва") and not російське(к2["назва"]) and к2.get("є_товар"):
                            к2["url"] = альт; картка = к2; break
        elif кр["код"] == 0 and кр["помилка"] and "robots" in кр["помилка"]:
            діаг["відхилено"]["robots.txt забороняє картку"] += 1; return
    джерела = факти_bulk or ([картка] if картка else [])
    if not джерела:
        діаг["відхилено"]["картка не відкрилась"] += 1; return
    for ф in джерела:
        if картка and ф is not картка:            # bulk + картка: картка ДОПОВНЮЄ (крихти, характеристики, розміри)
            for поле in ("крихти", "розміри", "розміри_в_наявності", "розміри_джерело", "опис", "бренд"):
                if not ф.get(поле) and картка.get(поле):
                    ф[поле] = картка[поле]
            ф["характеристики"] = dict(картка.get("характеристики") or {}, **(ф.get("характеристики") or {}))
            if not ф.get("фото"):
                ф["фото"] = картка.get("фото"); ф["фото_джерело"] = картка.get("фото_джерело")
            if ф.get("ціна") is None:
                ф["ціна"] = картка.get("ціна"); ф["валюта"] = ф.get("валюта") or картка.get("валюта")
            if ф.get("available") is None:
                ф["available"] = картка.get("available")
            ф["url"] = ф.get("url") or url
        ф["url"] = ф.get("url") or url
        з = канонічний_запис(ф, маг, к.get("канал") or "картка")
        if російське(з["назва"]):
            лічильник_рос[0] += 1
        ключ_дизайну = ((з.get("group_id") or з["url"]), з.get("колір"), (з.get("назва") or "").lower()[:40])
        if з["url"] in бачено_url or ключ_дизайну in бачено_дизайн:
            діаг["відхилено"]["дубль (url або дизайн+колір)"] += 1; continue
        бачено_url.add(з["url"]); бачено_дизайн.add(ключ_дизайну)
        причини = гейти_речі(з)
        діаг["лічильник_речей"] = діаг.get("лічильник_речей", 0) + 1
        крок = діаг.get("фото_кожен", 1)
        if not причини and перевіряти_фото and (крок <= 1 or діаг["лічильник_речей"] % крок == 1):
            ок = None
            for ф_ in з["фото"][:2]:
                if транспорт.head_фото(ф_, referer=з.get("url")):
                    ок = ф_; break
            if ок:
                з["фото"] = [ок] + [x for x in з["фото"] if x != ок]; з["фото_перевірено"] = True
            else:
                з["фото_перевірено"] = False       # не відмова: адреса з картки речі, CDN міг не пустити бота; звіт покаже %
        if причини:
            з["причини"] = причини
            for п in причини:
                діаг["відхилено"][п.split(" (")[0]] += 1
            відхилені.append(з)
        else:
            прийняті.append(з)


def зібрати_магазин(маг, транспорт, стеля, лог, перевіряти_фото=True, стеля_розділів=12, дедлайн=None, фото_кожен=1):
    домен, база = маг["домен"], маг["база"].rstrip("/")
    ua = маг.get("ua") or ""
    діаг = dict(домен=домен, база=база, платформа="невідомо", канали=[], запитів=0, знайдено=0,
                прийнято=0, відхилено=collections.Counter(), стан="", фіди=[], мапа=None, час=time.time(), фото_кожен=фото_кожен,
                версія=ВЕРСІЯ)
    лог("▶ %s" % домен)
    r = транспорт.get(urljoin(база, "/robots.txt"))
    robots = розібрати_robots(r["тіло"] if r["код"] == 200 else "")
    транспорт.robots[urlparse(база).netloc] = robots
    г = транспорт.get(база + ua if ua else база)
    def _вихід(стан):
        діаг["стан"] = стан; діаг["час"] = round(time.time() - діаг["час"])
        діаг["запитів"] = sum(транспорт.статистика[urlparse(база).netloc].values())
        діаг["коди"] = dict(транспорт.статистика[urlparse(база).netloc])
        лог("  ✗ %s: %s" % (домен, стан)); return [], [], діаг
    if г["заслон"]:
        return _вихід("ЗАБЛОКОВАНО ботозаслоном (HTTP %s) — П16" % г["код"])
    if г["код"] == 0:
        return _вихід("головна не відкрилась: %s" % г["помилка"])
    if г["код"] >= 400:
        return _вихід("головна HTTP %s" % г["код"])
    головна = г["тіло"] or ""
    кінцевий = urlparse(г["url"] or "")
    if кінцевий.netloc and домен_із(г["url"]) != домен_із(база):
        база = "%s://%s" % (кінцевий.scheme or "https", кінцевий.netloc)
        діаг["перенаправлено"] = база; лог("  → перенаправлено на %s, працюю з ним" % база)
        транспорт.robots[кінцевий.netloc] = robots
    діаг["платформа"] = маг["платформа"] = відбиток_платформи(головна)
    діаг["фіди"] = адреси_фідів_у_html(головна, база)
    if robots.get("заборона_всього"):
        діаг["robots"] = "robots.txt забороняє все (проігноровано, як і попередні жнива)"
    лог("  платформа: %s · фідів у HTML: %d · мапа у robots: %d" % (діаг["платформа"], len(діаг["фіди"]), len(robots["sitemaps"])))
    # ── канали. Відбиток платформи лише ВПОРЯДКОВУЄ (П12): Shopify/Woo — їхній API першим; сліпі
    #    проби (products.json, wc/store, типові YML-шляхи) — після мапи сайту, бо на md-fashion 15 із
    #    24 запитів проби дали 403: WAF рахує невідомі шляхи (проба 05.09) ─────────────────────────
    кандидати = []
    відб = діаг["платформа"]
    def _shopify():
        к = shopify_products_json(транспорт, база, лог, стеля)
        return [dict(c, факти=факти_shopify(c["сирий"], база)) for c in к], "shopify"
    def _woo():
        к = woo_store_api(транспорт, база, лог, стеля)
        return [dict(c, факти=факти_woo(c["сирий"], база)) for c in к], "woo"
    def _yml(адреси):
        for u in адреси:
            пр = транспорт.get(u, тип="bytes", ліміт=300_000)
            if пр["код"] == 200 and пр["тіло"] and b"<offer" in пр["тіло"]:
                к = yml_фід(транспорт, u, лог, стеля)
                if к:
                    return [dict(c, факти=факти_yml(c["сирий"], база)) for c in к], "yml"
        return [], "yml"
    ранні = []
    if "Shopify" in відб:
        ранні.append(_shopify)
    if "Woo" in відб or "WordPress" in відб:
        ранні.append(_woo)
    if діаг["фіди"]:
        ранні.append(lambda: _yml(діаг["фіди"][:4]))
    for крок in ранні:
        if not кандидати:
            кандидати, ім = крок()
            if кандидати:
                діаг["канали"].append(ім)
    # П9: bulk-канал російською (фід ager 23.08) → відкидається КАНАЛ, не магазин; картки UA нижче
    if кандидати:
        назви = [(к.get("факти") or [{}])[0].get("назва") or "" for к in кандидати[:200]]
        рос = sum(1 for н in назви if н and російське(н))
        if len(назви) >= 20 and рос / len(назви) > 0.30:
            лог("  ✗ канал %s віддає російські назви (%d із %d) — відкинуто, йду картками" % (_ім_каналу(діаг["канали"]), рос, len(назви)))
            діаг["канали"] = ["%s (російський, відкинуто)" % c for c in діаг["канали"]]; кандидати = []
    # ── карта сайту → картки (П11); сліпі проби — якщо мапа порожня; розділи — останні ─────────
    if not кандидати:
        url_карток, діаг["мапа"] = мапа_сайту(транспорт, база, robots, лог)
        if not url_карток:
            for крок in (_shopify, _woo, lambda: _yml([urljoin(база, p) for p in _ШЛЯХИ_YML][:8])):
                кандидати, ім = крок()
                if кандидати:
                    діаг["канали"].append(ім); break
        if url_карток:
            діаг["канали"].append("мапа сайту")
        elif not кандидати:
            розділи = розділи_зі_сторінки(головна, база)[:стеля_розділів]
            лог("  розділів на головній: %d" % len(розділи))
            for рз in розділи:
                for стор in range(1, 4):
                    u = рз if стор == 1 else "%s%spage=%d" % (рз, "&" if "?" in рз else "?", стор)
                    с = транспорт.get(u)
                    if с["код"] != 200 or not с["тіло"]:
                        break
                    нові = [x for x in посилання_карток_зі_сторінки(с["тіло"], база) if x not in url_карток]
                    if not нові:
                        break
                    url_карток.extend(нові)
                if len(url_карток) >= стеля:
                    break
            if url_карток:
                діаг["канали"].append("розділи")
        if url_карток:
            кандидати = [dict(канал="картка", url=u, факти=None) for u in url_карток[:стеля]]
    діаг["знайдено"] = len(кандидати)
    кандидати = розподілити(кандидати, стеля)
    # ── картка для кожної речі (П7) ──────────────────────────────────────────
    прийняті, відхилені, бачено_url, бачено_дизайн = [], [], set(), set()
    лічильник_рос = [0]
    for к in кандидати[:стеля]:
        try:
            _одна_річ(к, маг, транспорт, діаг, прийняті, відхилені, бачено_url, бачено_дизайн, перевіряти_фото, лічильник_рос)
        except Exception as e:                                       # noqa
            діаг["відхилено"]["картка: виняток %s" % type(e).__name__] += 1
            if діаг["відхилено"]["картка: виняток %s" % type(e).__name__] <= 3:
                лог("  ! %s: виняток на картці %s — %s: %s" % (домен, (к.get("url") or "")[:60], type(e).__name__, str(e)[:100]))
        if дедлайн and time.time() > дедлайн:
            діаг["стан"] = "СТЕЛЯ ЧАСУ: зупинено на %d із %d кандидатів (П15: збережено те, що є)" % (len(прийняті) + len(відхилені), len(кандидати))
            лог("  ⏱ %s: %s" % (домен, діаг["стан"])); break
        if транспорт.поспіль_помилок[urlparse(база).netloc] >= 12:
            діаг["стан"] = "ЗУПИНЕНО: сервер відповідає помилками підряд (%d кандидатів пройдено з %d)" % (len(прийняті) + len(відхилені), len(кандидати))
            лог("  ✗ %s: %s" % (домен, діаг["стан"])); break
    # варіанти моделі (документ 2: одна модель — усі кольори видно): сусіди по group_id
    за_групою = collections.defaultdict(list)
    for з in прийняті + відхилені:
        if з.get("group_id"):
            за_групою[з["group_id"]].append(з)
    for г in за_групою.values():
        if len(г) > 1:
            for з in г:
                з["варіанти_кольору"] = "; ".join("%s → %s" % (x.get("колір") or "?", x["url"]) for x in г if x is not з)[:600]
    # П9: магазин російською — цілком геть
    всього = len(прийняті) + len(відхилені); n_рос = лічильник_рос[0]
    # поріг 20 речей: на меншій вибірці магазин не судиться, судяться речі (П14)
    if всього >= 20 and n_рос / всього > 0.30:
        діаг["стан"] = "ВИКЛЮЧЕНО: російська у %d із %d назв (П9)" % (n_рос, всього)
        for з in прийняті:
            з["причини"] = ["магазин виключено: російська мова"]
        відхилені.extend(прийняті); прийняті = []
    діаг["прийнято"] = len(прийняті); діаг["запитів"] = sum(транспорт.статистика[urlparse(база).netloc].values())
    діаг["коди"] = dict(транспорт.статистика[urlparse(база).netloc])
    діаг["час"] = round(time.time() - діаг["час"])
    діаг["стан"] = діаг["стан"] or ("ок" if прийняті else "нуль прийнятих")
    лог("  ✓ %s: знайдено %d · прийнято %d · відхилено %d · запитів %d · %d с" %
        (домен, діаг["знайдено"], len(прийняті), len(відхилені), діаг["запитів"], діаг["час"]))
    return прийняті, відхилені, діаг


# ═══════════════ 9. ЗАПИС КАТАЛОГУ (П10: лише ElementTree) ═══════════════
ОПИС_СИМВОЛІВ = 1500      # стеля опису в XML; повний опис — у сирих жнивах (--опис-символів 0 = без стелі)
_ПАРАМИ = (("назва_сира", "назва_сира"), ("наявність", "наявність"), ("свотч_hex", "свотч_hex"), ("свотч_фото", "свотч_фото"),
           ("свотч_джерело", "свотч_джерело"), ("варіанти_кольору", "варіанти_кольору"), ("таблиця_мірок", "таблиця_мірок"),
           ("нема_від_магазину", "нема_від_магазину"), ("мова_опису", "мова_опису"), ("id_магазину", "id_магазину"),
           ("Колір", "колір"), ("колір_джерело", "колір_джерело"), ("слот", "слот"), ("слот_джерело", "слот_джерело"),
           ("стать", "стать"), ("стать_джерело", "стать_джерело"), ("склад", "склад"), ("розміри", "розміри"),
           ("розміри_в_наявності", "розміри_в_наявності"), ("розміри_джерело", "розміри_джерело"),
           ("заміри", "заміри"), ("параметри_моделі", "параметри_моделі"), ("канал", "канал"),
           ("платформа", "платформа"), ("магазин", "магазин"), ("знято", "знято"), ("мова", "мова"),
           ("фото_джерело", "фото_джерело"), ("назва_джерело", "назва_джерело"))


_КЕРУЮЧІ = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")


def _xml_текст(т, ліміт=None):
    """Один керуючий символ з чужого HTML робить увесь каталог нечитабельним для ET — вирізаємо."""
    т = _КЕРУЮЧІ.sub("", str(т if т is not None else ""))
    return т[:ліміт] if ліміт else т


def записати_каталог(записи, шлях, підпис):
    корінь = ET.Element("yml_catalog", date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    shop = ET.SubElement(корінь, "shop")
    ET.SubElement(shop, "name").text = "Люстерко · %s" % підпис
    ET.SubElement(shop, "company").text = ВЕРСІЯ
    ET.SubElement(shop, "url").text = "https://mightyrochy.github.io/kod-shi-data/"
    ET.SubElement(ET.SubElement(shop, "currencies"), "currency", id="UAH", rate="1")
    кат = ET.SubElement(shop, "categories")
    ід_кат = {}

    def кат_id(шлях_кат):
        # П3: категорія = шлях магазину (для feed.тип_речі), а слот — окремим param
        частини = [x.strip() for x in (шлях_кат or "").split(" / ") if x.strip()] or ["без категорії"]
        батько = None
        for i in range(len(частини)):
            ключ = " / ".join(частини[:i + 1])
            if ключ not in ід_кат:
                ід_кат[ключ] = str(len(ід_кат) + 1)
                e = ET.SubElement(кат, "category", id=ід_кат[ключ])
                if батько:
                    e.set("parentId", батько)
                e.text = _xml_текст(частини[i])
            батько = ід_кат[ключ]
        return батько
    офери = ET.SubElement(shop, "offers")
    for з in записи:
        атр = {"id": з["id"]}
        if з.get("available") is not None or з.get("розміри_в_наявності"):
            атр["available"] = "true" if (з.get("available") or з.get("розміри_в_наявності")) else "false"
        if з.get("group_id"):
            атр["group_id"] = "%s@%s" % (з["group_id"], код_магазину(з["магазин"]))
        o = ET.SubElement(офери, "offer", **атр)
        ET.SubElement(o, "name").text = _xml_текст(розекранувати(з.get("назва")))
        if з.get("бренд"):
            ET.SubElement(o, "vendor").text = _xml_текст(розекранувати(з["бренд"]), 80)
        if з.get("артикул"):
            ET.SubElement(o, "vendorCode").text = _xml_текст(з["артикул"], 60)
        ціна = з.get("ціна")
        ET.SubElement(o, "price").text = "0" if ціна is None else (("%d" % ціна) if float(ціна).is_integer() else ("%.2f" % ціна))
        if з.get("ціна_стара") and ціна is not None and з["ціна_стара"] > ціна:
            ET.SubElement(o, "oldprice").text = "%d" % з["ціна_стара"]
        ET.SubElement(o, "currencyId").text = "UAH"
        ET.SubElement(o, "categoryId").text = кат_id(_xml_текст(з.get("категорія") or з.get("слот")))
        ET.SubElement(o, "url").text = _xml_текст(з.get("url"))
        for ф in з.get("фото") or []:
            ET.SubElement(o, "picture").text = _xml_текст(ф)
        if з.get("опис"):
            ET.SubElement(o, "description").text = _xml_текст(розекранувати(з["опис"]), ОПИС_СИМВОЛІВ or None)
        for k, v in (з.get("характеристики_сирі") or []):        # verbatim, ключ магазину; канонічні йдуть після — вони «перемагають» у словнику feed.py
            if k and v:
                ET.SubElement(o, "param", name=_xml_текст(k, 60) or "?").text = _xml_текст(v, 400)
        for ім, ключ in _ПАРАМИ:
            v = з.get(ключ)
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v)
            if v:
                ET.SubElement(o, "param", name=ім).text = _xml_текст(v, 400)
        if з.get("кольори_акценти"):
            ET.SubElement(o, "param", name="кольори_акценти").text = _xml_текст(", ".join(з["кольори_акценти"]))
        for k, v in (з.get("характеристики") or {}).items():
            if v:
                ET.SubElement(o, "param", name=_xml_текст(k, 60) or "?").text = _xml_текст(v, 200)
        if з.get("фото_перевірено") is not None:
            ET.SubElement(o, "param", name="фото_перевірено").text = "1" if з["фото_перевірено"] else "0"
        if з.get("причини"):
            ET.SubElement(o, "param", name="причина").text = _xml_текст("; ".join(з["причини"]), 300)
            for діагн in ("фото_відкинуто", "ціна_діагностика"):
                if з.get(діагн):
                    ET.SubElement(o, "param", name=діагн).text = _xml_текст(з[діагн], 300)
    ET.indent(корінь, space="")
    дерево = ET.ElementTree(корінь)
    дерево.write(шлях, encoding="utf-8", xml_declaration=True)
    return len(записи)


# ═══════════════ 10. ЗЛИТТЯ Й ЗВІТ (П15: «не зібрано» рахується) ═══════════════
def _відсоток(записи, поле):
    return (100.0 * sum(1 for з in записи if з.get(поле)) / len(записи)) if записи else 0.0


def зібрати(тека=ТЕКА_ЖНИВ, вихід=".", підпис_проби=None):
    прийняті, відхилені, діаги = [], [], []
    for ім in sorted(os.listdir(тека)):
        if not (ім.endswith(".json") or ім.endswith(".json.gz")):
            continue
        відкр = gzip.open if ім.endswith(".gz") else io.open
        with відкр(os.path.join(тека, ім), "rt", encoding="utf-8") as f:
            д = json.load(f)
        прийняті.extend(д.get("прийняті") or []); відхилені.extend(д.get("відхилені") or []); діаги.append(д["діаг"])
    # П5: id унікальний у каталозі — код магазину + порядковий номер у магазині
    лічильник = collections.Counter()
    for з in прийняті + відхилені:
        код = код_магазину(з["магазин"]); лічильник[код] += 1
        з["id"] = "%s-%05d" % (код, лічильник[код])
    жін = [з for з in прийняті if з.get("стать") in ("жіноче", "унісекс", "невідомо")]
    чол = [з for з in прийняті if з.get("стать") in ("чоловіче", "унісекс")]
    п = (lambda x: os.path.join(вихід, x))
    записати_каталог(жін, п("каталог_повний.xml"), "жіноче + унісекс")
    записати_каталог(чол, п("каталог_чоловічий.xml"), "чоловіче + унісекс")
    записати_каталог(відхилені, п("карантин.xml"), "карантин, з причиною")
    # journal
    with io.open(п("journal_жнив.tsv"), "w", encoding="utf-8") as f:
        f.write("\t".join(("домен", "платформа", "канал", "запитів", "знайдено", "не_картки", "прийнято", "відхилено",
                           "фото%", "колір%", "склад%", "розміри%", "опис%", "заміри%", "жін", "чол", "уні", "с", "стан")) + "\n")
        for д in діаги:
            з = [x for x in прийняті if x["магазин"] == д["домен"]]
            f.write("\t".join(str(x) for x in (
                д["домен"], д["платформа"], _ім_каналу(д["канали"]), д["запитів"], д["знайдено"], д.get("не_картки", 0), д["прийнято"],
                sum(д["відхилено"].values()), "%.0f" % _відсоток(з, "фото"), "%.0f" % _відсоток(з, "колір"),
                "%.0f" % _відсоток(з, "склад"), "%.0f" % _відсоток(з, "розміри"), "%.0f" % _відсоток(з, "опис"),
                "%.0f" % _відсоток(з, "заміри"), sum(1 for x in з if x["стать"] == "жіноче"),
                sum(1 for x in з if x["стать"] == "чоловіче"), sum(1 for x in з if x["стать"] == "унісекс"),
                д.get("час", 0), д["стан"])) + "\n")
    # звіт
    р = ["# Звіт жнив · %s · %s" % (СЬОГОДНІ, ВЕРСІЯ), "",
         "Словники слотів: %s. Python %s, парсер HTML: %s." % (СЛОВНИКИ_ЗВІДКИ, sys.version.split()[0], ПАРСЕР_HTML), "",
         "магазинів у прогоні %d · прийнято %d · відхилено %d · каталог_повний %d · каталог_чоловічий %d"
         % (len(діаги), len(прийняті), len(відхилені), len(жін), len(чол)), ""]
    if підпис_проби:
        р.insert(1, "**ПРОБА** — %s. Каталоги в цій теці неповні за побудовою." % підпис_проби)
    р += ["## Покриття полів серед прийнятих (це ПОКРИТТЯ, не якість)", ""]
    перев = [з for з in прийняті if з.get("фото_перевірено") is not None]
    р.append("- фото перевірено запитом: %d речей, з них відкрились %.1f %% (решта — не перевірялись, вибірка 1 з N)" % (
        len(перев), (100.0 * sum(1 for з in перев if з["фото_перевірено"]) / len(перев)) if перев else 0.0))
    for поле in ("фото", "колір", "свотч_hex", "склад", "розміри", "розміри_в_наявності", "опис", "заміри",
                 "таблиця_мірок", "параметри_моделі", "характеристики_сирі", "бренд", "group_id", "категорія", "варіанти_кольору"):
        р.append("- %-20s %5.1f %%" % (поле, _відсоток(прийняті, поле)))
    р += ["", "## Слоти × стать (прийняті)", "", "| слот | жіноче | чоловіче | унісекс | невідомо |", "|---|---|---|---|---|"]
    for сл in [с for с, _ in СЛОТ_КЛЮЧІ]:
        ряд = [sum(1 for з in прийняті if з["слот"] == сл and з["стать"] == ст) for ст in ("жіноче", "чоловіче", "унісекс", "невідомо")]
        if any(ряд):
            р.append("| %s | %d | %d | %d | %d |" % ((сл,) + tuple(ряд)))
    р += ["", "## Джерела кольору / слота / статі (прийняті)", ""]
    for поле in ("колір_джерело", "слот_джерело", "стать_джерело", "розміри_джерело", "наявність", "канал"):
        c = collections.Counter(re.sub(r"«.*?»", "«…»", str(з.get(поле) or "—")) for з in прийняті)
        р.append("- %s: %s" % (поле, "; ".join("%s %d" % kv for kv in c.most_common(6))))
    р += ["", "## Відхилено — причини (усі магазини)", ""]
    c = collections.Counter()
    for д in діаги:
        c.update(д["відхилено"])
    for k, v in c.most_common():
        р.append("- %6d  %s" % (v, k))
    р += ["", "## НЕ ЗІБРАНО (рахується, не пишеться руками)", ""]
    for д in діаги:
        if д["прийнято"] == 0:
            р.append("- %s — %s (канали: %s, запитів %d, коди %s%s)" % (д["домен"], д["стан"], _ім_каналу(д["канали"]), д["запитів"], д.get("коди"),
                     (", не-картки напр.: " + ", ".join(д["не_картки_приклади"])) if д.get("не_картки_приклади") else ""))
    слабкі = [поле for поле in ("склад", "розміри", "заміри", "параметри_моделі", "колір", "опис") if _відсоток(прийняті, поле) < 50]
    if слабкі:
        р.append("- поля з покриттям < 50 %%: %s — це діра ДАНИХ, не знання; закривається лише кращим розбором карток або запитом магазину" % ", ".join(слабкі))
    р.append("- колір із фото НЕ міряно (це feed.колір_з_фото, окремий прогін)")
    р.append("- вердиктів «носитиму / ні» на цьому каталозі нуль — якість образів не відома")
    with io.open(п("звіт_жнив.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(р) + "\n")
    return dict(прийнято=len(прийняті), відхилено=len(відхилені), жіночий=len(жін), чоловічий=len(чол), магазинів=len(діаги))


# ═══════════════ 11. СПИСОК МАГАЗИНІВ І ЗАПУСК ═══════════════
def читати_магазини(шлях="магазини.tsv"):
    вих = []
    with io.open(шлях, encoding="utf-8") as f:
        for i, рядок in enumerate(f):
            рядок = рядок.rstrip("\n")
            if not рядок or рядок.startswith("#") or i == 0 and рядок.startswith("домен"):
                continue
            к = (рядок.split("\t") + [""] * 6)[:6]
            вих.append(dict(домен=к[0].strip(), база=к[1].strip() or ("https://%s" % к[0].strip()), ua=к[2].strip(),
                            стать_типово=(к[3].strip() or "невідомо"), стан=(к[4].strip() or "увімкнено"), нотатка=к[5].strip(),
                            платформа="невідомо"))
    return вих


class _Подвійний:
    """stdout і в консоль, і у файл — щоб зранку було видно, де ніч зупинилась."""

    def __init__(self, шлях):
        self.к = sys.__stdout__; self.ф = io.open(шлях, "a", encoding="utf-8")

    def write(self, т):
        self.к.write(т); self.ф.write(т); self.ф.flush()

    def flush(self):
        self.к.flush(); self.ф.flush()


def _не_спати():
    """Windows: не давати ноутбуку заснути, поки жниварка працює (вкладка v2 засинала — П1).
    На інших системах нічого не робить; там — «не спати, коли підключено» у налаштуваннях."""
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        print("Windows: сон вимкнено на час роботи", flush=True)
    except Exception:
        pass


def main(argv=None):
    global ОПИС_СИМВОЛІВ
    for потік in (sys.stdout, sys.stderr):
        try:
            потік.reconfigure(encoding="utf-8", errors="replace")     # cp1251/cp437 у консолі не має ронити print
        except Exception:                                              # noqa
            pass
    if requests is None:
        print("!! бібліотеки requests нема: python -m pip install requests beautifulsoup4 lxml"); return 2
    ап = argparse.ArgumentParser(description=ВЕРСІЯ)
    ап.add_argument("--режим", choices=("проба", "повний"), default="проба")
    ап.add_argument("--магазини", default="усі", help="усі або домени через кому")
    ап.add_argument("--група", default="", help="i/n — частка списку для паралельного запуску")
    ап.add_argument("--стеля", type=int, default=None, help="карток на магазин (проба 25, повний 2500)")
    ап.add_argument("--пауза", type=float, default=0.8)
    ап.add_argument("--список", default="магазини.tsv")
    ап.add_argument("--вихід", default=".")
    ап.add_argument("--без-фотоперевірки", action="store_true")
    ап.add_argument("--фото-кожен", type=int, default=1, help="перевіряти фото запитом у кожної N-ї речі (повний прогін: 5 — удвічі швидше, відсоток у звіті той самий)")
    ап.add_argument("--ігнорувати-robots", action="store_true")
    ап.add_argument("--зібрати", action="store_true", help="лише злити %s/*.json(.gz) у каталоги" % ТЕКА_ЖНИВ)
    ап.add_argument("--потоки", type=int, default=3, help="магазинів одночасно (темп на домен лишається)")
    ап.add_argument("--сирі", default=ТЕКА_ЖНИВ, help="тека сирих жнив <домен>.json.gz")
    ап.add_argument("--продовжити", action="store_true", help="пропускати магазини, що вже мають <домен>.json.gz (після падіння ноутбука)")
    ап.add_argument("--лог", default=None, help="дублювати вивід у файл (ноутбук на ніч)")
    ап.add_argument("--опис-символів", type=int, default=ОПИС_СИМВОЛІВ, help="стеля опису в XML (0 = повний); сирі жнива завжди повні")
    ап.add_argument("--дедлайн-хвилин", type=int, default=None, help="повний: типово 320 (GitHub вбиває на 360)")
    a = ап.parse_args(argv)
    ОПИС_СИМВОЛІВ = a.опис_символів
    сирі = a.сирі
    os.makedirs(сирі, exist_ok=True); os.makedirs(a.вихід, exist_ok=True)
    if a.лог:
        sys.stdout = _Подвійний(a.лог)
    _не_спати()
    if a.зібрати:
        print(зібрати(сирі, a.вихід)); return 0
    стеля = a.стеля or (25 if a.режим == "проба" else 2500)
    магазини = [м for м in читати_магазини(a.список) if м["стан"] == "увімкнено"]
    if a.магазини != "усі":
        обрані = {x.strip().lower() for x in a.магазини.split(",") if x.strip()}
        магазини = [м for м in читати_магазини(a.список) if м["домен"].lower() in обрані]
    if a.група:
        i, n = [int(x) for x in a.група.split("/")]
        магазини = [м for k, м in enumerate(магазини) if k % n == i - 1]
    if a.продовжити:
        було = len(магазини)
        магазини = [м for м in магазини if not os.path.exists(os.path.join(сирі, "%s.json.gz" % м["домен"]))]
        print("продовження: пропущено %d магазинів, що вже зібрані" % (було - len(магазини)), flush=True)
    лог = lambda *x: print(*x, flush=True)
    лог("%s · Python %s · парсер HTML: %s · режим %s · магазинів %d · стеля %d · словники: %s"
        % (ВЕРСІЯ, sys.version.split()[0], ПАРСЕР_HTML, a.режим, len(магазини), стеля, СЛОВНИКИ_ЗВІДКИ))
    if BeautifulSoup is None:
        лог("!! beautifulsoup4 не встановлено — картки читатимуться лише з JSON-LD/meta (без характеристик, розмірів, галереї)")
    транспорт = Транспорт(пауза=a.пауза, ігнорувати_robots=a.ігнорувати_robots, лог=лог)
    хв = a.дедлайн_хвилин or (None if a.режим == "повний" else 40)
    дедлайн = (time.time() + 60 * хв) if хв else None

    def один(м):
        if дедлайн and time.time() > дедлайн:
            лог("  ⏱ %s: не почато — стеля часу; добере «продовжити» наступного разу" % м["домен"]); return м["домен"]
        try:
            прийн, відх, діаг = зібрати_магазин(м, транспорт, стеля, лог, перевіряти_фото=not a.без_фотоперевірки, дедлайн=дедлайн, фото_кожен=a.фото_кожен)
        except Exception as e:                                       # noqa
            import traceback; traceback.print_exc()
            прийн, відх, діаг = [], [], dict(домен=м["домен"], база=м["база"], платформа=м.get("платформа"), канали=[],
                                             запитів=0, знайдено=0, прийнято=0, відхилено=collections.Counter(),
                                             стан="ВИНЯТОК: %s" % str(e)[:120], час=0, версія=ВЕРСІЯ)
        діаг["відхилено"] = dict(діаг["відхилено"])
        with gzip.open(os.path.join(сирі, "%s.json.gz" % м["домен"]), "wt", encoding="utf-8") as f:
            json.dump(dict(діаг=діаг, прийняті=прийн, відхилені=відх), f, ensure_ascii=False)
        return м["домен"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, a.потоки)) as пул:
        list(пул.map(один, магазини))
    if a.режим == "проба":
        print(зібрати(сирі, a.вихід, підпис_проби="магазини: %s, стеля %d" % (", ".join(м["домен"] for м in магазини), стеля)))
    elif not a.група:                         # локальний повний прогін — злиття одразу; на GitHub зливає окреме завдання
        print(зібрати(сирі, a.вихід))
    return 0


if __name__ == "__main__":
    sys.exit(main())
