# -*- coding: utf-8 -*-
"""РОЗВІДКА — одна ніч, 58 українських магазинів зі списку власника (07.09.2026), справжній браузер.

Що міняє у світі: замість здогадів за формою URL наступна сесія пише РЕЦЕПТ магазину з того,
що реально віддав Chromium: відрендерений HTML розділу й картки, усі XHR/JSON-відповіді (внутрішні API),
коди й розміри відповідей, скриншоти. Речей не збирає, каталог не пише — це не жниварка.

Запуск
  python3 розвідка.py                              # усі 58, тека ./розвідка
  python3 розвідка.py --магазини 25union.com.ua,vilni.store
  python3 розвідка.py --старт https://example.com  # довільна адреса (проба механіки)
  python3 розвідка.py --видимо                     # видиме вікно Chromium (якщо headless не проходить заслон)

Вихід: розвідка/зведення.tsv (один рядок на магазин — читати першим) і розвідка/<домен>/:
  зведення.json · 01_головна.html/.jpg · 02_розділ.html/.jpg · 03_картка.html/.jpg · 03_картка_ld.json
  проби.json (robots, sitemap, Shopify products.json, Woo store API) · мережа.tsv · мережа/NNN.json (тіла JSON-відповідей)

Playwright і Chromium ставляться самі, якщо їх нема (разово ~150 МБ). Чоловічі розділи не шукаються —
рішення власника 07.09: спочатку жіноче.
"""
import argparse, asyncio, datetime, json, os, re, subprocess, sys, threading, time
from urllib.parse import urlparse, urljoin

ВЕРСІЯ = "розвідка v1 · 2026-09-07"

# Список власника 07.09.2026 мінус 8 міжнародних мереж (zara, reserved, mango, next, mohito, modivo, wittchen, answear).
# Стартова адреса — з повідомлення власника, без utm/gclid; де дано глибоку сторінку — узято мовний корінь.
МАГАЗИНИ = [
    ("giardini-shoes.com", "https://giardini-shoes.com/"),
    ("musthave.ua", "https://musthave.ua/ua"),
    ("yakfaino.com", "https://yakfaino.com/"),
    ("attico.ua", "https://attico.ua/"),
    ("andretan.ua", "https://andretan.ua/"),
    ("jecomestudio.com", "https://jecomestudio.com/"),
    ("favoriteshoes.com.ua", "https://favoriteshoes.com.ua/"),
    ("wearme.ua", "https://wearme.ua/"),
    ("sarahberlin.com", "https://sarahberlin.com/uk/"),
    ("alot.com.ua", "https://alot.com.ua/"),
    ("sunwin-store.com", "https://www.sunwin-store.com/"),
    ("diadia.ua", "https://diadia.ua/"),
    ("theoriginals.com.ua", "https://theoriginals.com.ua/ua"),
    ("fromus.ua", "https://fromus.ua/ua/"),
    ("morandi.ua", "https://morandi.ua/"),
    ("rito.ua", "https://rito.ua/"),
    ("vsisvoi.ua", "https://vsisvoi.ua/"),
    ("friendsoffashion.com.ua", "https://friendsoffashion.com.ua/"),
    ("natalibolgar.com", "https://natalibolgar.com/ua/"),
    ("md-fashion.ua", "https://md-fashion.ua/"),
    ("maryline.ua", "https://maryline.ua/"),
    ("onebyone.ua", "https://onebyone.ua/"),
    ("bella-bicchi.com", "https://bella-bicchi.com/"),
    ("tm-beart.com", "https://www.tm-beart.com/"),
    ("cooshwear.com", "https://cooshwear.com/"),
    ("pitaya.ua", "https://pitaya.ua/"),
    ("emmeliedelage.com", "https://emmeliedelage.com/"),
    ("cher17.com", "https://cher17.com/"),
    ("nyni.shop", "https://nyni.shop/uk/"),
    ("maxa.ua", "https://maxa.ua/"),
    ("skripka.com.ua", "https://skripka.com.ua/"),
    ("25union.com.ua", "https://25union.com.ua/"),
    ("likeangel.com.ua", "https://likeangel.com.ua/"),
    ("gepur.com", "https://gepur.com/uk/"),
    ("vittorossi.ua", "https://vittorossi.ua/ua/"),
    ("yulashop.com.ua", "https://yulashop.com.ua/"),
    ("miraton.ua", "https://www.miraton.ua/ua/"),
    ("stolyarchuk.com.ua", "https://stolyarchuk.com.ua/katalog/sukni"),
    ("sezone.ua", "https://sezone.ua/"),
    ("dolcedonna.com.ua", "https://dolcedonna.com.ua/"),
    ("k.ua", "https://k.ua/"),
    ("ricamare.com.ua", "https://ricamare.com.ua/"),
    ("brenda.ua", "https://brenda.ua/"),
    ("intimo.com.ua", "https://www.intimo.com.ua/ua/"),
    ("devari.com.ua", "https://devari.com.ua/"),
    ("provenceshop.com.ua", "https://provenceshop.com.ua/ua"),
    ("twice.com.ua", "https://twice.com.ua/"),
    ("otaje.com", "https://otaje.com/"),
    ("natali-style.com.ua", "https://natali-style.com.ua/"),
    ("cultboutique.com.ua", "https://cultboutique.com.ua/ua"),
    ("kasandra.ua", "https://kasandra.ua/"),
    ("honchstudio.com", "https://honchstudio.com/"),
    ("vilni.store", "https://vilni.store/"),
    ("vmma.com.ua", "https://vmma.com.ua/"),
    ("feelyou.com.ua", "https://feelyou.com.ua/"),
    ("vovk.com", "https://vovk.com/ua/"),
    ("welfare.ua", "https://welfare.ua/"),
    ("solmar.com.ua", "https://solmar.com.ua/ua/"),
]
assert len(МАГАЗИНИ) == 58 and len({д for д, _ in МАГАЗИНИ}) == 58, "список власника: 66 − 8 мереж = 58"

