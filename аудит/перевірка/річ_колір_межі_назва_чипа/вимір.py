"""Вимір 15198: слово точки поза вікнами коду кольору. Запуск: cd джерела && python3 ../аудит/перевірка/річ_колір_межі_назва_чипа/вимір.py
Точки — hex вибірки 40 речей (20261114) і решітка Lab; друкує: точок поза вікнами, слів не з родини точки."""
import sys, csv, collections
sys.path.insert(0, ".")
import surface as S, colorspace as CS, колір_тон as КТ, словник_кольору as СК
рядки = list(csv.DictReader(open("../аудит/проби/річ_колір_один_колір_1411/вибірка_40.tsv", encoding="utf-8"), delimiter="\t"))
точки = [CS.hx(р["hex"]) for р in рядки if р["hex"].startswith("#")]
точки += [(L, a, b) for L in range(10, 100, 10) for a in range(-80, 81, 20) for b in range(-80, 81, 20)]
поза = 0; чужі = collections.Counter(); приклад = {}
for lab in точки:
    сл, у = S.слово_з_lab(tuple(lab))
    if у: continue
    поза += 1
    ріднi = СК.НАЗВА_ПРОДУКТУ[СК.КОД_СІМ_Ї_МОДУЛЯ[КТ.сім_ї_кольору(tuple(CS.hx(CS.hex_з_lab(tuple(lab)))))[0][0]]] if КТ.сім_ї_кольору(tuple(CS.hx(CS.hex_з_lab(tuple(lab)))))[0][0] != КТ.НЕВІДОМО else "невідомо"
    if сл != ріднi:
        чужі[сл] += 1
print("точок", len(точки), "поза вікнами", поза, "слово не родини точки", sum(чужі.values()), dict(чужі))
