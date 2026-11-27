"""Ч5. Звіряє відповіді з дротовими схемами й адресами речей."""
from dataclasses import dataclass, replace
import json
from pathlib import Path

from внутрішня_мова import КОДИ_БРАКУ_СХЕМИ
from межа_текстів import ІдУТілі, КАНДИДАТ_ЗАМІНИ, ПРЕДМЕТ
from .поняття import Образ, Збій, НЕВІДОМО

НАРЯД = None
with Path(__file__).with_name("дані").joinpath("відповіді.json").open(encoding="utf-8") as _файл:
    _СХЕМИ = json.load(_файл)

_ВИДИ = {"складання": "образи", "ремонт": "образи", "вибір": "вибір", "опис": "опис", "перелік": "перелік",
         "турнір": "турнір", "оцінка": "оцінка"}
_ТИПИ = {"object": dict, "array": list, "string": str, "null": type(None), "boolean": bool}


@dataclass(frozen=True)
class Опис:
    """Поля опису, звірені зі складом, над яким його запитали."""
    образ: str
    склад: tuple
    текст: str
    носіння: tuple
    фото_не_те: tuple
    про_речі: tuple
    заміна: dict | None = None
    кадри_оцінено: bool = False
    речення: dict | None = None
    розбіжності: tuple = ()
    прийнято_речень: int = 0


def схема(вид):
    """Повертає схему, з якої також будується вимога формату запиту."""
    return _СХЕМИ[_ВИДИ[вид]]


def схема_тексту_картки(фото=False):
    """Додає до договору текстів лише ті поля, які потрібні для звірки фото."""
    рядок = {"type": "string", "minLength": 1}
    номери = {"type": "object", "properties": {}, "required": [], "additionalProperties": рядок}
    речення = {"type": "object", "properties": {"about": номери, "says": рядок},
               "required": ["about", "says"], "additionalProperties": False}
    список = {"type": "array", "items": речення, "minItems": 0}
    поля = {к: список for к in ("text", "advice", "unknown")}
    поля["names"] = номери
    обовʼязкові = list(поля)
    if фото:
        поля.update({к: схема("опис")["properties"][к] for к in ("wrong_photos", "swap")})
        обовʼязкові.append("wrong_photos")
    return {"type": "object", "properties": поля, "required": обовʼязкові, "additionalProperties": False}


class _Невірне(ValueError):
    def __init__(self, поле, що, вид="схема"):
        super().__init__(що)
        self.поле = поле
        self.вид = вид


def _перевірити(значення, опис, поле):
    """Перевіряє одне поле відповіді, зокрема вкладене."""
    тип = опис["type"]
    типи = [тип] if isinstance(тип, str) else тип
    if not isinstance(значення, tuple(_ТИПИ[дозволений] for дозволений in типи)):
        raise _Невірне(поле or "response", f"expected {тип}")
    if "enum" in опис and значення not in опис["enum"]:
        raise _Невірне(поле, "value outside enum")
    if "minLength" in опис and len(значення) < опис["minLength"]:
        raise _Невірне(поле, "empty field")
    if тип == "array":
        if len(значення) < опис["minItems"]:
            raise _Невірне(поле, "missing array values")
        for номер, елемент in enumerate(значення):
            _перевірити(елемент, опис["items"], f"{поле}[{номер}]" + ("." if isinstance(елемент, dict) else ""))
    if тип == "object":
        поля = опис["properties"]
        for ключ in опис["required"]:
            if ключ not in значення:
                вид = "опис_неповний" if ключ in ("about_items", "text") else "схема"
                raise _Невірне(f"{поле}{ключ}", "missing field", вид)
        for ключ, в in значення.items():
            адреса = f"{поле}{ключ}"
            правило = поля.get(ключ, опис.get("additionalProperties"))
            if not isinstance(правило, dict):
                raise _Невірне(адреса, "field outside schema")
            _перевірити(в, правило, адреса + "." if isinstance(в, dict) else адреса)


