# -*- coding: utf-8 -*-
"""Проба РЗ-К: сторож цитат розбору на СПРАВЖНЬОМУ тексті ж-01232 «СУКНЯ №1081 ШОКОЛАД» (рядок 404) — друкує факт.
Відповідь моделі повторює вигадку першого розбору (до коліна, без рукавів) поруч зі справжніми цитатами. «До» —
та сама відповідь без тексту речі (як читав розбір v2), «після» — зі сторожем `з_відповіді(відповідь, вхід())`.
Запуск: python3 джерела/проби/каталог_розбір_цитати.py"""
import json, os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import каталог_розбір as КР, фід_каталог as ФК, фід_розбір as ФР  # noqa: E401,E402
o = next(x for x in ФР.читати_yml(ФК.каталог_на_диску(), показ=False)[0] if x["id"].startswith("ж-01232@"))
п = lambda в, ц="": {"quote": ц, "value": в}  # noqa: E731
відп = {"slot": п("bottom", "СУКНЯ"), "item_type": п("dress_generic", "СУКНЯ"),       # слот — з таблиці типу
        "length": п("knee", "до коліна"), "sleeve": п("sleeveless"),                    # вигадка першого розбору
        "fabric": п("satin", "атлас"), "material": п(КР.НЕ_СТОСУЄТЬСЯ),                  # вигадана цитата; «не буває»
        "color_main": п("chocolate", "ШОКОЛАД"), "heel": {"present": п("no", "без підборів")},
        "set_parts": [{"slot": п("bottom"), "item_type": п("trousers", "БРЮКИ")}],       # БРЮКИ — блок «ви переглядали»
        "features": [п("chocolate shade", "шоколад"), п("satin sheen", "атласна")]}
до, _ = КР.з_відповіді(json.dumps(відп, ensure_ascii=False))
після, причини = КР.з_відповіді(json.dumps(відп, ensure_ascii=False), КР.вхід(o))
print("річ %s · назва «%s» · текст речі %d знаків" % (o["id"], o["назва"], len(json.dumps(КР.вхід(o), ensure_ascii=False))))
for ш in ("slot", "item_type", "length", "sleeve", "fabric", "material", "color_main", "color_from", "heel", "set_parts",
          КР.ОСОБЛИВОСТІ):
    print("  %-10s цитата %-16s до → %-34s після → %s" % (ш, json.dumps((відп.get(ш) or {}).get("quote"), ensure_ascii=False)
          if isinstance(відп.get(ш), dict) and "quote" in відп[ш] else "—", json.dumps(до.get(ш), ensure_ascii=False),
          json.dumps(після.get(ш), ensure_ascii=False)))
вигадані = [т.split(" · ")[2] for т in причини if т.startswith("invented")]
print("invented %d: %s" % (len(вигадані), ", ".join(вигадані)))
print("інші причини: %s" % " | ".join(т for т in причини if not т.startswith(("invented", "shared_quote")))[:300])
print("спільна цитата з типом (лише вимір): %s" % ", ".join(т.split(" · ")[1] for т in причини if т.startswith("shared_quote")))
лишилось = sum(1 for ш in ("length", "sleeve", "fabric") if після[ш] != КР.UNKNOWN)
print("ВИГАДКА ж-01232 (length, sleeve, fabric) після сторожа лишилась у %d полях з 3; справжні цитати: item_type=%s, color_main=%s"
      % (лишилось, після["item_type"], після["color_main"]))
