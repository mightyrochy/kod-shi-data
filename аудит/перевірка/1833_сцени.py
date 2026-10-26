import sys, io, contextlib, json
sys.path.insert(0, sys.argv[1]+"/джерела")
with contextlib.redirect_stdout(io.StringIO()):
    import мовний_шар as МШ
def шар(вн, сц, досі=None, слова=""):
    with contextlib.redirect_stdout(io.StringIO()):
        return МШ.паспорт_з_шару(вн, сц, паспорт_досі=досі, слова_ходу=слова)["паспорт"]
к = lambda п, п_: json.dumps((п.get("картка_запиту") or {}).get(п_), ensure_ascii=False)
# (i) година названа, наступний хід без оновлення
a = шар({"hour": 19, "quotes": {"hour": "о 19:00"}, "occasion": "work", "quotes2": 0}, {}, слова="сьогодні о 19:00")
b = шар({}, {}, досі=a, слова="додай сумку")
print("i  хід1 година:", a.get("година"), к(a, "година"), "| хід2:", b.get("година"), к(b, "година"), "| звідки:", (b.get("звідки") or {}).get("hour"))
# (ii) her → her інша цитата
c = шар({"occasion": "sport", "quotes": {"occasion": "йога"}}, {}, слова="йога")
d = шар({"occasion": "work", "quotes": {"occasion": "на роботу"}}, {}, досі=c, слова="ні, на роботу")
print("ii нагода:", d.get("нагода"), к(d, "нагода"), "| звідки:", (d.get("звідки") or {}).get("occasion"))
# (iii) плитка поверх her
e = шар({"occasion": "work", "quotes": {"occasion": "на роботу"}}, {}, слова="на роботу")
f = шар({}, {"нагода": "спорт"}, досі=e, слова="")
print("iii нагода:", f.get("нагода"), к(f, "нагода"), "| звідки:", (f.get("звідки") or {}).get("occasion"))
# (iv) хід без цитати змінює нагоду, її слова попереднього ходу
g = шар({"occasion": "work"}, {}, досі=e, слова="додай сумку")
print("iv нагода:", g.get("нагода"), к(g, "нагода"), "| звідки:", (g.get("звідки") or {}).get("occasion"))