def _обʼєкт(пари):
    """Відкидає дубльовані JSON-ключі замість мовчазної втрати."""
    д = {}
    for ключ, в in пари:
        if ключ in д:
            raise _Невірне(ключ, "duplicate field")
        д[ключ] = в
    return д


def _дані(відп, вид, спроба, *, усе_за_схемою=True):
    """Розпаковує JSON-об'єкт або повертає діагноз відповіді."""
    if "збій" in відп:
        з = відп["збій"]
        локальна_межа = (з.get("частина") == "запит" and з.get("вид") in ("вікно_моделі", "межа_транспорту")
                         and isinstance(з.get("дані"), dict))
        if локальна_межа:
            поле = "window" if з["вид"] == "вікно_моделі" else "messages"
            return Збій(з["вид"], "запит", поле, з.get("що", ""), спроба=спроба, дані=dict(з["дані"], stage=вид))
        return Збій(вид=з.get("вид") or "інше", частина="модель", поле=вид, що=з.get("що", ""),
                    секунди=з.get("секунди"), спроба=спроба)
    текст = відп.get("текст", "")
    дані = json.loads(текст, object_pairs_hook=_обʼєкт)
    if усе_за_схемою:
        _перевірити(дані, схема(вид), "")
    elif not isinstance(дані, dict):
        raise _Невірне("response", "expected an object")
    return дані


def _склад(номери, пул, поле, дозволені):
    """Розв'язує номери пулу та звіряє обов'язкові види й ліміти."""
    from .пул import СЛОТИ
    зайнято = {}
    склад = []
    бачили = set()
    for н in номери:
        if н not in дозволені:
            raise _Невірне(поле, f"{н} not in pool")
        річ = пул.записи[н]
        if річ.ід in бачили:
            raise _Невірне(поле, f"duplicate item {н}")
        бачили.add(річ.ід)
        вид = СЛОТИ[річ.слот]
        зайнято[вид] = зайнято.get(вид, 0) + 1
        if зайнято[вид] > пул.межі_слотів.get(вид, 1):
            raise _Невірне(поле, f"too many items of kind {вид}")
        склад.append({"н": н, "ід": річ.ід})
    for вид in пул.обовʼязкові:
        if вид not in зайнято:
            raise _Невірне(поле, f"missing required kind {вид}")
    види = set(зайнято)
    if not (види & {"dress", "set"} or {"top", "bottom"} <= види):
        raise _Невірне(поле, "missing dress, set, or top and bottom")
    return tuple(склад)


def _образи(дані, вид, пул, попередні, дозволені, відкинуті):
    """Пише лише образи, для яких склад пройшов договір Ч5."""
    попередні = {о.номер: о for о in попередні}
    вихід = {}
    for рядок in дані["outfits"]:
        номер = рядок["id"]
        if номер in вихід:
            raise _Невірне(f"{номер}.id", "duplicate outfit")
        старий = попередні.get(номер)
        if вид == "ремонт" and старий is None:
            raise _Невірне(f"{номер}.id", "not an offered outfit")
        try:
            речі = _склад(рядок["items"], пул, f"{номер}.items", дозволені)
        except _Невірне as помилка:
            if відкинуті is None:
                raise
            відкинуті.append(помилка)
            continue
        if старий is not None and {р["ід"] for р in речі} == {р["ід"] for р in старий.речі}:
            вихід[номер] = старий
            continue
        склад = {р["н"] for р in речі}
        свідомі = tuple({"річ": заява["item"], "заява": заява.get("finding"), "чому_en": заява["why"]}
                        for заява in рядок.get("deliberate", ()))
        if будь_що_поза(свідомі, склад, "річ"):
            raise _Невірне(f"{номер}.deliberate", "item outside outfit")
        носіння = tuple(рядок.get("worn", ()))
        if будь_що_поза(носіння, склад, "item"):
            raise _Невірне(f"{номер}.worn", "item outside outfit")
        вихід[номер] = Образ(ід=номер if старий is None else f"{старий.ід}:ремонт", номер=номер, рука=пул.рука,
                             джерело=вид, версія_ситуації=пул.версія_ситуації, речі=речі,
                             полюс=рядок.get("pole", старий.полюс if старий else НЕВІДОМО),
                             підпис_en=рядок.get("caption", ""), день_en=рядок.get("day", ""),
                             свідомі=свідомі, попередник=старий.ід if старий else None, носіння=носіння)
    if not вихід and відкинуті:
        raise відкинуті[0]
    return tuple(вихід.values())


