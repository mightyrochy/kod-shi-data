# -*- coding: utf-8 -*-
"""ВИКОНАВЕЦЬ v1 · 2026-09-07 — тупий, інкрементний, з журналом. Читає рецепти.tsv, нічого не вгадує.

Запуск
  python3 виконавець.py                                   # усі рецепти з транспортом http/браузер (не «дім»)
  python3 виконавець.py --магазини vovk.com,25union.com.ua
  python3 виконавець.py --транспорт дім                    # на ноутбуці: сім заблокованих із дата-центру
  python3 виконавець.py --стеля 150 --секунд-на-магазин 900

Вихід
  сирі/<домен>.jsonl   — журнал: один JSON на адресу (url, хеш, дата, стан, бал, картка). Повторний запуск
                          пропускає вже взяті картки; дедлайн обмежує ніч, не каталог.
  сирі/<домен>.стан.json — курсор пошуку (розділи/сторінки, sitemap), помилки, лічильники.
  огляд/<домен>.jpg    — контактний аркуш: 6 карток із найвищим балом, фото + підпис — «подивитись очима».
  зведення_жнив.tsv    — рядок на магазин: карток, з них повних, середній бал, причини відмов.

ГЕЙТ ПОВНОТИ (рішення власника 07.09):
  Г1 зліпок — картка пишеться цілком: усі рядки «мітка: значення», весь текст картки, усі фото, усі розміри з
     наявністю, хлібні крихти, усі JSON-LD і og. Жнива не відбирають полів — відбирає складання.
  Г2 бал   — на кожній картці рахується бал інформації за КОРИСНІ_ПОЛЯ (поле ← рішення, яке воно змінює).
  Г3 поріг — картка нижче ПОРОГУ не існує для складання (стан «нижче_порогу»), але лишається в журналі.
  Г4 рецепт — якщо картки магазину мають блок характеристик у DOM, а зліпок узяв 0 рядків — це збій розбору:
     стан «неповна_розбірка», рецепт не може стати активним, поки такі є.
  Складання (окремий крок) бере спершу картки з найвищим балом; нижчі — лише коли покриття слота чи
  несхожість недостатні; нижче порогу — ніколи.
  Числові пороги — фольклорні константи до калібрування на стенді.
"""
import argparse, asyncio, csv, datetime, hashlib, json, os, re, sys, time, threading
from urllib.parse import urlparse, urljoin

ВЕРСІЯ = "виконавець v1 · 2026-09-07"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0.0.0 Safari/537.36")
assert UA.isascii()

# ── корисні поля: поле → (вага, рішення, яке воно змінює). Спільний список для жнив, складання і feed.py. ──
КОРИСНІ_ПОЛЯ = {
    "назва":          (1, "слот, тип речі"),
    "слот_шлях":      (2, "слот (хлібні крихти / категорія магазину)"),
    "фото":           (2, "показ; колір із фото, якщо не оголошений"),
    "фото_2плюс":     (1, "силует і деталі з другого ракурсу"),
    "колір":          (3, "палітра, контраст з обличчям"),
    "склад":          (3, "температура, матеріал, драпірування"),
    "тканина":        (1, "матеріал, формальність"),
    "розміри":        (2, "посадка, доступність"),
    "наявність":      (1, "чи можна купити зараз"),
    "опис_200":       (1, "крій і деталі для пояснення"),
    "характеристик_5":(2, "крій, довжина, деталі — структуровано"),
    "крій_ключі":     (2, "силует: довжина / рукав / виріз / талія / каблук / посадка"),
    "заміри_модель":  (2, "посадка й довжина на тілі (зріст моделі, заміри)"),
    "сезон":          (1, "температура"),
    "артикул":        (0, "ідентифікація (рішень не змінює)"),
    "догляд":         (0, "рішень не змінює — береться, бо є на картці"),
}
ПОРІГ = {"мін_бал": 8, "обовʼязково": ["назва", "фото"], "одне_з": [["колір", "склад"], ["розміри", "опис_200", "характеристик_5"]],
         "без_розмірів": re.compile(r"сумк|bag|аксесуар|ремін|belt|хустк|шарф|шапк|рукавич|прикрас|сережк|кольє|браслет|каблучк|окуляр|гаманц|клатч|рюкзак", re.I),
         "характеристик_мін_без_розмірів": 3}
# ↑ фольклорні константи: поріг 8 з максимуму 24; калібрувати на вердиктах стенду.

_ЧИСЛО = r"(?:\d{1,3}(?:[ \u00a0,]?\d{3})+|\d{3})(?:[.,]\d{2})?"
_ЦІНА = re.compile(r"(?<![\d.,])(?:₴|грн\.?|uah)\s?" + _ЧИСЛО + r"(?![\d])|(?<![\d.,])" + _ЧИСЛО + r"\s?(?:₴|грн\.?|uah)(?![\w])", re.I)
_ШУМ_РЯДКА = re.compile(r"режим роботи|кошик|пн[-–\s]|вт[-–\s]|сб[-–\s]|нд[-–\s]|тел|viber|telegram|instagram|facebook|"
                        r"\{|\}|fill|css|http|@|підпис|розсилк|знижк|акці|доставк|оплат|самовивіз|повернен|гарант|"
                        r"відповімо|працюємо|графік|адрес|e-?mail|пошт", re.I)
_КОЛІР_СЛОВО = re.compile(r"\b(чорн\w*|біл\w*|сір\w*|бежев\w*|синь\w*|син\w*|блакитн\w*|червон\w*|зелен\w*|рожев\w*|бордов\w*|"
                          r"коричнев\w*|молочн\w*|пісочн\w*|хакі|оливков\w*|гірчичн\w*|фіолетов\w*|бузков\w*|лавандов\w*|жовт\w*|"
                          r"помаранчев\w*|м'ятн\w*|бірюзов\w*|золот\w*|срібн\w*|кремов\w*|графіт\w*|кемел|карамел\w*|шоколадн\w*|"
                          r"пудров\w*|смарагдов\w*|теракот\w*|корал\w*|фуксі\w*|індиго|деним|електрик|марсала|айворі|екрю|"
                          r"мультиколор|принт|леопард|клітин\w*|смужк\w*|(?:темно|світло|ніжно|яскраво)-[а-яіїє]+|"
                          r"black|white|gr[ae]y|beige|blue|navy|red|green|pink|brown|milk|sand|khaki|olive|mustard|purple|"
                          r"lilac|lavender|yellow|orange|mint|turquoise|gold|silver|cream|graphite|camel|caramel|chocolate|"
                          r"powder|emerald|terracotta|coral|fuchsia|indigo|burgundy|ivory|ecru|coffee|nude|taupe)\b", re.I)
