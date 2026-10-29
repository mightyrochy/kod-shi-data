# -*- coding: utf-8 -*-
"""Частка вартості сесій після першого ходу й пробудження за джерелом — мірило В.2 (`аудит/витрати/аналіз_2910.md`,
§5 п.3 і §7 п.3: виконавці 22–29.10 — 39,5 %, мета ≤ 10 %; наряд хук-фонові-завдання).

Вхід — тека з файлами `<session_id>.jsonl`: по рядку на подію `list_events` (інструмент MCP `claude-code-remote`, зі
скрипта не викликається — події зберігає сесія чи субагент для читання), щонайменше `kinds=["result"]` за всю історію
сесії (гортати `before_id`, доки `has_more`). Хід — подія `result`; його вартість — `model_usage_since_last_result`
(сума `costUSD`), джерело — `origin.kind` (`task-notification` — пробудження фоновим завданням; нема — перший хід чи
людина). Перший хід — найраніший `result` сесії; вікно `--від/--до` (UTC, ISO) відсікає ходи поза ним.

ЗАПУСК:
    python3 джерела/прилади/частка_після_першого_ходу.py <тека> [--від 2026-10-29T00:00] [--до 2026-11-05T00:00]
"""
import argparse
import glob
import json
import os
from collections import defaultdict


def ходи(шлях):
    """[(час, вартість, джерело)] за часом; повтори подій (перекриття сторінок) — один раз."""
    бачені, вихід = set(), []
    with open(шлях, encoding="utf-8") as ф:
        for рядок in ф:
            if not рядок.strip():
                continue
            e = json.loads(рядок)
            подія = e.get("event") or {}
            тіло = подія.get("internal_anthropic_catchall") or подія.get("result") or {}
            if e.get("kind") != "result" or not isinstance(тіло, dict) or подія.get("uuid") in бачені:
                continue
            бачені.add(подія.get("uuid"))
            вартість = sum(м.get("costUSD", 0) for м in (тіло.get("model_usage_since_last_result") or {}).values())
            вихід.append((e.get("created_at", ""), вартість, (тіло.get("origin") or {}).get("kind") or "без origin"))
    return sorted(вихід)


def main():
    п = argparse.ArgumentParser()
    п.add_argument("тека")
    п.add_argument("--від", default="")
    п.add_argument("--до", default="9999")
    а = п.parse_args()
    усього = після = 0.0
    за_джерелом = defaultdict(lambda: [0, 0.0])
    сесій = 0
    for шлях in sorted(glob.glob(os.path.join(а.тека, "*.jsonl"))):
        х = ходи(шлях)
        if not х:
            continue
        сесій += 1
        for і, (час, вартість, джерело) in enumerate(х):
            if not (а.від <= час < а.до):
                continue
            усього += вартість
            if і:
                після += вартість
                за_джерелом[джерело][0] += 1
                за_джерелом[джерело][1] += вартість
    частка = після / усього if усього else 0.0
    print(f"сесій {сесій}; вартість ${усього:.2f}; після першого ходу ${після:.2f} — {частка:.1%} (мета ≤ 10 %)")
    for джерело, (н, в) in sorted(за_джерелом.items(), key=lambda к: -к[1][1]):
        print(f"  {джерело}: {н} ходів, ${в:.2f}")


if __name__ == "__main__":
    main()
