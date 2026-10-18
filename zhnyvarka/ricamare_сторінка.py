# -*- coding: utf-8 -*-
"""Українська картка RicaMare → чинний запис v1 (5624, один рецепт із 58).

Знімок `<тека>/ricamare.com.ua.json.gz` — список {url, html, знято, sha256}:
HTML дослівний, дата — дата отримання, sha256 — відбиток UTF-8 байтів.
`складальник.py --ricamare-знімок <тека>` оновлює лише наявні адреси цих знімків.
Нових речей, об'єднання сторінок розмірів і мережевого обходу тут немає.

Структура перевірена на HTML ноутбука від 13.10.2026. Семантичні коди старого
запису не переобчислюються зі слів; характеристики й колір — дослівні свідки.
Стан Offer стосується вибраного розміру, решта кнопок не доводить його наявності.
"""
import collections
import csv
import datetime
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
import woo_варіанти as ва

ДОМЕН = "ricamare.com.ua"
ЗБИРАЧ = "адаптер ricamare v1"
СТАНИ = {"https://schema.org/InStock": "true", "https://schema.org/OutOfStock": "false"}
ПЕРЕПИСАНІ = ва.ПЕРЕПИСАНІ | {"назва_джерело", "назва_сира", "категорія_магазину", "мова", "магазин"}


def рецепт():
    """Читає селектори єдиного рецепта RicaMare з чинної таблиці."""
    with Path(__file__).with_name("рецепти.tsv").open(encoding="utf-8") as потік:
        return next(р for р in csv.DictReader(потік, delimiter="\t") if р["домен"] == ДОМЕН)


def адреса(значення):
    """Нормалізує адресу української картки, не змінюючи її шляху."""
    частини = urlsplit(значення)
    if частини.scheme != "https" or частини.netloc != ДОМЕН or частини.path.startswith("/ru/"):
        raise ValueError("потрібна українська адреса RicaMare")
    if частини.query or частини.fragment:
        raise ValueError("потрібна канонічна адреса без параметрів")
    return urlunsplit(частини)


def _поле(вузол, селектор, атрибут=None):
    """Бере одне структуроване поле, відсутнє поле лишає порожнім."""
    елементи = вузол.select(селектор)
    if len(елементи) > 1:
        raise ValueError("неоднозначне поле: " + селектор)
    if not елементи:
        return ""
    return (елементи[0].get(атрибут, "") if атрибут else елементи[0].get_text(" ", strip=True)).strip()


def розібрати(старий, знімок, налаштування):
    """Оновлює один запис v1 з власної української картки й перевіряє походження."""
    if старий["схема"] != "v1":
        raise ValueError("основа запису має бути v1")
    дата = datetime.date.fromisoformat(знімок["знято"]).isoformat()
    сторінка = адреса(знімок["url"])
    if адреса(старий["адреса"]) != сторінка:
        raise ValueError("знімок іншої речі")
    if hashlib.sha256(знімок["html"].encode("utf-8")).hexdigest() != знімок["sha256"]:
        raise ValueError("відбиток HTML не збігається")
    документ = BeautifulSoup(знімок["html"], "html.parser")
    if _поле(документ, "html", "lang") != "uk":
        raise ValueError("HTML не має української локалі")
    if адреса(_поле(документ, 'link[rel="canonical"]', "href")) != сторінка:
        raise ValueError("канонічна адреса не збігається")
    товари = документ.select('section.product[itemtype="https://schema.org/Product"]')
    if len(товари) != 1:
        raise ValueError("потрібен один блок Product")
    товар = товари[0]
    назва = _поле(товар, 'h1[itemprop="name"]')
    артикул = _поле(товар, 'meta[itemprop="sku"]', "content")
    ціна = _поле(товар, '.product-price meta[itemprop="price"]', "content")
    валюта = _поле(товар, '.product-price meta[itemprop="priceCurrency"]', "content")
    if not назва or not артикул or not ціна or not валюта:
        raise ValueError("неповна картка: назва, sku, price, priceCurrency")
    стан = СТАНИ.get(_поле(товар, '.product-price link[itemprop="availability"]', "href"))
    кадри = list(dict.fromkeys(urljoin(сторінка, е["data-href"])
                              for е in товар.select('.gallery__photos .j-gallery-link[data-href]')))
    if not кадри or any(urlsplit(к).scheme != "https" for к in кадри):
        raise ValueError("немає власної HTTPS-галереї")
    опис = _поле(товар, налаштування["селектор_опису"])
    колір = _поле(товар, налаштування["атрибут_кольору"], "title")
    розмір = _поле(товар, налаштування["атрибут_розміру"])
    характеристики = []
    for рядок in товар.select(налаштування["селектор_характеристик"] + " tr"):
        клітини = рядок.find_all(["th", "td"], recursive=False)
        if len(клітини) == 2:
            характеристики.append(["~" + клітини[0].get_text(" ", strip=True).strip(),
                                   клітини[1].get_text(" ", strip=True), "к"])
    параметри = [list(п) for п in старий["параметри"] if п[2] == "с" and п[0] not in ПЕРЕПИСАНІ]
    джерела = {"магазин": ДОМЕН, "адаптер": "ricamare v1", "канал": "html:microdata",
               "платформа": "Horoshop", "мова": "укр", "знято": дата, "id_магазину": сторінка,
               "назва_джерело": 'h1[itemprop=name]', "назва_сира": назва,
               "кадри_джерело": ".gallery__photos .j-gallery-link[data-href]",
               "фото_джерело": ".gallery__photos .j-gallery-link[data-href]",
               "категорія_магазину": _поле(товар, 'meta[itemprop="category"]', "content"),
               "розміри": розмір, "розміри_в_наявності": розмір if стан == "true" else "",
               "розміри_джерело": налаштування["атрибут_розміру"],
               "наявність": {"true": "є", "false": "нема"}.get(стан, "невідомо")}
    if колір:
        джерела.update({"Колір": колір, "колір_джерело": налаштування["атрибут_кольору"] + "@title"})
    параметри.extend([ім, знач, "с"] for ім, знач in джерела.items())
    параметри.extend(характеристики)
    return dict(старий, назва=назва, артикул=артикул, ціна=ціна, валюта=валюта, доступність=стан,
                кадри=кадри, опис=опис or None, параметри=параметри, збирач=ЗБИРАЧ,
                вихід={"опис": len(параметри)} if опис else {})


def перебрати(записи, знімки, збагачення, виміри_кадрів):
    """Оновлює тільки адреси знімка, зберігає ід і чинну прив'язку вимірів до кадру."""
    за_адресою = {адреса(з["адреса"]): з for з in записи if ва.магазин(з) == ДОМЕН}
    нові, лічба, черга = {}, collections.Counter(), []
    зб, км = dict(збагачення), dict(виміри_кадрів)
    налаштування = рецепт()
    for знімок in знімки:
        ключ = адреса(знімок["url"])
        if ключ in нові or ключ not in за_адресою:
            raise ValueError("повторна або невідома адреса знімка: " + ключ)
        зап = розібрати(за_адресою[ключ], знімок, налаштування)
        нові[ключ] = зап
        ід = зап["ід"]
        зб.pop(ід + "@" + ДОМЕН, None)
        км.pop(ід + "@" + ДОМЕН, None)
        ва._вимір(збагачення, виміри_кадрів, зб, км, ід, ід, зап, лічба, черга)
        лічба["записів_зі_знімка"] += 1
    результат = [нові.get(з["адреса"], з) for з in записи]
    лічба["без_знімка"] = len(за_адресою) - len(нові)
    return результат, зб, км, лічба, черга
