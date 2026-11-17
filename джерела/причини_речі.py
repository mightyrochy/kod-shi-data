"""Причини «чому ця річ тут для неї» — від коду, з номером речі, джерелом і певністю (корінь Е2-опора-пояснення).

ЧОМУ МОДУЛЬ (менеджер 17.11 після прогону #4205, наряд `Е2-опора-пояснення-причини-за`). Крок «без опису речі» зняв з
дроту пояснення вигляд речі й попросив «чому вона тут» — а причин не дав: на дроті річ мала лише рід і кадри, а з суду
доходили тільки знахідки проти неї, які прийняв вибір. Модель добудовувала причину сама: «Tall boots suit a 20-minute
walk in snow» при `sole_grip_unknown_ice` тієї самої руки, «staying steady for an outdoor ceremony», «let you walk and
sit comfortably through dinner» (дошка 16385–16389). Причин «за» у вході — 0 із 30 речей. Тепер причину пише ОДИН
писач — цей модуль — з того, що код знає сам, і пояснення лише каже її словами; річ без причини окремого запису не
дістає (`розбір_відповідей.опис_відповідь_з_json`, `з_причинами`).

Причини (`about`) — ті, що назвав власник, і день:
- `occasion` — рівень речі (`graph.зона` → `формальність.інтервал`) перетинає рівень її нагоди (`день_кодами.formality`);
- `palette` — барва речі в дузі її палітри (`у_дузі` запису пулу суду), з джерелом кольору (`L_from`);
- `figure` — крій речі в ярусі кроїв її постаті (`hypergraph.крої_для_пулу`, той самий ярус, що `cuts_best_on_her`);
- `day` — смуга тканини речі (`зона.сезон.смуга`) покриває смугу погоди, яку назвала вона (лише факт «day» на її словах);
- `her_words` — річ того роду й кольору, який вона назвала побажанням (`паспорт.бажання_коди`), з її фразою;
- `found` — знахідка суду ЗА цю річ (`ЗА_РІЧ`), заявами;
- `unknown` — «не знаю» суду про цю річ (`card_unchecked` з `ЇЙ_У_НЕПЕРЕВІРЕНОМУ`), заявами: `sure: no`.
Речення моделей складання й вибору (`why`, `день_образу`) причиною не стають: їх ніхто не звіряв.
Вигляду речі (колір, крій, тканина словами) запис не несе (слово власника 17.11): причина каже, ЩО код знайшов, а не яка річ.
"""
import json as _json
import graph as _Г
import hypergraph as _ГГ
import outfit as _О
import внутрішня_мова as _ВМ
import дріт_моделі as _Д
from реєстр_правил import ТИПОВИЙ_НАМІР

# Знахідки суду, що кажуть ЗА річ (полярності в словнику заяв нема — `внутрішня_мова.ЗАЯВИ`; визначення цих кодів
# кажуть, що річ дає образу, а не чого їй бракує). Решта знахідок суду — проти речі чи про образ цілий: на дріт
# пояснення вони йдуть лише прийнятими вибором (`your_declared`).
ЗА_РІЧ = frozenset((
    "wool_declared_goes_higher", "layer_closes_wet_windy_regime", "face_field_carrier_frees_top",
    "high_stand_collar_frees_slot", "colour_in_her_palette", "item_suits", "item_suits_with_condition",
))
# «Не знаю» суду, що стає причиною з певністю «ні»: те, що вона бачить на своїй речі чи дасть сама
# (`ЇЙ_У_НЕПЕРЕВІРЕНОМУ`), крім вигляду (колір і крій зі слова — пояснення вигляду не каже) і способу носіння (його
# несуть `ways_to_wear`)
_ВИГЛЯД_НЕВІДОМО = ("colour_", "cut_", "photo_shows_other_colour", "mourning_colour_word_only")
_СПОСІБ_НЕВІДОМО = frozenset(("wear_way_not_chosen", "scarf_near_face_way_unknown"))
НЕ_ЗНАЮ_ПРО_РІЧ = frozenset(к for к in _ВМ.ЇЙ_У_НЕПЕРЕВІРЕНОМУ
                            if not к.startswith(_ВИГЛЯД_НЕВІДОМО) and к not in _СПОСІБ_НЕВІДОМО)
