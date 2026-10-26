import sys, io, contextlib, json
sys.path.insert(0, sys.argv[1]+"/джерела")
with contextlib.redirect_stdout(io.StringIO()):
    import мовний_шар as МШ
def шар(вн, сц, досі=None, слова=""):
    with contextlib.redirect_stdout(io.StringIO()):
        return МШ.паспорт_з_шару(вн, сц, паспорт_досі=досі, слова_ходу=слова)["паспорт"]
к = lambda п, п_: json.dumps((п.get("картка_запиту") or {}).get(п_), ensure_ascii=False)
п1 = шар({}, {"нагода": "спорт"}, досі=шар({}, {}))
п2 = шар({"occasion": "work"}, {"нагода": "спорт"}, досі=п1, слова="додай сумку")
print("P1a нагода:", п2.get("нагода"), "| картка:", к(п2, "нагода"))
a = шар({"occasion": "sport", "quotes": {"occasion": "йога"}}, {}, слова="йога зранку")
b = шар({"occasion": "work"}, {}, досі=a, слова="додай сумку")
print("P1b ходу1:", a.get("нагода"), к(a, "нагода"))
print("P1b ходу2:", b.get("нагода"), к(b, "нагода"), "| звідки:", (b.get("звідки") or {}).get("occasion"), "| цитата:", (b.get("цитати_полів") or {}).get("нагода"))
с = {"година": 11, "нагода": "щоденне", "типові_поля": ["година", "нагода"]}
c = шар({}, с, слова="додай сумку")
print("P2a звідки:", {x: (c.get("звідки") or {}).get(x) for x in ("occasion", "hour", "part_of_day")})
d = шар({"part_of_day": "evening", "quotes": {"part_of_day": "ввечері"}}, с, слова="ввечері")
print("P2b hour у вимірах:", (d.get("виміри") or {}).get("hour"), "| звідки:", {x: (d.get("звідки") or {}).get(x) for x in ("hour", "part_of_day")})
print("P2c _година_названа(18,'на 30 людей'):", МШ._година_названа({"value": 18, "quote": "на 30 людей", "named": "clock_time"}))
print("P2c' (18,'о 7 вечора'):", МШ._година_названа({"value": 19, "quote": "о 7 вечора", "named": "clock_time"}))
