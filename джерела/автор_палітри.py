"""Походження кожної частини вибору кольору."""
import statements as _СТ

ОСНОВА_З_РЕЧІ = "her_item_photo"

_КЛЮЧ_ЧАСТИНИ = {"base": "база", "saturation": "насиченість"}

def автор_палітри(вибір, частина):
    """Хто обрав частину `base` чи `saturation` у записі `вибір_кольору`: канонічний автор (`statements.АВТОРИ`) чи
    `ОСНОВА_З_РЕЧІ`; частини в записі нема — None; про неї нема ні позначки коду, ні запису дії `обрала` — «unknown»."""
    в = вибір if isinstance(вибір, dict) else {}
    if not в.get(_КЛЮЧ_ЧАСТИНИ[частина]):
        return None
    if частина == "base":
        if в.get("база_з_речі"):
            return ОСНОВА_З_РЕЧІ
        if в.get("база_за_замовчуванням"):
            return "code_rank"
        if в.get("база_стилістки"):
            return "stylist"
    return _СТ.автор((в.get("обрала") or {}).get(частина) if isinstance(в.get("обрала"), dict) else None)