def будь_що_поза(рядки, склад, поле):
    """Чи структурована згадка посилається на річ поза складом."""
    return any(рядок[поле] not in склад for рядок in рядки)


def _опис(дані, образ):
    """Звіряє згадки й повноту пояснення за номерами речей."""
    склад = tuple(р["н"] for р in образ.речі)
    про_речі = дані["about_items"]
    описані = [рядок["n"] for рядок in про_речі]
    if set(описані) != set(склад) or len(описані) != len(склад):
        raise _Невірне("about_items", "description does not cover its composition", "опис_неповний")
    if будь_що_поза(дані.get("named", ()), склад, "n"):
        raise _Невірне("named", "named item outside outfit")
    фото_не_те = tuple(dict.fromkeys(дані.get("wrong_photos", ())))
    if set(фото_не_те) - set(склад):
        raise _Невірне("wrong_photos", "item outside outfit")
    пояснення = {рядок["n"]: рядок["text"] for рядок in про_речі}
    return Опис(образ.ід, склад, дані["text"], tuple(дані.get("how_to_wear", ())),
                фото_не_те, tuple((н, пояснення[н]) for н in склад), дані.get("swap"), "wrong_photos" in дані)


def невідоме_картки(межа, речення=()):
    """Повертає рядки з темами тих самих фактів на випадок пропуску або збою показу."""
    рядки, _, _ = межа.рядки_невідомого(речення, ("held",), формат="Не вдалося перевірити {тема}.", з_номерами=True)
    return рядки


def запас_картки(межа):
    """Той самий склад і відкладене невідоме, коли пояснення не прочитане."""
    return dict(unknown=невідоме_картки(межа), fallback=межа.запасні_рядки_картки())


def _тексти_картки(дані, межа):
    """Звіряє опори, зберігає поділ на пояснення, поради та невідоме."""
    суд = межа.судити(дані)
    розбіжності = [з for з in суд["відкинуто"] if з["чому"] != "facts_not_told"]
    предмети = {н for н, ф in межа.факти.items() if ф["state"] == ПРЕДМЕТ}
    факти_вибору = {н for н, ф in межа.факти.items() if ф["state"] in КОДИ_БРАКУ_СХЕМИ}
    пояснення = [р for р in суд["text"] if факти_вибору.isdisjoint(р["about"])]
    дозволені_в_рядку = факти_вибору | предмети
    рядок_вибору = next((р for р in суд["text"] if факти_вибору.intersection(р["about"])
                        and дозволені_в_рядку.issuperset(р["about"])), None)
    поради = [р for р in суд["advice"] if предмети.intersection(р["about"])
              and факти_вибору.isdisjoint(р["about"])]
    if len(поради) != len(суд["advice"]):
        розбіжності.append(dict(чому="advice_item_missing"))
    дані_назв = дані.get("names")
    назви = {н: назва for н, т in (дані_назв.items() if isinstance(дані_назв, dict) else ())
             if н in предмети and межа.факти[н].get("needs_name") and isinstance(т, str)
             and (назва := межа.назва_речі(т))}
    для_назви = {н for н in предмети if межа.факти[н].get("needs_name")}
    if для_назви != назви.keys() or not isinstance(дані_назв, dict) or len(назви) != len(дані_назв):
        розбіжності.append(dict(чому="item_names_missing", про=sorted(для_назви - назви.keys())))
    if not поради:
        розбіжності.append(dict(чому="advice_item_missing"))
    if not пояснення:
        розбіжності.append(dict(чому="explanation_missing"))
    сказані = {н for р in пояснення + поради for н in р["about"]}
    if рядок_вибору:
        сказані.update(рядок_вибору["about"])
    відсутні = (предмети - сказані) | set(суд["не_сказано"])
    if відсутні:
        розбіжності.append(dict(чому="facts_not_told", про=sorted(відсутні)))
    прийнято_речень = len(пояснення) + len(поради) + len(суд["unknown"]) + bool(рядок_вибору)
    return dict(text=пояснення, advice=поради, action=[рядок_вибору] if рядок_вибору else [],
                unknown=невідоме_картки(межа, суд["unknown"]),
                names=назви, fallback=межа.запасні_рядки_картки()), розбіжності, прийнято_речень


