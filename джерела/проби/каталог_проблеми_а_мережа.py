# -*- coding: utf-8 -*-
"""Реєстр А (рядок 5630), клас А10: чи відкриваються фото крамниць із ЦЬОГО середовища (403 з хмари).
По одному кадру жнив на хост — запит із браузерним UA, як `жнива_фото._качати`; друкує статус і
`content-type` кожного хоста й підсумок. Результат залежить від середовища (хмара сесії, ChatGPT,
ноутбук) — це вимір мережі, не каталогу. Мережа потрібна; без неї кожен хост — збій.
Запуск: cd джерела && python3 проби/каталог_проблеми_а_мережа.py"""
import collections, concurrent.futures as cf, os, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф
зб, по = Ф.читати_збагачення(), {}
for з in зб.values():
    к = з.get("фото") if isinstance(з, dict) else None
    if к:
        по.setdefault(urllib.parse.urlsplit(к).netloc, к)
def статус(u):
    """(код чи ім'я збою, content-type) для однієї адреси."""
    зап = urllib.request.Request(urllib.parse.quote(u, safe=":/?&=%#+@;,~!$*'()[]"), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(зап, timeout=20) as в:
            return str(в.status), str(в.headers.get("content-type"))
    except Exception as e:
        return type(e).__name__ + " " + str(getattr(e, "code", "") or e)[:40], "—"
with cf.ThreadPoolExecutor(16) as ex:
    рез = dict(zip(по, ex.map(статус, по.values())))
for х, (к, т) in sorted(рез.items(), key=lambda x: x[1]):
    print("  %-30s %-10s %s" % (х[:30], к, т))
лічба = collections.Counter("200 image" if к == "200" and т.startswith("image/") else к + " " + т for к, т in рез.values())
print("хостів %d ·" % len(рез), dict(лічба.most_common()))