# ЛИШЕ ASCII в усьому, що йде в HTTP (урок жниварки 05.09: кирилиця в User-Agent поклала всі магазини).
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0.0.0 Safari/537.36")
assert UA.isascii()

# ── розпізнавання за HTML (лише впорядковує наступну роботу, нічого не вмикає й не вимикає) ──
ПЛАТФОРМИ = [
    ("Хорошоп", re.compile(r"horoshop", re.I)),
    ("Shopify", re.compile(r"cdn\.shopify\.com|Shopify\.theme|shopify-section", re.I)),
    ("WooCommerce", re.compile(r"woocommerce", re.I)),
    ("WordPress", re.compile(r"/wp-content/|/wp-json/", re.I)),
    ("OpenCart", re.compile(r"index\.php\?route=|catalog/view/theme|/image/cache/", re.I)),
    ("Bitrix", re.compile(r"/bitrix/", re.I)),
    ("PrestaShop", re.compile(r"prestashop", re.I)),
    ("Magento", re.compile(r"Magento|/static/version\d+/", re.I)),
    ("Prom.ua", re.compile(r"prom\.ua", re.I)),
    ("Weblium", re.compile(r"weblium", re.I)),
    ("Tilda", re.compile(r"tilda", re.I)),
    ("Wix", re.compile(r"wix\.com|wixstatic", re.I)),
    ("Next.js", re.compile(r"__NEXT_DATA__|/_next/", re.I)),
    ("Nuxt", re.compile(r"__NUXT__|/_nuxt/", re.I)),
    ("Shop-Express", re.compile(r"shop-express", re.I)),
    ("Хост:cloudflare", re.compile(r"cloudflare", re.I)),
]
ЗАСЛОН = re.compile(r"just a moment|attention required|checking your browser|enable javascript and cookies|"
                    r"access denied|ddos-guard|captcha|перевірка браузера|проверка браузера|cf-chl|challenge-platform", re.I)
РОСІЙСЬКА = re.compile(r"[ыэъё]|\b(платье|юбка|брюки|обувь|одежда|женск\w*|сумка для|пальто женское)\b", re.I)

# посилання на розділ: що вище бал, то ймовірніше це жіночий розділ одягу/взуття
_РОЗДІЛ_СИЛЬНО = re.compile(r"sukn|platt|plat[iy]|dress|bluz|blous|sorochk|shirt|spidn|yubk|skirt|shtan|bryuk|pants|trous|"
                            r"jeans|dzhins|zhaket|jacket|blazer|kardig|sweater|svetr|sviter|jumper|dzhemper|palto|coat|"
                            r"trench|kurtk|vzutt|obuv|shoes|tufl|cherevik|chobot|boot|sandal|sumk|bag|kostyum|suit|"
                            r"верх|низ|сукн|плат|блуз|спідн|штан|взутт|сумк", re.I)