def _кадри_картки(дані, межа, фото, розбіжності):
    """Переводить номери фактів кадрів і заміни в адреси лише після перевірки."""
    схема_опису = схема("опис")["properties"]
    хибні, заміна, оцінено = (), None, False
    if фото or "wrong_photos" in дані:
        try:
            номери = дані.get("wrong_photos")
            межа.тіло(json.dumps(номери, ensure_ascii=False))
            _перевірити(номери, схема_опису["wrong_photos"], "wrong_photos")
            адреси = tuple(dict.fromkeys(межа.адреса_речі(н) for н in номери))
            if set(адреси) - set(фото):
                raise _Невірне("wrong_photos", "fact has no delivered photo")
            хибні, оцінено = адреси, True
        except ІдУТілі as помилка:
            розбіжності.append(dict(чому="pool_address" if помилка.збій.вид == "pool_address_in_body" else "wrong_photo_fact"))
        except _Невірне:
            розбіжності.append(dict(чому="wrong_photo_fact"))
    if "swap" in дані:
        try:
            зміна = дані["swap"]
            межа.тіло(json.dumps(зміна, ensure_ascii=False))
            _перевірити(зміна, схема_опису["swap"], "swap")
            забрати, взяти = зміна["item"], зміна.get("to")
            адреса, кандидат = межа.адреса_речі(забрати), межа.адреса_речі(взяти)
            if адреса not in хибні or кандидат is None or межа.факти[взяти]["state"] != КАНДИДАТ_ЗАМІНИ:
                raise _Невірне("swap", "expected a flagged photo and candidate fact")
            заміна = dict(зміна, item=адреса, to=кандидат)
        except ІдУТілі as помилка:
            розбіжності.append(dict(чому="pool_address" if помилка.збій.вид == "pool_address_in_body" else "swap_fact"))
        except _Невірне:
            розбіжності.append(dict(чому="swap_fact"))
    return хибні, заміна, оцінено


def текст_картки(відп, межа, склад, спроба, фото=()):
    """Читає спільний вихід мовної моделі й звірку доставлених кадрів, коли вона була запитана."""
    try:
        дані = _дані(відп, "опис", спроба, усе_за_схемою=False)
        if isinstance(дані, Збій):
            return дані
        речення, розбіжності, прийнято = _тексти_картки(дані, межа)
        хибні, заміна, оцінено = _кадри_картки(дані, межа, фото, розбіжності)
        номери = (н for н, ф in межа.факти.items() if ф["state"] == ПРЕДМЕТ)
        речення["items"] = dict(zip((р["н"] for р in склад.речі), номери, strict=True))
        return Опис(склад.образ, tuple(р["н"] for р in склад.речі), "", (), хибні, (),
                    заміна, оцінено, речення, tuple(розбіжності), прийнято)
    except (ValueError, TypeError) as помилка:
        поле = помилка.поле if isinstance(помилка, _Невірне) else "response"
        return Збій("схема", "розбір", поле, str(помилка), відп.get("текст"), спроба)


