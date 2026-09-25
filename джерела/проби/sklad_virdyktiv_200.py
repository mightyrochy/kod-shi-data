# -*- coding: utf-8 -*-
"""ЩО СПРАЦЮВАЛО (рядок 200). Вісім вердиктів «Ір» (22–23.09) з речами каталогу — руки 1 і 2 — речами:
колір слова крамниці, сім'я (`колір_річ.сім_я`), світлота L, формальність типу. Підсумок на образ: скільки
хроматичних сімей, скільки нейтралей, розмах світлоти ΔL (контраст образу). Запуск: cd джерела && python3 проби/sklad_virdyktiv_200.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import json, bridge as B, колір_річ as КР, colorspace as cs, формальність as ФО
В = [("0", 1, "змінити/не моє", "03970@maxa.ua 06361@sunwin-store.com 02168@twice.com.ua 08868@cooshwear.com 11514@theoriginals.com.ua 11814@theoriginals.com.ua"),
     ("0", 2, "ЯК Є/гарний·палітра→н+а", "01846@maryline.ua 02662@sunwin-store.com 07116@feelyou.com.ua 08904@jecomestudio.com 08135@welfare.ua"),
     ("0", 1, "змінити/гарний", "02662@sunwin-store.com 06633@maryline.ua 02844@25union.com.ua 10110@favoriteshoes.com.ua 08117@welfare.ua"),
     ("0", 2, "НЕ/не моє·музей", "00365@maryline.ua 05264@alot.com.ua 10474@giardini-shoes.com 08117@welfare.ua"),
     ("3", 1, "змінити/САМЕ МОЄ", "03177@vilni.store 02664@sunwin-store.com 10795@skripka.com.ua 09919@emmeliedelage.com 07852@giardini-shoes.com"),
     ("3", 2, "ЯК Є/гарний·година", "03882@likeangel.com.ua 06645@ricamare.com.ua 04393@likeangel.com.ua 11202@theoriginals.com.ua 08183@attico.ua"),
     ("4", 2, "ЯК Є/САМЕ МОЄ·темп", "03664@feelyou.com.ua 06898@twice.com.ua 01748@25union.com.ua 09919@emmeliedelage.com 08124@welfare.ua"),
     ("4", 1, "ЯК Є/САМЕ МОЄ", "02626@sunwin-store.com 06190@twice.com.ua 03390@25union.com.ua 09011@kasandra.ua 08122@welfare.ua 08655@likeangel.com.ua")]
if __name__ == "__main__":
    json.loads(B.виклик("запити", open("стенд_вх.json", encoding="utf-8").read()))     # лише щоб мати каталог продукту
    кат = {c["id"]: c for c in B.каталог_останнього_пакета()}
    for прогін, рука, вердикт, склад in В:
        речі = [кат["ж-" + i] for i in склад.split()]
        рядки, сім = [], []
        for р in речі:
            L, C, h = cs.lch(р["lab"]); ф = КР.сім_я(р["lab"]); сім.append(ф)
            лоу, хай = ФО.інтервал_формальності(dict(р, річ=р["назва"]))[:2]
            рядки.append("   %-9s %-22s %-12s %-24s L%3.0f C%3.0f форм %s" % (р["слот"], (р.get("тип") or "")[:22],
                         (р.get("колір_ім") or "—")[:12], ф, L, C, "—" if лоу is None else "%.1f–%.1f" % (лоу, хай)))
        хр = sorted({ф for ф in сім if not ф.startswith("нейтраль")})
        Ls = [cs.lch(р["lab"])[0] for р in речі]
        print("прогін %s · рука %d · %-26s ФАКТ: нейтралей %d/%d · хром. сімей %d %s · ΔL %.0f"
              % (прогін, рука, вердикт, len(сім) - sum(1 for ф in сім if not ф.startswith("нейтраль")), len(сім),
                 len(хр), хр, max(Ls) - min(Ls)))
        print("\n".join(рядки))
