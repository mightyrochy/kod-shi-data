"""Ч4. Будує дротові запити зі Ситуації, пулу й перевірених складів."""
from collections import Counter
from itertools import zip_longest
import json
from math import isfinite
from pathlib import Path

from . import задуми, знання, розбір
from .поняття import Запит, Збій, НЕВІДОМО, НЕ_ПЕВНИЙ
from .пул import ДОБІР, СЛОТИ

НАРЯД = None
with Path(__file__).with_name("дані").joinpath("запити.json").open(encoding="utf-8") as _файл:
    _ЗАДАЧІ = json.load(_файл)
with Path(__file__).with_name("дані").joinpath("вікно.json").open(encoding="utf-8") as _файл:
    _МЕЖІ = json.load(_файл)

_ПОЛЯ_ДНЯ = {
    "подія": "occasion", "роль": "role", "місяць": "month", "день_тижня": "weekday",
    "смуга_погоди": "weather_band", "опади": "precipitation", "ошатність": "formality",
    "рух": "movement", "пішки_хв": "walk_min", "поверхня": "surface", "тривалість": "duration_hours",
    "пора_року": "season", "смуга_ошатності": "formality_range", "світло": "light", "сіль": "salt",
}
_ПОЛЯ_РЕЧІ = {
    "тип": "type", "довжина": "length", "довжина_виробу": "garment_length", "тканина": "fabric", "сезон_тканини": "fabric_season",
    "крій": "cut", "візерунок": "pattern", "блиск": "shine", "ошатність": "formality",
    "колір_другий": "secondary_color", "каблук": "heel", "підошва": "sole", "рукав": "sleeve",
    "виріз": "neckline", "посадка": "rise", "реєстр": "register", "ярус_крою": "cut_tier", "метал": "metal",
}
_КОЛОНКИ_КОЛЬОРУ = ("color", "hex", "family", "L", "branch_source", "in_arc", "L_from", "palette_branch")
_КОЛОНКИ = ("n", "price", "kind", *_КОЛОНКИ_КОЛЬОРУ, *_ПОЛЯ_РЕЧІ.values(), "reason", "sources", "rank_facts")
_ПОЛЯ_ДЖЕРЕЛ = {**_ПОЛЯ_ДНЯ, **_ПОЛЯ_РЕЧІ, "чужий_колір": "reserved_color", "названі_речі": "named_items"}


def _значення(значення):
    """Перекладає мітки стану на дріт."""
    if значення == НЕВІДОМО:
        return "unknown"
    if значення == НЕ_ПЕВНИЙ:
        return "uncertain"
    return значення


def _поле(факт):
    """Подає значення й доступний провенанс без уривків із годинами."""
    значення = _значення(факт.значення)
    if not факт.джерело:
        return значення
    вихід = {"value": значення, "source": факт.джерело}
    if факт.з_чого:
        вихід["from"] = [_ПОЛЯ_ДЖЕРЕЛ.get(п, п) for п in факт.з_чого]
    if факт.значення == НЕ_ПЕВНИЙ:
        вихід["range"] = факт.межі
    return вихід


def _день(ситуація):
    """Переносить факти дня і всі етапи в одному місці."""
    факти = {**ситуація.сказала, **ситуація.виведено}
    день = {дріт: _поле(факти[поле]) for поле, дріт in _ПОЛЯ_ДНЯ.items()}
    етапи = ситуація.сказала["етапи"]
    день["stages"] = ([] if етапи == НЕВІДОМО else [
        {"place": _значення(е.місце), "outdoors": _значення(е.надворі),
         "part_of_day": _значення(е.частина_дня), "source": е.джерело} for е in етапи])
    if день["stages"] and день["stages"][0]["place"] != "unknown":
        день["place"] = день["stages"][0]["place"]
    день["unknown"] = [ключ for ключ, в in день.items() if в == "unknown"]
    return день


