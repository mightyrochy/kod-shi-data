# -*- coding: utf-8 -*-
"""Промпт руки 3–4 до/після П-1 на сирих прогонах ноутбука 25.09 (p315_ruky34, m5e — main).

Друкує символи й токени Gemma 3 (коли GEMMA_TOKENIZER — шлях до tokenizer.json) старого
промпта й нового (`руки_без_коду.промпт_руки`) з ТИМИ САМИМИ даними, і чи кожен факт старого
(випадок, hex, зріст, обхвати, назва її речі, рядки вимог) стоїть у новому. Слот її речі не
йде свідомо: місце речі модель знає сама (власник, 24–25.09)."""
import sys, os, re, glob
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, К)
import руки_без_коду as Р
Т = None
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer; Т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"])
ток = lambda s: len(Т.encode(s, add_special_tokens=False).ids) if Т else "—"
for ф in sorted(glob.glob(os.path.join(К, "..", "аудит", "тести", "сирі_2026-09-25", "p315_ruky34", "m5e_*", "*.txt"))):
    с = open(ф, encoding="utf-8").read()
    if "── ПРОМПТ" not in с: continue
    п = с.split("── ПРОМПТ")[1].split("\n", 1)[1].split("\n\n── ВІДПОВІДЬ")[0]
    if "ЗАУВАЖЕННЯ" in п: continue                    # перепис мови — свій промпт
    бл = {б.split("\n")[0]: б for б in п.split("\n\n")}
    знайти = lambda поч: next((б for к, б in бл.items() if к.startswith(поч)), "")
    випадок, вимоги, ф_ = бл["ВИПАДОК"].split("\n", 1)[1], знайти("ВИМОГИ").split("\n", 1)[-1], знайти("ФАКТИ")
    hx, зр = re.findall(r"#[0-9a-f]{6}", ф_), re.search(r"зріст (\d+)", ф_)
    обх = {к: int(v) for к, v in re.findall(r"(\w+) (\d+) см", ф_.split("обхвати:")[-1])} if "обхвати:" in ф_ else {}
    річ = [dict(ід="с%d" % (i + 1), назва=н, слот=сл, закріплена=True)
           for i, (н, сл) in enumerate(re.findall(r"^· (.+) — (\S+)$", знайти("ЇЇ РІЧ"), re.M))]
    факти = Р.особа(*hx[:3], зріст=зр and зр.group(1), обхвати=обх) if hx else None
    рука = "3" if факти else "4"
    н = Р.промпт_руки(рука, випадок, вимоги, речі_паспорта=річ, факти=факти, мова_тексту="English")
    старі = [випадок, *hx[:3], *(зр.groups() if зр else ()), *map(str, обх.values()),
             *[р["назва"] for р in річ], *[р for р in вимоги.split("\n") if р]]
    без = [ф0 for ф0 in старі if ф0.replace('"', '\\"') not in н]
    print("%-24s рука %s: було %5d симв / %4s ток → стало %5d симв / %4s ток; фактів %2d, загублено: %s"
          % (ф.split(os.sep)[-2][:24], рука, len(п), ток(п), len(н), ток(н), len(старі), без or "нічого"))