def прочитати(відп, вид, пул, спроба=1, образи=(), образ=None, дозволені=None, відкинуті=None):
    """Розбирає відповідь даного виду або повертає Збій із сирою відповіддю."""
    try:
        дані = _дані(відп, вид, спроба)
        if isinstance(дані, Збій):
            return дані
        if вид in ("складання", "ремонт"):
            return _образи(дані, вид, пул, образи, пул.записи if дозволені is None else дозволені, відкинуті)
        if вид == "опис":
            return _опис(дані, образ)
        return дані
    except json.JSONDecodeError as помилка:
        вид_збою = "схема" if помилка.msg == "Extra data" else "не_json"
        return Збій(вид_збою, "розбір", вид, помилка.msg, відп.get("текст"), спроба)
    except _Невірне as помилка:
        return Збій(помилка.вид, "розбір", помилка.поле, str(помилка), відп.get("текст"), спроба)
    except TypeError as помилка:
        return Збій("схема", "розбір", вид, str(помилка), repr(відп.get("текст")), спроба)


def замінити(образ, пул, прибрати, додати, джерело):
    """Пише перевірений новий склад після явної модельної правки."""
    старі = [р["н"] for р in образ.речі]
    нові = [додати if н == прибрати and додати is not None else н for н in старі
            if н != прибрати or додати is not None]
    try:
        if прибрати not in старі or not нові or нові == старі:
            raise _Невірне("swap", "swap does not change the composition")
        речі = _склад(нові, пул, f"{образ.номер}.items", пул.записи)
    except _Невірне as помилка:
        return Збій(помилка.вид, "розбір", помилка.поле, str(помилка))
    return Образ(ід=f"{образ.ід}:{джерело}", номер=образ.номер, рука=образ.рука, джерело=джерело,
                 версія_ситуації=образ.версія_ситуації, речі=речі, полюс=образ.полюс,
                 попередник=образ.ід, свідомі=tuple(з for з in образ.свідомі if з["річ"] != прибрати),
                 носіння=tuple(з for з in образ.носіння if з["item"] != прибрати))


with Path(__file__).with_name("дані").joinpath("руки_без_коду.json").open(encoding="utf-8") as _файл:
    _СЛОТИ_БЕЗ_КОДУ = json.load(_файл)["слоти"]
_МІТКА_ПРОЗИ = "OUTFIT_TEXT"   # код форми відповіді в чинному промпті рук 3–4 (`answer`)
_ОБГОРТКА = " \t\r\n*#_`\"'"
_HEX = frozenset("0123456789abcdefABCDEF")


def проза(відп, спроба=1):
    """Ч5 руки 3–4: проза образу. Код знімає з початку лише свій код форми (`OUTFIT_TEXT`), слів не читає;
    порожньо — `Збій`."""
    if "збій" in відп:
        return _дані(відп, "образ", спроба)
    т = відп.get("текст")
    if not isinstance(т, str):
        return Збій("схема", "розбір", "text", "expected text", repr(т), спроба)
    і = 0
    while і < len(т) and т[і] in _ОБГОРТКА:
        і += 1
    if т[і:і + len(_МІТКА_ПРОЗИ)] == _МІТКА_ПРОЗИ:
        і += len(_МІТКА_ПРОЗИ)
        while і < len(т) and т[і] in _ОБГОРТКА + ":":
            і += 1
        т = т[і:]
    if not т or all(с in _ОБГОРТКА for с in т):
        return Збій("порожньо", "розбір", "text", "the hand returned no outfit text", відп.get("текст"), спроба)
    return т


