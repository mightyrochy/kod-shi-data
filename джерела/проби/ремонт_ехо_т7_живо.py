# -*- coding: utf-8 -*-
"""Т-7 · той самий вердикт у СТАРІЙ формі промпта (як його зберіг стенд, `VIDPOVIDI`) і в НОВІЙ (форма на
дроті й вимоги цієї гілки; ноти вітрини — новими словами з тими самими параметрами): що з кожним робить
розбір ОБРАЗИ_V1. Без MODEL_URL — лише збережена відповідь; з MODEL_URL і MODELS=м1,м2 — ще й обидва промпти
живій моделі (4 000 т., reasoning_effort none — як `рв6_стенд.js`). Друкує факт: символи, обрив, образи, ехо.
Запуск: cd джерела && [MODEL_URL=http://127.0.0.1:1234/v1 MODELS=…] python проби/ремонт_ехо_т7_живо.py <тека VIDPOVIDI> [сід]"""
import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.stdout.reconfigure(encoding="utf-8")
import протокол as P, вердикт_моделі as ВМ, міст_відповіді as МВ, повнота_образу as ПО
def частини(ф):
    т = open(ф, encoding="utf-8").read(); п, _, в = т.partition("\n\n── ВІДПОВІДЬ")
    return п[п.index("\n") + 1:], (в[в.index("\n") + 1:] if "\n" in в else "")
НОТИ = ((r"ПОВНОТА ОБРАЗУ — це умова показу, не порада: (.+?)\. Слоти, яких", ПО.нота_повноти),
        (r"Де можна ламати палітру: слот «(.+?)»", ПО.нота_розриву), (r"«вітрина» — речі, яких ти ще", lambda: ПО.НОТА_ВІТРИНИ),
        (r"«мова» — вирок над ТВОЇМ текстом", lambda: ВМ._ВИМОГА_МОВИ))
нота = lambda р: next((ф(*м.groups()) for в_, ф in НОТИ for м in [re.match(в_, р)] if м), р)
def новий(старий):
    об = json.loads(старий); в = об["завдання"]["вимоги"]
    і = next((k for k, р in enumerate(в) if р.startswith("Дай стільки допрацьованих")), None)
    if і is not None:        # промпт ремонту; промпт повноти лишає свої вимоги (їх чистить сесія промптів)
        об["завдання"]["вимоги"] = list(ВМ.ВИМОГИ_ВЕРДИКТУ) + [нота(р) for р in в[і + 1:]] + list(ВМ.ВИМОГИ_ВІДПОВІДІ_РЕМОНТУ)
    return json.dumps(МВ._вердикт_для_моделі(об), ensure_ascii=False, separators=(",", ":"))
def факт(т, обрив):
    об, чому, нот = P.розбір_за_схемою(т, "ОБРАЗИ_V1"); обр = [о for о in ((об or {}).get("образи") or []) if isinstance(о, dict)]
    return ("%d симв. · обрив %s · образів за схемою %d (ід: %s) · «виконано» %d · ехо: %s" % (
        len(т), "так" if (обрив or нот["обрізано"]) else "ні", len(обр), ",".join(str(о.get("ід")) for о in обр) or "—",
        sum(len(о.get("виконано") or []) for о in обр), (нот["ехо"][0]["де"] + ": " + нот["ехо"][0]["що"][:70]) if нот["ехо"] else "нема"))
def модель(м, промпт):
    т0 = time.time(); тіло = dict(model=м, max_tokens=4000, stream=False, reasoning_effort="none", messages=[dict(role="user", content=промпт)])
    з = urllib.request.Request(os.environ["MODEL_URL"].rstrip("/") + "/chat/completions", json.dumps(тіло).encode(), {"Content-Type": "application/json"})
    в = json.load(urllib.request.urlopen(з, timeout=3600))["choices"][0]
    return (в["message"].get("content") or ""), в.get("finish_reason") == "length", time.time() - т0
а = sys.argv[1:] or ["."]; сід = а[1] if len(а) > 1 else ""
for ф in sorted(os.path.join(а[0], х) for х in os.listdir(а[0]) if "ВЕРДИКТ_V1_ОБРАЗИ_V1" in х and х.startswith("seed" + сід)):
    старий, відп = частини(ф); н = новий(старий); ім = os.path.basename(ф)[:9]
    print("%s · промпт: старий %d симв., новий %d · збережена відповідь: %s" % (ім, len(старий), len(н), факт(відп, False)))
    for м in [x for x in os.environ.get("MODELS", "").split(",") if x] if os.environ.get("MODEL_URL") else []:
        for форма, п in (("старий", старий), ("новий", н)):
            т, обрив, с = модель(м, п)
            print("%s · %s · %s промпт · %.0f с · %s" % (ім, м, форма, с, факт(т, обрив)))
