import collections, copy, json, os, subprocess, sys, types; sys.path.insert(0, "."); import оцінка_образу as НОВ, схема_відповіді as СВ
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
СТ = types.ModuleType("оцінка_образу_до"); СТ.__file__ = os.path.abspath("оцінка_образу.py")
exec(git("show", "origin/main:джерела/оцінка_образу.py"), СТ.__dict__)
ТЕКИ = {"pachka-14": "пачка_14", "pachka-15": "пачка_15", "22": "22", "24": "24", "25": "25", "27": "27"}
def _вим(в):
    def г(*а, **к): return copy.deepcopy(в); yield
    return г
def сторож(М, т, суд):
    с = СВ.схема_за_назвою("OUTFIT_REVIEW_V1"); р = с.виконати_розбір(т)
    return М._сторож_оцінки_об(*р[:1], суд, *р[1:])
for г, т in ТЕКИ.items():
    for ф in [ф for ф in git("ls-tree", "-r", "--name-only", "origin/claude/zhyvi-" + г, ":/аудит/живі_" + т).split("\n") if "оціни_образ" in ф and ф.endswith("/вердикти.txt")]:
        d0 = json.loads(git("show", "origin/claude/zhyvi-%s:%s" % (г, ф)))
        if "вхід_прогону" not in d0["спільне"]: continue
        for н, в in enumerate([в for п in d0["прогони"] for в in п["вердикти"] if (в.get("етапи") or {}).get("суд", {}).get("образ")]):
            е = в["етапи"]; зап = [dict(р, палітра=None) for р in е["суд"]["речі"]]
            рез = {}
            for ім, М in (("до", СТ), ("після", НОВ)):
                М._виміри_кроками = _вим(зап); d = dict(d0["спільне"]["вхід_прогону"], речі=е["речі"]["речі"], пікселі={}, сценарій_оцінки=е.get("сценарій_екрана") or {}); d.pop("каталог", None)
                суд = М.суд(d)
                for н2, в_ in enumerate([x for x in е["виклики"] if x["крок"].startswith("оцінка") and x.get("відповідь_сира")]):
                    рез[(ім, н2)] = (суд, сторож(М, в_["відповідь_сира"], суд))
            for (ім, н2), (суд, ст) in list(рез.items()):
                екз = {р["ід"]: р for р in суд["речі"]}
                for p in (ст["картка"] or {}).get("вдало") or []:
                    РОД = {"верх": "верх", "верхній_шар": "верх", "сукня": "верх", "низ": "низ", "взуття": "взуття"}
                    хиб = [і for і in p["речі"] if (екз[і]["фото"] == "ф2" and РОД.get(екз[і]["слот"]) != "взуття") or (екз[і]["фото"] == "ф1" and РОД.get(екз[і]["слот"]) == "взуття")]
                    print("ВДАЛО", ім, г, ф.split("/")[-2][:2], н, н2, p["про"], p["речі"], "ХИБНІ:" if хиб else "", хиб, [(екз[і]["фото"], екз[і]["слот"], екз[і].get("колір")) for і in хиб])
