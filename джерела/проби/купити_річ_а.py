"""Мірило А наряду Функція-купити-річ: 5 спідниць каталогу (ід, назва, крій, колір, lab, довжина, см картки, тканина) як
речі з фото «хочу купити», 2 тіла, без портрета → `bridge.виклик("річ_з_фото")` і вибір у промпті стилістки; лічба (1)–(7)."""
import sys, os, json, time; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bridge, суд_покупки as СП
Р = [("ж-06737@ricamare.com.ua", "Спідниця міні на запах", "wrap", "white", (99, 0, 0), "mini", 44, None),
     ("ж-06105@sarahberlin.com", "Спідниця олівець з розрізом", "pencil", "graphite", (32, 0, 0), "midi", 72.5, None),
     ("ж-05634@likeangel.com.ua", "Спідниця сатинова лаванда", "bodycon", "lilac", (70, 10, -9), "midi", 82, "satin"),
     ("ж-05994@likeangel.com.ua", "Спідниця плісе чорна", "pleated", "black", (4, 0, 2), "midi", 90, None),
     ("ж-11167@theoriginals.com.ua", "Спідниця помаранчева на затин", "straight", "orange", (75, 19, 27), "midi", None, None)]
ТІЛА = {"А": dict(зріст=160, обхвати={"плечі": 92, "груди": 88, "талія": 70, "стегна": 106, "високе_стегно": 92}),
        "В": dict(зріст=174, обхвати={"плечі": 108, "груди": 98, "талія": 78, "стегна": 94, "високе_стегно": 86})}
# відповідь задачі фото (`річ_з_фото.промпт_фото`) кодами; см — з картки крамниці на фото
відп = json.dumps({"items": [dict(photo="ф%d" % і, name=н, slot="bottom", kind="skirt", color=к, cut=кр, length=д,
                                  length_cm=см, fabric=т, pattern="solid", owner="want_to_buy") for і, (_, н, кр, к, _l, д, см, т) in enumerate(Р)]})
фото = [dict(ід="ф%d" % і, ширина=800, висота=1200) for і in range(len(Р))]
речі = json.loads(bridge.виклик("річ_з_фото", json.dumps(dict(опис_фото="відповідь", відповідь_моделі=відп, фото=фото)))).get("речі_з_фото") or []
for р, з in zip(речі, Р):   # вимір кольору пікселями речі (`річ_з_фото.виміряти`) — lab запису каталогу
    р["вимір"] = dict(lab=list(з[4]), слово=р.get("колір"))
лічба, коди, мс, вибір, рядки_6 = dict.fromkeys(range(1, 8), 0), {}, [], [], []
ТІЛО_ПРОЙШЛО = {"maxi_holds"}   # заяви правила тіла, яке річ пройшла (`суд_покупки.тіло_речі`, `судилось`)
for тіло, вх in ТІЛА.items():
    d, вв = dict(вх, шкіра=[], волосся=[], очі=None, сценарій={}, колір_відмова="portrait_face_small", паспорт={"речі_з_фото": речі}), {}
    for р, з in zip(речі, Р):
        т = time.time()
        try: в = json.loads(bridge.виклик("річ_з_фото", json.dumps(dict(d, річ=р["ід"]))))["вердикт"]
        except Exception as е: в = dict(рівень="збій", повідомлення=None, причина=repr(е)[:80])
        мс.append(time.time() - т); вв[р["ід"]] = dict(р, вердикт=в)
        зз = (в.get("повідомлення") or {}).get("statements") or []; к = [x["code"] for x in зз]
        коди.setdefault(р["ід"], set()).add(json.dumps(зз, sort_keys=True))
        if тіло != "А": continue
        лічба[1] += bool(к) and (в["рівень"] != "невідомо" or any(x.endswith(("_not_judged", "_needs_portrait")) for x in к))
        лічба[2] += any(x in к for x in ("hem_on_her_body", "hem_not_judged")) and any(x in к for x in ("rise_of_item", "rise_not_named"))
        помітна = з[4][0] > 80 or з[7] == "satin"   # світла чи блискуча
        лічба[4] += any(x.startswith("colour_role_") for x in к) and any(x.startswith("pairs_with_") for x in к) and (not помітна or "draws_eye_enlarges" in к)
        # «личить» без пройденого правила тіла (клас краю — факт, не перевірка; перевірка-1211-11 на #3578)
        лічба[5] += в["рівень"] == "личить" and not set(к) & ТІЛО_ПРОЙШЛО
        лічба[7] += "colour_profile_needs_portrait" in к
    # (6) по суті: перша — ОДНА річ із причиною (заяви, яких у решти нема, чи ризики решти), без нічиї
    в6 = СП.вибір({і: р["вердикт"] for і, р in вв.items()})["заяви"]
    з6 = next((з for з in в6 if з["code"] == "buy_first"), {})
    перша = з6.get("values") or {}
    вибір.append(len(з6.get("item_ids") or ()) == 1 and bool(перша.get("reasons") or перша.get("avoids"))
                 and not any(з["code"] == "buy_order_tie" for з in в6))
    рядки_6.append("  %s: перша %s, причини %s, уникає %s, далі %s" % (тіло, з6.get("item_ids"), перша.get("reasons"),
                                                                       перша.get("avoids"), перша.get("then")))
лічба[3] = sum(len(в) > 1 for в in коди.values())
лічба[6] = int(all(вибір) and not any(р.get("чому_не_закріплена") == "her_item_later_item_in_same_place" for р in речі))
print("А:", " ".join("(%d) %d/5" % (н, ч) if н != 6 else "(6) %s" % ("так" if ч else "ні") for н, ч in лічба.items()),
      "| суд речі: %.0f–%.0f мс" % (min(мс) * 1000, max(мс) * 1000), "| закріплення:", sorted({str(р.get("чому_не_закріплена")) for р in речі}))
print("\n".join(рядки_6))
