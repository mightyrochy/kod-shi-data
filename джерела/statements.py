"""Договір заяви: предмет і походження переживають переклад та перестановку рядків."""
import hashlib
import json

# Автор поля паспорта й автор вибору палітри — один перелік. Старі записи
# читаються лише цим адаптером; нові писачі передають канонічні коди.
АВТОРИ = frozenset(("her", "conversation", "stylist", "code_rank", "form_default",
                    "item_default", "pending", "unselected", "unknown", "occasion_part_conflict"))
СТАРІ_АВТОРИ = {"рука": "her", "розмова": "conversation", "стилістка": "stylist",
                "типове_форми": "form_default", "типово для речі з фото": "item_default",
                "вона обрала сама": "her", "стилістка обрала під цей вихід": "stylist",
                "код запропонував, вона не міняла": "code_rank",
                "she_chose": "her", "stylist_chose": "stylist", "code_default": "code_rank"}
АДРЕСАТИ = frozenset(("woman", "stylist", "journal"))
ДЖЕРЕЛА = frozenset(("catalogue", "photo", "model", "default", "unknown"))


def автор(значення):
    """Код автора; старе збереження мігрує тут, невідомий автор не стає жінкою."""
    if isinstance(значення, bool):
        return "her" if значення else "code_rank"
    if not isinstance(значення, str):
        return "unknown"
    return значення if значення in АВТОРИ else СТАРІ_АВТОРИ.get(значення, "unknown")


def ідентифікатори(значення):
    """Ідентифікатори предметів з адресних значень, без читання назв і слотів."""
    вих = []
    if isinstance(значення, dict):
        if значення.get("item_id") is not None:
            вих.append(str(значення["item_id"]))
        вих.extend(str(і) for і in значення.get("item_ids", ()) if і is not None)
        for к, в in значення.items():
            if к not in ("item_id", "item_ids"):
                вих.extend(ідентифікатори(в))
    elif isinstance(значення, (list, tuple)):
        for в in значення:
            вих.extend(ідентифікатори(в))
    return list(dict.fromkeys(вих))


def номерами(значення, номер):
    """Те саме значення, де адреса предмета (`item_id`, `item_ids`) — номер речі виклику `номер(id)` замість повного
    id: id несе крамницю й до моделі не йде (Е2-вхід-опису-кодами). Код читає саму заяву; номер — лише для промпту."""
    if isinstance(значення, dict):
        return {к: (номер(в) if к == "item_id" and в is not None
                    else [номер(і) for і in в if і is not None] if к == "item_ids" and isinstance(в, (list, tuple))
                    else номерами(в, номер)) for к, в in значення.items()}
    if isinstance(значення, (list, tuple)):
        return [номерами(в, номер) for в in значення]
    return значення


def створити(код, значення=None, *, recipient="woman", source="unknown", choice="unknown",
             rank=None, item_ids=(), part=None):
    """Повна заява зі стабільним ключем змісту; назва не підмінює ідентифікатор."""
    if recipient not in АДРЕСАТИ or source not in ДЖЕРЕЛА or choice not in АВТОРИ:
        raise ValueError("statement_metadata_outside_schema")
    з = dict(code=код, values=значення or {}, recipient=recipient, source=source,
             choice=choice, rank=rank, item_ids=list(dict.fromkeys(
                 [str(і) for і in item_ids if і is not None] + ідентифікатори(значення))))
    if part is not None:
        з["part"] = part
    з["key"] = "s_" + hashlib.sha256(json.dumps(з, ensure_ascii=False, sort_keys=True,
                                                separators=(",", ":")).encode()).hexdigest()[:24]
    return з


def уточнити(заява, **поля):
    """Той самий договір для сирої заяви показу й для уточненого контексту рішення."""
    мета = {к: заява[к] for к in ("recipient", "source", "choice", "rank", "item_ids", "part") if к in заява}
    мета.update(поля)
    return створити(заява["code"], заява.get("values"), **мета)