_РОЗДІЛ_СЛАБКО = re.compile(r"katalog|catalog|collection|odyag|odiag|odezhd|clothing|aksesuar|accessor|shop|"
                            r"new|novynk|zhinoch|zhink|women|woman", re.I)
_РОЗДІЛ_НЕ = re.compile(r"blog|news|novyn|about|pro-nas|o-nas|contact|kontakt|deliver|dostavk|oplat|payment|cart|"
                        r"checkout|login|account|wishlist|compare|lookbook|sertif|certif|gift|podarun|vakans|career|"
                        r"privacy|terms|offer|return|obmin|povern|faq|review|vidguk|brand|tel:|mailto:|javascript:|"
                        r"(?:^|[/-])(?:kids|dyt\w*|dit[iy]|child\w*|detsk\w*|men|man|cholov\w*|muzh\w*)(?:$|[/-])|"
                        r"про нас|контакт|доставк|оплат|блог|новин|відгук|вакансі|дитяч|чолові|подарунк|сертифікат|"
                        r"кошик|увійти|вхід|реєстрац", re.I)
_ПАГІНАЦІЯ = re.compile(r"[?&]page=\d+|/page/\d+|/page-\d+|PAGEN_\d+=|[?&]p=\d+|[?&]start=\d+|[?&]offset=\d+|[?&]limit=", re.I)
_ЩЕ = re.compile(r"показати ще|завантажити ще|показать ещ|load more|show more|більше товар", re.I)
_ЦІНА = re.compile(r"\d[\d\s\u00a0]{1,7}\s?(грн|₴|uah)", re.I)
_СЛУЖБОВЕ = re.compile(r"\.(css|js|png|jpe?g|webp|gif|svg|pdf|ico|xml|json|zip|mp4|woff2?|ttf)(\?|$)", re.I)


def лог(т):
    print(time.strftime("%H:%M:%S"), т, flush=True)


def домен_із(url):
    return (urlparse(url).netloc or "").lower().replace("www.", "")


def _підготувати_playwright(лог=лог):
    try:
        import playwright  # noqa
    except ImportError:
        лог("ставлю playwright…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "playwright"])
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            b.close()
    except Exception as e:  # noqa
        лог("Chromium нема або не запускається (%s) — завантажую…" % str(e).splitlines()[0][:120])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])


def платформа(html):
    return [ім for ім, рх in ПЛАТФОРМИ if рх.search(html or "")]


def json_ld(html):
    вих = []
    for м in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html or "", re.S | re.I):
        т = м.group(1).strip()
        try:
            в = json.loads(т)
        except Exception:  # noqa
            try:
                в = json.loads(re.sub(r",\s*([\]}])", r"\1", т))
            except Exception:  # noqa
                continue
        вих.extend(в if isinstance(в, list) else [в])
    return вих


def типи_ld(html):
    типи = []
    for в in json_ld(html):
        if isinstance(в, dict):
            т = в.get("@type")
            типи.extend(т if isinstance(т, list) else [т])
            for е in (в.get("@graph") or []):
                if isinstance(е, dict):
                    т = е.get("@type")
                    типи.extend(т if isinstance(т, list) else [т])
    return sorted({str(т) for т in типи if т})


def мета(html, ім):
    м = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']*)' % re.escape(ім), html or "", re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']%s["\']' % re.escape(ім), html or "", re.I)
    return м.group(1) if м else ""


def мова_html(html):
    м = re.search(r"<html[^>]*\slang=[\"']?([\w-]+)", html or "", re.I)
    href = re.findall(r'<link[^>]+hreflang=["\']([^"\']+)["\'][^>]+href=["\']([^"\']+)', html or "", re.I)
    href += [(б, а) for а, б in re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+hreflang=["\']([^"\']+)', html or "", re.I)]
    return {"lang": м.group(1) if м else "", "hreflang": {к: в for к, в in href}}


