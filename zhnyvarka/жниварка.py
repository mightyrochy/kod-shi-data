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
import argparse, collections, concurrent.futures, csv, datetime, functools, gzip, html, io, json, os, re, sys, threading, time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, parse_qsl, urlencode, quote

try:
    import requests
except ImportError:                                   # noqa
    requests = None
try:
    # curl_cffi відтворює TLS/HTTP2-рукостискання Chrome. Cloudflare оцінює запит за трьома речами:
    # репутація IP (дата-центр гірша за домашній), відбиток TLS, заголовки. Це закриває другу й третю;
    # першу не закриває нічим, окрім домашнього IP (вимір 06.09: skripka 403 з Azure, 200 з дому).
    from curl_cffi import requests as _curl                     # noqa
except ImportError:                                              # noqa
    _curl = None
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

ВЕРСІЯ = "жниварка v4.0 · 2026-09-07"
# ЛИШЕ ASCII: HTTP-заголовки кодуються latin-1; кирилиця тут поклала 62/62 магазини 05.09
# (UnicodeEncodeError до першого байта в мережу). Гейт: assert нижче + мережевий тест.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0.0.0 Safari/537.36 Lyusterko-zhnyvarka/3.0 (+catalog for a styling test stand)")
assert UA.isascii(), "User-Agent має бути ASCII"
# Заголовки як у справжнього Chrome: частина магазинів ріже за самим лише набором (порожній Sec-Fetch тощо)
ЗАГОЛОВКИ = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    # Accept-Encoding НЕ задаємо: requests сам оголошує те, що вміє розпакувати. Ручний «br» 06.09
    # зробив вміст усіх 63 магазинів нечитабельним (платформа «невідомо», 0 карток у мапі).
    "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none", "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1", "Cache-Control": "max-age=0",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
}
assert all((k + str(v)).isascii() for k, v in ЗАГОЛОВКИ.items()), "заголовки мають бути ASCII (latin-1)"
СЬОГОДНІ = datetime.date.today().isoformat()
ТЕКА_ЖНИВ = "жнива_сирі"          # <домен>.json.gz — сире, щоб перезбирати один магазин і зливати з рештою

# ═══════════════ 0. СЛОВНИКИ: ЄДИНИЙ ЧИТАЧ ВИДУ РЕЧІ ═══════════════
# Слот речі читає `фід_слот.вид_речі` з теки джерел, а не друга копія словників: розходження копії
# з читачем фіду було фейл-кейсом П3. Тека джерел лежить поруч у репозиторії; без неї жниварка не стартує.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "джерела"))
from фід_слот import вид_речі as _вид_речі, НЕ_ОДЯГ, ІМЕНА_СЛОТІВ    # noqa: E402
СЛОВНИКИ_ЗВІДКИ = "фід_слот.вид_речі"

# П13: поза слотами — річ не може стати частиною образу, і слот розділу її не рятує.
ПОЗА_СЛОТАМИ = ("білизн", "бюстгальтер", "трус", "купальник", "купальн", "плавк", "піжам", "пижам", "халат",
                "рукавичк", "перчатк", "рукавиц", "постіл", "рушник", "подушк", "ковдр", "свічк",
                "парфум", "аромат", "косметик", "сертифікат", "подарунков", "пакет", "брелок",
                "окуляр", "годинник", "термос", "чашк", "іграшк", "книг", "ланцюжок для окуляр",
                "догляд", "аерозол", "крем для взуття", "спрей", "щітк", "устілк", "шнурк", "ложк", "просочен", "дезодорант",
                "готовий образ", "бралет", "panties", "lingerie", "скатерт", "серветк", "плед",
                "blanket", "candle", "umbrella", "sunglass", "perfume",
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


# Плитка блоку «схожі товари» теж лежить у li/tr: bella-bicchi давала `~Ціна` = «770 грн Жіноча шапка
# 0 0 В наявності Арт. zh_shap1 Код 5048…» (190 оферів) — ЧУЖА назва й ціна в полях цієї речі. Ознака —
# власний хвіст плитки «<ціле> <ціле> <статус> Арт.», та сама, що в `чистка_каталогу._ПЛИТКА_СХОЖОГО`.
ПЛИТКА_СХОЖОГО = re.compile(r"\b\d+ \d+ (?:[^\W\d_]+ ){1,4}Арт\. ")


def розекранувати(т):
    """П10: до нерухомої точки, не більше трьох проходів (`&amp;amp;quot;` → `"`)."""
    т = str(т or "")
    for _ in range(3):
        н = html.unescape(т)
        if н == т:
            break
        т = н
    return " ".join(т.split())


_ТЕГ = re.compile(r"<[^>]+>")


def текст_з_html(т):
    """Поле-розмітка (`description` JSON-LD, `body_html`, Woo `description`) → видимий текст. Спершу сутності, потім теги,
    потім сутності ще раз: двічі закодований `&lt;p&gt;` інакше лишає в описі голі теги."""
    return розекранувати(_ТЕГ.sub(" ", розекранувати(_ТЕГ.sub(" ", html.unescape(str(т or ""))))))


# ═══════════════ 1. ТРАНСПОРТ ═══════════════
_ЗАСЛОН = re.compile(r"just a moment|attention required|cf-browser-verification|checking your browser|"
                     r"enable javascript and cookies|access denied|ddos-guard|captcha", re.I)


class Транспорт:
    """Пряме HTTP. Темп — на домен, не глобальний; 429/503 — відпочинок, не смерть черги (П1)."""

    def __init__(self, пауза=0.8, ігнорувати_robots=False, лог=None, не_маскуватись=False, дедлайн=None):
        # Дедлайн ПРОГОНУ. Уся мережа йде крізь get()/head_фото, тому одна перевірка тут зупиняє
        # геть усе: розвідку, фасети, картки, перевірку фото. 06.09: без цього одне завдання йшло
        # 3 год 40 хв — стелі стояли на магазині, а хвилі магазинів на 4 потоки їх множили.
        self.дедлайн = дедлайн
        self.пауза, self.ігнорувати_robots, self.лог = пауза, ігнорувати_robots, лог or (lambda *a: None)
        self._останній = {}; self._замок = threading.Lock()
        self.статистика = collections.defaultdict(collections.Counter)   # домен → код → n
        self.поспіль_помилок = collections.Counter()                     # домен → невдач підряд (429/5xx/мережа)
        self.браузером_вдалось = set()                                   # домени, які пустили лише з відбитком Chrome
        self.robots = {}                                                  # домен → dict(disallow, sitemaps, delay)
        self.сесія = requests.Session() if requests else None
        if self.сесія:
            self.сесія.headers.update(ЗАГОЛОВКИ)
        self.браузер = None
        if _curl is not None and не_маскуватись is not True:
            try:
                self.браузер = _curl.Session(impersonate="chrome")
                self.браузер.headers.update({k: v for k, v in ЗАГОЛОВКИ.items() if k != "User-Agent"})
            except Exception:                                    # noqa
                self.браузер = None
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

    def _браузером(self, url, тип, ліміт, заголовки):
        if self.час_вийшов():
            return None
        """Повтор із TLS-відбитком Chrome. → dict або None, якщо теж не вийшло."""
        домен = urlparse(url).netloc
        try:
            self._зачекати(домен)
            r = self.браузер.get(url, timeout=25, headers=заголовки or {}, allow_redirects=True)
            self.статистика[домен]["браузер:%s" % r.status_code] += 1
            if r.status_code >= 400:
                return None
            тіло = r.content[:ліміт]
            заслон = bool(_ЗАСЛОН.search(r.text[:5000]))
            if заслон:
                return None
            self.браузером_вдалось.add(домен)
            return dict(код=r.status_code, тіло=(r.text if тип == "text" else тіло), url=str(r.url),
                        ctype=(r.headers.get("Content-Type") or "").lower(), заслон=False, помилка=None)
        except Exception:                                        # noqa
            self.статистика[домен]["браузер:помилка"] += 1
            return None

    def час_вийшов(self):
        return bool(self.дедлайн) and time.time() > self.дедлайн

    def get(self, url, тип="text", ліміт=6_000_000, повтори=2, заголовки=None, _вже_браузером=False,
            секунд=25, секунд_усього=45):
        if self.час_вийшов():
            return dict(код=0, тіло=None, url=url, ctype="", заслон=False, помилка="дедлайн прогону")
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
        причина_код = "TRANSPORT"
        кінець_url = time.time() + секунд_усього          # 06.09: k.ua 26 запитів за 43 хв — стеля була
        for спроба in range(повтори):                      # на одну спробу, а не на спробу+повтори+браузер
            if time.time() > кінець_url:
                break
            self._зачекати(домен)
            try:
                початок = time.time()
                r = self.сесія.get(url, timeout=(6, 15), stream=True, allow_redirects=True,
                                   headers=заголовки or {})
                код = r.status_code
                ctype = (r.headers.get("Content-Type") or "").lower()
                шматки, обсяг, обірвано = [], 0, False
                for ш in r.iter_content(65536):
                    шматки.append(ш); обсяг += len(ш)
                    if обсяг > ліміт:
                        break
                    if time.time() - початок > секунд:   # таймаут читання рахує ЧАНКИ, не весь файл:
                        обірвано = True; break           # повільний потік на 30 МБ ішов ~50 хв (06.09)
                r.close()
                тіло = b"".join(шматки)
                self.статистика[домен][код] += 1
                if код in (429, 503, 502, 520, 521, 522, 524):
                    self.поспіль_помилок[домен] += 1
                    if спроба < повтори - 1 and self.поспіль_помилок[домен] < 4:
                        self.лог("  ⏸ %s → %s, відпочинок %d с" % (url[:70], код, 4 * (спроба + 1)))
                        time.sleep(4 * (спроба + 1)); continue
                    return dict(код=код, тіло=None, url=r.url, ctype=ctype, заслон=False, помилка="HTTP %s" % код)
                if код < 400:
                    self.поспіль_помилок[домен] = 0
                кодування_відп = (r.headers.get("Content-Encoding") or "").lower()
                if кодування_відп in ("br", "zstd") and not _вміємо(кодування_відп) and not _вже_браузером:
                    # requests оголошує лише те, що вміє; але сервер (або проксі) може віддати br усе одно.
                    # 06.09: ручний «br» без пакета brotli зробив вміст 63 магазинів нечитабельним.
                    self.лог("  ⚠ %s віддав %s — повтор без стиснення" % (домен, кодування_відп))
                    return self.get(url, тип, ліміт, повтори=1, заголовки=dict(заголовки or {}, **{"Accept-Encoding": "gzip, deflate"}),
                                    _вже_браузером=True)
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
                if обірвано:
                    self.статистика[домен]["обірвано за часом"] += 1
                заслон = код in (403, 503, 429) and bool(_ЗАСЛОН.search((текст or тіло.decode("utf-8", "replace"))[:5000]))
                if (заслон or код == 403) and self.браузер is not None and not _вже_браузером:
                    друга = self._браузером(url, тип, ліміт, заголовки)
                    if друга is not None:
                        return друга
                return dict(код=код, тіло=(текст if тип == "text" else тіло), url=r.url, ctype=ctype,
                            заслон=заслон, помилка=None)
            except Exception as e:                                 # noqa
                помилка = "%s: %s" % (type(e).__name__, str(e)[:120])
                причина_код = "TIMEOUT" if isinstance(e, requests.exceptions.Timeout) else "TRANSPORT"
                self.статистика[домен]["помилка"] += 1; self.поспіль_помилок[домен] += 1
                if self.поспіль_помилок[домен] >= 4:
                    break                                          # сервер/мережа мовчать підряд — не чекати далі
                time.sleep(1.5 * (спроба + 1))
        return dict(код=0, тіло=None, url=url, ctype="", заслон=False, помилка=помилка, причина_код=причина_код)

    def head_фото(self, url, referer=None):
        if self.час_вийшов():
            return False
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


def _вміємо(кодування):
    """Чи розпакує requests це кодування (br — лише з пакетом brotli/brotlicffi, zstd — із zstandard)."""
    import importlib.util
    if кодування == "br":
        return bool(importlib.util.find_spec("brotli") or importlib.util.find_spec("brotlicffi"))
    if кодування == "zstd":
        return bool(importlib.util.find_spec("zstandard"))
    return True


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


_UA_ПРЕФІКСИ = ("/ua", "/uk", "/ua-ua", "/uk-ua")


def виявити_ua_префікс(html_текст, база, з_tsv=""):
    """Український префікс шляху для ЦЬОГО магазину: `магазини.tsv` → hreflang → перемикач мов.
    Потрібен, бо (а) без нього беремо російську версію, (б) gepur 05.09: 905 речей зібрано двічі —
    той самий шлях із /uk/ і без. → «/uk» | «/ua» | «» ."""
    з_tsv = (з_tsv or "").strip().rstrip("/")
    if з_tsv:
        return з_tsv if з_tsv.startswith("/") else "/" + з_tsv
    т = html_текст or ""
    for м in re.finditer(r'<link[^>]+rel=["\']alternate["\'][^>]*>', т, re.I):
        тег = м.group(0)
        if re.search(r'hreflang=["\']uk(?:-ua)?["\']', тег, re.I):
            hr = re.search(r'href=["\']([^"\']+)["\']', тег, re.I)
            if hr:
                шлях = urlparse(канонічна(hr.group(1), база)).path.rstrip("/")
                if шлях.lower() in _UA_ПРЕФІКСИ:
                    return шлях
    for м in re.finditer(r'href=["\'](/(?:ua|uk)(?:-ua)?)/?["\']', т, re.I):   # перемикач мов на головній
        return м.group(1)
    return ""


def з_префіксом(url, префікс):
    """/catalog/platya → /uk/catalog/platya. Якщо префікс уже є або його нема — без змін."""
    if not префікс:
        return url
    u = urlparse(url)
    шлях = u.path or "/"
    if re.match(r"^/(ua|uk)(-ua)?(/|$)", шлях, re.I):
        return url
    return urlunparse((u.scheme, u.netloc, префікс.rstrip("/") + шлях, "", u.query, ""))


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
                        r"search|cart|checkout|account|login|wishlist|compare|contact|contacts|about|about_us|about-us|"
                        r"delivery|dostavka|payment|oplata|payment-delivery|oplata-i-dostavka|obmin|exchange|"
                        r"povernennia|return|returns|garantiya|faq|sitemap|siteindex|lookbook|reviews|manufacturer|"
                        r"filter|vacancies|kontakty|pro-nas|info|information|campaign|coop|dropshipping|"
                        r"pokuptsiu|all-posts|last-size|privacy|terms|ugoda|offerta|store|about-us-press|"
                        r"delivery-and-payment|dostavka-i-oplata|help|support|shipping|"
                        r"public-offer|publichna|oferta|look-?book|black-friday|chorna-pjatnycia|"
                        r"cdn-cgi|email-protection|loyal|cashback|keshbek|sertifikat|podarunk|"
                        r"garanti|harant|policy|polityk|otzyv|vidhuk|feedback|poshuk|porivn|"
                        r"look-?details|look-?book|obrazy|idei|blog-?post|f)(/|$)", re.I)
# службові файли й порожні шляхи, що трапилися в мапах 06.09 (devari .css, vmma .png, morandi %-URL)
# Фасетна адреса лістингу (favoriteshoes: /tufli/f/material-leather-and-type-loafers) — це фільтр,
# а не річ: у ній два+ ознаки, зшиті «-and-», або сегмент /f/ чи /filter/.
_ФАСЕТНА_АДРЕСА = re.compile(r"/f/|/filter/|/filters/|-and-type-|-and-color-|-and-material-|-and-size-", re.I)
_СЛУЖБОВЕ = re.compile(r"\.(css|js|png|jpe?g|webp|gif|svg|pdf|ico|xml|json|zip|mp4|woff2?|ttf)(\?|$)|"
                       r"/catalog/view/|/image/(cache|catalog)/|/wp-content/|/wp-json/|/assets?/|/static/", re.I)


def _не_наша_мова(url):
    шлях = urlparse(url).path.lower()
    return any(шлях.startswith(п) for п in _МОВНІ_ПРЕФІКСИ) or "/ru/" in шлях


