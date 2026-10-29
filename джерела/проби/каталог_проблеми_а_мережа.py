# -*- coding: utf-8 -*-
"""Реєстр А (рядок 5630), клас А10: чи відкриваються фото крамниць із ЦЬОГО середовища (403 з хмари).
Вибірка — до 20 різних кадрів жнив на хост (перші за порядком збагачення), запит із браузерним UA,
як `жнива_фото._качати`. Друкує по хосту: відкрилось як картинку / усього, без `content-type`,
інші відповіді; і підсумок. Вимір мережі середовища (хмара сесії, ChatGPT, ноутбук), не каталогу.
Запуск: cd джерела && python3 проби/каталог_проблеми_а_мережа.py"""
import collections, concurrent.futures as cf, os, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф
НА_ХОСТ = 20
по = collections.defaultdict(list)
for з in Ф.читати_збагачення().values():
    к = з.get("фото") if isinstance(з, dict) else None
    х = urllib.parse.urlsplit(к).netloc if к else None
    if к and len(по[х]) < НА_ХОСТ and к not in по[х]:
        по[х].append(к)
def статус(u):
    """'image' / 'без типу' / код чи ім'я збою для однієї адреси."""
    зап = urllib.request.Request(urllib.parse.quote(u, safe=":/?&=%#+@;,~!$*'()[]"), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(зап, timeout=20) as в:
            т = str(в.headers.get("content-type") or "")
            return "image" if т.startswith("image/") else ("без типу" if not т else "200 " + т[:20])
    except Exception as e:
        return str(getattr(e, "code", "") or type(e).__name__)
пари = [(х, u) for х, uu in по.items() for u in uu]
with cf.ThreadPoolExecutor(24) as ex:
    рез = list(ex.map(lambda п: (п[0], статус(п[1])), пари))
по_хосту = collections.defaultdict(collections.Counter)
for х, с in рез:
    по_хосту[х][с] += 1
for х, c in sorted(по_хосту.items(), key=lambda x: x[1]["image"] / sum(x[1].values())):
    print("  %-30s картинка %2d/%-2d %s" % (х[:30], c["image"], sum(c.values()), dict((к, н) for к, н in c.items() if к != "image") or ""))
разом = collections.Counter(с for _, с in рез)
print("хостів %d · адрес %d (до %d на хост) ·" % (len(по_хосту), len(рез), НА_ХОСТ), dict(разом.most_common()))
