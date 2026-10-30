# -*- coding: utf-8 -*-
"""4949: сім'я пакета проти суду за тим самим hex; каталог без нових вимірів."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import colorspace as КС
import колір_річ as КР
import дріт_моделі as Д
import фід_каталог as Ф
import пакет_моделі as П
import композитор_річ as КМ

def проба():
    """Друкує розбіжності темних бурих та зміни бордо поза вікном."""
    кат = Ф.база_прогону(Ф.каталог_на_диску("каталог_повний.xml"), ліміт_фото=0)["каталог"]
    бурі = []; бордо = []; інші = []
    for р in кат:
        р = dict(р, hex=КР.hex_кольору(р) or (КМ.hex_від_lab(КР.точка_кольору(р)) if КР.точка_кольору(р) else None),
                 колір=р.get("колір") or р.get("колір_назва"))
        if not КР.hex_кольору(р):
            continue
        lab = КС.hx(КР.hex_кольору(р))
        вхід = П.річ_пулу(dict(р, сім_я=П.сім_я_тону(КР.hex_кольору(р))), {})
        до = Д.код_переліку(Д.СІМ_Я, вхід.get("сім_я"))
        після = Д.річ(вхід).get("family")
        if КР._темне_буре(*КС.lch(lab)):
            суд = Д.код("colour_family", КР.сім_я(lab))
            бурі.append((до, після, суд))
        else:
            інші.append((до, після))
            if Д.колір_код(р.get("колір"))[0] == "burgundy":
                бордо.append((до, після))
    print("Темні бурі %d: не нейтральний family ДО %d, ПІСЛЯ %d; розбіжних із судом %d" %
          (len(бурі), sum(not str(a).startswith("neutral_") for a, _, _ in бурі),
           sum(not str(b).startswith("neutral_") for _, b, _ in бурі),
           sum(b != c for _, b, c in бурі)))
    print("Бордо поза вікном %d: змінено %d; решта поза вікном: змінено %d" %
          (len(бордо), sum(a != b for a, b in бордо), sum(a != b for a, b in інші)))

if __name__ == "__main__":
    проба()
