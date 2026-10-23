"""Х25-Н.3 (рядки 6870, 6871, 6872, 6785): назва в заявах ціла, усі заяви рядка разом, факт схеми кодами, ремонт без
«answer». ДО — записи шару ЖИВІ-15 №11 (`seed3_31`) і ЖИВІ-1016-2 Ж:08 (`seed3_28`); ПІСЛЯ — чинний код, без моделі.
Запуск із джерела/ (записи — `git show`, шляхи в рядках 6870, 6872 дошки):
python3 -W ignore проби/заяви_промпт_6870.py /tmp/s31.txt /tmp/s28.txt"""
import glob, json, re, sys
sys.path.insert(0, ".")
import мовний_шар as МШ, верхнє_стан as ВС, вердикт_моделі as ВМ
СТАРІ = {"card_added_by_code": "card_added_by_selection", "item_added_by_code": "item_added_by_selection",
         "code_swapped_item_from_stylist_look": "selection_swapped_item_from_stylist_look"}
def запис(шлях):
    т = open(шлях, encoding="utf-8").read(); запит, відп = т.split("── ВІДПОВІДЬ", 1)
    сирий = запит.split("\nПОВІДОМЛЕННЯ:\n", 1)[1].strip()
    for с, н in СТАРІ.items():
        сирий = re.sub(r"\b%s\b" % с, н, сирий)
    return запит, json.loads(сирий[: сирий.rindex("]") + 1]), json.loads(відп[відп.index("{"): відп.rindex("}") + 1])
межа = sum(open(f, encoding="utf-8").read().count("межа=44") for f in glob.glob("*.py"))
print("6871 · «межа=44» у джерела/*.py: %d" % межа)
запит, р31, т31 = запис(sys.argv[1])
з11 = [з for р in р31 for з in р["заяви"] if з["code"] == "outer_will_not_fit_over_bulky"][0]["values"]
was = [з for р in р31 for з in р["заяви"] if з["code"].endswith("swapped_item_from_stylist_look")][0]["values"]["was"]
з = dict(id="ж-1", слот="верх", тип="піджак", назва=з11["outer"]["free_text"], крій="fitted")
в = dict(id="ж-2", слот="верхній_шар", тип="куртка", назва=was["free_text"], крій="oversize")
після = [x for зн in ВС.драбина_шарів([з, в]) for x in зн.get("заяви") or []][0]["values"]
print("6871 · seed3_31 №11 under ДО: %s · ПІСЛЯ: %s (item_id %s)" % (з11["under"]["free_text"],
      після["under"]["name"]["free_text"], після["under"].get("item_id")))
п31 = МШ.промпт_повідомлень(МШ.розмітити_повідомлення({str(р["н"]): {"kind": р["вид"], "statements": р["заяви"]} for р in р31}))
print("6872 · рядок «ключ кожної заяви без перенумерації» у промпті шару: ДО %d · ПІСЛЯ %d · відповідь ДО: %s" % (
      int("кожна стоїть у тексті своїм змістом" in запит), int("Ключі не нумеруй" in п31), т31.get("1", "")[:90]))
запит28, р28, т28 = запис(sys.argv[2])
сх = [з for р in р28 for з in р["заяви"] if з["code"] == "scheme_tonal_tone_not_on_large_items"][0]["values"]
print("6870 · Ж:08 значення заяви схеми ДО: %s · ПІСЛЯ додано: off_tone, unmeasured — %s" % (
      sorted(сх), "unmeasured" in МШ.промпт_повідомлень(МШ.розмітити_повідомлення({str(р["н"]): {"kind": р["вид"], "statements": р["заяви"]} for р in р28}))))
print("6870 · відповідь ДО: %s" % т28.get("1", ""))
print("6785 · «under «answer»» у правилі кінця ремонту: %d" % ВМ._РЯДОК_КІНЕЦЬ.count("under «answer»"))