# Заява, що спирається на обставину дня, виведену кодом (сіль — з морозу й снігу, `сценарій` K-WEA-07): на дріт
# пояснення вона йде з позначкою, звідки та обставина (`day_facts`), — «виведено» не стає обставиною її дня (16409)
ФАКТ_ДНЯ_ЗАЯВИ = {"salt_slush_warmer_wears_faster": "road_salt", "outer_composition_unknown_salt": "road_salt"}
for _к in ЗА_РІЧ | set(ФАКТ_ДНЯ_ЗАЯВИ):
    if _к not in _ВМ.ЗАЯВИ:
        raise KeyError("причини_речі: заява поза словником ЗАЯВИ: %r" % (_к,))
_СЛОТ_EN = {v: к for к, v in _ВМ.ТАБЛИЦЯ["slot"].items()}
_ВЕРХ_НИЗ = {"верх": "верх", "низ": "низ", "сукня": "верх", "верхній_шар": "верх"}


def _підпис(з):
    """Зміст заяви — код і значення: та сама знахідка двох проходів суду несе різний `key` (джерело, ранг), а жінці це
    одне й те саме (ж3_театр_тріада: `outfit_level_off_occasion` двічі при кожній речі)."""
    return (з.get("code"), _json.dumps(з.get("values") or {}, sort_keys=True, ensure_ascii=False, default=str))


def додати(куди, заяви):
    """Дописує до списку `куди` заяви, чийого змісту (`_підпис`) там ще нема; вертає `куди`."""
    є = {_підпис(з) for з in куди}
    for з in заяви or []:
        if isinstance(з, dict) and _підпис(з) not in є:
            є.add(_підпис(з))
            куди.append(з)
    return куди


def позначити_виведене(заяви, день):
    """Заяви → ті самі, де заява, що спирається на виведену обставину дня, несе `day_facts` {факт: звідки}."""
    звідки = (день or {}).get("provenance") or {}
    вих = []
    for з in заяви or []:
        ф = ФАКТ_ДНЯ_ЗАЯВИ.get((з or {}).get("code")) if isinstance(з, dict) else None
        if ф and звідки.get(ф) != "her_words":
            з = dict(з, day_facts={ф: звідки.get(ф) or "unknown"})
        вих.append(з)
    return вих


def _ід_заяви(з):
    """Id речей, які називає сама заява (`item_ids`, `item_id`, `item.item_id`, `items[].item_id`)."""
    в = (з or {}).get("values") or {}
    ід = [str(і) for і in ((з or {}).get("item_ids") or [])]
    for к in ("item_id",):
        if в.get(к):
            ід.append(str(в[к]))
    if isinstance(в.get("item"), dict) and в["item"].get("item_id"):
        ід.append(str(в["item"]["item_id"]))
    for x in (в.get("items") or []) if isinstance(в.get("items"), list) else []:
        if isinstance(x, dict) and x.get("item_id"):
            ід.append(str(x["item_id"]))
    return list(dict.fromkeys(ід))


def адресати(речі_запису, заяви, речі):
    """Id речей образу, яких стосується запис суду: спершу адреса самих заяв, далі `речі` запису — id, назва, слот
    (слот — лише коли в образі одна річ цього слота); «образ» і чуже — нікому."""
    склад = {str(р.get("id")): р for р in речі or []}
    ід = [і for з in заяви or [] for і in _ід_заяви(з) if і in склад]
    if ід:
        return list(dict.fromkeys(ід))
    вих = []
    for x in речі_запису or []:
        x = str(x)
        if x in склад:
            вих.append(x)
            continue
        за_назвою = [і for і, р in склад.items() if x in (str(р.get("назва") or ""), str(р.get("назва_показу") or ""))
                     and x]
        за_слотом = [і for і, р in склад.items() if р.get("слот") == x]
        if len(за_назвою) == 1:
            вих.append(за_назвою[0])
        elif len(за_слотом) == 1:
            вих.append(за_слотом[0])
    return list(dict.fromkeys(вих))


