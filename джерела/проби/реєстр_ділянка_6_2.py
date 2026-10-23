"""6.2-Б, 8773/9190: усі 10 записаних сцен пачки 15, суд наново на повному каталозі.
Із джерела/: python3 -W ignore проби/реєстр_ділянка_6_2.py [ref ДО=7e143bda] [ref main=feba6049].
Речі — записаний розбір відповіді; у 04 перенос ділянки зіставлено через ід_моделі. Моделі немає."""
import copy, json, os, subprocess, sys, types
sys.path.insert(0, ".")
import оцінка_образу as НОВ
git = lambda *а: subprocess.check_output(["git", *а]).decode()
модулі = [("main", sys.argv[2] if len(sys.argv) > 2 else "feba60494d0deb0df61a32079317172d3a241c25"),
          ("ДО", sys.argv[1] if len(sys.argv) > 1 else "7e143bda124456134ee06ebdb8345f09def0808e")]
for і, (ім, ref) in enumerate(модулі):
    М = types.ModuleType("оцінка_" + ім); М.__file__ = os.path.abspath("оцінка_образу.py")
    exec(git("show", ref + ":джерела/оцінка_образу.py"), М.__dict__); модулі[і] = (ім, М)
модулі.append(("ПІСЛЯ", НОВ))
for н in range(1, 11):
    шлях = "origin/claude/zhyvi-pachka-15:аудит/живі_пачка_15/%02d_ж1_оціни_образ_6б/" % н
    в = json.loads(git("show", шлях + "вердикти.txt")); е = в["прогони"][0]["вердикти"][0]["етапи"]
    підсумок = []
    for ім, М in модулі:
        речі = copy.deepcopy(е["речі"]["речі"]); виміри = {р.get("ід_моделі") or р["ід"]: р for р in е["суд"]["речі"]}
        for р in речі:
            з = виміри[р["ід"]]; р.update(фото=з["фото"], вимір=copy.deepcopy(з.get("вимір") or {}))
        с = М.суд(dict(в["спільне"]["вхід_прогону"], каталог="каталог_повний.xml", речі=речі, крамниця=True))
        підсумок.append("%s: образ=%s; крамниця=%d" % (ім, ",".join(с["образ"]), sum(з.get("звідки") == "shop" for з in с["зміни"])))
        if ім != "ПІСЛЯ": continue
        if н in (1, 5):
            ід = "ф2·2" if н == 1 else "ф2"; р = next(р for р in с["речі"] if р["ід"] == ід)
            assert not р["вимір"].get("lab") and ід not in с["образ"] + с["запасні"] and not any(з["ціль"] == ід for з in с["зміни"])
            assert р["вимір"]["причина"] == М.ПРИЧИНА_ДІЛЯНКИ
            спір = р["вимір"]["ненадійний"]["спір"]; assert спір["відстань_до_вікна"] >= спір["допуск"]
            дріт = next(з for з in М.дані_оцінки(с)["items"] if з["id"] == ід)
            assert дріт["photo"] == р["фото"] and дріт["location_status"] == М.ПРИЧИНА_ДІЛЯНКИ and дріт["color"] == "burgundy"
            assert any(б.get("input") == "item_location" for б in с["без_входу"]) and all(ід not in з.get("items", []) for з in М.опори_вдалого(с))
        if н in (6, 9, 10):
            ід = "ф1·2" if н == 9 else "ф2"; р = next(р for р in с["речі"] if р["ід"] == ід)
            assert ід in с["образ"] and р["вимір"].get("lab") and р["вимір"]["спір"]["відстань_до_вікна"] == 0
            assert len(с["образ"]) == (4 if н == 9 else 2)
            if н != 9: assert sum(з.get("звідки") == "shop" for з in с["зміни"]) == 3
    print("%02d | %s" % (н, " | ".join(підсумок)))
