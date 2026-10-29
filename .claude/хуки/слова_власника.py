#!/usr/bin/env python3
"""Хук SessionStart: після стиснення вкладає в сесію слова власника з її чату — дослівно, з часом.

Власник 26.10 10:51: «мої слова забуваються». Підсумок стиснення слова переказує, а правила від них відстають, тож
після стиснення діяло старе правило. Хук нічого не пам'ятає сам: бере з транскрипту сесії повідомлення людини
(`origin.kind == "human"`) і друкує їх; stdout хука SessionStart платформа додає в контекст. Лист з ноутбука
(`claude -p --cloud`) приходить як повідомлення користувача, тож рядок з міткою відправника великими літерами
(«ЗАПУСКАЧ:», «НОУТБУК …») — лист, не слово власника (`AGENTS.md`, «Безпека»): його пропускаємо. Повідомлення,
надіслане посеред ходу, лягає в транскрипт вкладенням `queued_command` — його теж беремо. Транскрипт — файл
контейнера: після перезапуску в ньому лише нові події (26.10: з 12:12), тож давніші слова — лише з журналу власника.

Субагентові слів не вкладаємо (власник 26.10 14:00). Транскрипт субагента лежить у `<сесія>/subagents/…/agent-<id>.jsonl`
(Claude Code 2.1.310): впізнаємо його за шляхом, а не за роллю останнього запису — та мовчала й у головній сесії на
ручному `/compact` між ходами. Листи інших сесій (`send_message`) лягають у транскрипт службовим записом (`isMeta`,
без `origin`) з обгорткою `<cross-session-message`: це не слова власника.

Час слова — час надсилання: запис `queue-operation`/`enqueue` з тим самим текстом (`content`); `timestamp` запису
`user`/`queued_command` — час доставки в чат, на хвилини пізніше. Нема `enqueue` — час доставки.
"""
import json
import re
import sys

МАКС_СИМВОЛІВ = 12000
# Закритий перелік міток листа (`AGENTS.md`, «Безпека»); «СПОСТЕРІГАЧ» — доки його не знято (наряд П.4-В). Решта ходу
# людини, хай і «СТОП: …» чи «ВАЖЛИВО: …», — слово власника.
МІТКА_ЛИСТА = re.compile(r"^(ЗАПУСКАЧ:|GEMINI ОБГОРТКА:|НОУТБУК\b|СПОСТЕРІГАЧ\b|<cross-session-message\b)")
НАГАДУВАННЯ = ("Після стиснення: перечитай файл своєї ролі, наряд і записаний стан роботи (`AGENTS.md`, «Пам'ять — у "
               "файлах»); менеджер і диспетчер — ще записи власника за дві доби (`аудит/РІШЕННЯ_ВЛАСНИКА.md`).")


def текст(вміст):
    if isinstance(вміст, list):
        вміст = "\n".join(б.get("text", "") for б in вміст if isinstance(б, dict) and б.get("type") == "text")
    return вміст.strip() if isinstance(вміст, str) else ""


def слова_людини(шлях):
    """Слова людини з транскрипту сесії: [(час "РРРР-ММ-ДД ГГ:ХХ" UTC, текст)]. Спільне з `листи_менеджерові.py`."""
    слова, бачені, надіслано = [], set(), {}
    with open(шлях, encoding="utf-8") as ф:
        for рядок in ф:
            try:
                подія = json.loads(рядок)
            except ValueError:
                continue
            if подія.get("type") == "queue-operation" and подія.get("operation") == "enqueue":
                надіслано.setdefault(текст(подія.get("content")), []).append(подія.get("timestamp", ""))
                continue
            if подія.get("isSidechain"):
                continue
            тип, вкладення = подія.get("type"), подія.get("attachment") or {}
            if тип == "user" and not подія.get("isMeta"):
                джерело, т, ід = подія.get("origin"), текст(подія.get("message", {}).get("content")), подія.get("uuid")
            elif тип == "attachment" and вкладення.get("type") == "queued_command":
                джерело, т, ід = вкладення.get("origin"), текст(вкладення.get("prompt")), вкладення.get("source_uuid")
            else:
                continue
            if (джерело or {}).get("kind") != "human":
                continue
            черга = надіслано.get(т)
            коли = (черга.pop(0) if черга else подія.get("timestamp", ""))[:16].replace("T", " ")
            ключ = (коли, т)
            if т and not МІТКА_ЛИСТА.match(т) and ключ not in бачені and ід not in бачені:
                бачені.update({ключ, ід or ключ})
                слова.append((коли, т))
    return слова


def початок_транскрипту(шлях):
    """Час першої події транскрипту "РРРР-ММ-ДД ГГ:ХХ" UTC; порожній чи без часу — None."""
    with open(шлях, encoding="utf-8") as ф:
        for рядок in ф:
            try:
                коли = json.loads(рядок).get("timestamp")
            except (ValueError, AttributeError):
                continue
            if isinstance(коли, str) and коли:
                return коли[:16].replace("T", " ")
    return None


def прочитати(шлях):
    return [f"- {коли} UTC «{т}»" for коли, т in слова_людини(шлях)]


def main():
    try:
        дані = json.load(sys.stdin)
    except ValueError:
        return
    if дані.get("source") != "compact":
        return
    шлях = дані.get("transcript_path") or ""
    if дані.get("agent_id") or re.search(r"[/\\]subagents[/\\](?:.+[/\\])?agent-[^/\\]+\.jsonl$", шлях):
        return
    try:
        слова = прочитати(шлях)
    except OSError:
        слова = []
    вибрані, розмір = [], 0
    for с in reversed(слова):
        розмір += len(с)
        if розмір > МАКС_СИМВОЛІВ:
            break
        вибрані.append(с)
    if вибрані:
        пропущено = len(слова) - len(вибрані)
        print("СЛОВА ВЛАСНИКА З ЧАТУ ЦІЄЇ СЕСІЇ — дослівно; вклав хук `.claude/хуки/слова_власника.py` після стиснення. "
              "Новіше скасовує старіше; що робити зі словом, якого ще нема в журналі, — `AGENTS.md`, «Пам'ять — у файлах»"
              + (f" (старші {пропущено} — у транскрипті):" if пропущено else ":"))
        print("\n".join(reversed(вибрані)))
    print(НАГАДУВАННЯ)


if __name__ == "__main__":
    main()
