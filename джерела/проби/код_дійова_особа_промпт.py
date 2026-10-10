"""КАРТКА-СЛОВА (рядок 3657): скільки «code» бачить перекладачка повідомлень — ДО (записаний промпт) і ПІСЛЯ
(той самий вхід, перебудований `промпт_повідомлень`). Друкує імена заяв і видів з «code» та «the code» у визначеннях.
Запуск: cd джерела && python3 проби/код_дійова_особа_промпт.py <тека з VIDPOVIDI, напр. аудит/живі_14/А>"""
import os, re, sys, glob, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import мовний_шар as МШ
СТАРІ = {"item_added_by_code": "item_added_by_selection", "code_added_to_empty_slots": "selection_filled_empty_slots",
         "card_added_by_code": "card_added_by_selection", "scheme_taken_by_code": "scheme_taken_by_default",
         "code_removed_item_from_stylist_look": "selection_removed_item_from_stylist_look",
         "code_swapped_item_from_stylist_look": "selection_swapped_item_from_stylist_look",
         "code_removed_this_layer": "selection_removed_this_layer", "code_does_not_advise_here":
         "stylist_does_not_advise_here", "scheme_not_in_code_substituted": "scheme_not_in_set_substituted",
         "card_code_unknown": "card_unchecked"}
ІМЕНА = re.compile(r'"(?:code|вид)": "((?:[a-z]+_)*?code(?!_unchecked|_level|_requires|_band)[a-z_]*)"')

def лічба(промпт):
    заяви = промпт.split("\nЗАЯВИ:\n")[-1].split("ПОВІДОМЛЕННЯ:")[0]
    return len(ІМЕНА.findall(промпт)), len(re.findall(r"\bthe code\b", заяви))

до, після, n = [0, 0], [0, 0], 0
for ф in sorted(glob.glob(os.path.join(sys.argv[1], "*", "VIDPOVIDI", "*мовний_шар.txt"))):
    т = open(ф, encoding="utf-8").read().split("── ВІДПОВІДЬ")[0]
    if "\nПОВІДОМЛЕННЯ:\n" not in т:
        continue
    сирий = т.split("\nПОВІДОМЛЕННЯ:\n", 1)[1].strip()
    for с, н in СТАРІ.items():
        сирий = re.sub(r"\b%s\b" % с, н, сирий)
    розмітка = json.loads(сирий[: сирий.rindex("]") + 1])
    n += 1
    for сум, пр in ((до, т), (після, МШ.промпт_повідомлень(розмітка))):
        сум[0] += лічба(пр)[0]; сум[1] += лічба(пр)[1]
print("промптів повідомлень: %d · імен заяв/видів з «code»: %d → %d · «the code» у визначеннях: %d → %d"
      % (n, до[0], після[0], до[1], після[1]))
print("правило «the code» = перевірка стилістки для всіх видів:", "«the code» у" in МШ.РЯДОК_ЗАЯВ_АНГЛІЙСЬКОЮ)
