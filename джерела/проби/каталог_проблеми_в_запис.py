# -*- coding: utf-8 -*-
# Реєстр проблем бази одягу, напрям В, клас «запис речі для моделі». ФАКТ на пулі стенда
# (`стенд_вх.json`, одне повне збирання, запис як сьогодні): (1) речей і середня довжина
# запису; (2) скільки записів несуть бренд, `features`, опис — тобто чи доходять вони до
# моделі взагалі; (3) «тканина: невідомо» — де саме (на прикрасах тканини нема за природою
# речі, а запис каже «невідомо»); (4) однакові назви в одному пулі; (5) речі без типу.
import os, re, sys, json, collections as C
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП, каталог_коди as КК
ВХ = dict(json.load(open("стенд_вх.json", encoding="utf-8")), каталог=Ф.каталог_на_диску())
json.loads(B.виклик("запити", json.dumps(ВХ, ensure_ascii=False)))
пак = [п for п in МП._КЕШ_ПАКЕТА.values() if п.get("пакет")][0]
пул = [(с, р) for с, рр in пак["пакет"]["пул"].items() for р in рр]
д = [len(json.dumps(р, ensure_ascii=False, separators=(",", ":"))) for _, р in пул]
print("пул %d речей · запис сер. %d знаків · текст пакета %d знаків" % (len(пул), sum(д) / len(д), len(пак["текст"])))
ключі = C.Counter(к for _, р in пул for к in р)
print("записів з ключем: бренд %d · features %d · опис %d · тип %d · тканина %d"
      % tuple(sum(v for к, v in ключі.items() if re.search(x, к)) for x in ("бренд|vendor", "feature|особлив", "опис", "^тип$", "тканин")))
print("файл розбору (коди + features): %s" % (КК.шлях() or "нема — короткий запис і features не мають звідки взятись"))
ПРИКРАСИ = {"прикраси", "сережки", "каблучка", "браслет", "намисто", "кольє", "брошка"}
нев = [с for с, р in пул if р.get("тканина") == "невідомо"]
print("«тканина: невідомо» %d, з них на прикрасах %d · за слотами %s"
      % (len(нев), sum(1 for с in нев if с in ПРИКРАСИ), dict(C.Counter(нев).most_common(6))))
н = C.Counter(р["назва"] for _, р in пул)
print("однакових назв у пулі: %d зайвих записів, напр. %s" % (sum(v - 1 for v in н.values() if v > 1),
                                                            [k for k, v in н.items() if v > 1][:3]))
print("без типу %d %s" % (sum(1 for _, р in пул if "тип" not in р),
                          dict(C.Counter(с for с, р in пул if "тип" not in р))))