def мапа_сайту(транспорт, база, robots, лог, стеля_файлів=8, треба_карток=1500, секунд=90):
    """П11: URL карток із карт сайту. Повертає (список url, дiагностика)."""
    старт = list(dict.fromkeys(robots.get("sitemaps") or [])) or \
            [urljoin(база, p) for p in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/sitemap.xml.gz", "/sitemaps.xml")]
    черга, бачено, картки, файлів = list(старт), set(), [], 0
    інші = 0
    кінець = time.time() + секунд
    while черга and файлів < стеля_файлів and time.time() < кінець:
        if len(картки) >= треба_карток:      # 06.09: md-fashion 19 файлів і 64 524 адрес заради 3 карток
            break
        u = черга.pop(0)
        if u in бачено:
            continue
        бачено.add(u); файлів += 1
        r = транспорт.get(u, тип="bytes", ліміт=8_000_000, секунд=25)
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
            шлях_ = urlparse(loc).path
            if _СЛУЖБОВЕ.search(loc) or шлях_ in ("", "/") or re.fullmatch(r"/(ua|uk|en|ru)/?", шлях_, re.I):
                інші += 1; continue                      # мапа зображень / css / головна / корінь мови
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


# ── WOO STORE API → ВАРІАНТ КОЛЬОРУ (рядок 5652; проєкт `жниварка_логіка_2026-10-15.md` §3.1, §3.5) ──────
# Одиниця речі пулу — варіант кольору: його напис (значення атрибута, дослівно), кадр, який прив'язала
# платформа (зображення варіації), і розміри з `is_in_stock`. Список товарів Store API кадрів і наявності
# варіацій не дає, тому варіації беруться окремим запитом `type=variation&parent=…`. Який атрибут — колір,
# а який — розмір, каже рецепт крамниці КОДОМ таксономії (`pa_color`), код слів не читає (п.12).
РЕЦЕПТИ_TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "рецепти.tsv")
_ПОЛЯ_ВАРІАЦІЇ = "id,parent,sku,permalink,is_in_stock,images"


def woo_рецепт(домен, шлях=None):
    """{"колір": "pa_color", "розмір": "pa_size"} — коди таксономій атрибутів з колонок рецепта крамниці
    (`атрибут_кольору`, `атрибут_розміру`); None — рецепта нема, і крамниця йде як доти, одним записом на товар."""
    шлях = шлях or РЕЦЕПТИ_TSV
    if not os.path.exists(шлях):
        return None
    with io.open(шлях, encoding="utf-8") as f:
        for р in csv.DictReader(f, delimiter="\t"):
            if (р.get("домен") or "").strip().lower().replace("www.", "") == (домен or "").strip().lower().replace("www.", ""):
                колір = (р.get("атрибут_кольору") or "").strip()
                return dict(колір=колір, розмір=(р.get("атрибут_розміру") or "").strip()) if колір else None
    return None


@functools.lru_cache(maxsize=None)
def рецепт_селекторів(домен, шлях=None):
    """{"опис": css, "склад": css, "характеристик": css, "блок": css} з колонок `селектор_опису`, `селектор_складу`, `селектор_характеристик`, `селектор_блоку`
    рецепта крамниці: блоки, які її сторінка сама підписала описом, складом і таблицею характеристик (рядки 5657, 6899);
    порожні — {}, і опис береться лише з JSON-LD чи `itemprop="description"`, а пари — з усієї сторінки за межею розмітки."""
    шлях = шлях or РЕЦЕПТИ_TSV
    if not os.path.exists(шлях):
        return {}
    with io.open(шлях, encoding="utf-8") as f:
        for р in csv.DictReader(f, delimiter="\t"):
            if (р.get("домен") or "").strip().lower().replace("www.", "") == (домен or "").strip().lower().replace("www.", ""):
                return {к: (р.get(кол) or "").strip() for к, кол in (("опис", "селектор_опису"), ("склад", "селектор_складу"),
                                                                   ("характеристик", "селектор_характеристик"), ("блок", "селектор_блоку")) if (р.get(кол) or "").strip()}
    return {}


def woo_варіації(транспорт, база, товари, лог, пачка=8, стеля_сторінок=80):
    """Варіації змінних товарів: `сирий["_варіації"]` = [dict(ід, адреса, є, кадри)] за товар. Запит — пачкою
    батьків; не відповів — ключа в товару нема, і він іде як доти. → скільки товарів дістали варіації."""
    змінні = [т for т in товари if (т.get("type") == "variable" or т.get("variations")) and т.get("id")]
    дістали = 0
    for i in range(0, len(змінні), пачка):
        група = змінні[i:i + пачка]
        за_ід = {т["id"]: [] for т in група}
        сторінка, ок = 1, True
        while сторінка <= стеля_сторінок:
            r = транспорт.get(urljoin(база, "/wp-json/wc/store/v1/products?type=variation&parent=%s&per_page=100&page=%d&_fields=%s"
                                      % (",".join(str(т["id"]) for т in група), сторінка, _ПОЛЯ_ВАРІАЦІЇ)))
            if r["код"] != 200 or not r["тіло"] or not r["тіло"].lstrip().startswith("["):
                ок = False
                break
            try:
                д = json.loads(r["тіло"])
            except Exception:
                ок = False
                break
            for в in д:
                if в.get("parent") in за_ід:
                    за_ід[в["parent"]].append(dict(ід=в.get("id"), адреса=канонічна_з_запитом(в.get("permalink"), база),
                                                   є=bool(в.get("is_in_stock")),
                                                   кадри=[канонічна(x.get("src"), база) for x in (в.get("images") or []) if x.get("src")]))
            if len(д) < 100:
                break
            сторінка += 1
        if ок:
            for т in група:
                т["_варіації"] = за_ід[т["id"]]
                дістали += 1
    лог("  woo варіації: %d з %d змінних товарів" % (дістали, len(змінні)))
    return дістали


def канонічна_з_запитом(url, база=None):
    """Адреса варіації лишає запит `attribute_pa_…` (він і називає варіант); решта — як `канонічна`."""
    if not url:
        return ""
    u = urlparse(urljoin(база or "", url.strip()))
    шлях = re.sub(r"/{2,}", "/", u.path or "/")
    return urlunparse((u.scheme or "https", u.netloc.lower(), шлях, "", u.query, ""))