def _випадок(ситуація):
    """Подає побажання, відмови й намір з їхнім джерелом."""
    сказала = ситуація.сказала
    наміри = сказала["намір"]
    названі = сказала["названі_речі"]
    return {"goal": _поле(сказала["мета"]), "goal_priorities": _поле(сказала["мета_важливо"]),
            "goal_zones": _поле(сказала["мета_зони"]), "intent": [] if наміри == НЕВІДОМО else [_поле(ф) for ф in наміри],
            "wishes": _поле(сказала["бажання"]), "refusals": _поле(сказала["відмови"]),
            "palette_scheme": _поле(сказала["схема"]),
            "named_items": [] if названі == НЕВІДОМО else [
                {"type": _значення(р.що), "shop": _значення(р.крамниця), "color": _значення(р.колір),
                 "fabric": _значення(р.матеріал), "owned": _значення(р.її_річ), "source": р.джерело}
                for р in названі]}


def _палітра(ситуація, вид):
    підсумок = _поле(ситуація.виведено["палітра_дня"])
    план = getattr(ситуація, "план_палітри", None)
    if not план or вид not in ("складання", "опис"):
        return підсумок
    поля_дроту = план.get("поля_дроту", {})
    if not план["вікна"]:
        return {**підсумок, "value": поля_дроту} if вид == "складання" else підсумок

    from face_features import джерело_виміру
    from palettes import для_пакета, палітра_практична

    риси = план["F"]
    палітра = палітра_практична(риси, source=джерело_виміру(риси), самозвіт=план["самозвіт"])
    практична = для_пакета(палітра)
    if вид == "опис":
        метал = {"золото": "gold", "срібло": "silver"}.get(практична.get("метал"))
        if метал and (практична.get("axes") or {}).get("source_hue") == "self_report":
            return {"metal": метал, "metal_from": "her_words"}
        return підсумок

    from внутрішня_мова import код

    практична.pop("feature_measurements", None)
    практична.pop("метал", None)
    if "прийоми" in практична:
        практична["прийоми"] = [п for п in практична["прийоми"] if п["прийом"] != "метал"]
    for ключ, типи in (("neutrals", {"нейтраль", "світла_нейтраль", "темна_нейтраль"}), ("accents", {"колір"})):
        практична[ключ] = list(dict.fromkeys(
            " ".join(в for в in (код("color_name", к.get("назва")) or к.get("назва"), к.get("hex")) if в)
            for к in палітра["кольори"] if к["роль"] in типи))
    return {**підсумок, "value": {**підсумок["value"], "practical": практична, **поля_дроту}}


def _людина(ситуація, профіль, вид):
    """Подає відомі мірки й чинні обчислення профілю зі штатних вимірів."""
    мірки = профіль.get("мірки") or профіль
    тіло = {}
    зріст = мірки.get("зріст")
    try:
        зріст = float(зріст) if зріст else None
    except (TypeError, ValueError):
        зріст = None
    if зріст:
        тіло["height_cm"] = round(зріст, 1)
    обхвати = мірки.get("обхвати") or {}
    if all(isinstance(обхвати.get(к), (int, float)) and обхвати[к] > 0
           for к in ("плечі", "груди", "талія", "стегна")):
        from fit import зони

        обчислене = зони(мірки)
        назви = {"верх_проти_низу": "top_vs_bottom", "талія_виражена": "waist_defined", "талія_підстава": "waist_basis"}
        ярлик = обчислене["ярлик"]
        тіло.update(shape="HX" if ярлик == "H/X межа" else ярлик,
                    zones={назви.get(к, к): в for к, в in обчислене["вектор"].items()})
    наміри = ситуація.сказала["намір"]
    if тіло.get("zones") and "профіль" in мірки and наміри != НЕВІДОМО and наміри and вид in ("складання", "опис"):
        намір = наміри[-1].значення
        if isinstance(намір, str) and намір not in (НЕВІДОМО, НЕ_ПЕВНИЙ):
            from hypergraph import тіло_для_опису

            фігура = тіло_для_опису(мірки, intent=намір)
            if фігура.get("заяви"):
                тіло["statements"] = фігура["заяви"]
    людина = {"palette": _палітра(ситуація, вид), "body": тіло}
    риси = getattr(ситуація, "риси_портрета", None)
    if риси:
        from face_features import для_моделі, ознаки

        людина["colouring"] = для_моделі(ознаки(риси))
    return людина