_SLUG_КОЛІР = {"chorn": "чорний", "bil": "білий", "sir": "сірий", "ser": "сірий", "bezh": "бежевий", "syn": "синій", "sin": "синій",
               "blakyt": "блакитний", "chervon": "червоний", "zelen": "зелений", "rozhev": "рожевий", "bordo": "бордовий",
               "korychn": "коричневий", "korichn": "коричневий", "moloch": "молочний", "pisoch": "пісочний", "khaki": "хакі",
               "olyvk": "оливковий", "girchych": "гірчичний", "fiolet": "фіолетовий", "buzk": "бузковий", "zhovt": "жовтий",
               "pomaranch": "помаранчевий", "biruz": "бірюзовий", "zolot": "золотий", "sribn": "срібний", "krem": "кремовий",
               "grafit": "графітовий", "kemel": "кемел", "karamel": "карамельний", "shokolad": "шоколадний", "pudr": "пудровий",
               "smaragd": "смарагдовий", "terakot": "теракотовий", "koral": "кораловий", "fuksi": "фуксія", "indigo": "індиго",
               "denim": "деним", "marsala": "марсала", "ivory": "айворі", "ekru": "екрю", "temno": "темно-", "svitlo": "світло-"}
_ВОЛОКНО = (r"(?:бавовн\w*|льон\w*|лляна|віскоз\w*|шовк\w*|вовн\w*|шерст\w*|кашемір\w*|поліестер\w*|поліест\w*|еластан\w*|"
            r"ліоцел\w*|модал\w*|тенсел\w*|поліамід\w*|нейлон\w*|акрил\w*|спандекс\w*|лайкр\w*|альпак\w*|мохер\w*|ангор\w*|"
            r"рамі|конопл\w*|купро|ацетат\w*|шкір\w*|замш\w*|гум\w*|поліуретан\w*|каучук\w*|текстил\w*|cotton|linen|"
            r"viscose|silk|wool|polyester|elastane|lyocell|modal|polyamide|nylon|acrylic|leather|suede)")
_СКЛАД = re.compile(r"\d{1,3}\s?%\s?" + _ВОЛОКНО + r"|" + _ВОЛОКНО + r"\s?[-–:]?\s?\d{1,3}\s?%", re.I)
_ТКАНИНА = re.compile(r"\b(бавовн\w*|льон\w*|лляна|віскоз\w*|шовк\w*|вовн\w*|кашемір\w*|трикотаж\w*|деним\w*|джинс\w*|"
                      r"поліестер\w*|еластан\w*|ліоцел\w*|модал\w*|тенсел\w*|замш\w*|шкір\w*|нубук\w*|атлас\w*|шифон\w*|"
                      r"креп\w*|твід\w*|велюр\w*|оксамит\w*|фланел\w*|футер\w*|кулір\w*|інтерлок\w*|плісе)\b", re.I)
_КРІЙ = re.compile(r"довжин|рукав|виріз|горловин|талі|посадк|каблук|підбор|силует|крій|фасон|застібк|підкладк|"
                   r"колір|розмір на моделі", re.I)
_МОДЕЛЬ = re.compile(r"(зріст|ріст)\s*модел|на моделі|параметри моделі|модель\s*одягнен|заміри|обхват|довжина виробу", re.I)
_СЕЗОН = re.compile(r"\b(демісезон\w*|зим\w*|літ\w*|весн\w*|осін\w*|всесезон\w*)\b", re.I)
_ДОГЛЯД = re.compile(r"пранн|прати|хімчист|прасув|догляд", re.I)
_РОСІЙСЬКА = re.compile(r"[ыэъё]")
_СЛУЖБОВЕ = re.compile(r"\.(css|js|svg|pdf|ico|xml|json|zip|mp4|woff2?|ttf)(\?|$)|/cdn-cgi/", re.I)
_ПАГІНАЦІЯ = re.compile(r"[?&]page=\d+|/page/\d+|/page-\d+|PAGEN_\d+=|[?&]p=\d+|[?&]start=\d+|[?&]offset=\d+", re.I)
_РОЗДІЛ_НЕ = re.compile(r"blog|news|novyn|about|pro-nas|o-nas|contact|kontakt|deliver|dostavk|oplat|payment|cart|checkout|"
                        r"login|account|wishlist|compare|lookbook|sertif|certif|gift|podarun|vakans|career|privacy|terms|"
                        r"offer|return|obmin|povern|faq|review|vidguk|brand|tel:|mailto:|javascript:|uhod|dogliad|kosmet|"
                        r"(?:^|[/-])(?:kids|dyt\w*|dit[iy]|child\w*|detsk\w*|men|man|cholov\w*|muzh\w*)(?:$|[/-])|"
                        r"про нас|контакт|доставк|оплат|блог|новин|відгук|вакансі|дитяч|чолові|подарунк|сертифікат|кошик|увійти|вхід", re.I)
_РОЗДІЛ_ТАК = re.compile(r"sukn|platt|plat[iy]|dress|bluz|blous|sorochk|shirt|spidn|yubk|skirt|shtan|bryuk|pants|trous|jeans|"
                         r"dzhins|zhaket|jacket|blazer|kardig|sweater|svetr|sviter|jumper|dzhemper|palto|coat|trench|kurtk|"
                         r"vzutt|obuv|shoes|tufl|cherevik|chobot|boot|sandal|sumk|bag|kostyum|suit|katalog|catalog|collection|"
                         r"odyag|odiag|clothing|aksesuar|accessor|zhinoch|women|верх|низ|сукн|плат|блуз|спідн|штан|взутт|сумк", re.I)

ВИТЯГ_ПОСИЛАНЬ = """() => Array.from(document.querySelectorAll('a[href]')).map(a => {
  const p = a.parentElement, g = p ? p.parentElement : null;
  const near = ((p && p.innerText) || '').slice(0, 200) + ' ' + ((g && g.innerText && g.innerText.length < 400) ? g.innerText : '');
  return {href: a.href, text: (a.innerText || '').trim().slice(0, 80), img: !!a.querySelector('img'), near: near.slice(0, 300)};
})"""

