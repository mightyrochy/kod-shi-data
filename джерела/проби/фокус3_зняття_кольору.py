"""ФОКУС-3 (рядки 1520–1522): знахідки на кольорових образах вердикта ремонту (руки 1–2), переграні чинним кодом на
речах вердикта; «зн.» — образи, з яких ремонт зняв колір. K-COL-02/K-COL-03: стоїть / ремонт лишає (keep) чи стишує
(quiet) слот знятої речі / без ремонту; R-CHEV-08 «собою»: слоти речей і чи лишається знахідка при зоні мети.
Волосся — з `face` вердикта. Запуск із джерела/: python3 проби/фокус3_зняття_кольору.py ../аудит/перевірки/fokus_2/ПІСЛЯ"""
import json, gzip, glob, os, sys, collections as K
sys.path.insert(0, "."); import colorspace as cs, palettes as P, внутрішня_мова as ВМ, суд_від_моделі as С, регістр_уваги as РУ, суд_ремесло as СР
ЗОНА = {"ж4_робота_живіт": ["живіт"]}   # код `goal_zones`, який мовна модель ставить на «приховати живіт»
на_мету = getattr(РУ, "на_мету", lambda *x: True)
хр = lambda i: bool(i.get("hex")) and i.get("color") not in ("golden", "silvery", "pearly") and P._хроматична(cs.hx(i["hex"]))
сл = lambda i: ВМ.ключ("slot", ВМ.СЛОТ_ТИПУ.get(i.get("type"), "jewelry")) or "прикраси"
def дж(t):
    try: return json.JSONDecoder().raw_decode(t[t.index("{"):])[0]
    except Exception: return {}
Л = K.Counter()
for f in sorted(glob.glob(sys.argv[1] + "/ж*_*/вердикти.txt.gz")):
    for в in json.load(gzip.open(f, "rt"))["прогони"][0]["вердикти"]:
        cc = {c["крок"]: c for c in в["етапи"]["виклики"]}
        if str(в["рука"]) not in "12" or "repair" not in cc: continue
        q = json.loads(cc["repair"]["запит"]["текст"]); a = {o["id"]: o for o in дж(cc["repair"].get("відповідь_сира") or "").get("outfits", [])}
        сп = {ВМ.ключ("slot", к) or к: {"роль": ВМ.ключ("scheme_role", р), "C": [1, 100]} for к, р in
              json.loads(cc["assembly"]["запит"]["текст"])["person"].get("palette", {}).get("slot_roles", {}).items()}
        сп["_схема"] = в.get("пал_схема_руки")
        for o in q["verdict"]:
            yo = o["your_outfit"]; ca = [i for i in yo["items"] if хр(i)]
            if not ca: continue
            кз = {ВМ.код("slot", сл(i)) for i in ca if yo["id"] in a and i["n"] not in a[yo["id"]]["items"]}
            речі = [dict(id=i["n"], слот=сл(i), hex=i["hex"], назва=i["name"]) for i in yo["items"] if i.get("hex")]
            face = [v for fd in o.get("findings", []) for s in fd.get("statements", []) if isinstance(s, dict)
                    for v in (s.get("loud_elements_over_budget") or {}).get("face", [])]
            сх = СР.слоти_акценту_схеми(речі, сп); кв = {"схема_слоти": сх} if "схема_слоти" in С.бюджет_і_відлуння.__code__.co_varnames else {}
            for z in [z for z in С.бюджет_і_відлуння(речі, {"волосся_%d" % k: {"C": 99} for k in range(len(face))}, None,
                                                    sorted(сх) or None, **кв) if z["правило"] == "K-COL-02"] + P.обіцянка_схеми(речі, сп):
                к, v = z["заяви"][0]["code"], z["заяви"][0]["values"]
                Л[к + " стоїть (кольорових)"] += 1; Л[к + " стоїть (зн.)"] += bool(кз)
                Л[к + " · зн.: лишає зняте"] += bool(кз & set(v.get("keep") or ())); Л[к + " · зн.: стишує зняте"] += bool(кз & set(v.get("quiet") or ()))
                Л[к + " · зн.: без ремонту"] += bool(кз) and not z.get("ремонт_заяви")
            for fd in o.get("findings", []):
                for i in (i for i in yo["items"] if str(fd.get("what", "")).startswith("річ помітна не кольором") and i["n"] in fd["items"]):
                    Л["R-CHEV-08 собою · %s · %s" % (сл(i), "лишається" if на_мету(сл(i), None, None, ЗОНА.get(f.split("/")[-2])) else "знято зоною")] += 1
for к, v in sorted(Л.items()): print("  %-60s %3d" % (к, v))
