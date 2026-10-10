"""Рядок 4283: вид її речі з фото → `вид` паспорта → `item_type` вердикту репліки (як `міст_річ`).
Вхід: файли VIDPOVIDI `…_речі_з_фото_шар_.txt` (Ж19 №6–8). Для кожного: чи промпт ПІСЛЯ просить `kind`; вид
із записаної відповіді (ДО: поля нема — «unknown»); вид, коли шар назве `kind` (відповідь + `"kind": "sandals"`).
Запуск: cd джерела && python3 проби/фото_вид_4283.py <файл>…"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import річ_з_фото as РФ, внутрішня_мова as ВМ, мовний_шар as МШ
пром = json.loads(РФ.промпт_фото([{"ід": "ф1", "ширина": 500, "висота": 700}]))
print("промпт просить kind:", "kind" in пром["task"]["answer_schema"]["items"][0],
      "· codes.item_type:", len(пром.get("codes", {}).get("item_type") or []))
def тип(відп, власні):
    р = РФ.речі_з_відповіді_фото(відп, [{"ід": "ф1"}], None, власні)["речі_з_фото"]
    return [(х.get("слот"), х.get("вид") or ВМ.UNKNOWN) for х in р]
for шлях in sys.argv[1:]:
    т = open(шлях, encoding="utf-8").read()
    п, в = т.split("── ВІДПОВІДЬ", 1)
    промпт = json.loads(п.split("──\n", 1)[1].strip())
    відп = в.split("\n", 1)[1].strip()
    власні = промпт.get("her_items_in_words") or []
    з_видом = json.loads(відп)
    for р in з_видом["items"]:
        р["kind"] = "sandals"
    print(os.path.basename(os.path.dirname(os.path.dirname(шлях)))[:2], "name=%r" % json.loads(відп)["items"][0]["name"],
          "| записана: %s | з kind: %s" % (тип(відп, власні), тип(json.dumps(з_видом), власні)))
р = МШ.промпт_репліки({"item_verdicts": [{"verdict": {"kind": "her_item_verdict", "statements": [{"code": "item_suits"}]},
                                         "slot": "shoes", "item_type": "sandals"}]})
print("промпт репліки:", next(р_ for р_ in р.split("\n") if р_.startswith("- item_verdicts"))[-150:])