def перелік(відп, рука, версія, спроба=1, повтор=1):
    """Ч5 руки 3–4: перелік речей прози за схемою `перелік` → `Образ` описаних речей; «не образ» — `Збій`."""
    дані = None
    try:
        дані = _дані(відп, "перелік", спроба)
    except json.JSONDecodeError as помилка:
        return Збій("не_json", "розбір", "перелік", помилка.msg, відп.get("текст"), спроба)
    except _Невірне as помилка:
        return Збій(помилка.вид, "розбір", помилка.поле, str(помилка), відп.get("текст"), спроба)
    if isinstance(дані, Збій):
        return дані
    if дані["is_outfit"] != "yes":
        return Збій("не_образ", "розбір", "is_outfit", "the list model says the description is not an outfit",
                    відп.get("текст"), спроба)
    речі = []
    for р in дані["items"]:
        if р.get("worn") in (False, "false"):
            continue
        hx = р.get("color_hex")
        речі.append({"н": f"о{len(речі) + 1}", "назва": р["name"], "деталі": р.get("details"),
                     "слот": _СЛОТИ_БЕЗ_КОДУ[р["slot"]],
                     "hex": hx if isinstance(hx, str) and len(hx) == 7 and hx[0] == "#" and set(hx[1:]) <= _HEX
                     else None, **({"її": р["own"]} if isinstance(р.get("own"), str) and р["own"] else {})})
    if not речі:
        return Збій("схема", "розбір", "items", "no worn item in the list", відп.get("текст"), спроба)
    return Образ(ід=f"р{рука}-без_коду-{повтор}", номер=f"р{рука}", рука=рука, джерело="модель_без_коду",
                 версія_ситуації=версія, речі=tuple(речі))


def турнір(відп, групи, спроба=1):
    """Ч5 турніру: відповідь за схемою `турнір` → ({група: (переможці)}, чужі). Переможець — лише член своєї групи,
    не більше двох; групу, якої не запитували, і номер не з групи код не бере, а називає в `чужі`."""
    from .пул import ПЕРЕМОЖЦІВ
    try:
        дані = _дані(відп, "турнір", спроба)
    except json.JSONDecodeError as помилка:
        return Збій("не_json", "розбір", "турнір", помилка.msg, відп.get("текст"), спроба)
    except _Невірне as помилка:
        return Збій(помилка.вид, "розбір", помилка.поле, str(помилка), відп.get("текст"), спроба)
    if isinstance(дані, Збій):
        return дані
    переможці, чужі = {}, []
    for запис in дані["winners"]:
        члени = групи.get(запис["group"])
        if члени is None:
            чужі.append(запис["group"])
            continue
        обрані = []
        for н in запис["items"]:
            н = н if н in члени or ("#" + н) not in члени else "#" + н   # «1·03» — та сама річ, що «#1·03»
            if н in члени and н not in обрані:
                обрані.append(н)
            elif н not in члени:
                чужі.append(f'{запис["group"]}:{н}')
        if обрані:
            переможці[запис["group"]] = tuple(обрані[:ПЕРЕМОЖЦІВ])
    return переможці, tuple(чужі)


def оцінка(відп, номери, спроба=1):
    """Ч5 оцінки: відповідь за схемою `оцінка` → ({номер: код}, чужі). Береться перша оцінка речі з запиту; номер не з
    запиту код не бере, а називає в `чужі`; річ без оцінки чекає наступного раунду (повноту звіряють руки)."""
    try:
        дані = _дані(відп, "оцінка", спроба)
    except json.JSONDecodeError as помилка:
        return Збій("не_json", "розбір", "оцінка", помилка.msg, відп.get("текст"), спроба)
    except _Невірне as помилка:
        return Збій(помилка.вид, "розбір", помилка.поле, str(помилка), відп.get("текст"), спроба)
    if isinstance(дані, Збій):
        return дані
    оцінки, чужі = {}, []
    for запис in дані["ratings"]:
        н = запис["n"]
        н = н if н in номери or ("#" + н) not in номери else "#" + н   # «1·03» — та сама річ, що «#1·03»
        if н not in номери:
            чужі.append(н)
        elif н not in оцінки:
            оцінки[н] = запис["verdict"]
    return оцінки, tuple(чужі)


def злити_частини(частини):
    """Образи частин пулу (перемикач «частин») — один набір: номер частини в ід і номері образу, щоб «o1» двох
    частин не злились; склад і решту, що сказала модель, злиття не чіпає."""
    return tuple(replace(о, ід=f"ч{і}-{о.ід}", номер=f"ч{і}-{о.номер}") for і, образи in частини for о in образи)
