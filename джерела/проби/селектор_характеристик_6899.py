# -*- coding: utf-8 -*-
# Рядок 6899 (а): `селектор_характеристик` рецепта — пари «ключ → значення» лише з названого вузла. Картка з таблицею
# характеристик і блоком доставки: без селектора в `характеристики_сирі` лізе «Нова пошта», з ним — тільки таблиця.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "zhnyvarka"))
import жниварка as ж
html = """<html><body><h1>Сукня</h1><div class="t"><table><tr><td>Склад</td><td>100% бавовна</td></tr>
<tr><td>Колір</td><td>синій</td></tr></table></div><div class="dostavka"><ul><li><span>Нова пошта</span><span>1-2 дні</span></li>
<li><span>Укрпошта</span><span>3-5 днів</span></li></ul></div></body></html>"""
for сел in ({}, {"характеристик": ".t"}):
    ф = ж.факти_з_картки(html, "https://x.ua/p/1", сел)
    print("%-28s ключів %d: %s" % (сел or "без селектора", len(ф["характеристики_сирі"]), [к for к, _ in ф["характеристики_сирі"]]))
print("колонка рецепта brenda.ua:", ж.рецепт_селекторів("brenda.ua"))
дві = html.replace("</table></div>", "</table></div><div class=\"t\"><table><tr><td>Зріст</td><td>170</td></tr></table></div>", 1)
ф = ж.факти_з_картки(дві, "https://x.ua/p/1", {"характеристик": ".t"})
print("два вузли .t: ключів %d: %s" % (len(ф["характеристики_сирі"]), [к for к, _ in ф["характеристики_сирі"]]))
