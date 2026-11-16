"""Ідентифікатор власного товару зі структурованих даних сторінки й межі його DOM."""
import json
import re
from urllib.parse import urljoin, urlsplit, urlunsplit


def ідентифікатор_запису(факти, адреса):
    """Дає id з фактів або дозволеного цифрового хвоста шляху, без параметрів відстеження."""
    хвіст = re.search(r"(\d{3,})/?$", urlsplit(адреса or "").path)
    return факти.get("id_магазину") or (хвіст[1] if хвіст else None)


def _значення(значення):
    """Нормалізує скалярний id, не перетворюючи порожні чи складені дані на ідентичність."""
    if isinstance(значення, bool) or not isinstance(значення, (str, int)):
        return None
    значення = str(значення).strip()
    return значення if значення and значення != "0" else None


def _адреса(адреса, база):
    """Звіряє адресу товару без фрагмента, зберігаючи параметри вибору варіанта."""
    if not isinstance(адреса, str) or not адреса.strip():
        return None
    частини = urlsplit(urljoin(база, адреса))
    return urlunsplit((частини.scheme.lower(), частини.netloc.lower(),
                       частини.path.rstrip("/"), частини.query, ""))


def _вбудовані_товари(скрипти, адреса, сторінки):
    """Дістає id з JSON-об'єктів Product, чия адреса або слаг називає саме цю сторінку."""
    значення = set()
    слаг = urlsplit(адреса).path.rstrip("/").rsplit("/", 1)[-1]
    for скрипт in скрипти:
        try:
            черга = [json.loads(скрипт)]
        except (TypeError, ValueError):
            continue
        while черга:
            вузол = черга.pop()
            if isinstance(вузол, list):
                черга.extend(вузол)
            elif isinstance(вузол, dict):
                if вузол.get("__typename") == "Product" or вузол.get("@type") == "Product":
                    власний = (_адреса(вузол["url"], адреса) in сторінки
                               if вузол.get("url") else bool(слаг and вузол.get("slug") == слаг))
                    ід = _значення(вузол.get("id"))
                    if власний and ід:
                        значення.add(ід)
                черга.extend(в for в in вузол.values() if isinstance(в, (dict, list)))
    return значення


def ідентифікатор_сторінки(продукт, вузли, корінь, скрипти, адреса, артикул=None, канонічні=()):
    """Повертає однозначний id власного товару: productID, форма, JSON платформи або sku.

    Переліки рекомендацій не є джерелом. DOM уже обмежений вузлом товару й очищений
    від чужих блоків; вкладені Product теж відсікаються. Різні id одного рівня
    доказу означають невідомо, а не вибір першого. Параметри URL тут не читаються.
    """
    сторінки = {_адреса(адреса, адреса)}
    канонічні = {_адреса(а, адреса) for а in канонічні if isinstance(а, str) and а.strip()}
    if len(канонічні) == 1 and urlsplit(next(iter(канонічні))).netloc == urlsplit(адреса).netloc.lower():
        сторінки.update(канонічні)
    власні = [в for в in вузли if not в.get("_у_списку") and
              any(т in ("Product", "ProductModel", "ProductGroup") for т in
                  (в.get("@type") if isinstance(в.get("@type"), list) else [в.get("@type")])) and
              _адреса(в.get("url") or в.get("@id"), адреса) in сторінки]
    власні = власні or ([продукт] if продукт and not (продукт.get("url") or продукт.get("@id")) else [])
    групи = [set(), set(), set(), set()]
    for вузол in власні:
        for поле, група in (("productID", 0), ("productId", 0), ("sku", 3)):
            ід = _значення(вузол.get(поле))
            if ід:
                групи[група].add(ід)
    if корінь is not None:
        селектор = ('[itemprop="productID"], [itemprop="sku"], [data-product-id], [data-product_id], '
                    'input[name="product_id"], input[name="id_product"], [name="add-to-cart"]')
        for елемент in [корінь] + корінь.select(селектор):
            предки = []
            for предок in елемент.parents:
                if предок is корінь:
                    break
                предки.append(предок)
            if елемент is not корінь and any(
                    str(п.get("itemtype") or "").rstrip("/").endswith("/Product") for п in [елемент] + предки):
                continue
            for поле in ("data-product-id", "data-product_id"):
                ід = _значення(елемент.get(поле))
                if ід:
                    групи[1].add(ід)
            if елемент.get("name") in ("product_id", "id_product", "add-to-cart"):
                ід = _значення(елемент.get("value"))
                if ід:
                    групи[1].add(ід)
            if елемент.get("itemprop") in ("productID", "sku"):
                ід = _значення(елемент.get("content") or елемент.get_text(" ", strip=True))
                if ід:
                    групи[0 if елемент["itemprop"] == "productID" else 3].add(ід)
    # Вбудований JSON потрібен лише коли явного productID чи id форми немає.
    if not any(групи[:2]):
        групи[2] = _вбудовані_товари(скрипти, адреса, сторінки)
    for значення in групи:
        if значення:
            return next(iter(значення)) if len(значення) == 1 else None
    return _значення(артикул)