def woo_store_api(транспорт, база, лог, стеля, рецепт=None, лише=None):
    """WooCommerce Store API: /wp-json/wc/store/v1/products — публічний без ключа. З рецептом крамниці
    (`woo_рецепт`) змінним товарам дістаються ще варіації (`woo_варіації`); `лише` — набір id товарів, чиї
    варіації потрібні (решта йде без них)."""
    вих, бачені, шлях, розмір = [], set(), "/wp-json/wc/store/v1/products", 100
    # maxa віддає товар із сотнями варіацій по секунді: сотня не вкладається в таймаут. Тому при невдачі розмір
    # половиниться, а сторінка рахується від зсуву (скільки товарів уже взято); повтори відсіюються за id.
    while len(вих) < стеля and len(вих) < 6000:
        r = транспорт.get(urljoin(база, "%s?per_page=%d&page=%d" % (шлях, розмір, len(бачені) // розмір + 1)))
        if r["код"] != 200 or not (r["тіло"] or "").lstrip().startswith("["):
            if розмір > 10:
                розмір = max(10, розмір // 2)
            elif not вих and шлях.endswith("v1/products"):
                шлях, розмір = "/wp-json/wc/store/products", 100       # старіший Woo без v1 (v2 пробувала обидва)
            else:
                break
            continue
        try:
            д = json.loads(r["тіло"])
        except Exception:
            break
        нові = [т for т in д if т.get("id") not in бачені]
        for т in нові:
            бачені.add(т.get("id"))
            вих.append(dict(канал="woo:wc/store", сирий=т, url=канонічна(т.get("permalink") or "", база)))
        if not нові or len(д) < розмір:
            break
    лог("  woo wc/store: %d товарів" % len(вих))
    if рецепт and шлях.endswith("v1/products"):
        woo_варіації(транспорт, база, [в["сирий"] for в in вих if лише is None or в["сирий"].get("id") in лише], лог)
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


# ── ФАСЕТИ (канал із v2, якого в v3 не було) ─────────────────────────────────────────────────
# `/ua/dresses/tsvet/korichnevyj` → колір, ОГОЛОШЕНИЙ магазином. v2, вимір 26.08: 96 % кольорів у
# заборі — здогад зі слага чи назви, оголошених магазином лише 4 %; склад — 0 із 24 магазинів.
# Фасет — єдине джерело такої мітки поза карткою. v2 спершу шукала фасети лише в ЗАПИТІ
# (?filters=color:, як у gepur) і дала 0 на 8 магазинах, хоча 238 адрес виду <поле>/<значення>
# лежали у «відсіяному» самого лише vovk: у OpenCart і Хорошопі фасет — це СЕГМЕНТ ШЛЯХУ.
_ПОЛЕ_У_ЗАПИТІ = re.compile(r"^(filters?|attribute_pa_\w+|filter_\w+|tsvet|cvet|color|colour|kolir|"
                            r"material|tkanina|sostav|sklad|razmer|rozmir|size|brand|brend|print|fason)$", re.I)
ПОЛЕ_У_ШЛЯХУ = re.compile(r"^(tsvet|cvet|color|colour|kolir|kolor|kolyor|material|tkanina|tkanyna|"
                          r"sostav|sklad|razmer|rozmir|size|dlina|dovzhyna|dovzhina|rukav|sleeve|"
                          r"fason|print|brend|brand|style|styl)$", re.I)
_ПОЛЕ_КАНОН = {"tsvet": "колір", "cvet": "колір", "color": "колір", "colour": "колір", "kolir": "колір",
               "kolor": "колір", "kolyor": "колір", "material": "склад", "tkanina": "склад", "tkanyna": "склад",
               "sostav": "склад", "sklad": "склад", "razmer": "розмір", "rozmir": "розмір", "size": "розмір",
               "dlina": "довжина", "dovzhyna": "довжина", "dovzhina": "довжина", "rukav": "рукав",
               "sleeve": "рукав", "fason": "крій", "print": "принт", "brend": "бренд", "brand": "бренд",
               "style": "крій", "styl": "крій"}


def фасети_сторінки(html_текст, база):
    """→ [(url, поле, значення)] для фільтрів виду `<поле>/<значення>` у шляху.
    Односегментний хвіст (/dresses/midi) НЕ береться: це підрозділ, він і так у черзі розділів."""
    вих = {}
    for м in re.finditer(r'href=["\']([^"\'#]+)["\'][^>]*>\s*([^<]{0,60})', html_текст or "", re.I):
        u = канонічна(м.group(1), база)
        if домен_із(u) != домен_із(база) or _не_наша_мова(u):
            continue
        сегменти = [x for x in urlparse(u).path.split("/") if x]
        if len(сегменти) < 2:
            continue
        поле, значення = сегменти[-2], сегменти[-1]
        if not ПОЛЕ_У_ШЛЯХУ.match(поле) or not значення:
            continue
        підпис = розекранувати(м.group(2))[:40]
        вих[u] = (u, _ПОЛЕ_КАНОН.get(поле.lower(), поле.lower()), підпис or значення.replace("-", " "))
    # ДРУГА СІМ'Я: фільтр у ЗАПИТІ (`?filters=color:chernyj` у gepur, `?attribute_pa_color=` у Woo).
    # v2 знала, що вона існує, але реалізувала лише сегментну — і дістала 0 фасетів на 8 магазинах із 8.
    for м in re.finditer(r'href=["\']([^"\'#]+)["\'][^>]*>\s*([^<]{0,60})', html_текст or "", re.I):
        u = канонічна(м.group(1), база)
        if домен_із(u) != домен_із(база) or _не_наша_мова(u) or "?" not in u or u in вих:
            continue
        підпис = розекранувати(м.group(2))[:40]
        for k, v in parse_qsl(urlparse(u).query):
            if not v or not _ПОЛЕ_У_ЗАПИТІ.match(k):
                continue
            поле, значення = k.lower(), v
            if ":" in v:
                поле, значення = v.split(":", 1)[0].lower(), v.split(":", 1)[1]
            поле = re.sub(r"^(attribute_pa_|filter_)", "", поле)
            канон = _ПОЛЕ_КАНОН.get(поле)
            if канон:
                вих[u] = (u, канон, підпис or значення.replace("-", " ")); break
    return list(вих.values())


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
# Рядок 126 дошки (21.09.2026): де крамниці РЕАЛЬНО тримають знімки речі. Перелік
# зроблено з живих сторінок, а не з гадання — виміряно на картках brenda.ua,
# alot.com.ua і miraton.ua, знятих 21.09 (числа — скільки атрибутів з адресою
# картинки на сторінці): brenda `a href` 5 і `style` background 10 (уся галерея
# лежить ТІЛЬКИ там, жодного `img src` галереї на сторінці нема), miraton
# `img data-src` 32 проти `img src` 11 (ліниве вантаження), alot `a href` 4.
_АТРИБУТИ_ФОТО = ("data-src", "data-lazy", "data-original", "data-zoom", "data-zoom-image",
                  "data-large", "data-large_image", "data-full", "data-image", "data-srcset",
                  "srcset", "src", "href")
_ФАЙЛ_КАРТИНКИ = re.compile(r"\.(jpe?g|png|webp|avif)(\?|$)", re.I)
_ФОН_КАРТИНКА = re.compile(r"background(?:-image)?\s*:[^;]*url\(\s*[\'\"]?([^\'\")]+)", re.I)
_НЕ_АДРЕСА = re.compile(r"^\s*(#|javascript:|mailto:|tel:|data:)", re.I)


def _під_чужою_карткою(ел, url):
    """Чи лежить цей знімок під посиланням на ІНШУ картку крамниці.

    ВИМІР, А НЕ СМАК (рядок 126 дошки, 21.09.2026). Тайл блоку «схожі товари» —
    це фото чужої речі, і відрізняє його не клас контейнера (у brenda блок
    зветься `product-layout`, і жодне слово з `_СУСІДИ` в нього не потрапляє) і
    не розмір тайла, а те, ЩО СТАНЕТЬСЯ ПО КЛІКУ: тайл рекомендації завжди
    загорнутий у посилання на СТОРІНКУ того іншого товару — інакше він не
    виконував би своєї роботи. Знімок власної галереї так не загортають: він або
    взагалі без посилання, або під посиланням на САМ ФАЙЛ картинки (lightbox:
    `<a class="thumbnail" href="…/19-1200x1800.jpg">` — brenda), або під
    посиланням на цю ж адресу.

    Виміряно на `https://brenda.ua/self-portrait-2` 21.09: 16 знімків під
    посиланнями на 8 інших карток (`/aninadin-1189`, `/roberto-cavalli-12`, …)
    і 5 знімків під посиланнями на файли `.jpg` — це і є власна галерея речі,
    яка доти в каталог не потрапляла жодного разу.

    Порогу тут нема й не треба: рішення приймається з однієї сторінки, офлайн і
    детерміновано. Незалежний детектор повторів (`джерела/фід_фото._спільні_фото`)
    лишається окремим шаром і цю роботу ПЕРЕВІРЯЄ, а не робить.
    """
    а = ел if getattr(ел, "name", None) == "a" and ел.get("href") else ел.find_parent("a")
    if а is None:
        return False
    h = (а.get("href") or "").strip()
    if not h or _НЕ_АДРЕСА.match(h):
        return False
    ціль = urlparse(канонічна(h, url))
    якщо_файл = _ФАЙЛ_КАРТИНКИ.search(ціль.path or "")
    if якщо_файл:
        return False                                  # lightbox на сам файл — це і є галерея
    свій = urlparse(url)
    return (ціль.netloc.lower(), (ціль.path or "/").rstrip("/")) != (свій.netloc.lower(), (свій.path or "/").rstrip("/"))


_РОЗМІР_СЕГМЕНТ_ФОТО = re.compile(r"^(\d{2,4})x(\d{2,4})(?![0-9x])", re.I)
_РОЗМІР_ХВІСТ_ФОТО = re.compile(r"[.\-_](\d{2,4})x(\d{2,4})(?=\.(?:webp|jpe?g|png|avif))", re.I)
_РОЗМІР_ПОЧАТОК_ФОТО = re.compile(r"^(\d{2,4})x(\d{2,4})(?![0-9x])", re.I)


def _кадр_і_площа(url):
    """(ім'я кадра без сегмента розміру, площа в пікселях або 0).

    Той самий кадр крамниця віддає в кількох розмірах, і галерея часто несе
    ОБИДВА поруч: у brenda мініатюра стоїть у `style` (`19-586x880.jpg`), а
    повний кадр — у `href` того ж посилання (`19-1200x1800.jpg`). Без згортання
    п'ять знімків речі займали б десять місць зі стелі `чисті_фото` у 8, і в
    каталог ішло б чотири кадри замість п'яти. Форми розміру — ті самі дві, що
    їх читає `джерела/фід_фото._файл_фото` (сегмент шляху і хвіст імені): там,
    де продукт каже «це той самий знімок», жнива мають казати те саме.
    """
    u = str(url or "").split("?")[0]
    ч = u.split("/")
    if u.lower().startswith(("http://", "https://")) and len(ч) > 3:
        ч = ч[3:]
    if not ч:
        return "", 0
    площа, тека = 0, []
    for c in ч[:-1]:                                  # ТЕКИ: `/23/400x600l95nn0/…` — сегмент-розмір
        м = _РОЗМІР_СЕГМЕНТ_ФОТО.match(c)
        if м:
            площа = max(площа, int(м.group(1)) * int(м.group(2)))
        else:
            тека.append(c)
    файл = ч[-1]
    # ІМ'Я ФАЙЛА — ОКРЕМО ВІД ТЕК (виміряно на miraton.ua 21.09). Якщо правило
    # сегмента пустити й на ім'я, то `1740x2280q90-000211588_1_.webp` зникає
    # цілком, і ключем кадра лишається сама тека `upload/webp_cache/` — тобто
    # УСІ знімки крамниці стають «одним кадром», і галерея з чотирьох ракурсів
    # згортається в один. Тому в імені розмір лише ЗРІЗАЄТЬСЯ: з початку
    # (`1740x2280q90-…`, miraton) або перед розширенням (`19-1200x1800.jpg`,
    # brenda), а решта імені лишається ключем.
    м = _РОЗМІР_ПОЧАТОК_ФОТО.match(файл)
    if м:
        площа = max(площа, int(м.group(1)) * int(м.group(2)))
        файл = файл[м.end():]
    м = _РОЗМІР_ХВІСТ_ФОТО.search(файл)
    if м:
        площа = max(площа, int(м.group(1)) * int(м.group(2)))
        файл = _РОЗМІР_ХВІСТ_ФОТО.sub("", файл)
    return "/".join(тека + [файл]).lower(), площа


def _найбільший_на_кадр(адреси):
    """Один — найбільший — знімок на кадр, у порядку першої появи кадра."""
    кращі, порядок = {}, []
    for a in адреси:
        к, площа = _кадр_і_площа(a)
        if к not in кращі:
            порядок.append(к); кращі[к] = (площа, a)
        elif площа > кращі[к][0]:
            кращі[к] = (площа, a)
    return [кращі[к][1] for к in порядок]


def _адреси_картинок(ел):
    """Усі адреси картинок, оголошені атрибутами цього елемента, у порядку `_АТРИБУТИ_ФОТО`.

    `srcset`/`data-srcset` згортаються до найширшого кандидата; `style` дає
    `background-image:url(...)` — саме там brenda тримає мініатюри галереї.
    """
    вих = []
    for атр in _АТРИБУТИ_ФОТО:
        v = ел.get(атр)
        if not v:
            continue
        if атр in ("srcset", "data-srcset"):
            кандидати_ = []
            for частина in str(v).split(","):
                ч = частина.strip().split()
                if ч:
                    шир = int(re.sub(r"\D", "", ч[1]) or 0) if len(ч) > 1 else 0
                    кандидати_.append((шир, ч[0]))
            v = max(кандидати_)[1] if кандидати_ else ""
        if атр == "href" and not _ФАЙЛ_КАРТИНКИ.search(str(v).split("?")[0]):
            continue                                  # посилання на сторінку — не картинка
        if v:
            вих.append(str(v))
    м = _ФОН_КАРТИНКА.search(ел.get("style") or "")
    if м:
        вих.append(м.group(1).strip())
    return вих
_РОЗМІР = re.compile(r"^(xxs|xs|s|m|l|xl|xxl|xxxl|3xl|4xl|5xl|6xl|one\s*size|os|onesize|універсальн\w*|"
                     r"\d{2}(?:[.,]5)?(?:\s*[-/–]\s*\d{2})?|\d{2}\s*[-/]\s*\d{2}\s*[-/]\s*\d{2}|"
                     r"\d{2,3}\s*(?:см)?(?:\s*\(\w+\))?|s/m|m/l|l/xl|xs/s|xl/xxl)$", re.I)
_ВІДСОТОК = re.compile(r"(\d{1,3}(?:[.,]\d{1,2})?)\s*%")
_ЗЛІПЛЕНО = re.compile(r"[а-яіїєґa-z][А-ЯІЇЄҐA-Z]")        # «еластанПравила»: межа вузлів розмітки загублена
СТЕЛЯ_СЛОВА_СКЛАДУ = 40
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
# кінець волокна: розділювач або підпис наступного блоку картки («…15% поліамід Розмір: XS/S») — підписи беруться з
# таблиці ключів вище (її синоніми «розмір»), а не з окремого переліку слів
_КІНЕЦЬ_ВОЛОКНА = re.compile(r"[,;|]|\.(?:\s|$)|(?i:\s+(?:%s))"
                             % "|".join(sorted(next(с for к, с in _КЛЮЧІ_ХАРАКТЕРИСТИК if к == "розмір"), key=len, reverse=True)))


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


def _відсоток_числом(рядок):
    return float(рядок.replace(",", "."))


def _показати_відсоток(n):
    return ("%d" % n) if float(n).is_integer() else ("%g" % n)


def _основи_часток(частина):
    return [(с.lower()[:4], н) for с, н in частина["волокна"]]


def склад_із(текст):
    """Значення підписаного блоку складу → структура «частина → волокно → %» з цитатою; None, коли відсотків нема.
    Рядок рахує код, слова — дослівно з цитати (п.12): ані словника волокон, ані переписування; лише число з «%» і сума.
    Сума частини = 100 закриває її (наступні відсотки — наступна частина, її підпис — слова крамниці перед двокрапкою);
    сума ≠ 100, слово завдовжки з речення чи зі зліплених вузлів — причина в `непевний`, а не мовчазна правка.
    {"цитата", "частини": [{"частина", "волокна": [[слово, %]], "сума"}], "непевний": [код причини]}"""
    т = " ".join(str(текст or "").split())
    збіги = [м for м in _ВІДСОТОК.finditer(т) if 0 < _відсоток_числом(м.group(1)) <= 100]
    if not збіги:
        return None
    слово_після = т[збіги[0].end():].lstrip()[:1].isalpha()               # «62% віскоза» проти «віскоза 62%»
    підписи, слова = [], []
    перед = т[:збіги[0].start()].strip()
    for i, м in enumerate(збіги):
        if слово_після:
            шматок = т[м.end():збіги[i + 1].start() if i + 1 < len(збіги) else len(т)]
            кінець = _КІНЕЦЬ_ВОЛОКНА.search(шматок)
            слова.append((шматок[:кінець.start()] if кінець else шматок).strip(" :-–—"))
            наступний = шматок[кінець.end():].strip() if кінець else ""                  # між волокнами: «Підкладка:»
            підписи.append(перед); перед = наступний
        else:
            шматок = т[збіги[i - 1].end() if i else 0:м.start()].lstrip(" ,;|./").rstrip(" :-–—=")
            підпис, _, слово = шматок.rpartition(":")
            підписи.append(підпис.strip()); слова.append((слово if підпис else шматок).strip(" ,-–—"))
    записи = [((п[:-1].strip() if п.endswith(":") else п) if слово_після else п) or None
              for п in підписи]
    записи = [п if п and re.search(r"[^\W\d_]", п) else None for п in записи]        # «,» між частинами — не підпис
    слова = [слово[:зл.start() + 1] if (зл := _ЗЛІПЛЕНО.search(слово)) and слово[:зл.start() + 1] else слово for слово in слова]
    записи = list(zip(записи, слова, (_відсоток_числом(м.group(1)) for м in збіги)))
    частини, непевний, відкрита = [], [], None
    for підпис, слово, n in записи:
        if відкрита and підпис:
            частини.append(відкрита); відкрита = None
        if відкрита is None:
            відкрита = {"частина": підпис, "волокна": [], "сума": 0.0}
        if any(n == н and слово.lower()[:4] == с.lower()[:4] for с, н in відкрита["волокна"]):
            continue                                  # «65% вовна; 65% вовни»: той самий склад двічі — не друга частка
        відкрита["волокна"].append([слово, n]); відкрита["сума"] = round(відкрита["сума"] + n, 2)
        if відкрита["сума"] >= 100:
            частини.append(відкрита); відкрита = None
        if not слово or len(слово) > СТЕЛЯ_СЛОВА_СКЛАДУ:
            непевний.append("слово")
        elif _ЗЛІПЛЕНО.search(слово):
            непевний.append("зліплено")
    if відкрита:
        частини.append(відкрита)
    for i, ч in reversed(list(enumerate(частини))):   # безпідписна основа й її повтор під підписом («матеріал: верх») — один склад
        if any(не_ч["частина"] in (None, ч["частина"]) and _основи_часток(не_ч) == _основи_часток(ч) for не_ч in частини[:i]):
            del частини[i]
    if any(ч["сума"] != 100 for ч in частини):
        непевний.append("сума_не_100")
    return {"цитата": т[:400], "частини": частини, "непевний": list(dict.fromkeys(непевний))}


def склад_рядком(структура):
    """Структура `склад_із` → рядок для `param склад`: слова крамниці як є; підписи частин — лише коли частин кілька."""
    ч = структура["частини"]
    return "; ".join(
        (("%s: " % p["частина"]) if len(ч) > 1 and p["частина"] else "") +
        ", ".join(("%s%% %s" % (_показати_відсоток(n), с)).strip() for с, n in p["волокна"]) for p in ч)[:400]


def склад_основа_із(структура):
    """Структура `склад_із` → рядок ОСНОВИ (перша частина, без підпису) лише коли частин кілька, інакше None.
    Основа — ПОЗИЦІЯ, не слово: частини ділить сума 100, а підпис («Підкладка:») лишається словом крамниці в `склад`;
    читачі каталогу (`фід_атрибути.матеріал_речі`, `слова_з_param`) беруть цей ключ і слів підпису не читають (п.12)."""
    if not структура or len(структура["частини"]) < 2:
        return None
    return склад_рядком({"частини": [dict(структура["частини"][0], частина=None)]}) or None


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


# ── МЕЖА БЛОКУ ХАРАКТЕРИСТИК (рядки 5625, 6803) ───────────────────────────────────────────────────────────────────────
# Пари «ключ → значення» картка збирає з усієї сторінки (tr, dl, li, p), тож у `характеристики_сирі` потрапляли меню
# («Жіночий одяг → Верхній одяг Бомбери…»), підвал («Компанія → Ми в соцмережах»), плитки ціни («6999 → ₴»), рядки таблиці
# розмірів і блоки доставки з оплатою. Межу тримає РОЗМІТКА, не слова назв: шапка/підвал/навігація/бічна колонка (тег чи
# ARIA-роль) і блок за класом-частиною (menu, footer, related…) — крім тих, що обгортають заголовок картки (зламана розмітка
# vmma вкладає всю сторінку в `div.bo-mainmenu`); таблиця з шапкою `th` (сітка, не ключ-значення); рядок із самих посилань;
# ключ із посиланням чи кнопкою; значення зі списком посилань; ключ без літер; ключ-речення і абзац замість значення — за
# довжиною (п.12: словника назв нема).
_МЕЖА_ТЕГИ = frozenset(("header", "footer", "nav", "aside"))
_МЕЖА_РОЛІ = frozenset(("navigation", "banner", "contentinfo", "complementary"))
_МЕЖА_КЛАСИ = frozenset(("menu", "footer", "related", "similar", "recommend", "recommended", "upsell", "viewed", "cookie",
                         "popup", "modal"))
_КЛЮЧ_СЛІВ_МАКС = 6
_ПОСИЛАНЬ_У_ЗНАЧЕННІ_МАКС = 4
_ЗНАЧЕННЯ_СИМВОЛІВ_МАКС = 200
_ЧАСТКА_ПОСИЛАНЬ_РЯДКА = 0.8


def поза_блоком_характеристик(ел, пам, обгортки=frozenset()):
    """True, коли елемент лежить у навігації, шапці, підвалі, бічній колонці, меню чи блоці «схожого»: його пари — не
    характеристики цієї речі. `обгортки` — id предків заголовка картки: вони обгортають і товар, тож межею не є. `пам` —
    {id вузла: відповідь}, спільний на сторінку (предки повторюються сотні разів)."""
    шлях = []
    вузол = ел
    відповідь = False
    while вузол is not None and getattr(вузол, "name", None) and вузол.name != "[document]":
        if id(вузол) in пам:
            відповідь = пам[id(вузол)]
            break
        частини = set(re.split(r"[-_\s]+", " ".join(вузол.get("class") or []).lower())) if вузол.name not in ("html", "body") else set()
        межа = вузол.name in _МЕЖА_ТЕГИ or (вузол.get("role") or "") in _МЕЖА_РОЛІ or bool(частини & _МЕЖА_КЛАСИ)
        if межа and id(вузол) not in обгортки:
            відповідь = True
            break
        шлях.append(вузол)
        вузол = вузол.parent
    for п in шлях:
        пам[id(п)] = відповідь
    return відповідь


def рядок_із_посилань(ряд):
    """True, коли текст рядка (li, tr, dd) на `_ЧАСТКА_ПОСИЛАНЬ_РЯДКА` складається з тексту посилань: це пункт меню, а не
    «ключ → значення» (у характеристиці ключ стоїть поза посиланням)."""
    текст = len(ряд.get_text("", strip=True))
    return bool(текст) and sum(len(a.get_text("", strip=True)) for a in ряд.find_all("a")) / текст >= _ЧАСТКА_ПОСИЛАНЬ_РЯДКА


def пара_придатна(ряд, ключ_ел, значення_ел, ключ, значення):
    """Чи пара «ключ → значення» має вигляд характеристики: ключ має літери й не довший за назву, без посилань і кнопок,
    значення не є списком посилань, рядок не складається з самих посилань. Рахує розмітку й довжину, слів не читає."""
    if not ключ or not значення or not re.search(r"[^\W\d_]", ключ):
        return False
    if len(ключ.split()) > _КЛЮЧ_СЛІВ_МАКС or len(значення) > _ЗНАЧЕННЯ_СИМВОЛІВ_МАКС:
        return False
    if ключ_ел is not None and ключ_ел.find(["a", "button", "input", "select"]) is not None:
        return False
    if значення_ел is not None and len(значення_ел.find_all("a")) > _ПОСИЛАНЬ_У_ЗНАЧЕННІ_МАКС:
        return False
    return not (ряд is not None and рядок_із_посилань(ряд))


def таблиця_сіткою(таблиця):
    """True, коли перший рядок таблиці — самі `th` (шапка сітки): це таблиця розмірів чи мірок, не перелік «ключ → значення»."""
    перший = таблиця.find("tr") if таблиця is not None else None
    клітини = перший.find_all(["th", "td"]) if перший is not None else []
    return len(клітини) >= 2 and all(к.name == "th" for к in клітини)


_МЕТА_ТЕГ = re.compile(r"<meta\b[^>]*>", re.I)
_МЕТА_АТРИБУТ = re.compile(r"""([\w:.-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""")


def мета_теги(html_текст):
    """{property|name у нижньому регістрі: content} усіх `<meta>` сторінки; перше значення виграє. Лапка-межа — та сама, що
    відкривала значення: апостроф усередині «…» не обриває його (06.09, ager.ua: og:title «Пов'язки на голову» давало «Пов»).
    Один лінійний прохід по тегах: пошук `<meta[^>]+…[^>]+content=…` по всій сторінці на 395 КБ (cultboutique) ішов
    18 с із 20 (рядок 6804)."""
    вих = {}
    for тег in _МЕТА_ТЕГ.findall(html_текст or ""):
        атр = {к.lower(): (а or б) for к, а, б in _МЕТА_АТРИБУТ.findall(тег)}
        if "content" not in атр:
            continue
        for ключ in ("property", "name"):
            if атр.get(ключ):
                вих.setdefault(атр[ключ].lower(), атр["content"])
    return вих


# Чужі вузли сторінки картки: блоки сусідніх товарів, відгуки, «швидкий перегляд», шапка. Вирізаються з розбору ДО
# читання полів — поле картки береться лише з вузла свого товару, а не чиститься після. Слів сторінки (п.12) тут нема:
# чужий блок — БУДОВА (перелік, чиї ≥ 2 діти — однакові плитки «посилання + ціна»), плюс токени розмітки
# платформи (клас не міняється з локалізацією) для відгуків і «швидкого перегляду», яких будова не видає: у них нема ціни.
_ЧУЖИЙ_КЛАС = re.compile(r"(?<![a-z])(?:related|similar|recommend(?:ed|ations?)?|upsell|cross-?sell|viewed|recent|also|reviews?|comments?|feedbacks?|"
                         r"fast-?view|quick-?view|testimonial|rating-?list|(?:mobile|site|main|top|global)-?(?:header|footer))"
                         r"(?![a-z])", re.I)
_ЗАГОЛОВКИ = ("h1", "h2", "h3", "h4", "h5")


def _не_розмір_числом(текст):
    """Голе число поза 30–60 — мірка в см чи лічильник, не розмір одягу/взуття; «M», «42», «36.5» лишаються."""
    м = re.fullmatch(r"(\d{2,3})(?:[.,]5)?", текст)
    return bool(м) and not 30 <= int(м.group(1)) <= 60


def _плитки(вузол):
    """Діти вузла, що повторюють одну будову плитки сусіднього товару: однаковий тег і клас, коротка, з посиланням і ціною.
    Дві і більше такі дитини — вузол є переліком чужих товарів."""
    групи = {}
    for д in вузол.find_all(True, recursive=False):
        текст = _текст(д, 400)
        if len(текст) < 300 and д.find("a", href=True) is not None and _ЦІНА.search(текст):
            групи.setdefault((д.name, tuple(д.get("class") or ())), []).append(д)
    return max((len(г) for г in групи.values()), default=0)


def вузол_товару(суп, h1, селектори):
    """Межа блоку товару — єдина для всіх полів DOM (ПС-2). Лише те, що підписала сторінка чи рецепт: `селектор_блоку`
    рецепта крамниці, інакше єдиний вузол `itemtype=…/Product`. Евристики (найближчий предок h1, перший «product») нема:
    вона брала сусідній текст. Повертає (вузол, «рецепт» | «itemtype») або (None, причина) — причина іде в запис і в звіт
    жнив. Блок має містити h1, коли h1 є: чужий вузол з того ж селектора межею не стає."""
    предки = {id(p) for p in h1.parents} if h1 is not None else None
    сел = (селектори or {}).get("блок")
    if not сел:
        знайдено, звідки, причина = суп.select('[itemtype$="/Product"], [itemtype$="/Product/"]'), "itemtype", "нема_межі_блоку"
    else:
        try:
            знайдено = суп.select(сел)
        except Exception:                                              # noqa — чужий селектор у рецепті не валить картку
            return None, "селектор_блоку_помилка"
        звідки, причина = "рецепт", "селектор_блоку_не_знайшов"
    if предки is not None:
        знайдено = [в for в in знайдено if id(в) in предки]
    elif len(знайдено) != 1:
        знайдено = []
    if not знайдено:
        return None, причина
    return знайдено[-1], звідки                              # найвужчий предок h1 з тим самим селектором


def прибрати_чуже(суп, h1):
    """Вирізає з розбору вузли, що не належать товару: шапка, підвал, навігація, блоки сусідніх товарів за будовою
    (перелік з ≥ 2 однаковими плитками «посилання + ціна») і блоки за токеном класу («review», «fast-view»…).
    Вузол, що містить h1, не чіпає. Повертає число вирізаних блоків (діагностика: скільки чужого відсічено)."""
    предки = {id(p) for p in h1.parents} if h1 is not None else set()
    вирізано = 0
    for вузол in list(суп.find_all(True)):
        if вузол.decomposed or id(вузол) in предки:
            continue
        if _плитки(вузол) >= 2:
            вузол.decompose(); вирізано += 1
    for вузол in list(суп.find_all(True)):
        if вузол.decomposed or id(вузол) in предки:
            continue
        клас = " ".join(вузол.get("class") or []) + " " + str(вузол.get("id") or "")
        if вузол.name in ("header", "footer", "nav") or _ЧУЖИЙ_КЛАС.search(клас):
            вузол.decompose(); вирізано += 1
    return вирізано


def факти_з_картки(html_текст, url, селектори=None):
    """Факти з HTML картки, з провенансом. Нічого не судить — лише читає. `селектори` — `рецепт_селекторів` крамниці."""
    селектори = селектори or {}
    ф = dict(назва=None, назва_джерело=None, опис=None, ціна=None, ціна_стара=None, валюта=None,
             available=None, наявність=None, фото=[], фото_джерело=None, крихти=[], характеристики={},
             характеристики_сирі=[], розміри=[], розміри_в_наявності=[], розміри_джерело=None, бренд=None,
             артикул=None, id_магазину=None, колір_ld=None, мова_альт=None, group_id=None, варіанти=[],
             свотчі=[], таблиця_мірок=None, склад_джерело=None)
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
        ф["опис"] = текст_з_html(p.get("description"))[:8000] or None
        ф["опис_джерело"] = "json-ld description" if ф["опис"] else None
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
            ф["характеристики"].setdefault("склад", розекранувати(мат)); ф["склад_джерело"] = "json-ld material"
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
            ф["ціна"] = min(ціни); ф["ціна_джерело"] = "json-ld offers"
        if наявн:
            ф["available"] = any(наявн)
    # ── meta / OpenGraph ───────────────────────────────────────────────────────
    мета = мета_теги(т)

    def meta(ім):
        значення = мета.get(ім.lower())
        return розекранувати(значення) if значення is not None else None
    if not ф["назва"]:
        ф["назва"] = meta("og:title"); ф["назва_джерело"] = "og:title" if ф["назва"] else None
    if ф["ціна"] is None:
        ф["ціна"] = _ціна_число(meta("product:price:amount") or meta("og:price:amount"))
        ф["ціна_джерело"] = "meta product:price" if ф["ціна"] is not None else None
        ф["валюта"] = ф["валюта"] or meta("product:price:currency") or meta("og:price:currency")
    if ф["available"] is None:
        ф["available"] = _наявність_ld(meta("product:availability") or meta("og:availability"))
    if not ф["є_товар"]:
        ф["є_товар"] = (meta("og:type") or "").startswith("product") and not ф.get("є_список")
    if not ф["є_товар"] and _ЯВНО_КАРТКА.search(url) and not ф.get("є_список"):
        # адреса виду /product/<slug>, /tovar/<id>, «…-1234» — найсильніший сигнал; далі досить ціни
        # (06.09: cher17 /product/shtani-z-skladkami-molochnij рахувався «не карткою» через блок
        # «схожі товари» — там більше 6 цін, і суворе DOM-правило його вбивало)
        ф["є_товар"] = bool(ф["ціна"]) or bool(re.search(r"\d[\d\s]{2,}\s*(?:грн|₴|UAH)", т, re.I))
    _шлях = urlparse(url).path
    if _шлях in ("", "/") or re.fullmatch(r"/(ua|uk|en|ru)/?", _шлях, re.I) or _НЕ_КАРТКА.search(_шлях):
        ф["є_товар"] = False; ф["є_список"] = True
        return ф                                          # головна, корінь мови, статична сторінка
    if re.search(r"/(product-category|category|categories|catalog|katalog|collections?|brand|brands)(/|$)", _шлях, re.I) \
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
    # `<base href>` (25union: `/image/cache/…` від кореня, не від картки — 542 хибні адреси фото, 5629)
    база_href = суп.find("base", href=True)
    url_бази = urljoin(url, база_href["href"].strip()) if база_href else url
    for s in суп(["script", "style", "noscript", "svg"]):
        s.decompose()
    h1 = суп.find("h1")
    h1_текст = _текст(h1, 200) if h1 else ""
    if h1_текст and (not ф["назва"] or російське(ф["назва"]) or re.match(r"^\s*(купити|купить|buy)\b", ф["назва"], re.I)):
        змістовний = len(h1_текст) >= 10 and len(h1_текст.split()) >= 2      # «Жіноче» (arber 06.09) — це рубрика, не назва
        if not російське(h1_текст) and (змістовний or not ф["назва"]):
            ф["назва"], ф["назва_джерело"] = h1_текст, "h1 (json-ld/og %s)" % ("російською" if ф["назва"] and російське(ф["назва"]) else "«купити…»" if ф["назва"] else "нема")
    if not ф["крихти"]:
        кр = суп.select_one('[class*="breadcrumb"], [id*="breadcrumb"], nav[aria-label*="rumb"], [class*="crumb"]')
        if кр:
            ф["крихти"] = [x for x in (_текст(a, 60) for a in кр.find_all(["a", "li", "span"])) if x and len(x) < 60]
            ф["крихти"] = list(dict.fromkeys(ф["крихти"]))[:8]
    ф["сирий"] = dict(h1=h1_текст or None, og_title=meta("og:title"), опис=ф["опис"],
                      назва_json_ld=розекранувати(продукт.get("name") or "") if продукт else None)
    ф["чужих_блоків"] = прибрати_чуже(суп, h1)         # поля нижче — лише з вузла цього товару
    блок, ф["межа_блоку"] = вузол_товару(суп, h1, селектори)
    # ПС-2: одна межа для всіх полів DOM нижче. Нема межі — це не «весь суп», а порожній корінь: поле «нема» з причиною
    # `межа_блоку` (JSON-LD, og й канали API — підписані самим джерелом — не чіпаються)
    кор = блок if блок is not None else BeautifulSoup("", ПАРСЕР_HTML)
    # блок опису, який сторінка підписала сама: селектор рецепта, інакше `itemprop="description"` (рядок 5657). Сусідні блоки,
    # що вона підписала «схожими» чи «рекомендованими», з нього геть; будь-який інший `class*="desc"` описом не вважається.
    блок_опису = None
    for сел in (селектори.get("опис"), '[itemprop="description"]'):
        try:
            знайдено = [e for e in кор.select(сел) if e.name != "meta"] if сел else []
        except Exception:                                              # noqa — чужий селектор у рецепті не валить картку
            ф["селектор_помилка"] = сел; знайдено = []
        if знайдено:
            блок_опису = знайдено[0]
            break
    if блок_опису is not None:
        for сус in блок_опису.select('[class*="related"], [class*="similar"], [class*="recommend"], [class*="upsell"], [class*="viewed"]'):
            сус.decompose()
    # характеристики: table tr(th|td, td), dl dt/dd, li «ключ: значення», div.label + div.value
    пари, пари_опису = [], []
    if блок_опису is not None:           # абзаци й пункти опису — окремі рядки розмітки: «Склад: …» стоїть в одному з них
        for рядок in блок_опису.find_all(["p", "li"]):
            tx = _текст(рядок, 300)
            a, _, b = tx.partition(":")
            if 2 < len(a) < 40 and b.strip() and _ключ_характеристики(a):
                пари_опису.append((a, b))
    пам, сітки = {}, {}                                    # межа блоку (рядки 5625, 6803): див. `поза_блоком_характеристик`
    обгортки = {id(п) for п in h1.parents} if h1 is not None else set()

    # рецепт назвав вузол характеристик (рядок 6899): пари — лише з нього, а не з блоків оплати, доставки, відгуків чи маркетингу
    if селектори.get("характеристик"):
        try:
            вузли = кор.select(селектори["характеристик"])             # усі збіги: на сторінці їх може бути кілька таблиць
            у_вузлі = {id(в) for в in вузли} | {id(x) for в in вузли for x in в.descendants}
        except Exception:                                              # noqa
            ф["селектор_помилка"] = селектори["характеристик"]; у_вузлі = None
    else:
        у_вузлі = None

    def в_межах(ел):
        if у_вузлі is not None and id(ел) not in у_вузлі:
            return False
        return not поза_блоком_характеристик(ел, пам, обгортки)

    def додати(ряд, ключ_ел, значення_ел, ключ=None, значення=None):
        к = ключ if ключ is not None else _текст(ключ_ел, 80)
        з = значення if значення is not None else _текст(значення_ел, 400)
        if пара_придатна(ряд, ключ_ел, значення_ел, розекранувати(к).strip(" :·-—"), розекранувати(з).strip()):
            пари.append((к, з))
    for tr in кор.find_all("tr"):
        кл = tr.find_all(["th", "td"])
        таблиця = tr.find_parent("table")
        if id(таблиця) not in сітки:
            сітки[id(таблиця)] = таблиця_сіткою(таблиця)
        if len(кл) == 2 and not сітки[id(таблиця)] and в_межах(tr):
            додати(tr, кл[0], кл[1])
    for dl in кор.find_all("dl"):
        if not в_межах(dl):
            continue
        dts, dds = dl.find_all("dt"), dl.find_all("dd")
        for a, b in zip(dts, dds):
            додати(None, a, b)
    for li in кор.find_all("li"):
        if not в_межах(li):
            continue
        діти = [x for x in li.find_all(["span", "div", "b", "strong", "p"], recursive=False)]
        if len(діти) == 2:
            додати(li, діти[0], діти[1])
        else:
            tx = _текст(li, 300)
            if ":" in tx and len(tx) < 200:
                a, b = tx.split(":", 1)
                if 2 < len(a) < 40 and not (a[-1:].isdigit() and b.strip()[:2].isdigit()):     # «Пн-Нд 12:00» — години, не ключ
                    додати(li, None, li, a, b)
    for ряд in кор.select("div.properties-group__item, div.properties__item"):
        if not в_межах(ряд):
            continue
        ключ = ряд.select_one(".properties-group__name, .properties__title")
        значення = ряд.select_one(".properties-group__value, .properties__value")
        if ключ is not None and значення is not None:
            додати(ряд, ключ, значення)
        else:
            клітини = ряд.find_all("span", recursive=False)
            if len(клітини) == 2:
                додати(ряд, клітини[0], клітини[1])
    for абзац in кор.find_all("p"):          # «<p><strong>Матеріал:</strong> 62% віскоза</p>»: підпис виділено розміткою
        жирний = абзац.find(["strong", "b"])
        tx, a = _текст(абзац, 300), _текст(жирний, 80) if жирний is not None else ""
        if a.endswith(":") and tx.startswith(a) and tx[len(a):].strip() and в_межах(абзац):
            додати(абзац, жирний, None, a, tx[len(a):])
    пари.extend(пари_опису)                 # після таблиць і списків: структурована характеристика сильніша за рядок опису
    бачені = set()
    for a, b in пари:
        a_, b_ = розекранувати(a).strip(" :·-—")[:60], розекранувати(b)[:400]
        if ПЛИТКА_СХОЖОГО.search(b_):
            continue                                  # чужа плитка «схожих товарів», не характеристика цієї речі (рядок 2360)
        if a_ and b_ and a_.lower() not in бачені and len(ф["характеристики_сирі"]) < 40 and not _РОЗМІР.match(a_.upper()):
            бачені.add(a_.lower()); ф["характеристики_сирі"].append([a_, b_])
        k = _ключ_характеристики(a)
        if k and b and k not in ф["характеристики"]:
            ф["характеристики"][k] = b_
            if k == "склад":
                ф["склад_джерело"] = "рядок опису" if (a, b) in пари_опису else "таблиця характеристик"
    # таблиця мірок виробу (см по розмірах): ≥ 3 колонки й шапка про розмір/обхват — verbatim
    for tbl in кор.find_all("table"):
        рядки_т = [[_текст(c, 40) for c in tr.find_all(["th", "td"])] for tr in tbl.find_all("tr")]
        рядки_т = [r for r in рядки_т if len(r) >= 3]
        if len(рядки_т) >= 2 and re.search(r"розмір|size|обхват|груд|талі|стегн|довжин|рукав|плеч|\bсм\b", " ".join(рядки_т[0]), re.I):
            ф["таблиця_мірок"] = " ; ".join(" | ".join(r) for r in рядки_т)[:800]; break
    # свотчі кольору: елемент зі стилем background/data-hex або картинкою, підпис з title/alt/тексту
    for ел in кор.select('[class*="swatch"], [class*="color"], [class*="colour"], [class*="kolir"], [class*="colir"], [data-color], [data-hex]'):
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
        кар = канонічна(img.get("data-src") or img.get("src") or "", url_бази) if img else None
        if not hex_ and not кар:
            continue
        підпис = розекранувати(ел.get("title") or ел.get("aria-label") or ел.get("data-title") or ел.get("data-value") or
                              (img.get("alt") if img else "") or _текст(ел, 30))[:40]
        активний = bool(re.search(r"active|selected|checked|current", " ".join(ел.get("class") or []) + " " + str(ел.get("aria-checked") or ""), re.I))
        if len(ф["свотчі"]) < 20:
            ф["свотчі"].append(dict(назва=підпис or None, hex=hex_, фото=кар, активний=активний))
    # склад з блоку, який рецепт крамниці назвав селектором, — сильніше за пари; з довільного тексту сторінки не беремо
    if селектори.get("склад"):
        try:
            ел_складу = кор.select_one(селектори["склад"])
        except Exception:                                              # noqa
            ф["селектор_помилка"] = селектори["склад"]; ел_складу = None
        if ел_складу is not None and _текст(ел_складу, 400):
            ф["характеристики"]["склад"] = _текст(ел_складу, 400); ф["склад_джерело"] = "селектор рецепта"
    # розміри: контейнери, чиї клас/ім'я/текст мітки кажуть «розмір»
    розміри, в_наявн = [], []
    for конт in кор.select('[class*="size"], [class*="rozmir"], [class*="razmer"], [id*="size"], [data-attribute*="size"],'
                           ' select[name*="size"], select[name*="rozmir"], [class*="variant"], [class*="option"], [class*="sku-props"]'):
        if re.search(r"gallery|image|photo|slider|swiper", " ".join(конт.get("class") or []), re.I):
            continue                                          # «gallery-size-large» — розмір кадру, не одягу
        for ел in конт.find_all(["option", "button", "label", "a", "li", "span", "input", "div"]):
            текст = (ел.get("value") if ел.name in ("input", "option") and not _текст(ел, 20) else _текст(ел, 20)) or ""
            текст = текст.strip().upper()
            if not текст or not _РОЗМІР.match(текст) or len(текст) > 12 or _не_розмір_числом(текст):
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
        for сус in кор.select('[class*="related"], [class*="similar"], [class*="recommend"], [class*="also"], '
                              '[class*="recent"], [class*="upsell"], [class*="viewed"], footer, header, nav'):
            сус.decompose()
        галерея = кор.select_one('[class*="gallery"], [class*="product-image"], [class*="product__media"], '
                                 '[class*="swiper"], [class*="slider"], [class*="fotorama"], [class*="carousel"], '
                                 '[class*="photos"], [class*="images"], [class*="product-photo"]') or кор
        картинки, чужих = [], 0
        # 21.09 (рядок 126): шукаємо по ВСІХ вузлах, а не лише по `img/source/a`, бо
        # brenda тримає мініатюри в `style="background-image:url(…)"` на `a`, а
        # повний кадр — у `href` того ж `a`; `img src` на її картці — самі тайли
        # блоку рекомендацій.
        for ел in галерея.find_all(True):
            if _під_чужою_карткою(ел, url):
                чужих += 1
                continue                              # тайл «схожих товарів» — фото чужої речі
            адреси = _адреси_картинок(ел)
            if not адреси:
                continue
            w = ел.get("width")
            if w and str(w).isdigit() and int(w) <= 300:
                continue
            картинки.extend(оригінал_фото(канонічна(v, url_бази)) for v in адреси)
        для = [x for x in dict.fromkeys(картинки) if re.search(r"\.(jpe?g|png|webp|avif)(\?|$)|/image|/photo|/img|/media|/upload", x, re.I)]
        для = _найбільший_на_кадр(для)
        if для:
            ф["фото"] = list(dict.fromkeys(ф["фото"] + для)); ф["фото_джерело"] = (ф["фото_джерело"] or "") + "+галерея"
        if чужих:
            ф["чужих_тайлів"] = чужих                 # не мовчати, скільки знімків відсічено як чужі
    # ціна з розмітки, якщо структурні джерела мовчали
    if ф["ціна"] is None:
        ел = кор.select_one('[itemprop="price"], [class*="price"] , [id*="price"]')
        # гейт «це картка» судить сторінку, а не поле: рахує ціни по всій сторінці, межа блоку його не стосується (ПС-2)
        if суп.select_one('[itemprop="price"], [class*="price"] , [id*="price"]') is not None and суп.find("h1") \
                and not ф["є_товар"] and not ф.get("є_список"):
            цін = len(суп.select('[itemprop="price"], [class*="price"]'))
            if _ЯВНО_КАРТКА.search(url):
                цін = min(цін, 6)                    # явна товарна адреса: блок «схожі» не рахуємо
            є_кнопка = bool(re.search(r"кошик|корзин|купити|купить|add to cart|add to bag|\bbuy\b|замовити|заказать", суп.get_text(" ")[:200000], re.I))
            ф["є_товар"] = 1 <= цін <= 6 and є_кнопка      # лістинг: десятки цін; картка: одна-дві
        if ел:
            v = _ціна_число(ел.get("content") or ел.get("data-price") or None)
            if v is None:
                м = _ЦІНА.search(_текст(ел, 120))
                v = _ціна_число(м.group(1)) if м else None
            if v:
                ф["ціна"] = v; ф["валюта"] = ф["валюта"] or "UAH"; ф["ціна_джерело"] = "розмітка ціни товару"
        if ф["ціна"] is None:
            ф["ціна_діагностика"] = " | ".join(_текст(e, 60) for e in кор.select('[class*="price"], [itemprop="price"]')[:3]) or None
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
    if (not ф["опис"] or російське(ф["опис"])) and блок_опису is not None:
        т_ = _текст(блок_опису, 8000)
        if т_ and (not ф["опис"] or not російське(т_)):
            ф["опис"] = т_; ф["опис_джерело"] = "блок опису"
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
    опис = текст_з_html(т.get("body_html"))[:8000] or None
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


def варіанти_woo(т, база, рецепт):
    """Товар Store API → [dict] варіантів кольору або None (рецепта чи атрибута кольору нема, чи варіації не
    дісталися: тоді товар іде одним записом, як доти). Колір і розмір знаходить КОД таксономії з рецепта,
    слово кольору — значення терма дослівно; запит `attribute_<таксономія>=<слаг>` в адресі варіації з'єднує
    варіацію з термом (слаг — код, не слово).
      · колір не варіація чи терм один → один варіант, кадри — уся галерея товару (інших кольорів тут нема);
      · кольорів ≥ 2 → варіант на терм; кадр варіанта — зображення його варіацій (платформа прив'язала), крім
        тих, що стоять і в іншого кольору (запасне зображення товару) — таких `кадри` не мають, «невідомі».
    Поля варіанта: слаг, слово, за_замовч, кадри, кадри_джерело (woo:images | woo:variations | None), розміри,
    розміри_в_наявності, розміри_джерело, є, ід_варіацій, кольорів_у_товарі."""
    if not рецепт or not рецепт.get("колір"):
        return None
    атр = {(a.get("taxonomy") or a.get("name") or ""): a for a in т.get("attributes") or []}
    кол = атр.get(рецепт["колір"])
    терми = [x for x in ((кол or {}).get("terms") or []) if x.get("name")]
    if not терми:
        return None
    розм = атр.get(рецепт.get("розмір") or "") or {}
    назва_розміру = {x.get("slug"): x.get("name") for x in розм.get("terms") or []}
    вар = т.get("_варіації")
    ключ_к, ключ_р = "attribute_" + рецепт["колір"], "attribute_" + (рецепт.get("розмір") or "-")
    галерея = list(dict.fromkeys(канонічна(i.get("src"), база) for i in (т.get("images") or []) if i.get("src")))

    def запит(в):
        return parse_qs(urlparse(в["адреса"]).query)

    def розміри_з(варіації):
        """(усі розміри, розміри в наявності) варіацій; нема розмірного атрибута — розмірів нема."""
        усі, є = [], []
        for в in варіації:
            с = (запит(в).get(ключ_р) or [""])[0]
            if not с:
                continue
            н = str(назва_розміру.get(с) or с).upper()
            усі.append(н)
            if в["є"]:
                є.append(н)
        return list(dict.fromkeys(усі)), list(dict.fromkeys(є))

    if вар is None and (т.get("variations") or т.get("type") == "variable"):
        return None                                     # варіації не дісталися — наявності розмірів не знаємо
    вар = вар or []
    один = len(терми) == 1 or not кол.get("has_variations")
    if один:
        слово = ", ".join(x["name"] for x in терми)
        if вар:
            усі, є = розміри_з(вар)
            ввімк, дж = any(в["є"] for в in вар), "woo:variations"
        else:                                           # проста річ: розміри — терми атрибута, наявність — товару
            ввімк = bool(т.get("is_in_stock"))
            усі = [str(x["name"]).upper() for x in розм.get("terms") or [] if x.get("name")]
            є, дж = (усі if ввімк else []), ("woo:attributes" if усі else None)
        return [dict(слаг=терми[0].get("slug"), слово=слово, за_замовч=bool(терми[0].get("default")), кадри=галерея,
                     кадри_джерело="woo:images" if галерея else None, розміри=усі, розміри_в_наявності=є, є=ввімк,
                     розміри_джерело=дж, ід_варіацій=[в["ід"] for в in вар], кольорів_у_товарі=len(терми))]
    за_кольором = {x["slug"]: [в for в in вар if (запит(в).get(ключ_к) or [""])[0] == x["slug"]] for x in терми}
    зображення = {с: list(dict.fromkeys(к for в in вв for к in в["кадри"])) for с, вв in за_кольором.items()}
    лічба = collections.Counter(к for кк in зображення.values() for к in кк)
    вих = []
    for x in терми:
        вв = за_кольором[x["slug"]]
        if not вв:
            continue                                    # терм є, а варіації цього кольору немає — продати його не можна
        власні = [к for к in зображення[x["slug"]] if лічба[к] == 1]
        усі, є = розміри_з(вв)
        вих.append(dict(слаг=x["slug"], слово=x["name"], за_замовч=bool(x.get("default")), кадри=власні,
                        кадри_джерело="woo:variations" if власні else None, розміри=усі, розміри_в_наявності=є,
                        є=any(в["є"] for в in вв), розміри_джерело="woo:variations", ід_варіацій=[в["ід"] for в in вв],
                        кольорів_у_товарі=len(терми)))
    return вих or None


def факти_woo(т, база, рецепт=None):
    """Store API → факти. Ціни в дрібних одиницях (currency_minor_unit). З рецептом крамниці (`woo_рецепт`) —
    факт на варіант кольору (`варіанти_woo`), інакше один на товар."""
    ц = т.get("prices") or {}
    мінор = ц.get("currency_minor_unit")
    div = 10 ** (2 if мінор is None or мінор == "" else int(мінор))     # 0 — це «без копійок» (attico, morandi), а не «не вказано»
    сира_ціна = _ціна_число(ц.get("price"))
    if div > 1 and сира_ціна and сира_ціна / div < ЦІНА_МІН <= сира_ціна:
        div = 1                       # магазин оголосив minor_unit=2, а поклав гривні (feelyou 06.09: 899 → 8.99)
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
    загальне = dict(назва=розекранувати(т.get("name") or ""), назва_джерело="woo",
                    опис=текст_з_html(т.get("description") or т.get("short_description"))[:8000] or None,
                    ціна=гр(ц.get("price")), ціна_стара=(гр(ц.get("regular_price")) if ц.get("sale_price") and ц.get("regular_price") != ц.get("price") else None),
                    валюта=ц.get("currency_code"), id_магазину=str(т.get("id") or ""),
                    свотчі=[], таблиця_мірок=None, крихти=[c.get("name") for c in (т.get("categories") or []) if c.get("name")],
                    бренд=None, колір_ld=None, мова_альт=None, варіанти=[], url=канонічна(т.get("permalink") or "", база))
    варіанти = варіанти_woo(т, база, рецепт)
    if варіанти is not None:
        # Артикул товару Woo — його власний (в sunwin він несе слово кольору головної варіації), тож у `артикул`
        # не йде: модель називає id товару, артикул лишається характеристикою магазину.
        сирі_без_кольору = [x for x in сирі if x[0] and x[1] and x[0] != (атр_назва(т, рецепт["колір"]) or "")]
        return [dict(загальне, available=в["є"], наявність="є" if в["є"] else "нема",
                     характеристики_сирі=сирі_без_кольору + ([["Артикул (магазин)", т["sku"]]] if т.get("sku") else []),
                     фото=в["кадри"], фото_джерело=в["кадри_джерело"] or "woo:невідомо",
                     характеристики=dict({k: v for k, v in хар.items() if k != "колір"}, колір=в["слово"]),
                     розміри=в["розміри"], розміри_в_наявності=в["розміри_в_наявності"],
                     розміри_джерело=в["розміри_джерело"],
                     артикул=None, group_id=str(т.get("id") or ""))
                for в in варіанти]
    return [dict(загальне, available=(стан != "нема"), наявність=стан,
                 характеристики_сирі=[x for x in сирі if x[0] and x[1]],
                 фото=[оригінал_фото(канонічна(i.get("src"), база)) for i in (т.get("images") or []) if i.get("src")], фото_джерело="woo:images",
                 характеристики=хар, розміри=[str(x).upper() for x in розміри if x],
                 розміри_в_наявності=([str(x).upper() for x in розміри if x] if т.get("is_in_stock") else []),
                 розміри_джерело="woo:attributes" if розміри else None,
                 артикул=(т.get("sku") or None), group_id=str(т.get("parent") or т.get("id") or ""))]


def атр_назва(т, таксономія):
    """Напис атрибута (його `name`) за кодом таксономії — щоб не класти колір двічі в сирі характеристики."""
    return next((a.get("name") for a in т.get("attributes") or [] if a.get("taxonomy") == таксономія), None)


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
    """→ слот, який єдиний читач виду бачить у тексті (назва, крихта), або None."""
    return _вид_речі({"назва": текст or "", "категорія": ""})[1]


def слот_речі(крихти, назва, url):
    """→ (слот, джерело) або (None, причина). Крихти → назва → слаг (П3)."""
    низ = (назва or "").lower()
    if any(x in низ for x in НЕ_ОДЯГ) or any(x in низ for x in ПОЗА_СЛОТАМИ):
        return None, "поза слотами (не одяг образу)"
    # КОМПЛЕКТ (рішення власника 01.09: не чіпати, бо дві речі в одному SKU): читач виду дає слот «комплект».
    зн = _слот_у_тексті(назва)
    if зн == "комплект":
        return зн, "назва: набір (дві речі в одному SKU)"
    # НАЗВА вирішує родину, коли її іменник однозначний — це те, що людина бачить (П3: «Сумка Maybelle» у «верх»).
    for кр in reversed(крихти or []):          # найглибша крихта — найточніша
        зк = _слот_у_тексті(кр)
        if зк == "комплект":
            continue          # «комплект» — лише слова назви (вище): крихта «костюми» не робить кофту набором
        if зк:
            if зн and зн != зк and _слот_у_тексті(назва.split()[0] if назва else "") == зн:
                return зн, "назва (перше слово) переважила крихту «%s»" % кр
            return зк, "крихта «%s»" % кр
    if зн:
        return зн, "назва"
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
# ── ЗНАННЯ, ПЕРЕНЕСЕНЕ З ЖНИВАРКИ v2 (кожне правило там має вимір; не виводити наново) ──────────
# Назва з самих категорійних слів — це розділ, не річ (v2 «назва_розділу»; 06.09 у нас пройшли
# cher17 «Одяг», vittorossi «Жіноче взуття», gepur «Сукні»).
РОЗДІЛ_СЛОВА = frozenset("""жіночі жіноча жіночий жіноче жіночого женские женская чоловічі чоловіча
чоловічий чоловіче мужские мужская дитячі дитяча дитячий унісекс новинки новинка новий нові акції акція
знижки знижка розпродаж sale new всі все усі каталог категорії категорія колекція колекции collection
одяг одежда взуття обувь аксесуари аксессуары товари товар продукція асортимент магазин shop store
модель моделі бренд бренди""".split())
# Рядок інтерфейсу замість назви (v2 «ІНТЕРФЕЙС»)
_ІНТЕРФЕЙС = re.compile(r"(товар (додано|видалено)|додано в обран|у обран|смотреть (все|всё)|"
                        r"дивит[ьи]с[яь] ус|переглянути (все|всі)|показати ще|завантажити ще|показать ещ|"
                        r"^перейти|^детальніше|^дізнатись|у кошик|в корзину|швидкий перегляд|"
                        r"быстрый просмотр|порівняти|сравнить|список бажань|wish ?list|add to cart|"
                        r"^дивитись$|^більше$|^читати далі$)", re.I)
# Відгук покупця (v2 «ВІДГУК»)
_ВІДГУК = re.compile(r"(^відгук на|^отзыв на|дякую за|спасибо за|^рекомендую|замовляла|заказывала|"
                     r"прийшло швидко|все як завжди супер|якість (пошиття|тканини))", re.I)
# Рекламний бейдж (v2 «БЕЙДЖ») і промо-банер (v2 «ПРОМО») замість назви
_БЕЙДЖ = re.compile(r"^\s*(-?\s?\d{1,2}\s?%|ss.?\d{4}|fw.?\d{4}|новинк|hit\b|new\b|sale\b|bestseller|"
                    r"топ продаж|\d{1,2}\s?%\s?знижк)", re.I)
_ПРОМО = re.compile(r"(final sale|black friday|чорна п'ятниц|безкоштовна доставка|бесплатная доставка|"
                    r"подарунковий сертифікат|подарочный сертификат|додаткові знижки|при покупці на суму)", re.I)


def назва_розділу(назва):
    """True, якщо назва складається лише з категорійних слів (v2: власний токен = це товар)."""
    слова = [w for w in re.split(r"[\s,·|/]+", str(назва or "").lower()) if w]
    if not слова or len(слова) > 4:
        return False
    for w in слова:
        w = w.strip("«»\"'()")
        if re.search(r"\d", w) and re.search(r"[a-zа-яіїєґ]", w, re.I):
            return False                  # «Шарф-41303P» — номер моделі, отже товар (06.09, andretan)
        if w in РОЗДІЛ_СЛОВА:
            continue
        if _слот_у_тексті(w) and len(w) <= 12:   # «сукні», «взуття» — категорійне слово цілком
            continue
        return False                      # власне ім'я / модель → це товар
    return True


def відірвати_ціну(назва):
    """→ (назва без ціни й хвостів, ціна або None).
    v2, вимір 26.08: правило «зрізати будь-які 3–10 цифр у кінці» вбивало речі —
    «Сукня 1077» → «Сукня» → далі гине як назва розділу; номер моделі в назві для українських
    магазинів звичайний (stolyarchuk так названо весь каталог). Тому хвостове число зрізається,
    лише якщо після нього лишається СПРАВЖНЯ назва: ≥3 слова і не назва розділу."""
    сира = розекранувати(назва or "")
    ціни = []
    for м in re.finditer(r"(\d[\d\s\u00a0\u202f]{2,9})\s*(?:UAH|грн|₴)", сира, re.I):
        v = int(re.sub(r"\D", "", м.group(1)) or 0)
        if v > 0:
            ціни.append(v)
    н = чиста_назва(сира)
    н = re.sub(r"\s*\d{1,2}\s?%\s*", " ", н)
    без_хвоста = re.sub(r"\s*\d[\d\s\u00a0\u202f]{2,9}\s*$", " ", н)
    без_хвоста = re.sub(r"\s{2,}", " ", без_хвоста).strip(" ·|,;:-–—")
    if без_хвоста != н.strip() and len(без_хвоста.split()) >= 3 and not назва_розділу(без_хвоста):
        н = без_хвоста
    н = re.sub(r"\s{2,}", " ", н).strip(" ·|,;:-–—")
    return н, (min(ціни) if ціни else None)


_СМІТТЯ_НАЗВИ = re.compile(r"!\[|\]\(|https?://|<[a-z/]|\bImage\s*\d|^\s*(картинка|зображення|фото)\s|"
                          r"додати (в|до) кошик|у кошик|інтернет-магазин|в наявності|детальніше|переглянути|"
                          r"^\s*(sale|new|акція|знижк)\s*$", re.I)
_ГОЛОВА_НАЗВИ = re.compile(r"^\s*(купити|купить|buy|замовити)\s+", re.I)
# Зрізаємо лише те, що ТОЧНО не частина назви: ціну з валютою, «N фото», знижку, SS'24, sale/new.
# Голе число чи «-0008329» НЕ чіпаємо — це номер моделі (v2-урок; ager 06.09: «AG-0008329» → «AG»).
_ХВІСТ_НАЗВИ = re.compile(r"[\s\-–|·]+(\d[\d\s]*(?:[.,]\d+)?\s*(?:грн|₴|uah)\.?|фото\s*\d*|"
                          r"\|\s*[^|]{0,40}\bфото\b|SS'?\d{2,4}|-\d{1,2}\s*%|\bnew\b|\bsale\b)\s*$", re.I)
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
    elif len(н) > 140:
        причини.append("назва довша за 140 — це абзац, не товар")          # v2
    elif _ІНТЕРФЕЙС.search(н):
        причини.append("рядок інтерфейсу замість назви")                    # v2
    elif _ВІДГУК.search(н):
        причини.append("відгук покупця замість назви")                      # v2
    elif _БЕЙДЖ.search(н):
        причини.append("рекламний бейдж замість назви")                     # v2
    elif _ПРОМО.search(н):
        причини.append("промо-банер замість назви")                         # v2
    elif назва_розділу(н):
        причини.append("назва розділу, не товару")                          # v2
    рос = російське(н)
    if рос:
        причини.append("назва російською (%s)" % ", ".join(рос[:3]))
    ц = з.get("ціна")
    if ц is None:
        pass          # ціну система не використовує (рішення власника); гейт коштував 194 придатні
                      # речі з фото і складом у прогоні 06.09 — тепер це лише мітка «ціни нема»
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


_АСКІ_ДРУК = "".join(chr(c) for c in range(33, 127))


def кадр_закодований(url):
    """Адреса кадру без пробілів і не-ASCII (`…/winter 2025-26 maneken/….webp` не відкривається): `%XX`, наявні лишаються."""
    return quote(url, safe=_АСКІ_ДРУК)


def чисті_фото(фото, url="", артикул=None, відкинуті=None):
    вих = []
    for ф in фото or []:
        if not ф or _НЕ_ФОТО.search(ф) or not ф.startswith("http"):
            if відкинуті is not None and ф and len(відкинуті) < 3:
                відкинуті.append(ф)
            continue
        ф = кадр_закодований(оригінал_фото(ф))     # документ 2: оригінал, не мініатюра
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
    # склад — лише з підписаного поля (пара характеристик, JSON-LD material, атрибут, селектор рецепта); з вільного тексту
    # опису не береться: сусідні речення дають «100% котон Колір: сіра *Будь ласка»; сума ≠ 100 — `склад_непевний`
    склад_джерело = ф.get("склад_джерело") or ("характеристика" if хар.get("склад") else None)
    будова = склад_із(хар.get("склад"))
    склад = склад_рядком(будова) if будова else (хар.get("склад") if хар.get("склад") and len(хар["склад"]) < 80 else None)
    склад_непевний = ", ".join(будова["непевний"] if будова else (["нема_відсотків"] if склад else [])) or None
    склад_основа = склад_основа_із(будова)
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
    назва, ціна_з_назви = відірвати_ціну(назва)
    if ф.get("ціна") is None and ціна_з_назви and ЦІНА_МІН <= ціна_з_назви <= ЦІНА_МАКС:
        ф = dict(ф, ціна=float(ціна_з_назви), валюта=(ф.get("валюта") or "UAH"))
    наявн = ф.get("наявність") or (None if ф.get("available") is None else ("є" if ф.get("available") else "нема")) or "невідомо"
    нема = [x for x, v in (("колір", колір), ("склад", склад), ("розміри", розміри), ("опис", опис or опис_рос),
                          ("заміри", хар.get("заміри") or ф.get("таблиця_мірок")), ("свотч", свотч),
                          ("характеристики", ф.get("характеристики_сирі")), ("крихти", крихти)) if not v]
    відкинуті_фото = []
    фото = чисті_фото(ф.get("фото"), url, ф.get("артикул"), відкинуті_фото)
    # джерело кожного поля картки; поле з bulk-каналу без власної позначки — «канал <канал>», а не безіменне
    джерела = {"назва": ф.get("назва_джерело") or (канал if назва else None), "опис": ф.get("опис_джерело") or (канал if опис else None),
               "ціна": ф.get("ціна_джерело") or (канал if ф.get("ціна") is not None else None),
               "фото": ф.get("фото_джерело") or (канал if фото else None), "склад": склад_джерело if склад else None,
               "розміри": ф.get("розміри_джерело") or ("варіанти" if ф.get("варіанти") else None), "колір": кол_дж,
               "стать": ст_дж, "слот": сл_дж}
    return dict(
        джерела_полів=джерела,
        сирий=ф.get("сирий"), чужих_блоків=ф.get("чужих_блоків"), межа_блоку=ф.get("межа_блоку"),
        url=url, назва=назва, назва_сира=(сира if сира != назва else None), назва_джерело=ф.get("назва_джерело"),
        фото_відкинуто=("; ".join(відкинуті_фото) if відкинуті_фото and not фото else None),
        ціна_діагностика=(ф.get("ціна_діагностика") if ф.get("ціна") is None else None),
        ціни_нема=("так" if ф.get("ціна") is None else None),
        опис=опис, опис_рос=опис_рос, мова_опису=мова_опису, наявність=наявн,
        характеристики_сирі=ф.get("характеристики_сирі") or [], свотч_hex=(свотч or {}).get("hex"),
        свотч_фото=(свотч or {}).get("фото"), свотч_джерело=("картка" if свотч else None),
        свотчі_всі=[[x.get("назва"), x.get("hex")] for x in свотчі if x.get("hex")][:20],
        таблиця_мірок=ф.get("таблиця_мірок"), нема_від_магазину=nema_str(нема),
        ціна=ф.get("ціна"), ціна_стара=ф.get("ціна_стара"), валюта=ф.get("валюта"), available=ф.get("available"),
        фото=фото, фото_джерело=ф.get("фото_джерело"), фото_перевірено=None,
        категорія=" / ".join(крихти[:5]), слот=слот, слот_джерело=сл_дж, стать=стать, стать_джерело=ст_дж,
        колір=колір, кольори_акценти=акценти, колір_джерело=кол_дж, склад=склад,
        склад_джерело=(склад_джерело if склад else None), склад_непевний=склад_непевний, склад_основа=склад_основа,
        склад_структура=будова,
        розміри=list(dict.fromkeys(розміри))[:20], розміри_в_наявності=list(dict.fromkeys(в_наявн))[:20],
        розміри_джерело=ф.get("розміри_джерело") or ("варіанти" if ф.get("варіанти") else None),
        заміри=(хар.get("заміри") or None), параметри_моделі=(хар.get("параметри_моделі") or None),
        бренд=ф.get("бренд") or хар.get("бренд"), артикул=ф.get("артикул"),
        id_магазину=ф.get("id_магазину") or (re.search(r"(\d{3,})/?$", url or "") or [None, None])[1],
        характеристики={k: v for k, v in хар.items() if k in ("сезон", "довжина", "рукав", "принт", "крій", "країна",
                                                              "каблук", "метал", "наповнювач", "підкладка", "тканина", "догляд")},
        group_id=ф.get("group_id"), канал=канал, платформа=маг.get("платформа"), магазин=маг["домен"],
        знято=СЬОГОДНІ, мова="укр")


# останній сегмент картки: дві+ частини через дефіс/підкреслення, або цифра, або одна довга пара слів
_СХОЖА_НА_КАРТКУ = re.compile(r"([-_].*[-_]|\d|^[a-zа-яіїєґ]{4,}[-_][a-zа-яіїєґ]{4,}$)", re.I)


def схожість_на_картку(url):
    """0 — найімовірніше картка, 2 — найімовірніше розділ. gepur: /uk/catalog/platya (розділ) проти
    /uk/catalog/platya/plate-midi-bezhevoe (картка). Порядок вибірки, не гейт (гейт — є_товар)."""
    шлях = urlparse(url or "").path
    сегменти = [x for x in шлях.split("/") if x]
    if not сегменти or _СЛУЖБОВЕ.search(url or "") or _НЕ_КАРТКА.search(шлях) or _ФАСЕТНА_АДРЕСА.search(шлях):
        return 3
    останній = сегменти[-1]
    if _ЯВНО_КАРТКА.search(url or ""):
        return 0
    if len(сегменти) >= 3 and _СХОЖА_НА_КАРТКУ.search(останній) and len(останній) > 8:
        return 0
    if _СХОЖА_НА_КАРТКУ.search(останній) and len(останній) > 12:
        return 1
    return 2


def розподілити(кандидати, стеля, лічба=None):
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
    for г in групи.values():          # проба 05.09: перші адреси мапи = розділи; беремо рівномірно, схожі на картку першими
        random.Random(0).shuffle(г)
    # групи теж упорядковуємо: інакше перші 3 адреси мапи (головна, /about, /oplata) з'їдають усю пробу
    лічба = лічба if лічба is not None else collections.Counter()

    def наявна(к):
        ф_ = (к.get("факти") or [{}])[0]
        return 0 if ф_.get("available") is not False else 1     # канал уже знає наявність — беремо живі

    for г in групи.values():
        г.sort(key=lambda к: (наявна(к), схожість_на_картку(к.get("url") or "")))

    def ключ_групи(г):
        схожість = min(схожість_на_картку(к.get("url") or "") for к in г)
        слот_ = next((слот_речі([], "", к.get("url") or "")[0] for к in г
                      if слот_речі([], "", к.get("url") or "")[0]), None)
        # спершу схожі на картку; серед них — слоти, яких у прогоні найменше (широта > кількість)
        return (схожість, лічба.get(слот_, 0) if слот_ else 10 ** 6, -len(г))
    впорядковані = sorted(групи.values(), key=ключ_групи)
    # Якщо є групи, схожі на картки, — групи-розділи взагалі не беруть квоти (кругова вибірка інакше
    # витрачає кожен другий запит на розділ; вимір 06.09: мапа має і категорії, і 13 021 картку).
    карткові = [г for г in впорядковані if min(схожість_на_картку(к.get("url") or "") for к in г) <= 1]
    if карткові:
        впорядковані = карткові
    вих, i = [], 0
    while len(вих) < стеля:
        взято = False
        for г in впорядковані:
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
            картка = факти_з_картки(кр["тіло"], url, рецепт_селекторів(маг["домен"])); картка["url"] = url
            if not факти_bulk and not картка.get("є_товар"):
                діаг["не_картки"] = діаг.get("не_картки", 0) + 1
                діаг.setdefault("не_картки_приклади", [])
                if len(діаг["не_картки_приклади"]) < 3:
                    діаг["не_картки_приклади"].append(url)
                # запит уже оплачено: якщо це список товарів — беремо з нього посилання на речі
                # (06.09: vilni.store 649 «не карток» із 670 запитів просто викинуто)
                нові_ = [u for u in посилання_карток_зі_сторінки(кр["тіло"], маг["база"])
                         if схожість_на_картку(u) <= 1]
                if нові_:
                    діаг.setdefault("додаткові", []).extend(нові_[:60])
                    діаг["з_розділів"] = діаг.get("з_розділів", 0) + len(нові_[:60])
                return    # сама сторінка — не в карантин
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
                        к2 = факти_з_картки(кр2["тіло"], альт, рецепт_селекторів(маг["домен"]))
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
            ф.setdefault("сирий", картка.get("сирий")); ф.setdefault("чужих_блоків", картка.get("чужих_блоків"))
            if not ф.get("фото"):
                ф["фото"] = картка.get("фото"); ф["фото_джерело"] = картка.get("фото_джерело")
            if ф.get("ціна") is None:
                ф["ціна"] = картка.get("ціна"); ф["валюта"] = ф.get("валюта") or картка.get("валюта")
            if ф.get("available") is None:
                ф["available"] = картка.get("available")
            ф["url"] = ф.get("url") or url
        ф["url"] = ф.get("url") or url
        фас = (діаг.get("мітки_фасетів") or {}).get(ф["url"]) or {}
        if фас:      # мітки, ОГОЛОШЕНІ магазином. Картка сильніша; колір ставимо після, щоб джерело не збрехало
            ф["характеристики"] = dict({k: v for k, v in фас.items() if k != "колір"}, **(ф.get("характеристики") or {}))
            ф["фасети"] = ", ".join("%s: %s" % kv for kv in фас.items())
        з = канонічний_запис(ф, маг, к.get("канал") or "картка")
        if фас.get("колір") and з.get("колір_джерело") in (None, "не названо", "слаг url", "слово в назві"):
            з["колір"], з["колір_джерело"] = фас["колір"].lower(), "фасет магазину"
        if російське(з["назва"]):
            лічильник_рос[0] += 1
        ключ_дизайну = ((з.get("group_id") or з["url"]), з.get("колір"), (з.get("назва") or "").lower()[:40])
        if з["url"] in бачено_url or ключ_дизайну in бачено_дизайн:
            діаг["відхилено"]["дубль (url або дизайн+колір)"] += 1; continue
        бачено_url.add(з["url"]); бачено_дизайн.add(ключ_дизайну)
        причини = гейти_речі(з)
        діаг["лічильник_речей"] = діаг.get("лічильник_речей", 0) + 1
        крок = діаг.get("фото_кожен", 1)
        хост_ = urlparse((з.get("фото") or [""])[0]).netloc
        перевірок_хоста = діаг.setdefault("фото_хости", collections.Counter())
        # 06.09: перевірка фото — окремі HTTP-запити поза лічильником «запитів»; на sunwin це були
        # сотні HEAD. Один CDN поводиться однаково, тому перевіряємо перші 20 картинок на хост.
        треба_ = перевірок_хоста[хост_] < 20
        if not причини and перевіряти_фото and треба_ and (крок <= 1 or діаг["лічильник_речей"] % крок == 1):
            перевірок_хоста[хост_] += 1
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
            if з.get("слот"):
                діаг["лічба"][з["слот"]] += 1


def зібрати_магазин(маг, транспорт, стеля, лог, перевіряти_фото=True, стеля_розділів=12, дедлайн=None,
                    фото_кожен=1, фасетів=3, лічба=None, хвилин_на_магазин=20, картки_потоків=3):
    домен, база = маг["домен"], маг["база"].rstrip("/")
    лічба = лічба if лічба is not None else collections.Counter()   # слот → скільки вже зібрано в прогоні
    глобальний = транспорт.дедлайн or (time.time() + 10 ** 6)
    кінець_магазину = min(time.time() + (хвилин_на_магазин * 60), глобальний)
    # 06.09, повний прогін: у 44 магазинів розвідка (мапа+фасети+розділи) з'їла всі 20 хв, і до карток
    # черга не дійшла — gepur зробив 15 запитів за 20 хв. Розвідці — не більше 30 % бюджету.
    кінець_розвідки = min(time.time() + (хвилин_на_магазин * 60 * 0.30), глобальний)
    # Продуктивний магазин може продовжувати себе, але не безмежно: 3× бюджету і не більше 60 хв —
    # інакше один магазин розтягує весь прогін (вікно власника ≈1,5 год на всі 56).
    тверда_межа = min(time.time() + min(хвилин_на_магазин * 60 * 3, 3600), глобальний)
    позначка = (time.time(), 0)                                     # (коли, скільки речей було)        # 06.09: gepur 3 396 с на 3 картки
    ua = маг.get("ua") or ""
    діаг = dict(лічба=лічба, домен=домен, база=база, платформа="невідомо", канали=[], запитів=0, знайдено=0,
                прийнято=0, відхилено=collections.Counter(), стан="", фіди=[], мапа=None, час=time.time(), фото_кожен=фото_кожен,
                версія=ВЕРСІЯ)
    лог("▶ %s" % домен)
    r = транспорт.get(urljoin(база, "/robots.txt"))
    robots = розібрати_robots(r["тіло"] if r["код"] == 200 else "")
    транспорт.robots[urlparse(база).netloc] = robots
    г = транспорт.get(база + ua if ua else база)
    def _вихід(стан, причина_код="UNKNOWN", доступ_код="UNKNOWN"):
        діаг.update(причина_код=причина_код, доступ_код=доступ_код)
        діаг["стан"] = стан; діаг["час"] = round(time.time() - діаг["час"])
        діаг["запитів"] = sum(транспорт.статистика[urlparse(база).netloc].values())
        діаг["коди"] = dict(транспорт.статистика[urlparse(база).netloc])
        лог("  ✗ %s: %s" % (домен, стан)); return [], [], діаг
    if г["заслон"] or (г["код"] == 403 and not г["тіло"]):
        причина = "ЗАБЛОКОВАНО ботозаслоном (HTTP %s)" % г["код"]
        if _curl is None:
            причина += " — curl_cffi не встановлено (відбиток Chrome не пробувався)"
        else:
            причина += " — не пустив навіть з відбитком Chrome; потрібен домашній IP (не дата-центр)"
        return _вихід(причина, "BOT_CHALLENGE" if г["заслон"] else "HTTP",
                      "UNKNOWN" if г["заслон"] else "UNAVAILABLE")
    if г["код"] == 0:
        return _вихід("головна не відкрилась: %s" % г["помилка"], г.get("причина_код", "UNKNOWN"))
    if г["код"] >= 400:
        return _вихід("головна HTTP %s" % г["код"], "HTTP", "UNAVAILABLE")
    головна = г["тіло"] or ""
    кінцевий = urlparse(г["url"] or "")
    if кінцевий.netloc and домен_із(г["url"]) != домен_із(база):
        база = "%s://%s" % (кінцевий.scheme or "https", кінцевий.netloc)
        діаг["перенаправлено"] = база; лог("  → перенаправлено на %s, працюю з ним" % база)
        транспорт.robots[кінцевий.netloc] = robots
    діаг["платформа"] = маг["платформа"] = відбиток_платформи(головна)
    діаг["фіди"] = адреси_фідів_у_html(головна, база)
    діаг["ua_префікс"] = виявити_ua_префікс(головна, база, маг.get("ua"))
    if діаг["ua_префікс"]:
        лог("  українська версія: %s" % діаг["ua_префікс"])
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
        рецепт = woo_рецепт(маг["домен"])
        к = woo_store_api(транспорт, база, лог, стеля, рецепт=рецепт)
        return [dict(c, факти=факти_woo(c["сирий"], база, рецепт)) for c in к], "woo"
    def _yml(адреси):
        for u in адреси:
            пр = транспорт.get(u, тип="bytes", ліміт=300_000)
            if пр["код"] == 200 and пр["тіло"] and b"<offer" in пр["тіло"]:
                к = yml_фід(транспорт, u, лог, стеля)
                if к:
                    return [dict(c, факти=факти_yml(c["сирий"], база)) for c in к], "yml"
        return [], "yml"
    відомий = (маг.get("канал") or "").strip().lower()
    ранні = []
    if відомий in ("woo", "shopify", "yml"):
        # 06.09: розвідка з'їдала бюджет магазину. Для магазинів із ВІДОМИМ каналом (шість прогонів
        # показали, який працює) вона зайва — беремо канал одразу.
        ранні = [{"woo": _woo, "shopify": _shopify,
                  "yml": (lambda: _yml(діаг["фіди"] + [urljoin(база, x) for x in _ШЛЯХИ_YML][:8]))}[відомий]]
        діаг["стратегія"] = "відомий канал: " + відомий
    else:
        if "Shopify" in відб:
            ранні.append(_shopify)
        if "Woo" in відб or "WordPress" in відб:
            ранні.append(_woo)
        if діаг["фіди"]:
            ранні.append(lambda: _yml(діаг["фіди"][:4]))
    for крок in ранні:
        if not кандидати and time.time() < кінець_розвідки:
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
    if not кандидати and відомий == "списки":
        # магазин, який у прогонах давав речі лише через сторінки-списки: мапу не читаємо взагалі
        діаг["стратегія"] = "відомий канал списки"
        зі_сп = []
        for рз in розділи_зі_сторінки(головна, база)[:стеля_розділів]:
            if time.time() > кінець_розвідки:
                break
            с = транспорт.get(рз)
            if с["код"] == 200 and с["тіло"]:
                зі_сп += [u for u in посилання_карток_зі_сторінки(с["тіло"], база) if схожість_на_картку(u) <= 1]
            if len(зі_сп) >= стеля * 2:
                break
        зі_сп = list(dict.fromkeys(зі_сп))
        if зі_сп:
            кандидати = [dict(канал="список", url=u, факти=None) for u in зі_сп]
            діаг["канали"].append("списки"); діаг["зі_списків"] = len(зі_сп)
            лог("  списки з головної: %d посилань на речі" % len(зі_сп))
    # ── карта сайту → картки (П11); сліпі проби — якщо мапа порожня; розділи — останні ─────────
    if not кандидати:
        url_карток, діаг["мапа"] = мапа_сайту(транспорт, база, robots, лог,
                                              секунд=max(20, int(кінець_розвідки - time.time())))
        if not url_карток:
            for крок in (_shopify, _woo, lambda: _yml([urljoin(база, p) for p in _ШЛЯХИ_YML][:8])):
                if time.time() > кінець_розвідки:
                    break
                кандидати, ім = крок()
                if кандидати:
                    діаг["канали"].append(ім); break
        if url_карток:
            діаг["канали"].append("мапа сайту")
        elif not кандидати:
            розділи = розділи_зі_сторінки(головна, база)[:стеля_розділів]
            лог("  розділів на головній: %d" % len(розділи))
            кінець_розділів = min(кінець_розвідки, time.time() + 180)
            for рз in розділи:
                if time.time() > кінець_розділів:
                    break
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
            # БЕЗ зрізання: стелю накладає розподілити(), інакше з 13 021 картки miraton у вибірку
            # потрапляли перші 3 адреси мапи — а це розділи (вимір 06.09: 23 магазини дали нуль).
            кандидати = [dict(канал="картка", url=u, факти=None) for u in url_карток]
    # ФАСЕТИ: мітки, оголошені магазином (v2). Кілька фасетних сторінок → яка річ під якою міткою.
    мітки = {}
    if фасетів and time.time() < кінець_розвідки:
        знайдені = фасети_сторінки(головна, база)
        if not знайдені:
            for рз in розділи_зі_сторінки(головна, база)[:2]:
                с = транспорт.get(рз)
                if с["код"] == 200 and с["тіло"]:
                    знайдені += фасети_сторінки(с["тіло"], база)
        по_полях = collections.Counter()
        кінець_фасетів = time.time() + (60 if фасетів <= 1 else 180)
        # v2, вимір: усі чотири фасетні запити пішли в один розділ («сукні»), бо бралися в порядку
        # знаходження. Черга — за слотом, якого в прогоні найменше: це і є широта покриття.
        знайдені.sort(key=lambda ф_: (лічба[слот_речі([], "", ф_[0])[0] or "?"], ф_[1] != "колір"))
        for u, поле, значення in знайдені:
            if по_полях[поле] >= фасетів or time.time() > кінець_фасетів:
                continue
            по_полях[поле] += 1
            с = транспорт.get(u)
            if с["код"] != 200 or not с["тіло"]:
                continue
            for посилання in посилання_карток_зі_сторінки(с["тіло"], база)[:60]:
                мітки.setdefault(посилання, {}).setdefault(поле, значення)
        if знайдені:
            діаг["фасети"] = "%d сторінок → мітки для %d речей %s" % (sum(по_полях.values()), len(мітки), dict(по_полях))
            лог("  фасети: %s" % діаг["фасети"])
    діаг["мітки_фасетів"] = мітки
    # UA-версія для всього магазину: переписати адреси й прибрати дублі «той самий шлях з /uk/ і без»
    преф = діаг.get("ua_префікс")
    if преф and кандидати:
        зразок = next((к for к in кандидати if к.get("url") and not re.match(r"^/(ua|uk)", urlparse(к["url"]).path, re.I)), None)
        if зразок is None:
            діаг["ua_переписано"] = "не треба (усі вже з префіксом)"
        else:
            зразки = [к for к in кандидати if к.get("url") and not re.match(r"^/(ua|uk)", urlparse(к["url"]).path, re.I)]
            зразки.sort(key=lambda к: схожість_на_картку(к["url"]))
            працює, коди = False, []
            for зр in зразки[:3]:                      # cultboutique 06.09: перший зразок був не карткою
                новий = з_префіксом(зр["url"], преф)
                проба_ = транспорт.get(новий); коди.append(проба_["код"])
                if проба_["код"] == 200 and проба_["тіло"] and факти_з_картки(проба_["тіло"], новий).get("є_товар"):
                    працює = True; break
            проба_ = dict(код="/".join(str(c) for c in коди))
            if працює:
                було = len(кандидати)
                бачені_шляхи = set()
                нові = []
                for к in кандидати:
                    if к.get("url"):
                        к = dict(к, url=з_префіксом(к["url"], преф))
                        if к["url"] in бачені_шляхи:
                            continue
                        бачені_шляхи.add(к["url"])
                    нові.append(к)
                кандидати = нові
                діаг["ua_переписано"] = "%d адрес → %s, дублів прибрано %d" % (len(кандидати), преф, було - len(кандидати))
                лог("  → %s" % діаг["ua_переписано"])
            else:
                діаг["ua_переписано"] = "префікс %s не працює (HTTP %s) — лишаю як є" % (преф, проба_["код"])
                лог("  ! %s" % діаг["ua_переписано"])
    # ── СПИСКИ ПЕРЕД МАПОЮ (вимір 06.09) ─────────────────────────────────────────────────────
    # Сторінка-список дає 20–60 ПЕРЕВІРЕНИХ посилань на речі за один запит; мапа дає тисячі адрес
    # невідомого типу. У прогоні 06.09 добір зі списків зібрав 642 посилання на miraton, 599 на virna,
    # 513 на bella-bicchi — і жодного разу не був використаний, бо вмикався після вичерпання черги.
    # Тепер списки формують основний пул ДО того, як витрачати запити на адреси з мапи.
    if кандидати and not any(к.get("факти") for к in кандидати) and time.time() < кінець_розвідки:
        схожі_на_розділ = [к["url"] for к in кандидати if к.get("url") and схожість_на_картку(к["url"]) >= 2]
        зі_списків = []
        for рз in (схожі_на_розділ + розділи_зі_сторінки(головна, база))[:12]:
            if time.time() > кінець_розвідки:
                break
            с = транспорт.get(рз)
            if с["код"] == 200 and с["тіло"]:
                зі_списків += [u for u in посилання_карток_зі_сторінки(с["тіло"], база) if схожість_на_картку(u) <= 1]
            if len(зі_списків) >= стеля * 2:
                break
        зі_списків = list(dict.fromkeys(зі_списків))
        було_ = {к.get("url") for к in кандидати}
        нові_к = [dict(канал="список", url=u, факти=None) for u in зі_списків if u not in було_]
        if нові_к:                       # канал додається, лише коли справді щось дав
            кандидати = нові_к + [к for к in кандидати if схожість_на_картку(к.get("url") or "") <= 1]
            діаг["канали"].append("списки"); діаг["зі_списків"] = len(нові_к)
            лог("  списки: %d нових посилань на речі" % len(нові_к))
    # Канал дав адреси, але серед них нема жодної схожої на картку → це перелік розділів.
    # Тоді мапа працює як список категорій: беремо з них посилання на речі (замість здаватися).
    if кандидати and all(схожість_на_картку(к.get("url") or "") >= 2 for к in кандидати if к.get("url")):
        розділи_з_мапи = [к["url"] for к in кандидати if к.get("url")][:стеля_розділів]
        зібрані = []
        for рз in розділи_з_мапи:
            с = транспорт.get(рз)
            if с["код"] == 200 and с["тіло"]:
                зібрані += [u for u in посилання_карток_зі_сторінки(с["тіло"], база)
                            if схожість_на_картку(u) <= 1]
            if len(зібрані) >= стеля * 4:
                break
        if зібрані:
            діаг["канали"].append("розділи з мапи")
            лог("  мапа дала лише розділи → з них узято %d посилань на речі" % len(зібрані))
            кандидати = [dict(канал="картка", url=u, факти=None) for u in dict.fromkeys(зібрані)]
    # 06.09: wearme віддав available=false на 2 459 із 2 501 речей, хоча магазин ними торгує.
    # Перш ніж викидати тисячі — перевіряємо кілька карток; якщо канал бреше, наявність стає «невідомо».
    усі_ф = [ф for к in кандидати for ф in (к.get("факти") or [])]
    нема_ = [ф for ф in усі_ф if ф.get("available") is False]
    if len(усі_ф) >= 20 and len(нема_) / max(1, len(усі_ф)) > 0.5:
        жив_ = 0
        for ф_ in нема_[:4]:
            кр_ = транспорт.get(ф_.get("url") or "")
            if кр_["код"] == 200 and кр_["тіло"] and факти_з_картки(кр_["тіло"], ф_["url"]).get("available") is True:
                жив_ += 1
        if жив_ >= 2:
            for ф_ in нема_:
                ф_["available"], ф_["наявність"] = None, "невідомо (канал магазину бреше)"
            діаг["наявність_каналу"] = "канал казав «нема» про %d речей — картки кажуть інше, знято" % len(нема_)
            лог("  ! %s" % діаг["наявність_каналу"])
        else:
            діаг["наявність_каналу"] = "канал каже «нема» про %d із %d — картки підтверджують" % (len(нема_), len(усі_ф))
    діаг["знайдено"] = len(кандидати)
    # Стеля рахує ЗІБРАНІ РЕЧІ, а не спроби: адресу, що виявилась розділом, заміняє наступна.
    # (06.09: за адресою «/catalog/leggensy-i-losiny» не відрізнити розділ від картки — вирішує лише
    # відкрита сторінка, тому беремо запас і зупиняємось за фактом.)
    кандидати = розподілити(кандидати, стеля * 3, лічба)
    # ── картка для кожної речі (П7) ──────────────────────────────────────────
    прийняті, відхилені, бачено_url, бачено_дизайн = [], [], set(), set()
    лічильник_рос = [0]
    черга_кандидатів = list(кандидати)
    додано_з_розділів = False
    паралельно = max(1, картки_потоків)
    while True:
        if not черга_кандидатів:                       # черга вичерпана — доливаємо з розділів, які вже завантажені
            if додано_з_розділів or not діаг.get("додаткові"):
                break
            додаткові = [u for u in dict.fromkeys(діаг.pop("додаткові")) if u not in бачено_url]
            черга_кандидатів = [dict(канал="картка з розділу", url=u, факти=None) for u in додаткові][:стеля * 3]
            додано_з_розділів = True
            if not черга_кандидатів:
                break
            лог("  + %d посилань зі сторінок-розділів" % len(черга_кандидатів))
            діаг["канали"].append("картки з розділів")
        # 06.09: на повільних магазинах один запит іде 25–100 с; послідовно це 15 карток за 20 хв.
        # Беремо їх пачками по 3: темп на домен лишається (пауза в транспорті), а простій зникає.
        лишилось = стеля - (len(прийняті) + len(відхилені))
        if лишилось <= 0:
            break
        пачка = [черга_кандидатів.pop(0) for _ in range(max(1, min(паралельно, len(черга_кандидатів), лишилось)))]
        к = пачка[0]
        if len(прийняті) + len(відхилені) >= стеля:
            break
        def _обробити(кандидат):
            try:
                _одна_річ(кандидат, маг, транспорт, діаг, прийняті, відхилені, бачено_url, бачено_дизайн,
                          перевіряти_фото, лічильник_рос)
            except Exception as e:                                   # noqa
                ключ = "картка: виняток %s" % type(e).__name__
                діаг["відхилено"][ключ] += 1
                if діаг["відхилено"][ключ] <= 3:
                    лог("  ! %s: виняток на картці %s — %s: %s" % (домен, (кандидат.get("url") or "")[:60], type(e).__name__, str(e)[:100]))
        if len(пачка) == 1:
            _обробити(пачка[0])
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(пачка)) as пул_:
                list(пул_.map(_обробити, пачка))
        if транспорт.час_вийшов():
            діаг["стан"] = "ДЕДЛАЙН ПРОГОНУ: %d речей" % len(прийняті)
            лог("  ⏹ %s: %s" % (домен, діаг["стан"])); break
        if time.time() > кінець_магазину:
            # 06.09: стеля різала САМЕ продуктивні магазини (sunwin 1 139 → 656, attico 510 → 152).
            # Поки магазин дає ≥30 речей за останні 5 хв — продовжуємо, до твердої межі 3× бюджету.
            темп = len(прийняті) - позначка[1]
            if темп >= 30 and time.time() < тверда_межа:
                позначка = (time.time(), len(прийняті))
                кінець_магазину = time.time() + 300
                лог("  ⏩ %s: %d речей за 5 хв — продовжую" % (домен, темп))
            else:
                діаг["стан"] = "СТЕЛЯ ЧАСУ МАГАЗИНУ: %d речей, темп %d/5хв" % (len(прийняті), темп)
                лог("  ⏱ %s: %s" % (домен, діаг["стан"])); break
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
    діаг.pop("мітки_фасетів", None); діаг.pop("лічба", None); діаг.pop("фото_хости", None)
    діаг["час"] = round(time.time() - діаг["час"])
    if urlparse(база).netloc in транспорт.браузером_вдалось:
        діаг["канали"].append("через відбиток Chrome")
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
           ("стать", "стать"), ("стать_джерело", "стать_джерело"), ("склад", "склад"), ("склад_джерело", "склад_джерело"),
           ("склад_непевний", "склад_непевний"), ("склад_основа", "склад_основа"), ("розміри", "розміри"),
           ("розміри_в_наявності", "розміри_в_наявності"), ("розміри_джерело", "розміри_джерело"),
           ("заміри", "заміри"), ("параметри_моделі", "параметри_моделі"), ("канал", "канал"),
           ("платформа", "платформа"), ("магазин", "магазин"), ("знято", "знято"), ("мова", "мова"),
           ("фото_джерело", "фото_джерело"), ("назва_джерело", "назва_джерело"), ("фасети", "фасети"),
           ("ціни_нема", "ціни_нема"))


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
        прийняті.extend(д.get("прийняті") or []); відхилені.extend(д.get("відхилені") or []); діаги.append(dict(д["діаг"], джерело_діагнозу=os.path.join(тека, ім)))
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
    # Кодований стан — окремо від вільного тексту старої діагностики.
    from стани_крамниць import стан_крамниці, рядки_звіту
    стани = [стан_крамниці(д["домен"], sum(з["магазин"] == д["домен"] for з in жін),
                          діаг=д, підстава=д["джерело_діагнозу"]) for д in діаги]
    with io.open(п("стани_крамниць.json"), "w", encoding="utf-8") as ф:
        json.dump(стани, ф, ensure_ascii=False, indent=2)
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
    for сл in sorted(ІМЕНА_СЛОТІВ):
        ряд = [sum(1 for з in прийняті if з["слот"] == сл and з["стать"] == ст) for ст in ("жіноче", "чоловіче", "унісекс", "невідомо")]
        if any(ряд):
            р.append("| %s | %d | %d | %d | %d |" % ((сл,) + tuple(ряд)))
    р += ["", "## Час і обриви", ""]
    часи = sorted(((д.get("час", 0), д["домен"]) for д in діаги), reverse=True)[:8]
    р.append("- найдовші магазини, с: " + ", ".join("%s %d" % (д, ч) for ч, д in часи))
    темпи = sorted(((д["прийнято"] / max(1, д.get("час", 1) / 60.0), д["домен"], д["прийнято"], д.get("час", 0)) for д in діаги
                    if д.get("час")), key=lambda x: x[0])
    повільні = [x for x in темпи if x[3] > 300 and x[0] < 3]
    if повільні:
        р.append("- багато часу, мало речей (речей/хв): " + ", ".join("%s %.1f (%d за %d с)" % (д, т, n, c) for т, д, n, c in повільні[:8]))
    обірв = [(д["домен"], (д.get("коди") or {}).get("обірвано за часом")) for д in діаги if (д.get("коди") or {}).get("обірвано за часом")]
    if обірв:
        р.append("- обірвано завантажень за часом: " + ", ".join("%s×%d" % x for x in обірв))
    брехня = [(д["домен"], д["наявність_каналу"]) for д in діаги if "картки кажуть інше" in str(д.get("наявність_каналу"))]
    if брехня:
        р.append("- канал магазину брехав про наявність (знято): " + "; ".join("%s — %s" % x for x in брехня[:6]))
    з_розд = [(д["домен"], д.get("з_розділів")) for д in діаги if д.get("з_розділів")]
    if з_розд:
        р.append("- посилань, узятих зі сторінок, що виявились розділами: " + ", ".join("%s %d" % x for x in з_розд[:8]))
    стелі = [д["домен"] for д in діаги if "СТЕЛЯ ЧАСУ" in д["стан"]]
    if стелі:
        р.append("- уперлись у стелю часу: " + ", ".join(стелі))
    р += ["", "## Українська версія сайту", ""]
    з_преф = [д for д in діаги if д.get("ua_префікс")]
    р.append("- магазинів з окремою UA-версією: %d із %d (%s)" % (len(з_преф), len(діаги),
             ", ".join("%s%s" % (д["домен"], д["ua_префікс"]) for д in з_преф[:12]) or "—"))
    перепис = [д for д in діаги if д.get("ua_переписано", "").startswith(("не треба", "префікс")) is False and д.get("ua_переписано")]
    for д in перепис[:10]:
        р.append("  - %s: %s" % (д["домен"], д["ua_переписано"]))
    не_вийшло = [д["домен"] + ": " + д["ua_переписано"] for д in діаги if str(д.get("ua_переписано", "")).startswith("префікс")]
    if не_вийшло:
        р.append("- НЕ переписано (перевірка не пройшла): " + "; ".join(не_вийшло[:6]))
    р += ["", "## Джерела кольору / слота / статі (прийняті)", ""]
    for поле in ("колір_джерело", "слот_джерело", "стать_джерело", "розміри_джерело", "наявність", "канал"):
        c = collections.Counter(re.sub(r"«.*?»", "«…»", str(з.get(поле) or "—")) for з in прийняті)
        р.append("- %s: %s" % (поле, "; ".join("%s %d" % kv for kv in c.most_common(6))))
    р += ["", "## Межа блоку товару (ПС-2): крамниці без межі — поля DOM «нема»", ""]
    без_межі = collections.defaultdict(collections.Counter)
    for з in прийняті:
        if з.get("межа_блоку") not in (None, "рецепт", "itemtype"):
            без_межі[з.get("магазин")][з["межа_блоку"]] += 1
    for м, c in sorted(без_межі.items(), key=lambda kv: -sum(kv[1].values())):
        р.append("- %s — карток без межі %d (%s): потрібен `селектор_блоку` у рецепті" % (м, sum(c.values()), ", ".join("%s %d" % kv for kv in c.items())))
    if not без_межі:
        р.append("- усі картки мають межу блоку")
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
    заблоковані = [д["домен"] for д in діаги if "ЗАБЛОКОВАНО" in д["стан"]]
    if заблоковані:
        with io.open(п("заблоковані.txt"), "w", encoding="utf-8") as f:
            f.write("# домени, які не пустили з цього IP. Прогнати з домашнього інтернету:\n"
                    "#   python3 жниварка.py --режим повний --магазини @заблоковані.txt\n")
            f.write("\n".join(заблоковані) + "\n")
        р.insert(5, "**Заблоковано %d магазинів** (список у `заблоковані.txt`): %s — потрібен домашній IP."
                 % (len(заблоковані), ", ".join(заблоковані)))
    р += рядки_звіту(стани)
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
            к = (рядок.split("\t") + [""] * 8)[:8]
            хв = к[6].strip()
            вих.append(dict(домен=к[0].strip(), база=к[1].strip() or ("https://%s" % к[0].strip()), ua=к[2].strip(),
                            стать_типово=(к[3].strip() or "невідомо"), стан=(к[4].strip() or "увімкнено"),
                            канал=к[5].strip().lower(),                    # відомий канал: woo/shopify/yml/списки
                            хвилин=(int(хв) if хв.isdigit() else 0),       # бюджет саме цього магазину
                            нотатка=(к[7] or к[5]).strip(), платформа="невідомо"))
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


def _зібрана(шлях):
    """`--продовжити`: крамниця зібрана, лише коли файл читається й жнива не впали на винятку.

    Файл, що ЛИШЕ ІСНУЄ, не доказ: обрив посеред запису дає битий gzip, а збій крамниці пишеться
    як порожній результат зі `стан: ВИНЯТОК` — обидва мають пройти знову, не лишитись «зібраними».
    """
    try:
        with gzip.open(шлях, "rt", encoding="utf-8") as f:
            д = json.load(f)
        return isinstance(д.get("прийняті"), list) and not str((д.get("діаг") or {}).get("стан", "")).startswith("ВИНЯТОК")
    except (OSError, EOFError, ValueError, AttributeError):
        return False


def main(argv=None):
    global ОПИС_СИМВОЛІВ
    for потік in (sys.stdout, sys.stderr):
        try:
            потік.reconfigure(encoding="utf-8", errors="replace")     # cp1251/cp437 у консолі не має ронити print
        except Exception:                                              # noqa
            pass
    if requests is None and "--зібрати" not in (argv if argv is not None else sys.argv[1:]):
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
    ап.add_argument("--картки-потоків", type=int, default=3, help="скільки карток одного магазину тягнути паралельно")
    ап.add_argument("--хвилин-на-магазин", type=int, default=0, help="стеля часу на магазин (0 = 3 у пробі, 20 у повному)")
    ап.add_argument("--фото-кожен", type=int, default=1, help="перевіряти фото запитом у кожної N-ї речі (повний прогін: 5 — удвічі швидше, відсоток у звіті той самий)")
    ап.add_argument("--ігнорувати-robots", action="store_true")
    ап.add_argument("--без-маскування", action="store_true", help="не підробляти відбиток Chrome навіть якщо curl_cffi є")
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
    if a.магазини.startswith("@"):                              # @файл — по домену на рядок (список заблокованих)
        with io.open(a.магазини[1:], encoding="utf-8") as f:
            a.магазини = ",".join(x.strip() for x in f if x.strip() and not x.startswith("#"))
    if a.магазини != "усі":
        обрані = {x.strip().lower() for x in a.магазини.split(",") if x.strip()}
        магазини = [м for м in читати_магазини(a.список) if м["домен"].lower() in обрані]
    лог = lambda *x: print(*x, flush=True)
    хв = a.дедлайн_хвилин or (90 if a.режим == "повний" else 40)   # прогін без дедлайну не буває
    дедлайн = time.time() + 60 * хв
    лог("дедлайн прогону: %d хв (до %s)" % (хв, datetime.datetime.fromtimestamp(дедлайн).strftime("%H:%M")))
    if a.група:
        i, n = [int(x) for x in a.група.split("/")]
        # 06.09: розподіл «кожен n-й» звів усі важкі магазини в одне завдання — воно йшло 3 год 40 хв,
        # решта п'ять закінчились за півтори. Розкладаємо жадібно за бюджетом: найважчий у найлегший кошик.
        кошики = [[] for _ in range(n)]
        вага = [0] * n
        for м in sorted(магазини, key=lambda м: -(м.get("хвилин") or 10)):
            j = вага.index(min(вага))
            кошики[j].append(м); вага[j] += (м.get("хвилин") or 10)
        лог("розподіл по завданнях, хв: %s" % вага)
        магазини = кошики[i - 1]
    if a.продовжити:
        було = len(магазини)
        магазини = [м for м in магазини if not _зібрана(os.path.join(сирі, "%s.json.gz" % м["домен"]))]
        print("продовження: пропущено %d магазинів, що вже зібрані" % (було - len(магазини)), flush=True)
    # 06.09: 45 карткових магазинів × 20 хв = 15 годин заради 750 речей. Базова стеля коротка,
    # а продуктивні магазини продовжують себе самі (≥30 речей за 5 хв, тверда межа 3×).
    хв_магазин = a.хвилин_на_магазин or (3 if a.режим == "проба" else 8)
    лог("%s · Python %s · парсер HTML: %s · відбиток Chrome: %s · режим %s · магазинів %d · стеля %d речей, %d хв/магазин · словники: %s"
        % (ВЕРСІЯ, sys.version.split()[0], ПАРСЕР_HTML, "curl_cffi" if (_curl and not a.без_маскування) else "нема",
           a.режим, len(магазини), стеля, хв_магазин, СЛОВНИКИ_ЗВІДКИ))
    if BeautifulSoup is None:
        лог("!! beautifulsoup4 не встановлено — картки читатимуться лише з JSON-LD/meta (без характеристик, розмірів, галереї)")
    транспорт = Транспорт(пауза=a.пауза, ігнорувати_robots=a.ігнорувати_robots, лог=лог,
                          не_маскуватись=a.без_маскування, дедлайн=дедлайн)
    лічба_слотів = collections.Counter()      # спільна на прогін: наступні магазини добирають рідкі слоти

    def один(м):
        if дедлайн and time.time() > дедлайн:
            лог("  ⏱ %s: не почато — стеля часу; добере «продовжити» наступного разу" % м["домен"]); return м["домен"]
        try:
            прийн, відх, діаг = зібрати_магазин(м, транспорт, стеля, лог, перевіряти_фото=not a.без_фотоперевірки, дедлайн=дедлайн, фото_кожен=a.фото_кожен, лічба=лічба_слотів,
                                                хвилин_на_магазин=((м.get("хвилин") or хв_магазин) if a.режим == "повний" else хв_магазин),
                                                картки_потоків=a.картки_потоків,
                                                фасетів=(1 if a.режим == "проба" else 3))
        except Exception as e:                                       # noqa
            import traceback; traceback.print_exc()
            прийн, відх, діаг = [], [], dict(домен=м["домен"], база=м["база"], платформа=м.get("платформа"), канали=[],
                                             запитів=0, знайдено=0, прийнято=0, відхилено=collections.Counter(),
                                             стан="ВИНЯТОК: %s" % str(e)[:120], причина_код="EXCEPTION", час=0, версія=ВЕРСІЯ)
        діаг.setdefault("причина_код", "UNKNOWN")
        діаг.setdefault("доступ_код", "UNKNOWN")
        діаг["відхилено"] = dict(діаг["відхилено"])
        шлях_м = os.path.join(сирі, "%s.json.gz" % м["домен"])
        with gzip.open(шлях_м + ".tmp", "wt", encoding="utf-8") as f:       # tmp + replace: обрив не лишає півфайла
            json.dump(dict(діаг=діаг, прийняті=прийн, відхилені=відх), f, ensure_ascii=False)
        os.replace(шлях_м + ".tmp", шлях_м)
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