def _рід_і_тип(річ):
    """Повертає підтверджені форму назви роду й типу для опису."""
    from знання_речі import тип_кодом, тип_свого_роду

    рід = СЛОТИ[річ.слот]
    тип = тип_свого_роду(тип_кодом({"тип": річ.поля["тип"].значення}), рід)
    return {"kind": рід, "type": тип or "unknown"}


def _рядок(н, річ, кандидат, *, спільні_поля=False):
    """Подає колонки речі з одного запису фактів."""
    колір = річ.поля["колір"]
    дані = колір.значення if isinstance(колір.значення, dict) else {}
    межі = колір.межі if isinstance(колір.межі, dict) else {}
    ранг = кандидат.get("факти_рангу", {})
    гілка = ранг.get("branch")
    вихід = {"n": н, "price": _значення(річ.ціна), "kind": СЛОТИ[річ.слот],
             "color": дані.get("color") or межі.get("color") or "unknown",
             "hex": дані.get("hex") or "unknown", "family": дані.get("family") or "unknown",
             "L": дані.get("L", "unknown"), "branch_source": колір.джерело or "unknown",
             "in_arc": "unknown",
             "palette_branch": гілка or "unknown", "L_from": колір.джерело if "L" in дані else "unknown",
             "reason": кандидат["за"] or {"code": "no_reason"}, "rank_facts": ранг}
    вихід.update({дріт: _значення(річ.поля[поле].значення) for поле, дріт in _ПОЛЯ_РЕЧІ.items()})
    вихід["sources"] = {дріт: _поле(річ.поля[поле]) for поле, дріт in _ПОЛЯ_РЕЧІ.items()
                        if річ.поля[поле].джерело}
    if спільні_поля:
        вихід["rank_facts"] = {к: в for к, в in ранг.items() if к != "branch"}
        for назва, факт in вихід["sources"].items():
            if факт["value"] == вихід[назва]:
                del факт["value"]
    довжина = річ.поля["довжина"]
    if довжина.джерело == "код" and довжина.межі:
        вихід["sources"]["length"]["catalogue_source"] = довжина.межі
    if колір.джерело:
        джерело = _поле(колір)
        if спільні_поля and дані:
            джерело["value"] = {к: в for к, в in дані.items()
                                 if к not in ("color", "hex", "family", "L") or в != вихід[к]}
        вихід["sources"]["color"] = джерело
    return вихід


def _стани(ситуація, речі, профіль):
    """Подає правило як діюче лише за наявного входу."""
    вихід = []
    for код, стан in знання.стан_правил(ситуація, речі, профіль).items():
        if стан["стан"] == "нема_чого":
            continue
        запис = {"id": код}
        if стан["стан"] == "немає_входу":
            запис["missing_input"] = стан["поле"]
        else:
            запис["rule"] = знання.ПРАВИЛА[код]["опис"]
        if код == "K-KOH-08":
            запис["origin"] = _поле(ситуація.виведено["чужий_колір"])
        вихід.append(запис)
    return вихід


def _номери_заяви(значення, адреси):
    """Перенумеровує лише предметні поля договору statements."""
    if isinstance(значення, dict):
        рядок = {}
        for ключ, в in значення.items():
            if ключ == "item_id" and isinstance(в, str):
                рядок[ключ] = адреси.get(в, "unknown")
            elif ключ == "item_ids" and isinstance(в, (tuple, list)):
                рядок[ключ] = [адреси.get(і, "unknown") for і in в if isinstance(і, str)]
            else:
                рядок[ключ] = _номери_заяви(в, адреси)
        return рядок
    if isinstance(значення, (tuple, list)):
        return [_номери_заяви(в, адреси) for в in значення]
    return значення


