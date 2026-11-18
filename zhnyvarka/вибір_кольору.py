"""Елементи вибору кольору сторінки → свотчі та сирі значення кольору оферт.

Розмітка визначає варіант; підпис і колір пікселів не визначають власника.
Посилання на іншу сторінку лишається сестрою, кнопка без галереї — лише вибором.
"""
import json
import re
from urllib.parse import urljoin, urlsplit


СВОТЧІ = ('[class*="swatch"], [class*="color"], [class*="colour"], '
          '[class*="kolir"], [class*="colir"], [data-color], [data-hex], '
          '[data-color-value], .sku-props--pict button[data-onevalue]')
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


def _перехід(ел, база):
    """Читає href або буквальну адресу переходу onclick, не виконуючи JavaScript."""
    посилання = _посилання(ел)
    if посилання is not None:
        return _адреса(посилання.get("href"), база)
    кнопка = ел if ел.has_attr("onclick") else ел.find_parent(attrs={"onclick": True})
    if кнопка is not None:
        м = re.fullmatch(r"\s*(?:window\.)?location(?:\.href)?\s*=\s*(['\"])(.*?)\1\s*;?\s*", кнопка["onclick"])
        if м:
            return _адреса(м.group(2), база)
    return None


def _вузли_свотчів(кор):
    """Розгортає контейнер кольорів у його елементи, не беручи перше фото контейнера."""
    вихід, бачені = [], set()
    for ел in кор.select(СВОТЧІ):
        група = ел.name not in ("img", "button", "input", "label", "a") and (
            len(ел.find_all("img")) > 1 or ел.select_one("[data-color-value], button[data-onevalue]") is not None or any(
                re.search(r"(?:colou?rs|swatches|[-_](?:list|image|name))$", к, re.I) for к in ел.get("class") or []))
        вузли = []
        if група:
            if not ел.select(СВОТЧІ):
                for зображення in ел.find_all("img"):
                    опція = зображення.find_parent("a") or зображення.find_parent("button") or зображення
                    вузли.append(опція if ел in опція.parents else зображення)
        else:
            вузли = [ел]
        for вузол in вузли:
            if id(вузол) not in бачені:
                бачені.add(id(вузол))
                вихід.append(вузол)
    return вихід