def фіди_в_html(html, база):
    вих = set()
    for м in re.finditer(r'href=["\']([^"\']+)["\']', html or "", re.I):
        u = м.group(1)
        if re.search(r"yml|feed|export|products\.xml|price.*\.xml|\.xml(\?|$)|rss", u, re.I) and not re.search(r"sitemap", u, re.I):
            вих.add(urljoin(база, u))
    for м in re.finditer(r'<link[^>]+type=["\']application/(?:rss\+xml|atom\+xml)["\'][^>]+href=["\']([^"\']+)', html or "", re.I):
        вих.add(urljoin(база, м.group(1)))
    return sorted(вих)[:20]


def характеристики(html):
    """Скільки рядків «ключ: значення» видно в картці (таблиця/dl/li з двокрапкою)."""
    n = len(re.findall(r"<t[dh][^>]*>[^<]{2,40}</t[dh]>\s*<td", html or "", re.I))
    n += len(re.findall(r"<dt[^>]*>[^<]{2,40}</dt>", html or "", re.I))
    n += len(re.findall(r"<li[^>]*>\s*(?:<[^>]+>\s*)*[А-ЯІЇЄA-Z][^<:]{2,30}:\s*(?:<[^>]+>\s*)*[^<]{1,60}<", html or ""))
    return n


ВИТЯГ_ПОСИЛАНЬ = """() => Array.from(document.querySelectorAll('a[href]')).map(a => {
  const p = a.parentElement, g = p ? p.parentElement : null;
  const near = ((p && p.innerText) || '').slice(0, 200) + ' ' + ((g && g.innerText && g.innerText.length < 400) ? g.innerText : '');
  return {href: a.href, text: (a.innerText || '').trim().slice(0, 80), img: !!a.querySelector('img'),
          near: near.slice(0, 300), cls: ((a.className || '') + ' ' + ((p && p.className) || '')).toString().slice(0, 120)};
})"""


def кандидати_розділів(посилання, база):
    д = домен_із(база)
    бали = {}
    for п in посилання:
        u = п["href"].split("#")[0]
        if домен_із(u) != д or _СЛУЖБОВЕ.search(u) or _РОЗДІЛ_НЕ.search(u) or _РОЗДІЛ_НЕ.search(п["text"]) \
           or _ПАГІНАЦІЯ.search(u) or "?" in u or "/filter" in u:
            continue
        шлях = urlparse(u).path
        if шлях in ("", "/"):
            continue
        глибина = len([x for x in шлях.split("/") if x])
        текст = (п["text"] or "") + " " + шлях
        б = 0
        if _РОЗДІЛ_СИЛЬНО.search(текст):
            б += 3
        if _РОЗДІЛ_СЛАБКО.search(текст):
            б += 1
        if п["img"] or _ЦІНА.search(п["near"] or ""):
            б -= 2                                      # картинка/ціна поруч — це товар або банер, не пункт меню
        if глибина >= 3:
            б -= 1
        if б > 0:
            бали[u] = max(бали.get(u, 0), б)
    return [u for u, _ in sorted(бали.items(), key=lambda x: (-x[1], len(urlparse(x[0]).path)))][:8]


def кандидати_карток(посилання, база, поточна):
    """→ (список url у порядку схожості на річ, скільки посилань мають і картинку, і ціну поруч)."""
    д = домен_із(база)
    бали, з_ціною = {}, set()
    for п in посилання:
        u = п["href"].split("#")[0]
        if домен_із(u) != д or u.rstrip("/") == поточна.rstrip("/") or _СЛУЖБОВЕ.search(u) or \
           _РОЗДІЛ_НЕ.search(u) or _ПАГІНАЦІЯ.search(u) or "/filter" in u or ("?" in u and "product_id" not in u):
            continue
        б = 0
        if п["img"]:
            б += 2
        if _ЦІНА.search(п["near"] or ""):
            б += 2
        if re.search(r"product|tovar|item|card", п["cls"] or "", re.I):
            б += 1
        if re.search(r"/(product|products|tovar|tovary|goods|item|p)/|product_id=|\.html$|-\d{3,}/?$", u, re.I):
            б += 1
        if б >= 2:
            бали[u] = max(бали.get(u, 0), б)
        if п["img"] and _ЦІНА.search(п["near"] or ""):
            з_ціною.add(u)
    return [u for u, _ in sorted(бали.items(), key=lambda x: -x[1])], len(з_ціною)


