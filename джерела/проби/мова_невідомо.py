# -*- coding: utf-8 -*-
"""«Невідомо» — ОДНЕ значення схеми, хоч у якій формі його дала модель (знахідка тестувальниці
№2, 25.09): JSON null і рядки "null" / "None" / "unknown" / "невідомо" (будь-яким регістром) у
полі вільного тексту, коду, числа, списку чи об'єкта. Друкує, куди потрапила кожна форма: у
`невідомо`, у її текст, у `незнайомі` чи кодом поля (`none` — код опадів і прикрас). І вихід:
текст-форма «невідомо» від перекладача — не текст для неї.
Запуск: cd джерела && python3 проби/мова_невідомо.py"""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import мовний_шар as М
ФОРМИ = [None, "null", "None", "NULL", " unknown ", "невідомо", "Невідомо", "none"]
ПОЛЯ = [("scenario", п) for п in ("event", "question", "occasion", "place", "temperature_c", "hour", "registers",
                                  "vetoes", "own_items", "mood", "precipitation", "jewelry")] + [("verdict_comment", "note")]
лік = collections.Counter()
for вид, поле in ПОЛЯ:
    клітинки = []
    for ф in ФОРМИ:
        р = М.прийняти_вхід(вид, json.dumps({поле: ф}, ensure_ascii=False))
        v = р["внутрішня"].get(поле)
        т = [x["free_text"] for x in (v if isinstance(v, list) else [v]) if isinstance(x, dict) and "free_text" in x]
        куди = ("незнайомі" if р["незнайомі"] else "невідомо" if поле in р["невідомо"] else "нема") if v is None \
            else "текст «%s»" % "; ".join(т) if т else "код %s" % json.dumps(v, ensure_ascii=False)
        лік[куди.split()[0]] += 1
        клітинки.append("%s → %s" % (json.dumps(ф, ensure_ascii=False), куди))
    print("%s.%s: %s" % (вид, поле, " · ".join(клітинки)))
for ф in ("null", "None", "невідомо"):
    р = М.прийняти_репліку(json.dumps({"text": ф}, ensure_ascii=False))
    т = М.прийняти(М.розмітити({"опис": "Тримайте сумку в руці."}), json.dumps({"1": ф}, ensure_ascii=False))
    print("ВИХІД %s: репліка → %s · готовий текст → %s%s" % (json.dumps(ф, ensure_ascii=False),
          json.dumps(р["текст"] or "(нема тексту: %s)" % р["причина"], ensure_ascii=False),
          json.dumps(т["тексти"]["опис"], ensure_ascii=False), " (лишився вхідний)" if т["без_відповіді"] else ""))
print("\nПІДСУМОК входу (%d форм × %d полів): %s" % (len(ФОРМИ), len(ПОЛЯ), dict(лік)))
