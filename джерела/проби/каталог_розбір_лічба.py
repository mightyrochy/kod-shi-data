# -*- coding: utf-8 -*-
"""Проба: на ЗБЕРЕЖЕНИХ відповідях прогону розбору каталогу друкує факт — валідний JSON, покриття кожного поля
(і `features`), форму `features`, коди без цитати в тексті речі (`invented`, РЗ-К) і незгоду з кодом. Моделі не кличе.
Запуск: python3 джерела/проби/каталог_розбір_лічба.py <тека від каталог_розбір_прогін.py>"""
import collections, json, os, sys                                             # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import каталог_розбір as КР, каталог_розбір_прогін as П, фід_каталог as ФК, фід_розбір as ФР  # noqa: E401,E402
тека = sys.argv[1] if len(sys.argv) > 1 else sys.exit("треба тека прогону"); мірка = json.load(open(os.path.join(тека, "прогін.json"), encoding="utf-8"))  # noqa: E702
офери = {o["id"]: o for o in ФР.читати_yml(ФК.каталог_на_диску(), показ=False)[0]}
валідні, причини, покр, види, незгоди, збої_коду, ос = 0, [], dict.fromkeys(КР.покриття({}), 0), {}, [], {}, collections.Counter()
for р in мірка["речі"]:
    дані, відп = П.розділити(open(os.path.join(тека, р["файл"]), encoding="utf-8").read())  # що модель бачила
    поля, пр = КР.з_відповіді(відп, дані)                                     # сторож цитат (РЗ-К)
    причини += [(р["файл"], т) for т in пр]
    if not поля: continue                                                     # noqa: E701
    валідні += 1; покр.update({ш: покр[ш] + є for ш, є in КР.покриття(поля).items()})  # noqa: E702
    ос["+".join(т.split(" — ")[0][10:] for т in пр if т.startswith("features:"))
       or ("unknown" if поля[КР.ОСОБЛИВОСТІ] == КР.UNKNOWN else "прийнято")] += 1
    код, збої = КР.що_каже_код(офери[р["id"]]); збої_коду.update(збої)  # noqa: E702
    for вид, ш, к, м in КР.незгода(код, поля):
        види[(вид, ш)] = види.get((вид, ш), 0) + 1
        if вид == "незгода":
            незгоди.append((р["id"], ш, к, м))
n = len(мірка["речі"]) or 1; print("модель %s · мова %s · речей %d · валідний JSON %d (%d %%) · впало викликів %d"
      % (мірка["модель"], мірка["мова"], n, валідні, round(100 * валідні / n),
         sum(1 for р in мірка["речі"] if р["впало"])), flush=True)
print("покриття полів (з %d валідних):" % валідні)
for ш in покр:
    print("  %-18s %2d  %3d %%" % (ш, покр[ш], round(100 * покр[ш] / (валідні or 1))))
print("форма features (з %d валідних): %s" % (валідні, dict(ос)))
for вид in ("незгода", "код не знає", "модель не знає"):
    п = sorted(((ч, ш) for (в, ш), ч in види.items() if в == вид), reverse=True)
    print("%s: %d на %d полях · %s" % (вид, sum(ч for ч, _ in п), len(п), ", ".join("%s×%d" % (ш, ч) for ч, ш in п[:12])))
for id_, ш, к, м in незгоди:
    print("  НЕЗГОДА %-26s %-14s код=%-14s модель=%s" % (id_, ш, к, м))
вигадки = collections.Counter(т.split(" · ")[2][6:] for _, т in причини if т.startswith("invented"))
print("без цитати в тексті речі (invented → unknown): %d · %s" % (sum(вигадки.values()), ", ".join("%s×%d" % к for к in вигадки.most_common(14))))
вади = [т for _, т in причини if not т.startswith(("features:", "invented", "shared_quote", "slot"))]
print("вад форми відповіді (коди): %d · %s" % (len(вади), "; ".join(вади[:6])))
print("збої коду на звірці: %s" % (збої_коду or "нема"))
