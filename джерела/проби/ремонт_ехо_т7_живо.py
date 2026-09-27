# -*- coding: utf-8 -*-
"""Т-7 · той самий вердикт у СТАРІЙ формі промпта (як його зберіг стенд, `VIDPOVIDI`) і в НОВІЙ
(з П-2 — англійський промпт збирача з тих самих даних, `дріт_факти.ремонт_з_сирого`): що з кожним робить розбір ОБРАЗИ_V1.
Без MODEL_URL — лише збережена відповідь; з MODEL_URL і MODELS=м1,м2 — ще й промпти FORMY (типово «старий,новий»;
«версія_в_кінці» — новий, де «version» кореня стоїть останньою) живій моделі (4 000 т., reasoning_effort none — як
стенд). Друкує факт: символи, обрив, образи, ехо. Запуск: cd джерела && [MODEL_URL=… MODELS=… FORMY=…] python проби/ремонт_ехо_т7_живо.py <тека> [сід]"""
import json, os, re, sys, time, urllib.request; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import протокол as P, дріт_факти as Ф; sys.stdout.reconfigure(encoding="utf-8")
def частини(ф):
    т = (__import__("gzip").open if ф.endswith(".gz") else open)(ф, "rt", encoding="utf-8").read(); п, _, в = т.partition("\n\n── ВІДПОВІДЬ")
    return п[п.index("\n") + 1:], (в[в.index("\n") + 1:] if "\n" in в else "")
дж = lambda о: json.dumps(о, ensure_ascii=False, separators=(",", ":"))
новий = lambda старий: дж(Ф.ремонт_з_сирого(старий)[0])   # П-2: англійський промпт збирача з тих самих даних
версія_в_кінці = lambda т: дж(dict({к: v for к, v in json.loads(т).items() if к != "version"}, version=json.loads(т).get("version")))
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
    старий, відп = частини(ф); н = новий(старий); ім = os.path.basename(ф)[:9]; форми = dict(старий=старий, новий=н, версія_в_кінці=версія_в_кінці(н))
    print("%s · промпт: старий %d симв., новий %d · збережена відповідь: %s" % (ім, len(старий), len(н), факт(відп, False)))
    for м in [x for x in os.environ.get("MODELS", "").split(",") if x] if os.environ.get("MODEL_URL") else []:
        for форма in os.environ.get("FORMY", "старий,новий").split(","):
            т, обрив, с = модель(м, форми[форма])
            print("%s · %s · %s промпт · %.0f с · %s" % (ім, м, форма, с, факт(т, обрив)))