def це_картка(html):
    типи = типи_ld(html)
    ld = any("Product" in т for т in типи)
    og = мета(html, "og:type").lower().startswith("product") or bool(мета(html, "product:price:amount"))
    ціна = bool(_ЦІНА.search(re.sub(r"<[^>]+>", " ", html or "")[:200000]))
    return ld, og, ціна, типи


class Розвідник:
    def __init__(self, тека, секунд, видимо, паралельно, лог=лог):
        self.тека, self.секунд, self.видимо, self.паралельно, self.лог = тека, секунд, видимо, паралельно, лог
        self.замок = threading.Lock()
        os.makedirs(тека, exist_ok=True)
        self.зведення = os.path.join(тека, "зведення.tsv")
        if not os.path.exists(self.зведення):
            with open(self.зведення, "w", encoding="utf-8") as f:
                f.write("\t".join(КОЛОНКИ) + "\n")

    async def усі(self, магазини):
        from playwright.async_api import async_playwright
        сем = asyncio.Semaphore(self.паралельно)
        async with async_playwright() as p:
            браузер = await p.chromium.launch(headless=not self.видимо,
                                              args=["--disable-blink-features=AutomationControlled", "--lang=uk-UA"])
            try:
                await asyncio.gather(*[self._один(браузер, д, s, сем) for д, s in магазини])
            finally:
                await браузер.close()

    async def _один(self, браузер, домен, старт, сем):
        async with сем:
            з = {"домен": домен, "старт": старт, "версія": ВЕРСІЯ, "дата": datetime.datetime.now().isoformat(timespec="seconds"),
                 "помилки": [], "мережа_json": 0, "мережа_відповідей": 0}
            тека = os.path.join(self.тека, домен)
            os.makedirs(os.path.join(тека, "мережа"), exist_ok=True)
            контекст = await браузер.new_context(user_agent=UA, locale="uk-UA", timezone_id="Europe/Kyiv",
                                                 viewport={"width": 1366, "height": 900}, ignore_https_errors=True,
                                                 extra_http_headers={"Accept-Language": "uk-UA,uk;q=0.9,en;q=0.7"})
            мережа = open(os.path.join(тека, "мережа.tsv"), "w", encoding="utf-8")
            мережа.write("час\tкод\tтип\tcontent-type\tбайт\turl\n")
            t0 = time.time()

            async def _тіло(r, ctype, n):
                try:
                    if len(await r.body()) <= 3_000_000:
                        т = await r.text()
                        with open(os.path.join(тека, "мережа", "%03d.json" % n), "w", encoding="utf-8") as f:
                            f.write("// %s\n// %s\n" % (r.url[:500], ctype))
                            f.write(т[:600_000])
                except Exception:  # noqa
                    pass

            def _відповідь(r):
                try:
                    з["мережа_відповідей"] += 1
                    ctype = (r.headers.get("content-type") or "").lower()
                    тип = r.request.resource_type
                    мережа.write("%.1f\t%s\t%s\t%s\t%s\t%s\n" % (time.time() - t0, r.status, тип, ctype[:60],
                                                                 r.headers.get("content-length") or "", r.url[:400]))
                    if "json" in ctype and тип in ("xhr", "fetch", "document") and з["мережа_json"] < 60:
                        з["мережа_json"] += 1
                        asyncio.ensure_future(_тіло(r, ctype, з["мережа_json"]))
                except Exception:  # noqa
                    pass

            сторінка = await контекст.new_page()
            сторінка.on("response", _відповідь)
            try:
                await asyncio.wait_for(self._кроки(сторінка, контекст, домен, старт, тека, з), timeout=self.секунд)
            except asyncio.TimeoutError:
                з["помилки"].append("бюджет %d с вичерпано" % self.секунд)
            except Exception as e:  # noqa
                з["помилки"].append("збій: %s" % str(e).splitlines()[0][:200])
            finally:
                з["секунд"] = round(time.time() - t0, 1)
                try:
                    мережа.close()
                    await контекст.close()
                except Exception:  # noqa
                    pass
                self._записати(тека, з)
                self.лог("%-24s %s" % (домен, self._рядок(з)))

    async def _сторінка(self, сторінка, url, тека, ім, з, ключ):
        """Перехід + очікування + збереження HTML і скриншота. → html або None."""
        t = time.time()
        try:
            r = await сторінка.goto(url, wait_until="domcontentloaded", timeout=35_000)
            код = r.status if r else None
        except Exception as e:  # noqa
            з["помилки"].append("%s: %s" % (ім, str(e).splitlines()[0][:160]))
            з[ключ + "_код"] = "збій"
            return None
        try:
            await сторінка.wait_for_load_state("networkidle", timeout=12_000)
        except Exception:  # noqa
            pass
        html = await сторінка.content()
        заслон = bool(ЗАСЛОН.search(html[:6000])) or (код and код in (403, 429, 503)) or len(html) < 1500
        if заслон:                                       # справжній браузер може пройти JS-заслон сам — даємо йому 10 с
            await сторінка.wait_for_timeout(10_000)
            html2 = await сторінка.content()
            з[ключ + "_заслон"] = "так→пройдено" if (len(html2) > len(html) * 2 and not ЗАСЛОН.search(html2[:6000])) else "так"
            html = html2
        else:
            з[ключ + "_заслон"] = "ні"
        з[ключ + "_код"] = код
        з[ключ + "_байт"] = len(html)
        з[ключ + "_url"] = сторінка.url
        з[ключ + "_секунд"] = round(time.time() - t, 1)
        з[ключ + "_заголовок"] = (await сторінка.title())[:120]
        with open(os.path.join(тека, ім + ".html"), "w", encoding="utf-8") as f:
            f.write(html)
        try:
            await сторінка.screenshot(path=os.path.join(тека, ім + ".jpg"), type="jpeg", quality=55, full_page=True,
                                      clip={"x": 0, "y": 0, "width": 1366, "height": 2400})   # шапка + перші ряди речей
        except Exception:  # noqa
            pass
        return html

    async def _проба(self, контекст, url, що):
        try:
            r = await контекст.request.get(url, timeout=15_000, max_redirects=3)
            ctype = (r.headers.get("content-type") or "").lower()
            тіло = await r.body()
            текст = тіло[:400_000].decode("utf-8", "replace")
            в = {"url": url, "код": r.status, "ctype": ctype[:60], "байт": len(тіло)}
            if що == "robots":
                в["sitemap"] = re.findall(r"(?im)^sitemap:\s*(\S+)", текст)[:10]
                в["disallow"] = len(re.findall(r"(?im)^disallow:", текст))
            elif що == "sitemap":
                loc = re.findall(r"<loc>\s*([^<\s]+)", текст)
                в["індекс"] = "<sitemapindex" in текст
                в["loc"] = len(loc)
                в["перші"] = loc[:6]
            elif що in ("shopify", "woo"):
                try:
                    j = json.loads(текст)
                    n = len(j.get("products", [])) if isinstance(j, dict) else len(j)
                    в["товарів_у_відповіді"] = n
                    в["json"] = True
                except Exception:  # noqa
                    в["json"] = False
            return в
        except Exception as e:  # noqa
            return {"url": url, "код": "збій", "помилка": str(e).splitlines()[0][:120]}

    async def _кроки(self, сторінка, контекст, домен, старт, тека, з):
        # 1. головна (або задана власником сторінка)
        html = await self._сторінка(сторінка, старт, тека, "01_головна", з, "головна")
        if html is None:
            return
        база = сторінка.url
        з["платформа"] = платформа(html)
        з["мова"] = мова_html(html)
        з["фіди_в_html"] = фіди_в_html(html, база)
        з["generator"] = мета(html, "generator")[:80]
        посилання = await сторінка.evaluate(ВИТЯГ_ПОСИЛАНЬ)
        з["посилань_на_головній"] = len(посилання)
        # дешеві проби ТИМ САМИМ браузерним контекстом (cookies, UA)
        корінь = "%s://%s/" % (urlparse(база).scheme, urlparse(база).netloc)
        проби = {"robots": await self._проба(контекст, корінь + "robots.txt", "robots")}
        мапи = проби["robots"].get("sitemap") or [корінь + "sitemap.xml"]
        проби["sitemap"] = await self._проба(контекст, мапи[0], "sitemap")
        проби["shopify"] = await self._проба(контекст, корінь + "products.json?limit=5", "shopify")
        проби["woo"] = await self._проба(контекст, корінь + "wp-json/wc/store/v1/products?per_page=5", "woo")
        з["проби"] = проби
        with open(os.path.join(тека, "проби.json"), "w", encoding="utf-8") as f:
            json.dump(проби, f, ensure_ascii=False, indent=1)

        # 2. розділ: якщо стартова сторінка вже список речей — вона і є розділ
        картки, з_ціною = кандидати_карток(посилання, база, сторінка.url)
        if з_ціною >= 8:
            з["розділ_url"], з["розділ_це_старт"] = сторінка.url, True
            html_розділу = html
        else:
            з["розділ_це_старт"] = False
            html_розділу = None
            for u in кандидати_розділів(посилання, база)[:3]:
                html_розділу = await self._сторінка(сторінка, u, тека, "02_розділ", з, "розділ")
                if html_розділу is None:
                    continue
                посилання = await сторінка.evaluate(ВИТЯГ_ПОСИЛАНЬ)
                картки, з_ціною = кандидати_карток(посилання, база, сторінка.url)
                if з_ціною >= 3 or len(картки) >= 8:
                    break
            if html_розділу is None:
                з["помилки"].append("розділ не відкрився")
                return
        з["речей_на_сторінці"] = з_ціною
        з["кандидатів_карток"] = len(картки)
        з["пагінація"] = sorted({m.group(0) for m in _ПАГІНАЦІЯ.finditer(html_розділу)})[:6]
        з["кнопка_ще"] = bool(_ЩЕ.search(html_розділу))
        з["розділ_ld"] = типи_ld(html_розділу)
        з["розділ_фасети"] = sorted({m.group(0) for m in re.finditer(r"/filter/[^\"'/]+|[?&]filter[^&\"']*|/(?:tsvet|color|kolir|rozmir|size)/[^\"'/]+", html_розділу)})[:10]

        # 3. картка: до 3 спроб, поки не схоже на річ
        for u in картки[:3]:
            html_картки = await self._сторінка(сторінка, u, тека, "03_картка", з, "картка")
            if html_картки is None:
                continue
            ld, og, ціна, типи = це_картка(html_картки)
            _, речей_поруч = кандидати_карток(await сторінка.evaluate(ВИТЯГ_ПОСИЛАНЬ), база, сторінка.url)
            з["картка_ld"], з["картка_og"], з["картка_ціна"], з["картка_ld_типи"] = ld, og, ціна, типи
            if ld or og or (ціна and речей_поруч <= 2):     # ціна є і на списку; список ≠ картка
                break
        else:
            з["помилки"].append("картка не знайдена серед %d кандидатів" % len(картки))
            return
        with open(os.path.join(тека, "03_картка_ld.json"), "w", encoding="utf-8") as f:
            json.dump(json_ld(html_картки), f, ensure_ascii=False, indent=1)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html_картки, re.S | re.I)
        назва = re.sub(r"<[^>]+>|\s+", " ", h1.group(1)).strip() if h1 else мета(html_картки, "og:title")
        з["назва"] = назва[:120]
        з["назва_російська"] = bool(РОСІЙСЬКА.search(назва))
        з["картка_мова"] = мова_html(html_картки)
        з["картка_характеристик"] = характеристики(html_картки)
        з["картка_фото"] = len(set(re.findall(r'<img[^>]+src=["\']([^"\']+\.(?:jpe?g|webp|png))', html_картки, re.I)))
        з["картка_розмірів"] = len(re.findall(r"(?<![\w-])(?:XXS|XS|S|M|L|XL|XXL|3XL|4XL|3[4-9]|4[0-8]|5[0-8])(?![\w-])",
                                             re.sub(r"<[^>]+>", " ", html_картки)[:300000]))
        з["картка_склад"] = bool(re.search(r"\d{1,3}\s?%\s?(?:бавовн|віскоз|поліест|вовн|льон|ліоцел|еластан|шовк|акрил|нейлон|"
                                            r"хлоп|полиэст|шерст|лен|вискоз|cotton|polyester|wool|viscose|linen)", html_картки, re.I))

    def _записати(self, тека, з):
        with open(os.path.join(тека, "зведення.json"), "w", encoding="utf-8") as f:
            json.dump(з, f, ensure_ascii=False, indent=1)
        with self.замок, open(self.зведення, "a", encoding="utf-8") as f:
            f.write("\t".join(str(self._поле(з, к)).replace("\t", " ").replace("\n", " ") for к in КОЛОНКИ) + "\n")

    @staticmethod
    def _поле(з, к):
        п = з.get("проби", {})
        if к == "платформа":
            return ",".join(з.get("платформа") or []) or "?"
        if к == "sitemap":
            s = п.get("sitemap", {})
            return "%s/%s%s" % (s.get("код"), s.get("loc", ""), "/індекс" if s.get("індекс") else "")
        if к == "products_json":
            s = п.get("shopify", {})
            return "%s/%s" % (s.get("код"), s.get("товарів_у_відповіді", "-"))
        if к == "wc_store":
            s = п.get("woo", {})
            return "%s/%s" % (s.get("код"), s.get("товарів_у_відповіді", "-"))
        if к == "мова_html":
            return (з.get("мова") or {}).get("lang", "")
        if к == "hreflang":
            return ",".join(sorted((з.get("мова") or {}).get("hreflang", {}))) or ""
        if к == "пагінація":
            return ",".join(з.get("пагінація") or []) + ("+ще" if з.get("кнопка_ще") else "")
        if к == "помилки":
            return " | ".join(з.get("помилки") or [])
        if к == "фіди":
            return len(з.get("фіди_в_html") or [])
        return з.get(к, "")

    def _рядок(self, з):
        return "код %s · %s · %s Б · заслон %s · речей у розділі %s · картка ld=%s og=%s ціна=%s · %s с%s" % (
            з.get("головна_код"), ",".join(з.get("платформа") or ["?"]), з.get("головна_байт", "-"), з.get("головна_заслон", "-"),
            з.get("речей_на_сторінці", "-"), з.get("картка_ld", "-"), з.get("картка_og", "-"), з.get("картка_ціна", "-"),
            з.get("секунд"), (" · " + з["помилки"][-1]) if з.get("помилки") else "")