ЗЛІПОК_DOM = """() => {
  const T = e => (e && (e.innerText || e.textContent) || '').replace(/\\s+/g, ' ').trim();
  const rows = [];
  document.querySelectorAll('tr').forEach(tr => { const c = tr.querySelectorAll('td,th'); if (c.length === 2) rows.push([T(c[0]), T(c[1])]); });
  document.querySelectorAll('dl').forEach(dl => { const dt = dl.querySelectorAll('dt'), dd = dl.querySelectorAll('dd');
    for (let i = 0; i < Math.min(dt.length, dd.length); i++) rows.push([T(dt[i]), T(dd[i])]); });
  document.querySelectorAll('li, p, div, span').forEach(el => { if (el.children.length <= 3) { const t = T(el);
    if (t.length > 4 && t.length < 160) { const m = t.match(/^([^:]{2,40}):\\s*(.{1,120})$/); if (m) rows.push([m[1].trim(), m[2].trim()]); } } });
  const imgs = [...document.querySelectorAll('img, source')].flatMap(i => [i.currentSrc, i.src, i.dataset && i.dataset.src, i.srcset, i.dataset && i.dataset.srcset])
    .filter(Boolean).flatMap(s => s.split(',').map(x => x.trim().split(' ')[0])).filter(s => /\\.(jpe?g|webp|png)/i.test(s) && !/logo|icon|sprite|payment|visa|master|flag|banner|placeholder|pixel|1x1/i.test(s));
  let main0 = document.body, best = 0;
  document.querySelectorAll('main, [role=main], #content, .product-page, .product, .card-product, #product, .product-detail, .product__info, [itemtype*=Product]').forEach(e => {
    const n = (e.textContent || '').length; if (n > best) { best = n; main0 = e; } });
  if (best < 500) main0 = document.body;
  const main = main0.cloneNode(true); main.querySelectorAll('script, style, noscript, header, footer, nav').forEach(e => e.remove());
  const sizeRe = /^(XXS|XS|S|M|L|XL|XXL|XXXL|3XL|4XL|5XL|\\d{2}([-\\/]\\d{2})?|ONE ?SIZE|UNI|універсальн\\w*|один розмір)$/i;
  const sizes = [];
  document.querySelectorAll('select option, button, label, a, span, li, div').forEach(e => { if (e.children.length <= 1) { const t = T(e);
    if (sizeRe.test(t)) sizes.push({р: t.toUpperCase(), нема: !!(e.disabled || /disabled|out-of-stock|outofstock|sold|nostock|unavailable|not-available|нема|немає/i.test(e.className + ' ' + (e.title || '')))}); } });
  const crumbs = [...document.querySelectorAll('[class*=breadcrumb] a, [class*=breadcrumb] span, nav[aria-label*=read] a, [itemtype*=BreadcrumbList] [itemprop=name]')].map(T).filter(Boolean);
  const opts = [...document.querySelectorAll('[class*=color] [title], [class*=colour] [title], [data-color], [class*=color] option')].map(e => e.title || e.dataset.color || T(e)).filter(Boolean);
  return {h1: T(document.querySelector('h1')), title: document.title, rows, imgs: [...new Set(imgs)], text: (main.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 30000),
          sizes, crumbs, opts: [...new Set(opts)].slice(0, 30), has_table: !!document.querySelector('table, dl, [class*=characteristic], [class*=attribute], [class*=params], [class*=specif]')};
}"""


def лог(т):
    print(time.strftime("%H:%M:%S"), т, flush=True)


def домен_із(url):
    return (urlparse(url).netloc or "").lower().replace("www.", "")


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


def ог(html):
    вих = {}
    for м in re.finditer(r'<meta[^>]+(?:property|name)=["\']((?:og|product|twitter):[^"\']+)["\'][^>]+content=["\']([^"\']*)', html or "", re.I):
        вих.setdefault(м.group(1), м.group(2))
    return вих


def ld_product(html):
    for в in json_ld(html):
        кандидати = [в] + [е for е in (в.get("@graph") or []) if isinstance(е, dict)] if isinstance(в, dict) else []
        for е in кандидати:
            т = е.get("@type")
            if (isinstance(т, list) and any("Product" in str(x) for x in т)) or (isinstance(т, str) and "Product" in т):
                return е
    return None


def бал_інформації(к):
    """← картка з полями зліпка. → (бал, список наявних полів, чи вище порога)."""
    є = []
    рядки = {(м or "").lower(): (з or "") for м, з in к.get("характеристики") or []}
    текст = (к.get("текст") or "") + " " + " ".join(f"{м} {з}" for м, з in рядки.items())
    if к.get("назва"): є.append("назва")
    if к.get("слот_шлях"): є.append("слот_шлях")
    if к.get("фото"): є.append("фото")
    if len(к.get("фото") or []) >= 2: є.append("фото_2плюс")
    if к.get("колір") or к.get("колір_hex"): є.append("колір")
    if к.get("склад"): є.append("склад")
    if _ТКАНИНА.search(текст): є.append("тканина")
    if к.get("розміри"): є.append("розміри")
    if any("нема" in р for р in к.get("розміри") or []) or к.get("наявність") is not None: є.append("наявність")
    if len(к.get("опис") or "") >= 200: є.append("опис_200")
    if len(к.get("характеристики") or []) >= 5: є.append("характеристик_5")
    elif len(к.get("характеристики") or []) >= ПОРІГ["характеристик_мін_без_розмірів"] and ПОРІГ["без_розмірів"].search((к.get("назва") or "") + " " + (к.get("слот_шлях") or "")):
        є.append("характеристик_5")                   # сумки/аксесуари: розмірів нема за природою, 3 рядки — достатньо
    if sum(1 for м in рядки if _КРІЙ.search(м)) >= 2: є.append("крій_ключі")
    if _МОДЕЛЬ.search(текст): є.append("заміри_модель")
    if _СЕЗОН.search(" ".join(рядки.keys()) + " " + " ".join(рядки.values())): є.append("сезон")
    if к.get("артикул"): є.append("артикул")
    if _ДОГЛЯД.search(текст): є.append("догляд")
    бал = sum(КОРИСНІ_ПОЛЯ[п][0] for п in є)
    вище = (бал >= ПОРІГ["мін_бал"] and all(п in є for п in ПОРІГ["обовʼязково"])
            and all(any(п in є for п in група) for група in ПОРІГ["одне_з"]))
    return бал, є, вище


