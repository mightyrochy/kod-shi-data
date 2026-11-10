"""НЕВДАЛЕ (крок 21): вердикт двома рівнями — першою барвна, коли сума сил тону більша за ахроматичну. Лічить, скільки
речей змінили б першу сім'ю. Запуск із кореня (розпакований каталог)."""
import sys, collections, pickle, os
sys.path.insert(0, "джерела")
import колір_річ as КР, колір_тон as Т, фід_каталог as ФК
from колір_простір_перетворення import lch, hex_з_lab
З = Т.РЕЄСТР["значна_сила"]["val"]
кеш = "/tmp/точки_каталогу.pkl"
if os.path.exists(кеш):
    точки = pickle.load(open(кеш, "rb"))
else:
    кат = ФК.прочитати_каталог(ФК.каталог_на_диску("каталог_повний.xml"), 0)["каталог"]
    точки = []
    for р in кат:
        lab = КР.точка_кольору(р)
        if lab is not None:
            точки.append(([float(x) for x in lab], р.get("колір_назва") or "", (р.get("назва") or "")[:40], р.get("id")))
    pickle.dump(точки, open(кеш, "wb"))
пер, слова, прикл = collections.Counter(), collections.Counter(), []
for lab, сл, наз, ід in точки:
    с = Т.сили_сімей(lab)
    ахр = с.get("achromatic", 0.0)
    тон = [(к, в) for к, в in с.items() if к not in ("achromatic", Т.НЕВІДОМО)]
    сума = sum(в for _, в in тон)
    в = Т.сім_ї_кольору(lab)
    if в[0][0] == "achromatic" and тон and сума > ахр and тон[0][1] >= З:
        пер[(в[0][0], тон[0][0])] += 1; слова[сл.lower()] += 1
        L, C, h = lch(lab)
        прикл.append((round(L), round(C, 1), round(h), hex_з_lab(lab), сл, наз, round(ахр, 2), round(сума, 2), тон[0]))
print("точок", len(точки), "першою стала б барвна:", sum(пер.values()))
for к, н in пер.most_common(): print("  ", к, н)
print("слова:", слова.most_common(25))
import random; random.Random(1).shuffle(прикл)
for п in прикл[:25]: print(п)