def факти_вибору(кор, база, база_фото=None, товар=None):
    """Читає вибір сторінки; до перевірки всіх переліків власник галереї невідомий."""
    вихід = []
    for ел in _вузли_свотчів(кор):
        if any(ФІЛЬТР.search(" ".join(п.get("class") or []) + " " + str(п.get("id") or ""))
               for п in [ел, *ел.parents]):
            continue
        кнопка = ел.name == "button" and ел.has_attr("data-onevalue")
        група = ел.find_parent(class_="sku-props--pict") if кнопка else None
        if кнопка and (група is None or not КОЛІР.search(група.get_text(" ", strip=True).split(":")[0])):
            continue
        зразок = ел.find("span", style=True, recursive=False)
        стиль = str(ел.get("style") or (зразок.get("style") if зразок else "") or "")
        hex = None
        м = re.search(r"#([0-9a-f]{6}|[0-9a-f]{3})\b", стиль + " " + str(ел.get("data-color") or "")
                      + " " + str(ел.get("data-hex") or ""), re.I)
        if м:
            знач = м.group(1).lower()
            hex = "#" + ("".join(с * 2 for с in знач) if len(знач) == 3 else знач)
        else:
            м = re.search(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", стиль)
            if м and all(int(с) <= 255 for с in м.groups()):
                hex = "#%02x%02x%02x" % tuple(int(с) for с in м.groups())
        зображення = ел if ел.name == "img" else ел.find("img")
        кар = _адреса(зображення.get("data-src") or зображення.get("src"), база_фото or база) if зображення else None
        м = re.search(r"\bbackground(?:-image)?\s*:[^;]*?url\(['\"]?([^)'\"]+)", стиль, re.I)
        кар = _адреса(м.group(1), база_фото or база) if м else кар
        радіо = ел.name == "input" and ел.has_attr("data-color-value")
        if not hex and not кар and not кнопка and not радіо:
            continue
        підпис = (ел.get("title") or ел.get("aria-label") or ел.get("data-title") or ел.get("data-color-value") or ел.get("data-value")
                  or (зображення.get("alt") if зображення else "") or ел.get_text(" ", strip=True))[:40]
        адреса = _перехід(ел, база_фото or база)
        сестра = bool(адреса and _сторінка(адреса)[:2] != _сторінка(база)[:2])
        запис = dict(назва=підпис or None, hex=hex, фото=кар, активний=_активний(ел), сестра=сестра)
        if кнопка:
            запис.update(ключ=str(ел["data-onevalue"]), атрибут="PROP_" + str(група.get("data-id") or ""))
        попередній = next((с for с in вихід if (с.get("ключ"), с["назва"], с["hex"], с["фото"], с["сестра"])
                           == (запис.get("ключ"), запис["назва"], hex, кар, сестра)), None)
        if попередній is None:
            вихід.append(запис)
        else:
            попередній["активний"] |= запис["активний"]
    кольори = кольори_оферт(кор, вихід)
    return dict(свотчі=вихід, кольори_оферт=кольори or [], вибір_пошкоджено=кольори is None,
                галерея_вибору=галерея_оферт(кор, база_фото or база, вихід, товар),
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


def галерея_оферт(кор, база, свотчі, товар):
    """Зв'язує кадри з сирими id оферт лише в явно підписаній галереї товару.

    Активна кнопка дає ключ кольору, TREE — id оферт цього кольору. Кадри
    беруться з власних даних оферти або з DOM з її data-offer-id та id товару.
    Спільний кадр різних кольорів та непідписана галерея доказом не стають.
    """
    активні = {(с["атрибут"], с["ключ"]) for с in свотчі if с.get("активний") and с.get("ключ")}
    if len(активні) != 1 or not товар:
        return {}
    атрибут, ключ = next(iter(активні))
    оферти, зв_язки = {}, {}
    for ел in кор.select("template.offers-template-json, script.offers-template-json"):
        try:
            дані = json.loads(ел.string or ел.get_text())
        except (TypeError, ValueError):
            return {}
        if not isinstance(дані, list):
            return {}
        for о in дані:
            if not isinstance(о, dict) or not о.get("ID") or not isinstance(о.get("TREE"), dict):
                continue
            ід, знач = str(о["ID"]), str(о["TREE"].get(атрибут, ""))
            if ід in оферти and оферти[ід] != знач:
                return {}
            оферти[ід] = знач
            кадри = о.get("image") or о.get("images") or []
            for к in кадри if isinstance(кадри, list) else [кадри]:
                к = к.get("url") or к.get("src") if isinstance(к, dict) else к
                if адреса := _адреса(к, база):
                    зв_язки.setdefault(адреса, set()).add(ід)
    for ел in кор.select("[data-offer-id]"):
        ід = str(ел.get("data-offer-id") or "")
        продукт = ел.get("data-product-id") or ел.get("data-item-id")
        if ід not in оферти or str(продукт) != str(товар):
            continue
        for зображення in ел.select("img"):
            # Вкладена галерея іншої оферти не успадковує власника зовнішньої.
            if зображення.find_parent(attrs={"data-offer-id": True}) is not ел:
                continue
            if адреса := _адреса(зображення.get("data-src") or зображення.get("src"), база):
                зв_язки.setdefault(адреса, set()).add(ід)
    обрані = sorted(і for і, знач in оферти.items() if знач == ключ)
    кадри = {к: sorted(ід) for к, ід in зв_язки.items() if ід and ід <= set(обрані)}
    return dict(варіанти=обрані, зв_язки=кадри, вибір=атрибут + "=" + ключ) if кадри else {}