def _колір_із(рядки, назва, opts):
    """→ (назва кольору, hex). Порядок: рядок «Колір» → слово в назві → опція, якщо це слово-колір або hex."""
    hex_ = next((o for o in opts or [] if re.fullmatch(r"#?[0-9a-fA-F]{6}", o)), "")
    for м, з in рядки:
        if re.search(r"(^|\s)(колір|кольор|color|colour)", (м or "").strip(), re.I) and з and not _ШУМ_РЯДКА.search(з):
            return з.strip()[:60], hex_
    м = _КОЛІР_СЛОВО.search(назва or "")
    if м:
        return м.group(0), hex_
    for o in opts or []:
        if _КОЛІР_СЛОВО.search(o):
            return o[:60], hex_
    return "", hex_


def _колір_зі_slug(url):
    """Останній засіб: колір із транслітерованого slug магазину (напр. …_vrokhutro_chorniy.html → чорний)."""
    шлях = urlparse(url).path.lower()
    знайдені = [укр for lat, укр in _SLUG_КОЛІР.items() if re.search(r"(?:^|[-_/])" + lat, шлях)]
    знайдені = [x for x in знайдені if not x.endswith("-")] or []
    return знайдені[0] if знайдені else ""


def картка_з_dom(url, html, dom):
    """Г1: повний зліпок картки з DOM браузера + HTML."""
    ld = ld_product(html) or {}
    o = ог(html)
    рядки = [(м, з) for м, з in dom.get("rows") or [] if м and з and len(м) < 60 and not _ШУМ_РЯДКА.search(м) and not re.search(r"\d{1,2}:\d{2}", з)]
    # дедуп рядків, зберігаючи порядок
    бач, рядки2 = set(), []
    for м, з in рядки:
        к = (м.lower(), з.lower())
        if к not in бач:
            бач.add(к); рядки2.append((м, з))
    назва = dom.get("h1") or ld.get("name") or o.get("og:title") or ""
    текст = dom.get("text") or ""
    опис = ld.get("description") or o.get("og:description") or ""
    м = re.search(r"(?:опис|описание|description)\s*(.{200,3000}?)(?:характеристик|склад|доставк|оплат|$)", текст, re.I | re.S)
    if м and len(м.group(1)) > len(опис):
        опис = м.group(1).strip()
    фото = [urljoin(url, x) for x in dom.get("imgs") or []]
    if ld.get("image"):
        for x in (ld["image"] if isinstance(ld["image"], list) else [ld["image"]]):
            if isinstance(x, str) and x not in фото: фото.insert(0, x)
            elif isinstance(x, dict) and x.get("url") and x["url"] not in фото: фото.insert(0, x["url"])
    if o.get("og:image") and o["og:image"] not in фото:
        фото.insert(0, urljoin(url, o["og:image"]))
    розміри = sorted({(s["р"] + (" нема" if s.get("нема") else "")) for s in dom.get("sizes") or []})
    склад = sorted({x.strip() for x in _СКЛАД.findall(текст)})[:12]
    ціна = (_ЦІНА.search(текст) or [None])
    ціна = ціна.group(0) if hasattr(ціна, "group") else ""
    склад = [x for x in склад if not re.search(r"від вартості|від ціни|від суми|знижк", x, re.I)]
    for м, з in рядки2:                               # взуття/сумки: «Матеріал верху: шкіра» — це склад без відсотків
        if re.search(r"матеріал|склад|тканин|верх|підкладк|підошв|устілк", м, re.I) and _ТКАНИНА.search(з) and len(з) < 80:
            склад.append(f"{м.strip(': ')}: {з.strip()}")
    склад = list(dict.fromkeys(склад))[:14]
    колір, колір_hex = _колір_із(рядки2, назва, dom.get("opts"))
    колір_джерело = "картка" if колір else ""
    if isinstance(ld.get("color"), str) and not колір:
        колір, колір_джерело = ld["color"][:60], "ld"
    if not колір:
        колір = _колір_зі_slug(url); колір_джерело = "slug" if колір else ""
    if ld.get("offers"):
        of0 = ld["offers"] if isinstance(ld["offers"], dict) else (ld["offers"] or [{}])[0]
        if isinstance(of0, dict) and of0.get("price"):
            ціна = f"{of0['price']} {of0.get('priceCurrency', '')}".strip()
    к = {"url": url, "назва": назва[:200], "слот_шлях": " > ".join(dict.fromkeys(dom.get("crumbs") or []))[:200] or (ld.get("category") or "")[:200],
         "колір": колір, "колір_hex": колір_hex, "колір_джерело": колір_джерело, "склад": склад, "розміри": розміри, "наявність": None,
         "ціна": ціна, "опис": опис[:4000], "характеристики": рядки2[:120], "фото": фото[:24],
         "артикул": (ld.get("sku") or ld.get("mpn") or next((з for м, з in рядки2 if re.search(r"артикул|код товару|sku|модель", м, re.I)), ""))[:60],
         "бренд": (ld.get("brand", {}) or {}).get("name", "") if isinstance(ld.get("brand"), dict) else str(ld.get("brand") or "")[:60],
         "ld": ld, "og": o, "текст": текст[:12000], "опції_кольору": dom.get("opts") or [], "має_таблицю": bool(dom.get("has_table")),
         "назва_російська": bool(_РОСІЙСЬКА.search(назва))}
    if ld.get("offers"):
        of = ld["offers"] if isinstance(ld["offers"], dict) else (ld["offers"] or [{}])[0]
        if isinstance(of, dict) and of.get("availability"):
            к["наявність"] = "InStock" in str(of["availability"])
    return к