def _заяви(вирок, адреси):
    """Кодує факти тільки з вироку цього складу."""
    заяви = []
    for з in вирок.заяви:
        д = з.значення
        запис = {"id": з.ід, "code": з.код, "values": _номери_заяви(д["факти"], адреси), "items": з.речі,
                 "rule": з.правило, "register": д["регістр"], "repair": д["ремонт"]}
        for поле, ключ in (("вага", "weight"), ("утримано", "withheld"), ("впевненість", "confidence")):
            if д.get(поле) is not None:
                запис[ключ] = д[поле]
        заяви.append(запис)
    return заяви


def _образ(образ, вирок, *, опис):
    """Подає вирок поточного складу і залишає попередній підпис поза описом."""
    адреси = {**{н: н for н in вирок.склад}, **{р["ід"]: р["н"] for р in образ.речі}}
    вихід = {"id": образ.номер, "items": вирок.склад, "findings": _заяви(вирок, адреси),
             "checklist": вирок.чекліст,
             "your_declared": [{"item": х["річ"], "finding": х["заява"], "why": х["чому_en"]}
                               for х in образ.свідомі]}
    if опис:
        вихід["findings"] = [{к: в for к, в in з.items() if в not in (None, [], (), {})}
                             for з in вихід["findings"]]
    else:
        вихід.update(caption=образ.підпис_en, day=образ.день_en)
        if образ.полюс != НЕВІДОМО:
            вихід["pole"] = образ.полюс
        if образ.носіння:
            вихід["worn"] = образ.носіння
    return вихід


def _укладка(образ, вирок, пул, ситуація):
    """Подає штатні команди обраного складу з адресами речей."""
    слоти = {р["н"]: пул.записи[р["н"]].слот for р in образ.речі}
    вихід = list(образ.носіння)
    формати = {н: set() for н, слот in слоти.items() if слот == "шарф"}
    відомі = set()
    for заява in вирок.заяви:
        команда = _ЗАДАЧІ["опис"]["команди_укладки"].get(заява.код)
        for н in заява.речі:
            if команда and команда == заява.правило and слоти.get(н) == "верхній_шар":
                вихід.append({"item": н, "finding": заява.ід})
                відомі.add((н, заява.код))
            if (н in формати and заява.правило == "K-CRA-12"
                    and заява.код in ("scarf_wraps_head", "scarf_too_small_to_wrap_head")):
                розмір = заява.значення["факти"].get("size_cm")
                if type(розмір) in (int, float) and isfinite(розмір) and розмір > 0:
                    формати[н].add(розмір)
    if формати:
        from аксесуари_структура import команди_розкладки

        хустки = [{"id": н, "слот": "шарф", "тип": пул.записи[н].поля["тип"].значення,
                   "розмір_см": next(iter(розміри)) if len(розміри) == 1 else None}
                  for н, розміри in формати.items()]
        for опції in команди_розкладки(хустки):
            вихід.append({"item": опції["річ"], "statements": [
                {"code": з["code"], "values": з["values"]} for з in опції["опції_заяви"]]})
    for рядок in знання.команди_верхнього_шару([(н, пул.записи[н]) for н in слоти], ситуація):
        заяви = [з for з in рядок["statements"] if (рядок["item"], з["code"]) not in відомі]
        if заяви:
            вихід.append(dict(рядок, statements=заяви))
    return вихід


