"""Статус наявних фактів речі без нових фактів зі слів каталогу.

Договір: status = measured / range / unknown / not_applicable; value — сам факт,
source — його чинний писач. Явна відсутність є measured + absent, а не unknown
чи not_applicable. Матриця визначає застосовність, а не наявність значення.
Склад — склад речі загалом: правило «без тканини» не робить його NA.
"""
import внутрішня_мова as _ВМ
import колір_річ as _К

СТАТУСИ = ("measured", "range", "unknown", "not_applicable")
ВЛАСТИВОСТІ = ("color", "composition", "metal")

# Походження чинних правил, а не нова класифікація матеріалів. Поле металу поза
# ювелірними слотами дозволене фід_атрибути.МЕТАЛ_СЛОТИ_ПОЛЕ. В інших типах
# фурнітура можлива, її застосовність невідома, а не заперечена.
ДЖЕРЕЛА_МАТРИЦІ = {
    "color": "колір_річ.не_вимір/межі_кольору/точка_кольору",
    "composition": "пакет_моделі.річ_пулу; фід_атрибути.матеріал_речі; ПРОДУКТ п.16",
    "metal": "фід_атрибути.МЕТАЛ_СЛОТИ/МЕТАЛ_СЛОТИ_ПОЛЕ; траурний_регістр.метал_біля_обличчя",
}
_ЮВЕЛІРНІ = frozenset(("earrings", "necklace", "collar_necklace", "bracelet", "ring",
                        "brooch", "watch", "jewelry"))
_ТКАНИННІ = frozenset(("top", "bottom", "dress", "set", "outerwear", "scarf", "headwear",
                       "gloves", "tights", "socks", "underwear", "swimwear"))
МАТРИЦЯ = {
    тип: {"color": {"applicability": "applicable", "source": ДЖЕРЕЛА_МАТРИЦІ["color"]},
          "composition": {"applicability": "applicable" if слот in _ТКАНИННІ else "unknown",
                          "source": ДЖЕРЕЛА_МАТРИЦІ["composition"]},
          "metal": {"applicability": "applicable" if слот in _ЮВЕЛІРНІ | {"belt", "bag"} else "unknown",
                    "source": ДЖЕРЕЛА_МАТРИЦІ["metal"]}}
    for тип, слот in _ВМ.СЛОТ_ТИПУ.items()
}


def тип_кодом(річ):
    """Тип із чинного enum: код або ключ ядра; незнайоме не вгадувати з назви."""
    тип = річ.get("тип")
    return тип if isinstance(тип, str) and тип in _ВМ.ТАБЛИЦЯ["item_type"] else _ВМ.код("item_type", тип)


def факт(статус, значення, джерело):
    """Утворити факт із чотирма станами та явним походженням."""
    if статус not in СТАТУСИ or not джерело:
        raise ValueError("невідомий статус чи немає походження факту")
    if статус in ("unknown", "not_applicable") and значення is not None:
        raise ValueError("невідоме й NA не містять значення")
    if статус in ("measured", "range") and значення is None:
        raise ValueError("відомий факт потребує значення")
    return dict(status=статус, value=значення, source=джерело)


def властивість(річ, властивість):
    """Адаптувати чинні значення кольору, складу й металу до одного договору.

    Сирий склад не є цитатним розбором. Його наявність не доводить жодного коду
    складу; чисел/слів з нього тут не добуваємо. Колір рахує лише його власник.
    """
    if властивість not in ВЛАСТИВОСТІ:
        raise ValueError("незнайома властивість")
    if властивість == "color":
        if not річ.get("колір_невідомий"):
            if _К.не_вимір(річ) is not None:
                межі = _К.межі_кольору(річ)
                if межі is not None:
                    return факт("range", межі, "color_window")
            elif ((річ.get("осі") or {}).get("L_from") in ("word", "word_or_photo")
                  or річ.get("джерело_кольору") == "назва_вікно"):
                # Старий запис уже втратив саме вікно: hex-центр не відновлює його.
                return факт("unknown", None, "color_provenance_missing")
            else:
                точка = _К.точка_кольору(річ)
                if точка is not None:
                    return факт("measured", точка, "color_point")
        return факт("unknown", None, "color_missing")
    if властивість == "metal":
        метал = річ.get("метал")
        код = метал if isinstance(метал, str) and метал in _ВМ.ТАБЛИЦЯ["metal"] else _ВМ.код("metal", метал)
        варіанти = річ.get("метал_варіанти")
        if isinstance(варіанти, (list, tuple)) and варіанти:
            коди = [v if isinstance(v, str) and v in _ВМ.ТАБЛИЦЯ["metal"] else _ВМ.код("metal", v) for v in варіанти]
            if all(коди):
                return факт("range", коди, "metal_variants")
        if код:
            return факт("measured", код, "metal_code")
        return факт("unknown", None, "metal_missing")
    if річ.get("склад_ненадійний"):
        return факт("unknown", None, "composition_unreliable")
    склад = річ.get("склад_коди")
    if склад:
        return факт("measured", list(склад), "composition_declared_codes")
    return факт("unknown", None, "composition_raw" if річ.get("матеріал") else "composition_missing")


def знання(річ):
    """Три факти разом із походженням застосовності для чинного коду типу."""
    тип = тип_кодом(річ)
    return {в: dict(властивість(річ, в), applicability=МАТРИЦЯ.get(тип, {}).get(в, {
        "applicability": "unknown", "source": ДЖЕРЕЛА_МАТРИЦІ[в]})) for в in ВЛАСТИВОСТІ}


def на_дріт(дані, має_точку=False):
    """Передати повні факти трьох властивостей до спільного codec промпту.

    Старі поля моделі лишаються. Значення діапазону кольору та відомого металу
    передаються окремо: центр колірного вікна не можна читати як вимір.
    """
    вих = {"knowledge": дані}
    if дані["color"]["status"] == "range":
        вих["color_range"] = дані["color"]["value"]
    elif дані["color"]["status"] == "measured" and not має_точку:
        вих["lab"] = дані["color"]["value"]
    if дані["metal"]["status"] in ("measured", "range"):
        вих["metal"] = дані["metal"]["value"]
    return вих