def картка_з_shopify(база, p):
    опис = re.sub(r"<[^>]+>", " ", p.get("body_html") or "")
    опис = re.sub(r"\s+", " ", опис).strip()
    варіанти = p.get("variants") or []
    опції = {о.get("name", "").lower(): о.get("values") or [] for о in p.get("options") or []}
    розміри = [str(v.get("option1") or v.get("title")) + ("" if v.get("available", True) else " нема") for v in варіанти]
    колір = ""
    for ім, зн in опції.items():
        if re.search(r"колір|color|colour", ім): колір = ", ".join(зн)[:60]
    ряд = [("Тип", p.get("product_type") or ""), ("Бренд", p.get("vendor") or ""), ("Теги", ", ".join(p.get("tags") or []) if isinstance(p.get("tags"), list) else str(p.get("tags") or ""))]
    ряд += [(ім, ", ".join(зн)) for ім, зн in опції.items()]
    return {"url": f"{база}/products/{p.get('handle')}", "назва": p.get("title") or "", "слот_шлях": p.get("product_type") or "",
            "колір": колір or _колір_із([], p.get("title"), [])[0], "склад": sorted({x.strip() for x in _СКЛАД.findall(опис)})[:12],
            "розміри": sorted(set(розміри)), "наявність": any(v.get("available", True) for v in варіанти) if варіанти else None,
            "ціна": (варіанти[0].get("price") if варіанти else ""), "опис": опис[:4000], "характеристики": [(м, з) for м, з in ряд if з],
            "фото": [i.get("src") for i in p.get("images") or [] if i.get("src")][:24], "артикул": (варіанти[0].get("sku") if варіанти else "") or "",
            "бренд": p.get("vendor") or "", "ld": {}, "og": {}, "текст": опис[:12000], "сире_json": p, "має_таблицю": True,
            "назва_російська": bool(_РОСІЙСЬКА.search(p.get("title") or ""))}


def картка_з_woo(база, p):
    опис = re.sub(r"<[^>]+>", " ", (p.get("description") or "") + " " + (p.get("short_description") or ""))
    опис = re.sub(r"\s+", " ", опис).strip()
    атр = [(a.get("name", ""), ", ".join(t.get("name", "") for t in a.get("terms") or [])) for a in p.get("attributes") or []]
    колір = next((з for м, з in атр if re.search(r"колір|color|colour", м, re.I)), "")
    розміри = next(([x.strip() for x in з.split(",")] for м, з in атр if re.search(r"розмір|size", м, re.I)), [])
    ряд = атр + [("Категорії", ", ".join(c.get("name", "") for c in p.get("categories") or [])), ("Теги", ", ".join(t.get("name", "") for t in p.get("tags") or []))]
    return {"url": p.get("permalink") or f"{база}/?p={p.get('id')}", "назва": p.get("name") or "", "слот_шлях": " > ".join(c.get("name", "") for c in p.get("categories") or []),
            "колір": колір or _колір_із([], p.get("name"), [])[0], "склад": sorted({x.strip() for x in _СКЛАД.findall(опис)})[:12],
            "розміри": sorted(set(розміри)), "наявність": p.get("is_in_stock"), "ціна": ((p.get("prices") or {}).get("price") or ""),
            "опис": опис[:4000], "характеристики": [(м, з) for м, з in ряд if з], "фото": [i.get("src") for i in p.get("images") or [] if i.get("src")][:24],
            "артикул": p.get("sku") or "", "бренд": "", "ld": {}, "og": {}, "текст": опис[:12000], "сире_json": p, "має_таблицю": True,
            "назва_російська": bool(_РОСІЙСЬКА.search(p.get("name") or ""))}


def завершити(к):
    """Г2+Г3+Г4: бал, поріг, стан."""
    бал, є, вище = бал_інформації(к)
    к["бал"], к["поля_є"] = бал, є
    if к.get("має_таблицю") and not к.get("характеристики") and "сире_json" not in к:
        стан = "неповна_розбірка"                       # Г4: блок є, рядків 0 — це збій розбору, не бідна картка
    elif к.get("назва_російська"):
        стан = "російська_назва"
    elif not вище:
        стан = "нижче_порогу"
    else:
        стан = "картка"
    return стан