КОЛОНКИ = ["домен", "платформа", "головна_код", "головна_байт", "головна_заслон", "головна_секунд", "розділ_url",
           "розділ_заслон", "речей_на_сторінці", "кандидатів_карток", "пагінація", "картка_url", "картка_ld", "картка_og",
           "картка_ціна", "картка_характеристик", "картка_фото", "картка_розмірів", "картка_склад", "назва",
           "назва_російська", "мова_html", "hreflang", "sitemap", "products_json", "wc_store", "фіди", "мережа_json",
           "секунд", "помилки"]


def main(argv=None):
    п = argparse.ArgumentParser(description=ВЕРСІЯ)
    п.add_argument("--магазини", default="усі", help="усі — або домени через кому")
    п.add_argument("--старт", default=None, help="довільна стартова адреса (проба механіки на будь-якому сайті)")
    п.add_argument("--вихід", default="розвідка")
    п.add_argument("--паралельно", type=int, default=3)
    п.add_argument("--секунд-на-магазин", type=int, default=150)
    п.add_argument("--видимо", action="store_true", help="видиме вікно Chromium")
    п.add_argument("--без-підготовки", action="store_true", help="не перевіряти/не ставити playwright і Chromium")
    a = п.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa
        pass
    if not a.без_підготовки:
        _підготувати_playwright()
    if a.старт:
        магазини = [(домен_із(a.старт), a.старт)]
    elif a.магазини.strip() in ("усі", "all", ""):
        магазини = list(МАГАЗИНИ)
    else:
        хочу = {д.strip().lower().replace("www.", "") for д in a.магазини.split(",") if д.strip()}
        магазини = [(д, s) for д, s in МАГАЗИНИ if д in хочу]
        нема = хочу - {д for д, _ in магазини}
        if нема:
            лог("НЕ У СПИСКУ ВЛАСНИКА, пропускаю: %s" % ", ".join(sorted(нема)))
    лог("%s · магазинів %d · паралельно %d · бюджет %d с/магазин · тека %s" % (ВЕРСІЯ, len(магазини), a.паралельно,
                                                                                a.секунд_на_магазин, a.вихід))
    р = Розвідник(a.вихід, a.секунд_на_магазин, a.видимо, a.паралельно)
    asyncio.run(р.усі(магазини))
    лог("готово: %s" % р.зведення)


if __name__ == "__main__":
    main()
