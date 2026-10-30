#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вибірка (в) приладу ПК-дотримання-правил: 20 правил «тримає механізм» і 20 «тримає пам'ять» з доказом.

Механізм: у файлах, що його складають, є названий маркер (рядок `grep`); проби П1…П11 запускає
`корінь_пк_дотримання.py --перелік … --проби`. Пам'ять: у `.claude/settings.json`, `.claude/хуки/`, `.github/workflows/` і
`аудит/адаптери/gemini/*.ps1` нема слова, яке мало б ловити правило, — число збігів 0 підтверджує, що механізму нема.
Запуск (з кореня репозиторію): python3 -I аудит/проби/пк_вибірка_в.py — друкує дві таблиці й `розбіжностей: N`.
"""
import glob
import os
import sys

КОРІНЬ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ПЕРЕЛІК = os.path.join(КОРІНЬ, "аудит/корені/ПК-дотримання-правил-перелік.md")

# адреса рядка переліку → (файли, маркер, що доводить). Рядок — «тримає механізм».
МЕХАНІЗМ = [
    ("AGENTS.md:30–31", ["аудит/адаптери/gemini/gemini_run.ps1", "аудит/адаптери/gemini/queue_lanes.ps1"], "gemini-queue", "позначка черги читається обгорткою"),
    ("AGENTS.md:40–41", [".claude/хуки/листи_менеджерові.py"], "СЛОВО ВЛАСНИКА", "хук знає початок «СЛОВО ВЛАСНИКА» і час"),
    ("AGENTS.md:42–43", [".claude/settings.json"], "\"compact\"", "SessionStart на compact"),
    ("AGENTS.md:72–74", [".github/workflows/khrapovyk.yml"], "храповик_кореня", "CI запускає храповик кореня"),
    ("AGENTS.md:79–80", [".github/workflows/zbirka.yml"], "згорнути_дошку", "CI згортає дошку"),
    ("CLAUDE.md:15–16", [".claude/settings.json"], "\"Bash\"", "PreToolUse на Bash"),
    ("CLAUDE_КЕРУВАННЯ.md:29–31", [".claude/settings.json"], "subscribe_pr_activity", "інструмент у permissions.deny"),
    ("ДИСПЕТЧЕР.md:35–38", ["аудит/адаптери/gemini/смуги.json"], "claude_laptop", "смуга claude_laptop у смуги.json"),
    ("ДИСПЕТЧЕР.md:60", [".claude/settings.json"], "ScheduleWakeup", "інструмент у permissions.deny"),
    ("ДИСПЕТЧЕР.md:83–84", [".github/workflows/obhortka.yml"], "windows-latest", "CI стенд Windows"),
    ("ДИСПЕТЧЕР.md:101–104", [".claude/settings.json"], "send_message", "PreToolUse на send_message"),
    ("ДИСПЕТЧЕР.md:105–107", [".claude/хуки/листи_менеджерові.py"], "ЗВЕДЕННЯ", "хук знає «ЗВЕДЕННЯ»"),
    ("МЕНЕДЖЕР.md:61–63", [".claude/settings.json"], "subscribe_pr_activity", "інструмент у permissions.deny"),
    ("МЕНЕДЖЕР.md:93–96", [".github/workflows/zbirka.yml"], "журнал_і_розмір_правил", "CI показує розмір правил"),
    ("ВИКОНАВЕЦЬ.md:42–44", [".claude/settings.json"], "\"Workflow\"", "інструмент у permissions.deny"),
    ("ПЕРЕВІРКА.md:23–24", [".github/workflows/zbirka.yml"], "згорнути_дошку", "CI звіряє поля рядка дошки"),
    ("GEMINI.md:6–10", ["аудит/адаптери/gemini/gemini_publish.ps1"], "ISOLATION_FAILED", "обгортка відмовляє без ізоляції"),
    ("GEMINI.md:11–15", ["аудит/адаптери/gemini/gemini_publish.ps1"], "gemini/", "публікатор пушить лише gemini/*"),
    ("ЧЕРГА.md:23–31", ["аудит/адаптери/gemini/claude_run.ps1"], "CLAUDE_NOT_LAPTOP", "обгортка відмовляє Claude без claude_laptop"),
    ("ЧЕРГА.md:65–68", ["аудит/адаптери/gemini/queue_lanes.ps1", "аудит/адаптери/gemini/gemini_run.ps1"], "gpu", "замок GPU (проби нема)"),
]

# адреса рядка переліку → (слова-маркери, що мали б ловити правило). Рядок — «тримає пам'ять».
ПАМ_ЯТЬ = [
    ("AGENTS.md:24–25", ["через третю", "ПЕРЕСИЛАННЯ"]),
    ("AGENTS.md:59", ["git push", "незапушен"]),
    ("AGENTS.md:86", ["merge_pull_request"]),
    ("AGENTS.md:95", ["actions_run_trigger", "enable_pr_auto_merge"]),
    ("AGENTS.md:96–98", ["@codex"]),
    ("AGENTS.md:88–91", ["\"Stop\""]),
    ("CLAUDE.md:16", ["\"Agent\""]),
    ("CLAUDE.md:31–33", ["create_trigger", "fire_trigger"]),
    ("CLAUDE_КЕРУВАННЯ.md:8–10", ["create_session"]),
    ("CLAUDE_КЕРУВАННЯ.md:25–26", ["list_events", "list_sessions"]),
    ("ДИСПЕТЧЕР.md:69–72", ["expectedHeadSha"]),
    ("ДИСПЕТЧЕР.md:116–118", ["archive_session"]),
    ("МЕНЕДЖЕР.md:3–5", ["Opus"]),
    ("МЕНЕДЖЕР.md:47–48", ["ЗЛИТИ"]),
    ("ВИКОНАВЕЦЬ.md:3–4", ["draft"]),
    ("ВИКОНАВЕЦЬ.md:31–33", ["ГОТОВО"]),
    ("ПЕРЕВІРКА.md:12–14", ["pachka"]),
    ("ПЕРЕВІРКА.md:78–80", ["ПЕРЕВІРЕНО"]),
    ("НОУТБУК.md:22–23", ["no-thin"]),
    ("AGENTS.md:107–108", ["AGENTS.md", "МЕНЕДЖЕР.md"]),
]
МЕХАНІЗМИ_ФАЙЛИ = [".claude/settings.json", ".claude/хуки/*", ".github/workflows/*", "аудит/адаптери/gemini/*.ps1"]


def читати(шлях):
    try:
        return open(os.path.join(КОРІНЬ, шлях), encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return ""


def рядки_переліку():
    результат = {}
    for рядок in open(ПЕРЕЛІК, encoding="utf-8"):
        к = [х.strip() for х in рядок.strip().strip("|").split("|")]
        if len(к) == 7 and ":" in к[0]:
            результат[к[0]] = к
    return результат


def головна():
    перелік, розбіжностей = рядки_переліку(), 0
    print("## (в-1) тримає механізм: адреса · тримає · проба · маркер у файлах · збігів")
    for адреса, файли, маркер, що in МЕХАНІЗМ:
        р = перелік.get(адреса)
        збігів = sum(читати(ф).count(маркер) for ф in файли)
        добре = р is not None and not р[4].startswith("пам'ять") and збігів > 0
        розбіжностей += not добре
        print(f"| {адреса} | {р[4] if р else 'НЕМА В ПЕРЕЛІКУ'} | {р[5] if р else '-'} | `{маркер}` у {', '.join(файли)} · {що} | "
              f"{збігів} | {'вірно' if добре else 'РОЗБІЖНІСТЬ'} |")
    print("\n## (в-2) тримає пам'ять: адреса · тримає · слова-маркери · збігів у механізмах · вердикт")
    файли_мех = [ф for шаблон in МЕХАНІЗМИ_ФАЙЛИ for ф in sorted(glob.glob(os.path.join(КОРІНЬ, шаблон)))]
    for адреса, слова in ПАМ_ЯТЬ:
        р = перелік.get(адреса)
        збіги = {с: sum(читати(os.path.relpath(ф, КОРІНЬ)).count(с) for ф in файли_мех) for с in слова}
        перші = [f"{os.path.relpath(ф, КОРІНЬ)}:{н}" for с in слова for ф in файли_мех
                 for н, рядок in enumerate(читати(os.path.relpath(ф, КОРІНЬ)).split("\n"), 1) if с in рядок][:3]
        добре = р is not None and р[4].startswith("пам'ять")
        розбіжностей += not добре
        print(f"| {адреса} | {р[4] if р else 'НЕМА В ПЕРЕЛІКУ'} | {', '.join(f'`{с}`' for с in слова)} | "
              f"{', '.join(f'{с}: {н}' for с, н in збіги.items())}{' (перші: ' + ', '.join(перші) + ')' if перші else ''} | "
              f"{'вірно' if добре else 'РОЗБІЖНІСТЬ'} |")
    print(f"\nрозбіжностей: {розбіжностей}")
    return 1 if розбіжностей else 0


if __name__ == "__main__":
    sys.exit(головна())