class Виконавець:
    def __init__(self, a):
        self.a = a
        os.makedirs("сирі", exist_ok=True); os.makedirs("огляд", exist_ok=True)
        self.замок = threading.Lock()
        self.зведення = "зведення_жнив.tsv"
        if not os.path.exists(self.зведення):
            open(self.зведення, "w", encoding="utf-8").write("дата\tдомен\tсімейство\tтранспорт\tадрес_знайдено\tвідкрито\tкарток\tнижче_порогу\tнеповна_розбірка\tросійських\tне_картка\tзбоїв\tсередній_бал\tсекунд\tнотатка\n")

    # ── журнал ──
    def _журнал(self, домен):
        ш = f"сирі/{домен}.jsonl"
        взято = {}
        if os.path.exists(ш):
            for р in open(ш, encoding="utf-8"):
                try:
                    з = json.loads(р); взято[з["url"]] = з.get("стан")
                except Exception:  # noqa
                    pass
        return ш, взято

    def _стан(self, домен):
        ш = f"сирі/{домен}.стан.json"
        return ш, (json.load(open(ш, encoding="utf-8")) if os.path.exists(ш) else {"розділи": {}, "sitemap": [], "помилки": []})

    def _пиши(self, ш, зап):
        with self.замок, open(ш, "a", encoding="utf-8") as f:
            f.write(json.dumps(зап, ensure_ascii=False) + "\n")

    async def усі(self, рецепти):
        from playwright.async_api import async_playwright
        сем = asyncio.Semaphore(self.a.паралельно)
        async with async_playwright() as p:
            браузер = await p.chromium.launch(headless=not self.a.видимо, args=["--disable-blink-features=AutomationControlled", "--lang=uk-UA"])
            try:
                await asyncio.gather(*[self._магазин(браузер, р, сем) for р in рецепти])
            finally:
                await браузер.close()

    async def _магазин(self, браузер, р, сем):
        async with сем:
            домен, t0 = р["домен"], time.time()
            л = {"адрес": 0, "відкрито": 0, "картка": 0, "нижче_порогу": 0, "неповна_розбірка": 0, "російська_назва": 0, "не_картка": 0, "збій": 0, "бали": [], "нотатка": ""}
            контекст = await браузер.new_context(user_agent=UA, locale="uk-UA", timezone_id="Europe/Kyiv", viewport={"width": 1366, "height": 900},
                                                 ignore_https_errors=True, extra_http_headers={"Accept-Language": "uk-UA,uk;q=0.9,en;q=0.7"})
            try:
                await asyncio.wait_for(self._жнива(контекст, р, л), timeout=self.a.секунд_на_магазин)
            except asyncio.TimeoutError:
                л["нотатка"] = f"бюджет {self.a.секунд_на_магазин} с вичерпано"
            except Exception as e:  # noqa
                л["нотатка"] = "збій: " + str(e).splitlines()[0][:160]
            finally:
                try:
                    await self._огляд(контекст, домен)
                except Exception as e:  # noqa
                    л["нотатка"] += " | огляд: " + str(e).splitlines()[0][:80]
                try:
                    await контекст.close()
                except Exception:  # noqa
                    pass
                сер = round(sum(л["бали"]) / len(л["бали"]), 1) if л["бали"] else ""
                with self.замок, open(self.зведення, "a", encoding="utf-8") as f:
                    л["нотатка"] = re.sub(r"[\t\r\n]+", " ", л["нотатка"])
                    f.write("\t".join(str(x) for x in [datetime.date.today(), домен, р["сімейство"], р["транспорт"], л["адрес"], л["відкрито"], л["картка"],
                                                       л["нижче_порогу"], л["неповна_розбірка"], л["російська_назва"], л["не_картка"], л["збій"], сер,
                                                       round(time.time() - t0), л["нотатка"]]) + "\n")
                лог(f"{домен:<24} карток {л['картка']} · нижче порогу {л['нижче_порогу']} · неповна розбірка {л['неповна_розбірка']} · "
                    f"рос. {л['російська_назва']} · не картка {л['не_картка']} · збоїв {л['збій']} · бал {сер} · {round(time.time() - t0)} с {л['нотатка']}")

    async def _get(self, контекст, url, тайм=30_000):
        r = await контекст.request.get(url, timeout=тайм, max_redirects=4, headers={"Accept": "application/json, text/xml, text/html;q=0.8"})
        return r.status, await r.text()

    # ── сімейства ──
    async def _жнива(self, контекст, р, л):
        сім = р["сімейство"]
        база = р["старт"].rstrip("/")
        корінь = "%s://%s" % (urlparse(р["старт"]).scheme, urlparse(р["старт"]).netloc)
        ш, взято = self._журнал(р["домен"])
        if сім in ("shopify", "woo"):
            await self._json_сімейство(контекст, р, л, ш, взято, корінь)
            return
        if сім == "api":
            лог(f"{р['домен']}: API з рецепта ({р['пошук'][:60]}) ще не підключено — йду списками")
            л["нотатка"] = "api→список; "
        адреси = await (self._horoshop_адреси(контекст, р, л, корінь) if сім == "horoshop" else self._список_адреси(контекст, р, л, корінь))
        if сім != "horoshop" and (len(адреси) < 30 or "sitemap" in (р.get("пошук") or "")):
            з_мапи = await self._sitemap_адреси(контекст, р, л, корінь)
            л["нотатка"] += f"sitemap +{len(з_мапи)}; "
            адреси = list(dict.fromkeys(адреси + з_мапи))
        л["адрес"] = len(адреси)
        сторінка = await контекст.new_page()
        await сторінка.route("**/*", lambda route: route.abort() if route.request.resource_type in ("image", "media", "font") else route.continue_())
        n = 0
        for url in адреси:
            if url in взято and взято[url] != "збій":
                continue
            if n >= self.a.стеля:
                л["нотатка"] += f"стеля {self.a.стеля}; "
                break
            n += 1
            await self._картка(сторінка, р, л, ш, url)
            await сторінка.wait_for_timeout(int(self.a.пауза * 1000))

    async def _json_сімейство(self, контекст, р, л, ш, взято, корінь):
        n = 1
        шаблон = р["пошук"].replace("per_page=100", "per_page=50")
        префікси = [""] + ([р["мова"].rstrip("/")] if р.get("мова") and р["мова"] != "/" else []) + ["/uk", "/ua"]
        while n <= 120:
            j = None
            for пр in префікси:
                url = корінь + пр + шаблон.replace("{n}", str(n))
                try:
                    код, т = await self._get(контекст, url, тайм=90_000)
                    j = json.loads(т); break
                except Exception as e:  # noqa
                    останнє = f"{url[:70]} → {str(e)[:50]} | тіло: {(т if 'т' in dir() else '')[:60]!r}"
                    if n > 1: break                        # далі першої сторінки префікси не перебираємо
            if j is None:
                л["збій"] += 1; л["нотатка"] += f"стор. {n}: {останнє}; "; break
            префікси = [url.replace(корінь, "", 1).replace(шаблон.replace("{n}", str(n)), "")]
            речі = j.get("products") if isinstance(j, dict) else j
            if not речі:
                if код != 200 and n == 1:
                    л["збій"] += 1; л["нотатка"] += f"{код} на {url[:60]}; "
                break
            for p in речі:
                к = картка_з_shopify(корінь, p) if р["сімейство"] == "shopify" else картка_з_woo(корінь, p)
                л["адрес"] += 1
                if к["url"] in взято:
                    continue
                л["відкрито"] += 1
                стан = завершити(к)
                л[стан] = л.get(стан, 0) + 1; л["бали"].append(к["бал"])
                self._пиши(ш, {"url": к["url"], "хеш": hashlib.md5(json.dumps(p, sort_keys=True).encode()).hexdigest()[:12],
                               "дата": datetime.date.today().isoformat(), "стан": стан, "бал": к["бал"], "поля_є": к["поля_є"], "картка": к})
                if л["відкрито"] >= self.a.стеля:
                    л["нотатка"] += f"стеля {self.a.стеля}; "; return
            n += 1

    async def _horoshop_адреси(self, контекст, р, л, корінь):
        _, стан = self._стан(р["домен"])
        адреси = []
        try:
            код, т = await self._get(контекст, корінь + "/sitemap.xml")
            мапи = [x for x in re.findall(r"<loc>\s*([^<\s]+)", т) if "catalog-sitemap" in x] or [корінь + f"/content/export/{р['домен']}/catalog-sitemap.xml"]
            for м in мапи:
                код, т = await self._get(контекст, м)
                адреси += re.findall(r"<loc>\s*([^<\s]+)", т)
            стан["sitemap"] = мапи
        except Exception as e:  # noqa
            л["нотатка"] += "sitemap: " + str(e)[:80] + "; "
        рх = re.compile(р["річ_regex"]) if р.get("річ_regex") else None
        адреси = [a for a in dict.fromkeys(адреси) if not _СЛУЖБОВЕ.search(a) and (not рх or рх.search(urlparse(a).path))]
        json.dump(стан, open(f"сирі/{р['домен']}.стан.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return адреси

    async def _sitemap_адреси(self, контекст, р, л, корінь):
        """Усі loc із sitemap (індекс → до 12 підмап); з regex речі — лише збіги, без нього — все, крім явного сміття (картку відсіє гейт)."""
        рх = re.compile(р["річ_regex"]) if р.get("річ_regex") else None
        адреси = []
        try:
            код, т = await self._get(контекст, корінь + "/robots.txt")
            мапи = re.findall(r"(?im)^sitemap:\s*(\S+)", т) if код == 200 else []
            мапи = мапи or [корінь + "/sitemap.xml"]
            черга, бачені = list(мапи), set()
            while черга and len(бачені) < 12:
                м = черга.pop(0)
                if м in бачені: continue
                бачені.add(м)
                код, т = await self._get(контекст, м)
                if код != 200: continue
                loc = re.findall(r"<loc>\s*([^<\s]+)", т)
                if "<sitemapindex" in т:
                    черга += [x for x in loc if not re.search(r"image|news|blog|video", x, re.I)]
                else:
                    адреси += loc
        except Exception as e:  # noqa
            л["нотатка"] += "sitemap: " + str(e)[:60] + "; "
        вих = []
        for a in dict.fromkeys(адреси):
            if домен_із(a) != р["домен"] or _СЛУЖБОВЕ.search(a) or _РОЗДІЛ_НЕ.search(a) or _ПАГІНАЦІЯ.search(a) or "/filter" in a:
                continue
            if рх and not рх.search(urlparse(a).path + ("?" + urlparse(a).query if urlparse(a).query else "")):
                continue
            if р.get("мова") and р["мова"] != "/" and р["мова"].strip("/") not in urlparse(a).path.split("/"):
                continue
            вих.append(a)
        return вих[:3000]

    async def _список_адреси(self, контекст, р, л, корінь):
        """Розділи з меню стартової → сторінки з пагінацією → посилання з картинкою і ціною поруч."""
        ш_стан, стан = self._стан(р["домен"])
        сторінка = await контекст.new_page()
        await сторінка.route("**/*", lambda route: route.abort() if route.request.resource_type in ("image", "media", "font") else route.continue_())
        адреси, розділи = [], []
        try:
            await сторінка.goto(р["старт"], wait_until="domcontentloaded", timeout=40_000)
            try: await сторінка.wait_for_load_state("networkidle", timeout=10_000)
            except Exception: pass  # noqa
            пос = await сторінка.evaluate(ВИТЯГ_ПОСИЛАНЬ)
            бали = {}
            for п in пос:
                u = п["href"].split("#")[0]
                if домен_із(u) != р["домен"] or _СЛУЖБОВЕ.search(u) or _РОЗДІЛ_НЕ.search(u) or _РОЗДІЛ_НЕ.search(п["text"]) or _ПАГІНАЦІЯ.search(u) or "?" in u or "/filter" in u:
                    continue
                шлях = urlparse(u).path
                if шлях in ("", "/") or п["img"] or _ЦІНА.search(п["near"] or ""):
                    continue
                б = (3 if _РОЗДІЛ_ТАК.search(п["text"] + " " + шлях) else 0) - (1 if len([x for x in шлях.split("/") if x]) >= 3 else 0)
                if б > 0: бали[u] = max(бали.get(u, 0), б)
            розділи = [u for u, _ in sorted(бали.items(), key=lambda x: (-x[1], len(x[0])))][:self.a.розділів]
            if р.get("мова") and р["мова"] != "/":
                розділи = [u for u in розділи if р["мова"].strip("/") in urlparse(u).path.split("/")] or розділи
            рх = re.compile(р["річ_regex"]) if р.get("річ_regex") else None
            for роз in розділи:
                було = стан["розділи"].get(роз)
                if isinstance(було, dict) and було.get("стан") == "готово" and було.get("адреси") is not None \
                   and (datetime.date.today() - datetime.date.fromisoformat(було.get("дата", "2000-01-01"))).days < 7:
                    адреси += було["адреси"]                    # обхід свіжий — беремо збережені адреси, картки добере журнал
                    continue
                адреси_розділу = []
                сторінок = 0
                url = роз
                бач = set()
                while url and сторінок < self.a.сторінок:
                    сторінок += 1
                    try:
                        await сторінка.goto(url, wait_until="domcontentloaded", timeout=40_000)
                        try: await сторінка.wait_for_load_state("networkidle", timeout=6_000)
                        except Exception: pass  # noqa
                        пос = await сторінка.evaluate(ВИТЯГ_ПОСИЛАНЬ)
                    except Exception as e:  # noqa
                        л["збій"] += 1; стан["помилки"].append(f"{url}: {str(e)[:80]}"); break
                    нові = 0
                    for п in пос:
                        u = п["href"].split("#")[0]
                        if домен_із(u) != р["домен"] or _СЛУЖБОВЕ.search(u) or _ПАГІНАЦІЯ.search(u) or "/filter" in u or u in бач:
                            continue
                        схоже = (п["img"] and _ЦІНА.search(п["near"] or "")) or (рх and рх.search(urlparse(u).path + ("?" + urlparse(u).query if urlparse(u).query else "")))
                        if схоже and not (рх and not рх.search(urlparse(u).path + ("?" + urlparse(u).query if urlparse(u).query else ""))):
                            бач.add(u); адреси.append(u); адреси_розділу.append(u); нові += 1
                    # наступна сторінка: посилання з пагінацією, номер більший за поточний
                    наст = None
                    for п in пос:
                        m = _ПАГІНАЦІЯ.search(п["href"])
                        if m and домен_із(п["href"]) == р["домен"]:
                            num = int(re.findall(r"\d+", m.group(0))[-1])
                            if num == сторінок + 1: наст = п["href"]; break
                    url = наст if нові else None
                стан["розділи"][роз] = {"стан": "готово" if not url else f"стор.{сторінок}", "адреси": адреси_розділу,
                                        "дата": datetime.date.today().isoformat()}
        except Exception as e:  # noqa
            л["нотатка"] += "пошук: " + str(e).splitlines()[0][:80] + "; "
        finally:
            await сторінка.close()
            стан["розділи_знайдено"] = розділи
            json.dump(стан, open(ш_стан, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return list(dict.fromkeys(адреси))

    async def _картка(self, сторінка, р, л, ш, url):
        зап = {"url": url, "дата": datetime.date.today().isoformat()}
        try:
            r = await сторінка.goto(url, wait_until="domcontentloaded", timeout=35_000)
            try: await сторінка.wait_for_load_state("networkidle", timeout=4_000)
            except Exception: pass  # noqa
            html = await сторінка.content()
            л["відкрито"] += 1
            if re.search(r"cf-chl|challenge-platform|Just a moment|Attention Required|перевірка браузера", html[:8000], re.I) or (r and r.status in (403, 429, 503)):
                л["заслон"] = л.get("заслон", 0) + 1
                зап["стан"], зап["код"] = "заслон", (r.status if r else None); self._пиши(ш, зап)
                await сторінка.wait_for_timeout(15_000)
                if л["заслон"] >= 3:
                    raise RuntimeError("заслон Cloudflare тричі поспіль → транспорт «дім»")
                return
            л["заслон"] = 0
            if (r and r.status >= 400) or len(html) < 1500:
                зап["стан"], зап["код"] = "збій", (r.status if r else None); л["збій"] += 1
                self._пиши(ш, зап); return
            dom = await сторінка.evaluate(ЗЛІПОК_DOM)
            к = картка_з_dom(сторінка.url, html, dom)
            # це взагалі картка? назва + (ціна або ld Product або og product)
            if not (к["назва"] and (к["ціна"] or к["ld"] or (к["og"].get("og:type") or "").startswith("product"))):
                зап["стан"] = "не_картка"; л["не_картка"] += 1; self._пиши(ш, зап); return
            стан = завершити(к)
            л[стан] = л.get(стан, 0) + 1; л["бали"].append(к["бал"])
            зап.update({"хеш": hashlib.md5(html.encode("utf-8", "replace")).hexdigest()[:12], "стан": стан, "бал": к["бал"], "поля_є": к["поля_є"], "картка": к})
            self._пиши(ш, зап)
        except Exception as e:  # noqa
            зап["стан"], зап["помилка"] = "збій", str(e).splitlines()[0][:160]; л["збій"] += 1
            self._пиши(ш, зап)

    async def _огляд(self, контекст, домен):
        """Контактний аркуш 3×2: шість карток з найвищим балом — фото + назва/колір/бал. Для очей."""
        ш = f"сирі/{домен}.jsonl"
        if not os.path.exists(ш):
            return
        картки = []
        for р in open(ш, encoding="utf-8"):
            try:
                з = json.loads(р)
                if з.get("стан") == "картка" and з.get("картка", {}).get("фото"): картки.append(з)
            except Exception:  # noqa
                pass
        картки = sorted(картки, key=lambda з: -з["бал"])[:6]
        if not картки:
            return
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
        except ImportError:
            return
        аркуш = Image.new("RGB", (3 * 360, 2 * 480), "white"); d = ImageDraw.Draw(аркуш)
        try:
            шрифт = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
        except Exception:  # noqa
            шрифт = ImageFont.load_default()
        for i, з in enumerate(картки):
            x, y = (i % 3) * 360, (i // 3) * 480
            try:
                r = await контекст.request.get(з["картка"]["фото"][0], timeout=20_000)
                im = Image.open(io.BytesIO(await r.body())).convert("RGB"); im.thumbnail((340, 380)); аркуш.paste(im, (x + 10, y + 10))
            except Exception as e:  # noqa
                d.text((x + 10, y + 10), "фото не завантажилось", fill="red", font=шрифт)
            к = з["картка"]
            d.text((x + 10, y + 396), (к["назва"] or "")[:40], fill="black", font=шрифт)
            d.text((x + 10, y + 418), f"{к.get('колір','')[:18]} · {к.get('ціна','')[:12]} · бал {з['бал']}", fill="black", font=шрифт)
            d.text((x + 10, y + 440), (к.get("слот_шлях") or "")[:44], fill="gray", font=шрифт)
        аркуш.save(f"огляд/{домен}.jpg", quality=80)


def читати_рецепти(шлях):
    з = list(csv.DictReader(open(шлях, encoding="utf-8"), delimiter="\t"))
    for р in з:
        р["старт"] = р.get("старт") or ""
    return з


def main(argv=None):
    п = argparse.ArgumentParser(description=ВЕРСІЯ)
    п.add_argument("--рецепти", default="рецепти.tsv")
    п.add_argument("--магазини", default="усі")
    п.add_argument("--транспорт", default="http,браузер", help="які транспорти брати: http,браузер | дім")
    п.add_argument("--паралельно", type=int, default=3)
    п.add_argument("--секунд-на-магазин", type=int, default=900)
    п.add_argument("--стеля", type=int, default=300, help="карток на магазин за один запуск")
    п.add_argument("--розділів", type=int, default=12)
    п.add_argument("--сторінок", type=int, default=6, help="сторінок пагінації на розділ")
    п.add_argument("--пауза", type=float, default=0.8)
    п.add_argument("--видимо", action="store_true")
    a = п.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa
        pass
    рецепти = читати_рецепти(a.рецепти)
    тр = {x.strip() for x in a.транспорт.split(",")}
    рецепти = [р for р in рецепти if р["транспорт"] in тр]
    if a.магазини.strip() not in ("усі", "all", ""):
        хочу = {x.strip().lower() for x in a.магазини.split(",")}
        рецепти = [р for р in рецепти if р["домен"] in хочу]
    if not all(р.get("старт") for р in рецепти):
        # стартові адреси — зі списку власника в розвідка.py, якщо в рецептах колонки «старт» нема
        try:
            import importlib.util
            sp = importlib.util.spec_from_file_location("розвідка", os.path.join(os.path.dirname(os.path.abspath(__file__)), "розвідка.py"))
            m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
            старти = dict(m.МАГАЗИНИ)
            for р in рецепти:
                р["старт"] = р.get("старт") or старти.get(р["домен"], "https://" + р["домен"] + "/")
        except Exception as e:  # noqa
            лог("розвідка.py не поруч (%s) — старт = https://домен/" % e)
            for р in рецепти:
                р["старт"] = р.get("старт") or "https://" + р["домен"] + "/"
    лог(f"{ВЕРСІЯ} · рецептів {len(рецепти)} · транспорт {a.транспорт} · паралельно {a.паралельно} · стеля {a.стеля} · бюджет {a.секунд_на_магазин} с")
    в = Виконавець(a)
    asyncio.run(в.усі(рецепти))
    лог("готово: сирі/ · огляд/ · зведення_жнив.tsv")


if __name__ == "__main__":
    main()
