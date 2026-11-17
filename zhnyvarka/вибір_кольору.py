"""Елементи вибору кольору сторінки → свотчі та сирі значення кольору оферт.

Розмітка визначає варіант; підпис і колір пікселів не визначають власника.
Посилання на іншу сторінку лишається сестрою, кнопка без галереї — лише вибором.
"""
import json
import re
from urllib.parse import urljoin, urlsplit


СВОТЧІ = ('[class*="swatch"], [class*="color"], [class*="colour"], '
          '[class*="kolir"], [class*="colir"], [data-color], [data-hex], '
          '.sku-props--pict button[data-onevalue]')
ФІЛЬТР = re.compile(r"woof|filter|facet|sidebar|widget", re.I)
КОЛІР = re.compile(r"колір|цвет|colou?r", re.I)


def _активний(вузол):
    """Читає стан елемента; false й inactive не стають активним вибором."""
    класи = " ".join(вузол.get("class") or [])
    return (bool(re.search(r"(?:^|[\s_-])(?:active|selected|checked|current)(?:$|[\s_-])", класи, re.I))
            or вузол.get("aria-checked") == "true" or вузол.get("aria-selected") == "true"
            or вузол.has_attr("checked") or вузол.has_attr("selected"))


def _адреса(значення, база):
    """Відносну вебадресу доповнює базою; якір і службова схема — не адреса."""
    значення = str(значення or "").strip()
    if not значення or значення.startswith(("#", "javascript:", "data:")):
        return None
    адреса = urljoin(база, значення)
    return адреса if urlsplit(адреса).scheme in ("http", "https") else None


def _сторінка(адреса):
    """Ідентичність сторінки разом із запитом, без якоря."""
    ч = urlsplit(адреса)
    return ч.netloc.lower(), ч.path.rstrip("/"), ч.query


def _посилання(ел):
    """Знаходить посилання самого варіанта, а не сусіднього блока."""
    return ел if ел.name == "a" else ел.find_parent("a") or ел.find("a")


def факти_вибору(кор, база):
    """Читає вибір сторінки; до перевірки всіх переліків власник галереї невідомий."""
    вихід = []
    for ел in кор.select(СВОТЧІ):
        класи = ел.get("class") or []
        if any(re.search(r"(?:colou?rs|swatches|[-_](?:list|image|name))$", к, re.I) for к in класи):
            continue
        if any(ФІЛЬТР.search(" ".join(п.get("class") or []) + " " + str(п.get("id") or ""))
               for п in [ел, *ел.parents]):
            continue
        кнопка = ел.name == "button" and ел.has_attr("data-onevalue")
        if not кнопка and len(ел.find_all("img")) > 1:
            continue
        група = ел.find_parent(class_="sku-props--pict") if кнопка else None
        if кнопка and (група is None or not КОЛІР.search(група.get_text(" ", strip=True).split(":")[0])):
            continue
        стиль = str(ел.get("style") or "")
        hex_ = None
        м = re.search(r"#([0-9a-f]{6}|[0-9a-f]{3})\b", стиль + " " + str(ел.get("data-color") or "")
                      + " " + str(ел.get("data-hex") or ""), re.I)
        if м:
            знач = м.group(1).lower()
            hex_ = "#" + ("".join(с * 2 for с in знач) if len(знач) == 3 else знач)
        else:
            м = re.search(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", стиль)
            if м and all(int(с) <= 255 for с in м.groups()):
                hex_ = "#%02x%02x%02x" % tuple(int(с) for с in м.groups())
        img = ел if ел.name == "img" else ел.find("img")
        кар = _адреса(img.get("data-src") or img.get("src"), база) if img else None
        if кнопка:
            м = re.search(r"background-image\s*:\s*url\(['\"]?([^)'\"]+)", стиль, re.I)
            кар = _адреса(м.group(1), база) if м else кар
        if not hex_ and not кар and not кнопка:
            continue
        підпис = (ел.get("title") or ел.get("aria-label") or ел.get("data-title") or ел.get("data-value")
                  or (img.get("alt") if img else "") or ел.get_text(" ", strip=True))[:40]
        посилання = _посилання(ел)
        адреса = _адреса(посилання.get("href"), база) if посилання is not None else None
        сестра = bool(адреса and _сторінка(адреса)[:2] != _сторінка(база)[:2])
        запис = dict(назва=підпис or None, hex=hex_, фото=кар, активний=_активний(ел), сестра=сестра)
        if кнопка:
            запис.update(ключ=str(ел["data-onevalue"]), атрибут="PROP_" + str(група.get("data-id") or ""))
        попередній = next((с for с in вихід if (с.get("ключ"), с["назва"], с["hex"], с["фото"], с["сестра"])
                           == (запис.get("ключ"), запис["назва"], hex_, кар, сестра)), None)
        if попередній is None:
            вихід.append(запис)
        else:
            попередній["активний"] |= запис["активний"]
    кольори = кольори_оферт(кор, вихід)
    return dict(свотчі=вихід, кольори_оферт=кольори or [], вибір_пошкоджено=кольори is None,
                власник_кадру=json.dumps("невідомо", ensure_ascii=False))


def кольори_оферт(кор, свотчі):
    """Читає сирі значення кольору оферт через ключі відповідних кнопок.

    TREE без фото не прив'язує галерею до активної кнопки: кілька значень
    кольору лишаються кількома навіть тоді, коли обрано лише одну оферту.
    """
    атрибути = {с["атрибут"] for с in свотчі if с.get("атрибут")}
    кольори = set()
    for ел in кор.select("template.offers-template-json, script.offers-template-json"):
        try:
            дані = json.loads(ел.string or ел.get_text())
        except (TypeError, ValueError):
            return None
        if not isinstance(дані, list):
            return None
        for о in дані:
            if not isinstance(о, dict) or not isinstance(о.get("TREE"), dict):
                continue
            for атрибут in атрибути:
                if о["TREE"].get(атрибут) is not None:
                    кольори.add(атрибут + "=" + str(о["TREE"][атрибут]))
    return sorted(кольори)


def переліки_кольору(ф):
    """Переліки кольорів цієї сторінки; сестринські сторінки — окремі записи."""
    return [{str(в["колір"]).strip().lower() for в in ф.get("варіанти") or [] if в.get("колір")},
            {(с.get("назва") or с.get("hex") or с.get("фото") or "").strip().lower()
             for с in ф.get("свотчі") or [] if not с.get("сестра")},
            set(ф.get("кольори_вибору") or []), set(ф.get("кольори_оферт") or [])]
