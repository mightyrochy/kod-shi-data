# -*- coding: utf-8 -*-
"""Промпт приміряння до/після П-1 на сирих прогонах ноутбука 25.09 (p4_ir_sobaky_gemma_seed13).

Старий текст складав JS показу; новий — `приміряння.промпт` (збирач, англійською) з ТИМИ САМИМИ
даними, розібраними зі старого: речі з фото (слот, назва, «її»), речі без фото, «Як носити»,
макіяж. Друкує символи й токени Gemma 3 (коли GEMMA_TOKENIZER — шлях до tokenizer.json) і
чи кожна назва, слот (кодом), рядок «Як носити» й hex помади стоять у новому. Проза «Чому
це працює» режиму «за описом» не йде свідомо: вона для жінки, картинці — речі (П-1)."""
import sys, os, re, gzip, glob, json
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, К)
import приміряння as ПР, внутрішня_мова as ВМ
Т = None
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer; Т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"])
ток = lambda s: len(Т.encode(s, add_special_tokens=False).ids) if Т else "—"
for ф in sorted(glob.glob(os.path.join(К, "..", "аудит", "тести", "сирі_2026-09-25", "p4_ir_sobaky_gemma_seed13", "*ПРИМІРЯННЯ*"))):
    с = gzip.open(ф, "rt", encoding="utf-8").read()
    п = с.split("──\n", 1)[1].split("\n── КАДР")[0].strip()
    зф = [dict(слот=сл, назва=н.replace(" (її власна річ — саме ця)", ""), власна="її власна" in н)
          for сл, н in re.findall(r"^Фото \d+ — ([^:\n]+): (.+)$", п, re.M)]
    бф = [dict(слот=сл, назва=н, власна=bool(в)) for сл, н, в in re.findall(r"^— ([^:\n]+): ([^(\n]+?)(?: \(.*?\))?( — її власна річ)?$", п, re.M)]
    опис = п.split("Опис образу:\n")[1].split("\n\nЧому")[0].split("\n\nЦей образ")[0] if "Опис образу:" in п else ""
    бф += [dict(назва=л.replace("Твоя річ: ", "").split(" — ")[0], власна=л.startswith("Твоя річ"))
           for л in опис.split("\n") if л.strip()]
    як = [р.strip(" .") for р in (re.findall(r"^Як носити: (.+)$", п, re.M) or [""])[0].split(";") if р.strip(" .")]
    мк = re.search(r"Макіяж на обличчі: (\S+?)[.,].*?(#[0-9a-f]{6})?", п)
    н = ПР.промпт(зф, бф, {"рівень": мк.group(1), "губи": мк.group(2)} if мк else None, як)
    факти = [р["назва"] for р in зф + бф] + [ВМ.код("slot", р["слот"]) or р["слот"] for р in зф + бф if р.get("слот")] + як
    без = [ф0 for ф0 in факти if ф0.replace('"', '\\"') not in н]
    print("%s %-9s було %4d симв / %4s ток → стало %4d симв / %4s ток; фактів %2d, загублено: %s"
          % (os.path.basename(ф)[:9], "за фото" if зф else "за описом", len(п), ток(п), len(н), ток(н), len(факти), без or "нічого"))
