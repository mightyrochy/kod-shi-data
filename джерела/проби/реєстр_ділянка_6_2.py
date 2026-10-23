"""6.2-Б, 8773: записані відповіді й виміри пачки 15, суд наново на повному каталозі.
Запуск із джерела/: python3 -W ignore проби/реєстр_ділянка_6_2.py [ref ДО]. Живої моделі тут немає."""
import copy, json, os, subprocess, sys, types
sys.path.insert(0, ".")
import оцінка_образу as НОВ
git = lambda *а: subprocess.check_output(["git", *а]).decode()
ДО = types.ModuleType("оцінка_до"); ДО.__file__ = os.path.abspath("оцінка_образу.py")
exec(git("show", (sys.argv[1] if len(sys.argv) > 1 else "origin/main") + ":джерела/оцінка_образу.py"), ДО.__dict__)
for н, ід in ((1, "ф2·2"), (5, "ф2")):
    шлях = "origin/claude/zhyvi-pachka-15:аудит/живі_пачка_15/%02d_ж1_оціни_образ_6б/" % н
    в = json.loads(git("show", шлях + "вердикти.txt"))
    е = в["прогони"][0]["вердикти"][0]["етапи"]
    текст = git("show", шлях + "VIDPOVIDI/seed%d_02_ОЦІНКА_речі_на_фото.txt" % н).split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]
    for ім, М in (("ДО", ДО), ("ПІСЛЯ", НОВ)):
        речі = М.речі_з_відповіді(текст, е["фото"])["речі"]
        виміри = {р["ід"]: р["вимір"] for р in е["суд"]["речі"]}
        for р in речі: р["вимір"] = copy.deepcopy(виміри[р["ід"]])
        с = М.суд(dict(в["спільне"]["вхід_прогону"], каталог="каталог_повний.xml", речі=речі, крамниця=True))
        р = next(р for р in с["речі"] if р["ід"] == ід)
        зміни = sum(з["ціль"] == ід for з in с["зміни"])
        print("%02d %s: чужий колір %d; у суді %d; зміни крамниці %d; причина %s" %
              (н, ім, bool(р["вимір"].get("lab")), ід in с["образ"], зміни, р["вимір"].get("причина")))
        if ім == "ПІСЛЯ":
            assert not р["вимір"].get("lab") and ід not in с["образ"] and ід not in с["запасні"] and not зміни
            assert р["вимір"]["причина"] == М.ПРИЧИНА_ДІЛЯНКИ
            assert р["вимір"]["ненадійний"]["спір"] and any(б.get("input") == "item_location" for б in с["без_входу"])
            дріт = next(з for з in М.дані_оцінки(с)["items"] if з["id"] == ід)
            assert дріт["photo"] == р["фото"] and дріт["location_status"] == М.ПРИЧИНА_ДІЛЯНКИ
            assert дріт["color"] == "burgundy" and not дріт["color_measured"]
            assert all(ід not in з.get("items", []) for з in М.опори_вдалого(с))