def _набір(образи, пул):
    """Рахує факти на складах запропонованих образів."""
    from coordination import C, ранг_у_наборі, розкид_набору, середня_близькість
    from outfit import елементи

    спільні, близькості = {}, {}
    for образ in образи:
        речі = [знання.старий_запис(пул.записи[р["н"]]) for р in образ.речі]
        for р in образ.речі:
            спільні.setdefault(р["н"], []).append(образ.номер)
        try:
            близькість = середня_близькість(елементи(речі))
        except ValueError:
            continue
        if близькість is not None:
            близькості[образ.номер] = близькість

    набір = {"offered_outfits": [о.номер for о in образи]}
    повтори = [{"item": н, "outfits": ід} for н, ід in спільні.items() if len(ід) > 1]
    if повтори:
        набір["shared_items"] = повтори
    числа = list(близькості.values())
    if розкид_набору(числа)["можна"]:
        вершина = min(0.95, max(0.05, 0.5 + C["зсув_вершини"]))
        набір["coordination"] = []
        for ід, близькість in близькості.items():
            ранг = ранг_у_наборі(близькість, числа)
            бік = "none" if abs(ранг - вершина) < 1e-9 else ("apart" if ранг < вершина else "together")
            набір["coordination"].append({"id": ід, "rank": ранг, "side": бік})
    return набір


def _спільне_ремонту(тіло):
    """Пише рівні чеклісти та повторювані тексти замін один раз."""
    вироки = тіло["verdict"]
    if len(вироки) > 1:
        разом = {к: в for к, в in вироки[0]["checklist"].items()
                 if all(о["checklist"].get(к) == в for о in вироки[1:])}
        if разом:
            тіло["set"]["shared_checklist"] = разом
            for образ in вироки:
                образ["checklist"] = {к: в for к, в in образ["checklist"].items() if к not in разом}
    знахідки = [з for о in вироки for з in о["findings"] if з["repair"]]
    відбитки = [json.dumps(з["repair"], ensure_ascii=False, sort_keys=True) for з in знахідки]
    повтори = Counter(відбитки)
    адреси = {}
    for заява, відбиток in zip(знахідки, відбитки):
        if повтори[відбиток] > 1:
            адреса = адреси.setdefault(відбиток, f"r{len(адреси) + 1}")
            тіло.setdefault("fixes", {}).setdefault(адреса, заява.pop("repair"))
            заява["repair_ref"] = адреса


def _під_вікно(тіло, поле_пулу, рядки, групи, закріплені, ліміт, оцінити, блоки_пулу):
    """Міряє весь текст і фото із запасом відповіді, зрізає лише додаткових кандидатів."""
    def текст(кандидати):
        номери = tuple(кандидати)
        тіло[поле_пулу]["rows"] = [рядки[н] for н in номери]
        тіло.update(блоки_пулу(номери))
        return json.dumps(тіло, ensure_ascii=False, separators=(",", ":"))

    всі = tuple(рядки)
    обовʼязкові = tuple(н for н in всі if н in закріплені)
    мінімум = текст(обовʼязкові)
    if оцінити(мінімум) > ліміт:
        return мінімум, обовʼязкові
    повний = текст(всі)
    if оцінити(повний) <= ліміт:
        return повний, всі
    решта = [н for ряд in zip_longest(*групи.values()) for н in ряд if н is not None and н not in закріплені]
    низ, верх = 0, len(решта)
    while низ < верх:
        середина = (низ + верх + 1) // 2
        вибір = закріплені | set(решта[:середина])
        if оцінити(текст(н for н in всі if н in вибір)) <= ліміт:
            низ = середина
        else:
            верх = середина - 1
    вибір = закріплені | set(решта[:низ])
    номери = tuple(н for н in всі if н in вибір)
    return текст(номери), номери


