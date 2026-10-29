#!/usr/bin/env python3
"""Хук PreToolUse на `send_message`: лист диспетчера менеджерові поза переліком не відходить.

Слово власника 29.10 ~09:16 UTC: «я не маю тобі нагадувати правила. Вони існують щоб їх виконувати. Чому правила не
виконуються?» `аудит/ДИСПЕТЧЕР.md`, «Стан і зведення»: лист менеджерові починається лише з «СЛОВО ВЛАСНИКА»,
«РІШЕННЯ ПОТРІБНЕ: …», «КОЛО», «ЛІМІТ», «ДИСПЕТЧЕР ПЕРЕДАЧА» чи «ЗВЕДЕННЯ <час UTC>», зведення — не частіше ніж раз на
~6 год; правило тримала пам'ять — тепер його перевіряє механізм у мить листа.

Адреси — рядки «менеджер» і «диспетчер» `аудит/СТАН.md` (робоче дерево сесії). Свою адресу сесія знає з
`CLAUDE_CODE_REMOTE_SDK_URL` (`…/sessions/cse_<id>` ↔ `session_<id>`); адреса невідома — правило для всіх відправників.
Відправник, чия адреса відома й не диспетчерська, правилом не зв'язаний. Час останнього зведення — файл
`~/.claude/листи_менеджерові_зведення` (для стенда: `ЛИСТИ_СТАН_ФАЙЛ`, час — `ЛИСТИ_ЗАРАЗ`, ISO UTC). Хук не падає сесію:
будь-яка помилка читання — пропуск листа з попередженням у stderr.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

ПЕРЕЛІК = ("СЛОВО ВЛАСНИКА", "РІШЕННЯ ПОТРІБНЕ:", "КОЛО", "ЛІМІТ", "ДИСПЕТЧЕР ПЕРЕДАЧА", "ЗВЕДЕННЯ")
ІНТЕРВАЛ = timedelta(hours=6)
АДРЕСА = re.compile(r"session_[A-Za-z0-9]+")


def попередження(т):
    print(f"хук листи_менеджерові: {т}; лист пропущено", file=sys.stderr)


def адреса_ролі(стан, роль):
    for рядок in стан.splitlines():
        комірки = [к.strip() for к in рядок.split("|")]
        if len(комірки) > 2 and комірки[1] == роль:
            збіг = АДРЕСА.search(комірки[2])
            return збіг.group(0) if збіг else None
    return None


def своя_адреса():
    збіг = re.search(r"/sessions/cse_([A-Za-z0-9]+)", os.environ.get("CLAUDE_CODE_REMOTE_SDK_URL", ""))
    return f"session_{збіг.group(1)}" if збіг else None


def зараз():
    т = os.environ.get("ЛИСТИ_ЗАРАЗ")
    return datetime.fromisoformat(т.replace("Z", "+00:00")) if т else datetime.now(timezone.utc)


def відмова(причина):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": причина}}, ensure_ascii=False))


def main():
    дані = json.load(sys.stdin)
    вхід = дані.get("tool_input") or {}
    корінь = os.environ.get("CLAUDE_PROJECT_DIR") or дані.get("cwd") or "."
    with open(os.path.join(корінь, "аудит", "СТАН.md"), encoding="utf-8") as ф:
        стан = ф.read()
    менеджер = адреса_ролі(стан, "менеджер")
    if not менеджер or вхід.get("session_id") != менеджер:
        return
    я = своя_адреса()
    if я and я != адреса_ролі(стан, "диспетчер"):
        return
    рядки = [р.strip() for р in str(вхід.get("message", "")).splitlines() if р.strip()]
    перший = рядки[0] if рядки else ""
    if not any(перший.startswith(п) for п in ПЕРЕЛІК):
        відмова("Лист менеджерові починається лише з «СЛОВО ВЛАСНИКА», «РІШЕННЯ ПОТРІБНЕ: <що вирішити>», «КОЛО», "
                "«ЛІМІТ», «ДИСПЕТЧЕР ПЕРЕДАЧА» чи «ЗВЕДЕННЯ <час UTC>» (`аудит/ДИСПЕТЧЕР.md`, «Стан і зведення»). "
                "Знахідка на твоїй ділянці — твій наряд, не лист менеджерові.")
        return
    if not перший.startswith("ЗВЕДЕННЯ"):
        return
    файл = os.environ.get("ЛИСТИ_СТАН_ФАЙЛ") or os.path.expanduser("~/.claude/листи_менеджерові_зведення")
    тепер = зараз()
    try:
        with open(файл, encoding="utf-8") as ф:
            минуле = datetime.fromisoformat(ф.read().strip())
    except (OSError, ValueError):
        минуле = None  # нема файлу чи він зіпсований — пропустити й записати
    if минуле and тепер - минуле < ІНТЕРВАЛ:
        відмова(f"«ЗВЕДЕННЯ» — не частіше ніж раз на ~6 год; попереднє було {минуле:%Y-%m-%d %H:%M} UTC, наступне — "
                f"не раніше {минуле + ІНТЕРВАЛ:%H:%M} UTC.")
        return
    try:
        os.makedirs(os.path.dirname(файл), exist_ok=True)
        with open(файл, "w", encoding="utf-8") as ф:
            ф.write(тепер.isoformat())
    except OSError as п:
        попередження(f"стан зведення не записано ({п})")


if __name__ == "__main__":
    try:
        main()
    except Exception as п:  # хук не падає сесію
        попередження(f"{type(п).__name__}: {п}")
