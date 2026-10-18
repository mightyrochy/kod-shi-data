# -*- coding: utf-8 -*-
"""Ф2 2.4: вимір копій ошатності на всьому каталозі; JSON за другим аргументом — для ДО/ПІСЛЯ."""
import json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed, формальність as Ф, композитор_придатні as П, композитор_слоти as С

def вимір():
    """Міряє інтервали речей та незгоду читачів на всіх цілих смугах 1–10."""
    кат = feed._прочитати_каталог(feed.каталог_на_диску(), 0)["каталог"]
    вих, незгода, типи = {}, 0, 0
    for р in кат:
        л, в = Ф.інтервал_формальності(р)
        тл, тв, _ = Ф.інтервал_типу(р.get("тип"))
        типи += (л, в) != (тл, тв)
        з = []
        for н in range(1, 11):
            нижче = bool(П.нижче_смуги(р, н))
            оч = в is not None and в < н
            від = С._відстань_фото(р, н, н)
            оч_від = None if л is None else max(н - в, л - н, 0)
            if нижче != оч or від != оч_від:
                з.append(н)
        незгода += bool(з)
        вих[р["id"]] = dict(смуга=[л, в], тип=[тл, тв], розходження=з)
    print(json.dumps(dict(речей=len(вих), тип_не_річ=типи, читачі_розходяться=незгода,
                          частка=round(100 * незгода / len(вих), 3)), ensure_ascii=False))
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as ф:
            json.dump(вих, ф, ensure_ascii=False, sort_keys=True)

if __name__ == "__main__":
    вимір()