def запит(вид, пул, ситуація, профіль, *, образи=(), вироки=None, спроба=1, збій=None,
          без_фото=False, дозволені=None, заміни=True, модель=None, перевірити_кадр=None, хибні=()):
    """Прив'язує модельний запит до версії й конкретного складу."""
    if пул.версія_ситуації != ситуація.версія:
        return Збій("застаріла_версія", "запит", "версія_ситуації")
    вироки = вироки or {}
    повний_пул = вид in ("складання", "ремонт")
    if вид == "опис" and len(образи) != 1:
        return Збій("схема", "запит", "outfit", "Description requires exactly one outfit", спроба=спроба)
    for образ in образи:
        вирок = вироки.get(образ.ід)
        if (вирок is None or вирок.образ != образ.ід or вирок.версія_ситуації != ситуація.версія
                or образ.версія_ситуації != ситуація.версія
                or tuple(вирок.склад) != tuple(р["н"] for р in образ.речі)):
            return Збій("схема", "запит", "verdict", "Verdict does not match the outfit and day", спроба=спроба)
    склад = tuple(dict.fromkeys(р["н"] for образ in образи for р in образ.речі))
    дозволені = None if дозволені is None else set(дозволені)
    доступні = {к["н"] for к in пул.речі if дозволені is None or к["н"] in дозволені}
    if not доступні.issuperset(склад) or any(
        пул.записи[р["н"]].ід != р["ід"] for образ in образи for р in образ.речі
    ):
        return Збій("схема", "запит", "items", "An outfit item is outside the allowed pool", спроба=спроба)
    можна_заміни = вид == "опис" and заміни and not без_фото and перевірити_кадр is None
    слоти_заміни = {пул.записи[н].слот for н in склад if пул.записи[н].фото} if можна_заміни else set()
    номери = [к["н"] for к in пул.речі if к["н"] in доступні
              and (повний_пул or к["н"] in склад
                   or слоти_заміни and пул.записи[к["н"]].слот in слоти_заміни and пул.записи[к["н"]].фото)]
    кандидати = {к["н"]: к for к in пул.речі}
    причини = {н: к["за"] for н, к in кандидати.items()}
    колонки = tuple(к for к in _КОЛОНКИ if к not in ("reason", "rank_facts")) if вид == "опис" else _КОЛОНКИ
    рядки, групи = {}, {}
    for н in номери:
        річ = пул.записи[н]
        групи.setdefault(річ.слот, []).append(н)
        рядок = _рядок(н, річ, кандидати[н], спільні_поля=вид != "вибір")
        рядки[н] = [рядок[поле] for поле in колонки]
    фото = tuple({"n": н, "url": пул.записи[н].фото[0], "токени": 2_000} for н in склад if пул.записи[н].фото
                 ) if вид == "опис" and not без_фото else ()
    поле_пулу = "candidates" if вид in ("ремонт", "вибір") else "pool"
    тіло = {
        "version": "1", "task": {"role": _ЗАДАЧІ[вид]["role"], "rules": _ЗАДАЧІ[вид]["rules"] + _ЗАДАЧІ["спільне"]},
        "version_of_day": ситуація.версія, "case": _випадок(ситуація), "day": _день(ситуація),
        "person": _людина(ситуація, профіль, вид),
        поле_пулу: {"cols": колонки, "rows": []}, "required_kinds": пул.обовʼязкові,
        "kind_limits": пул.межі_слотів, "kinds_missing": [СЛОТИ[р["слот"]] for р in пул.нема_в_каталозі],
        "answer_schema": розбір.схема(вид),
    }
    if вид != "складання":
        тіло["style_rules"] = _стани(ситуація, [пул.записи[н] for н in склад], профіль)
    if вид in ("складання", "ремонт"):
        тіло["outfits_wanted"] = ДОБІР["скласти" if вид == "складання" else "після_ремонту"]
    if вид == "складання" and "outerwear" in пул.обовʼязкові:
        тіло["coat_required"] = True
    твердження_тіла = тіло["person"]["body"].get("statements", ())
    коди = [з["code"] for з in твердження_тіла]
    for заява in твердження_тіла:
        if заява["code"] == "body_knot":
            коди.extend(заява["values"]["shared"])
            коди.extend(заява["values"]["own"])
    if образи:
        тіло["verdict"] = [_образ(о, вироки[о.ід], опис=вид == "опис") for о in образи]
        коди.extend(з.код for о in образи for з in вироки[о.ід].заяви)
    if вид in ("складання", "ремонт", "вибір"):
        тіло["selection_policy"] = {"priority": ["her occasion, day and intent", "distinct outfit idea"],
                                    "findings_are_scores": False}
        ключі = "pool_keys" if вид == "складання" else "item_keys"
        тіло[ключі] = {"n": "exact item number", "reason": "why this item is here, if known",
                       "sources": "provenance; repeated field values and color/hex/family/L are in the same row",
                       "palette_branch": "branch for rank_facts"}
    if вид in ("ремонт", "вибір"):
        тіло["set"] = _набір(образи, пул) if образи else {"offered_outfits": []}
        тіло["now"] = _ЗАДАЧІ[вид]["now"]
    if вид == "ремонт" and образи:
        _спільне_ремонту(тіло)
        недоступні = {}
        for група, пункти in знання.ЧЕКЛІСТИ.items():
            пропуски = [п for п in пункти if all(
                вироки[о.ід].чекліст.get(f"{група}.{п}", {}).get("стан") == "немає_входу" for о in образи)]
            if пропуски:
                недоступні[група] = пропуски
        тіло["not_run_everywhere"] = недоступні
    if вид == "вибір":
        за_кодом = {}
        for образ in тіло.get("verdict", ()):
            for заява in образ["findings"]:
                if not заява.get("withheld"):
                    за_кодом.setdefault(заява["code"], []).append({"outfit": образ["id"], "id": заява["id"]})
        тіло["remarks_by_code"] = за_кодом
    if вид == "опис":
        тіло["body"] = тіло["person"].pop("body")
        з_фото = {ф["n"] for ф in фото}
        тіло["outfit"] = {"id": образи[0].номер, "items": [
            {"n": н, **_рід_і_тип(пул.записи[н])} for н in склад]}
        укладка = _укладка(образи[0], вироки[образи[0].ід], пул, ситуація)
        if укладка:
            тіло["ways_to_wear"] = укладка
            коди.extend(з["code"] for рядок in укладка for з in рядок.get("statements", ()))
        тіло["reasons"] = [
            {"n": н, **(причини[н] or {}), "rank_facts": кандидати[н].get("факти_рангу", {})}
            for н in склад if причини[н] or кандидати[н].get("факти_рангу")]
        тіло["photos"] = [ф["n"] for ф in фото]
        if хибні:
            тіло["confirmed_wrong_photos"] = [н for н in склад if пул.записи[н].фото
                and (пул.записи[н].ід, пул.записи[н].фото[0]) in хибні]
        if перевірити_кадр in з_фото:
            тіло["photo_check_item"] = перевірити_кадр
            тіло["task"]["rules"].append(_ЗАДАЧІ["опис"]["звірка_заміни"])
            схема = тіло["answer_schema"]
            тіло["answer_schema"] = {**схема, "required": [*схема["required"], "wrong_photos"]}
    if коди:
        from внутрішня_мова import визначення_заяв

        тіло["task"]["statement_codes"] = визначення_заяв(коди)
    тіло["knowledge_legend"] = {
        "unknown": "The value is missing. Make no claim about it.",
        "uncertain": "Only the supplied interval or bounds are known.",
        "missing_input": "The rule could not be applied with the available inputs.",
    }
    if any(з["findings"] and any(р.get("withheld") for р in з["findings"]) for з in тіло.get("verdict", ())):
        тіло["knowledge_legend"]["withheld"] = "Judgment withheld. Keep the uncertainty. It is neither a finding to fix nor evidence of a pass."

    if вид == "опис":
        тіло["knowledge_legend"]["sources"] = "Repeated values are in the row."
        тіло["knowledge_legend"]["findings"] = "Omitted fields are empty."
        for ключ in ("kind_limits", "kinds_missing", "required_kinds"):
            if not тіло[ключ]:
                del тіло[ключ]
    базові_правила = тіло["task"]["rules"]

    def блоки_пулу(видимі):
        """Повертає блоки, істинні для речей після обрізання пакета."""
        речі = [пул.записи[н] for н in видимі]
        результат = {}
        if вид == "складання":
            правила = _стани(ситуація, речі, профіль)
            полюси, відсутні = задуми.доступні(речі, тіло["outfits_wanted"],
                                                    гілки=[кандидати[н].get("факти_рангу", {}).get("branch")
                                                           for н in видимі])
            результат.update(poles=полюси, poles_unavailable=відсутні, style_rules=правила,
                             occasion_rules=[п["id"] for п in правила if п["id"] in ("K-KOH-07", "K-KOH-08")],
                             kind_notes={СЛОТИ[слот]: кількість for слот, кількість in Counter(р.слот for р in речі).items()})
        elif вид == "ремонт":
            результат["showcase"] = [н for н in видимі if н not in склад]
            розрив = {СЛОТИ[пул.записи[н].слот] for н in видимі
                      if кандидати[н].get("факти_рангу", {}).get("primary_break") is True}
            if len(розрив) == 1:
                результат["break_kind"] = next(iter(розрив))
            else:
                тіло.pop("break_kind", None)
        elif вид == "опис":
            запасні = [н for н in видимі if н not in склад]
            результат["swap_candidates"] = запасні
            тіло["task"]["rules"] = ([*базові_правила, _ЗАДАЧІ["опис"]["заміна"]]
                                    if запасні else базові_правила)
        return результат
    if збій:
        тіло["format_error" if вид == "опис" else "retry"] = {"field": збій.поле, "reason": збій.що}
    налаштування = модель or {}
    відповідь = налаштування.get("вихід") or 4_000
    вікно = налаштування.get("вікно")
    if (type(відповідь) is not int or відповідь < 1
            or вікно is not None and (type(вікно) is not int or вікно < 1)):
        return Збій("вікно_моделі", "запит", "window", "Expected positive integer token counts", спроба=спроба)

    оцінити = знання.палітрові_знання().оцінити_текст_ядра
    фото_токени = sum(ф["токени"] for ф in фото)
    підписи = оцінити("\n".join("Catalogue photo for item " + ф["n"] for ф in фото))
    джерело = "model_context" if вікно is not None else "legacy_assembly_offline_max"
    межа = вікно if вікно is not None else _МЕЖІ[джерело]["limit_tokens"]
    ліміт = межа - відповідь - фото_токени - підписи
    закріплені = set(склад)
    for слот, група in групи.items():
        if повний_пул and СЛОТИ[слот] in пул.обовʼязкові and закріплені.isdisjoint(група):
            закріплені.add(група[0])
    текст, надіслано = _під_вікно(тіло, поле_пулу, рядки, групи, закріплені, ліміт, оцінити, блоки_пулу)
    оцінка = оцінити(текст)
    розмір = {"method": "offline_qwen_weighted_1.1", "context_tokens": вікно,
              "limit_source": джерело, "limit_tokens": межа,
              "json_utf8_bytes": len(текст.encode("utf-8")), "json_tokens_estimate": оцінка,
              "photo_label_tokens_estimate": підписи, "photo_count": len(фото),
              "photo_tokens_estimate": фото_токени, "response_reserved_tokens": відповідь}
    if оцінка > ліміт:
        дані = dict(розмір, stage=вид, mandatory_total_tokens_estimate=оцінка + підписи + фото_токени + відповідь)
        return Збій("вікно_моделі", "запит", "window",
                    "Required request exceeds the estimated limit", спроба=спроба, дані=дані)
    мітка = образи[0].ід if вид == "опис" else "рука"
    return Запит(ключ=f"р{пул.рука}-{вид}-{мітка}-{int(заміни)}-{спроба}", рука=пул.рука, вид=вид, версія_ситуації=ситуація.версія,
                 сід=пул.сід, модель={"max_tokens": відповідь, "messages": [{"role": "user", "content": текст}]},
                 фото=фото, номери=надіслано, знято=len(номери) - len(надіслано), розмір=розмір)