def _журналу(з):
    """Заява для журналу (адресат `journal` у самій заяві чи в `МЕТАДАНІ_ЗАЯВ`) — не для неї й не для моделі."""
    return (з.get("recipient") or (_ВМ.МЕТАДАНІ_ЗАЯВ.get(з.get("code")) or {}).get("recipient")) == "journal"


def заяви_за_слотом(заяви, ід_ходу, речі):
    """Заяви оголошеного ходу → {id: [заяви]}: заява з адресою речі (id, слот у значеннях) — при своїй речі (у ході чи,
    коли вона поза ходом, при єдиній такій речі образу); без адреси — при кожній речі ходу (так, як доти). Заява журналу на дріт моделі не йде (16, наряд «причини-за»)."""
    склад = {str(р.get("id")): р for р in речі or []}
    вих = {і: [] for і in ід_ходу}
    for з in заяви or []:
        if not isinstance(з, dict) or not з.get("code"):
            continue
        if _журналу(з):
            continue
        адреса = [і for і in _ід_заяви(з) if і in склад]
        if not адреса:
            слот = _ВМ.ТАБЛИЦЯ["slot"].get(str(((з.get("values") or {}).get("slot")) or ""))
            адреса = [і for і, р in склад.items() if слот and р.get("слот") == слот]
        if not адреса:
            for і in ід_ходу:
                додати(вих[і], [з])
            continue
        # заява з адресою — при своїй речі: у ході, а коли її річ поза ходом — при ній самій, якщо вона в образі одна;
        # не при чужій речі ходу (`accent_role_lost` слота «bag» стояв при туфлях, прогін наряду «причини-за»)
        свої = [і for і in адреса if і in вих] or (адреса if len(адреса) == 1 else [])
        for і in свої:
            додати(вих.setdefault(і, []), [з])
    return вих


def _рівень(р):
    try:
        ф = (_Г.зона(р) or {}).get("формальність") or {}
    except Exception:          # бита річ — без причини нагоди, не без опису (П.14: причина додає, не гейтує)
        return None
    return ф.get("інтервал")


def _смуга(р):
    try:
        с = (_Г.зона(р) or {}).get("сезон") or {}
    except Exception:
        return None
    return с.get("смуга")


def _джерело_кольору(р):
    """Звідки колір речі — та сама вісь, що бачила стилістка складання (`дріт_моделі.осі` → `L_from`)."""
    try:
        return (_Д.осі(_Г.зона(р), р) or {}).get("L_from") or "unknown"
    except Exception:          # бита річ — джерело невідоме, а не довіра
        return "unknown"


def _збіг_бажання(б, р):
    """Побажання (`бажання_коди`) збігається з річчю родом (тип, інакше слот) і кольором, коли вона його назвала."""
    if not isinstance(б, dict):
        return False
    рід = (б.get("тип") and б["тип"] == р.get("тип")) or (not б.get("тип") and б.get("слот") and б["слот"] == р.get("слот"))
    if not рід:
        return False
    колір = б.get("колір")
    return not колір or колір in (р.get("колір"), р.get("код_кольору"), р.get("колір_ім"))


