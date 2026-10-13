# -*- coding: utf-8 -*-
"""Перелік речей рук 3–4 до/після П-1: розмір промпта над тією самою прозою (сирі m5e 25.09)
і що стає з її речами прогону власника 3421 (спідниця ф1, козаки ф2) на відповіді КОДАМИ.

До П-1 перелік — рядки (`brief.ПРОМПТ_ПЕРЕЛІК_РЕЧЕЙ`, текст нижче — для заміру): слот код
вгадував словником (`feed.слот` не знав «козаків» — розбір 2/8, В-3), її річ — міткою в
назві, яку перелік губив (В-1). Токени — Gemma 3, коли GEMMA_TOKENIZER — шлях до tokenizer.json."""
import sys, os, json, glob
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, К)
import руки_без_коду as Р, розбір_відповідей as РВ, річ_з_фото as РФ
СТАРИЙ = ("Нижче — опис образу. Випиши з нього речі.\n\nВідповідь — JSON-список рядків і більше нічого:\n"
          '["<що це>, <крій>, <довжина>, <колір + hex>, <тканина>", "..."]\n\nОдин рядок на кожну річ '
          "образу, словами цього ж тексту. Речей, яких у тексті нема, не додавай.\n\nОПИС:\n__ПРОЗА__")
Т = None
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer; Т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"])
ток = lambda s: len(Т.encode(s, add_special_tokens=False).ids) if Т else "—"
В = os.path.join(К, "..", "аудит", "тести")
for ф in sorted(glob.glob(os.path.join(В, "сирі_2026-09-25", "p315_ruky34", "m5e_*", "*.txt"))):
    с = open(ф, encoding="utf-8").read()
    if "── ВІДПОВІДЬ" not in с or "ЗАУВАЖЕННЯ" in с: continue
    проза = с.split("── ВІДПОВІДЬ")[1].split("\n", 1)[1].strip()
    до, після = СТАРИЙ.replace("__ПРОЗА__", проза), Р.промпт_переліку(мова_тексту="Ukrainian").replace('"__ПРОЗА__"', json.dumps(проза, ensure_ascii=False))
    print("%-24s перелік: було %4d симв / %4s ток → стало %4d симв / %4s ток" % (ф.split(os.sep)[-2][:24], len(до), ток(до), len(після), ток(після)))
п = [x for x in json.load(open(os.path.join(В, "власник_2026-09-25", "verdykty-0phxvk-2026-09-25-2012.json"), encoding="utf-8"))["прогони"]
     if str(x["спільне"].get("розклад")) == "3421"][0]["спільне"]["паспорт"]["речі_з_фото"]
print("\nїї речі в промпті переліку:", [(р["id"], р.get("name")) for р in json.loads(Р.промпт_переліку(п))["her_items"]])
відп = json.dumps({"items": [dict(name="мініспідниця зі зміїним принтом", slot="bottom", color_hex="#7e7660", own="її-ф1"),
    dict(name="светр фактурної в'язки", slot="top", color_hex="#efe6d8", own=None),
    dict(name="високі коричневі козаки з вишивкою", slot="shoes", color_hex="#4a3320", own="її-ф2")]}, ensure_ascii=False)
в = РВ.перевірити_образ_моделі("", None, перелік=відп)
речі, стан = РФ.впізнати_в_тексті(в.get("речі"), п)
print("відповідь кодами → на картці:", [(р["id"], р["слот"]) for р in речі], "| її речей упізнано:", стан)