def причини(речі, *, день=None, тіло=None, намір=None, суд=None, паспорт=None, прогін_руки=None):
    """Речі картки (записи показу: id, слот, тип, …) → [{item_id, about, …}] — причини, що знає код.

    `день` — її день кодами з походженням (`міст_опис.день_опису`), `тіло` — `fit.тіло` або None, `суд` — суд образу
    картки, як його шле показ (`знахідки`, `питання` — лише коли верхній образ вердикта і є картка; `образ` — запис
    образу картки з `описи_н` і `ід_за_номером`), `паспорт` — для її побажань,
    `прогін_руки` — прогін поломки руки 2 (ярус кроїв радить так, як радив її бриф). Заяви — сирі, з `day_facts`;
    на дріт їх кладе `дріт_моделі.опис`."""
    вих = []
    день = день if isinstance(день, dict) else {}
    її_день = _Д.день_її_слів(день) or {}
    смуга_дня = її_день.get("weather_band")
    нагода = день.get("formality") if isinstance(день.get("formality"), dict) else None
    try:
        крої = _ГГ.крої_для_пулу(тіло, intent=намір or ТИПОВИЙ_НАМІР, прогін_руки=прогін_руки) if тіло else None
    except Exception:
        крої = None
    суд = суд if isinstance(суд, dict) else {}
    # «у дузі» — суд пулу над річчю картки (`пакет_моделі.у_дузі_вікон`, запис образу вердикта `описи_н`)
    о = суд.get("образ") if isinstance(суд.get("образ"), dict) else {}
    ід_н = о.get("ід_за_номером") if isinstance(о.get("ід_за_номером"), dict) else {}
    дуга = {str(ід_н[н]): з.get("у_дузі") for н, з in (о.get("описи_н") or {}).items()
            if н in ід_н and isinstance(з, dict)}
    бажання = [б for б in ((паспорт or {}).get("бажання_коди") or []) if isinstance(б, dict)]
    for р in речі or []:
        ід = str(р.get("id"))
        if р.get("власна"):
            continue
        рв = _рівень(р)
        if нагода and рв and рв[0] is not None and нагода.get("from") is not None \
                and рв[0] <= нагода.get("to", нагода["from"]) and рв[1] >= нагода["from"]:
            # рівень нагоди код виводить з її слів (місце, подія) — джерело йде поруч (`provenance.formality`)
            вих.append(dict(item_id=ід, about="occasion", what="item_level_within_occasion_level",
                            occasion_level_from=(день.get("provenance") or {}).get("formality") or "unknown",
                            sure="yes"))
        if дуга.get(ід) is True:
            джерело = _джерело_кольору(р)
            вих.append(dict(item_id=ід, about="palette", what="colour_inside_her_palette", colour_from=джерело,
                            sure="yes" if джерело in ("photo", "photo_point") else "no"))
        кр = (крої or {}).get(_ВЕРХ_НИЗ.get(р.get("слот")))
        крій = _О.крій_для_моделі(р) if кр else None
        if крій and set(крій.split("|")) <= set(кр.get("ярус") or ()):
            вих.append(dict(item_id=ід, about="figure", what="cut_in_best_tier_for_her_figure", sure="yes"))
        см = _смуга(р)
        if смуга_дня and см and смуга_дня in см:
            вих.append(dict(item_id=ід, about="day", what="fabric_suits_her_weather", weather_band=смуга_дня,
                            sure="yes"))
        for б in бажання:
            if _збіг_бажання(б, р):
                вих.append(dict(item_id=ід, about="her_words", what="item_she_asked_for",
                                **({"quote": str(б["фраза"])[:80]} if б.get("фраза") else {}), sure="yes"))
                break
    склад = [р for р in речі or [] if not р.get("власна")]
    за, не_знаю = {}, {}
    for з_суду in суд.get("знахідки") or []:
        if not isinstance(з_суду, dict):
            continue
        заяви = [з for з in (з_суду.get("заяви") or []) if isinstance(з, dict) and з.get("code") in ЗА_РІЧ
                 and not _журналу(з)]
        for і in (адресати(з_суду.get("речі"), заяви, склад) if заяви else []):
            додати(за.setdefault(і, []), заяви)
    for п in суд.get("питання") or []:
        пов = (п or {}).get("повідомлення") or {}
        if not isinstance(п, dict) or пов.get("kind") != "card_unchecked":
            continue
        заяви = [з for з in (пов.get("statements") or []) if isinstance(з, dict) and з.get("code") in НЕ_ЗНАЮ_ПРО_РІЧ
                 and not _журналу(з)]
        for і in (адресати(п.get("речі"), заяви, склад) if заяви else []):
            додати(не_знаю.setdefault(і, []), заяви)
    for і, заяви in за.items():
        вих.append(dict(item_id=і, about="found", statements=позначити_виведене(заяви, день), sure="yes"))
    for і, заяви in не_знаю.items():
        вих.append(dict(item_id=і, about="unknown", statements=позначити_виведене(заяви, день), sure="no"))
    порядок = {str(р.get("id")): к for к, р in enumerate(речі or [])}
    return sorted(вих, key=lambda x: порядок.get(x["item_id"], len(порядок)))
