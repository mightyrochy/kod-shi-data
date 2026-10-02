# -*- coding: utf-8 -*-
"""ЗАМІР-В (02.10): вирва 10→5→1 і сміливість ідей на ЗБЕРЕЖЕНИХ живих даних; нічого не викликає, запуск без аргументів.
Дані: аудит/перевірки/per_492/*_В/вердикти.txt.gz (6 нагод, руки 1–2 + руки 3–4 описово) і zhp_a/*/вікл (9 прогонів, руки 1–2) = 30 вирв.
СМІЛИВА ІДЕЯ = ≥2 з 4 ВИМІРЯНИХ ознак речей образу (hex→CIELAB D65; прикраси й золото/срібло/перли кольором не рахуються): гучний (C*≥40 — поріг коду
loud_from із промпту вибору), контраст (max L*−min L*≥50), фактура (ОДЯГ, не аксесуар: блиск/сатин/мереживо/оксамит/лак/атлас/принт),
багатобарвний (≥3 кольорові сектори по 60° серед речей з C*≥15). «Заявлено» (deliberate) і «поза палітрою» (in_arc) до балу не входять.
Вага знахідок: з промпту вибору, а коли її нема (після ВИБ-1) — з промпту ремонту за id знахідки; нема ніде → 0 і друкується «нема»."""
import gzip, json, glob, re, math, sys, collections as K
Р = "/home/user/kod-shi-data/аудит/перевірки/"
ДАНІ, ФІЛЬТР = (sys.argv[1] if len(sys.argv) > 1 else None), re.compile(sys.argv[2] if len(sys.argv) > 2 else ".")  # ЗАМІР-Ш: тека з <прогін>/вердикти.txt.gz замість ПЕР-492 + ЖП-а; фільтр — за іменем теки
ТЕК = {"satin", "lace", "guipure", "velvet", "velour", "patent_leather", "atlas", "openwork", "tweed", "boucle"}
АКС = ("bag", "jewel", "scarf", "belt", "headband", "shoes", "pumps", "loafers", "boots", "sandals", "sneakers", "mules", "flats", "plimsolls", "clutch", "tote", "ring", "kerchief", "hat", "glasses", "tights", "bracelet", "earring", "necklace", "brooch", "bow", "hair")
def дж(с):  # не-JSON (наприклад, виклик language_rewrite з «Text:» після схеми) — не вирва, пропускаємо
    try: return json.loads(с) if с and с.lstrip()[:1] in ("{", "[") else None
    except ValueError: return None
def лчх(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]; c = [((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c]; f = lambda u: u ** (1 / 3) if u > .008856 else 7.787 * u + 16 / 116
    X, Y, Z = f((.4124 * c[0] + .3576 * c[1] + .1805 * c[2]) / .95047), f(.2126 * c[0] + .7152 * c[1] + .0722 * c[2]), f((.0193 * c[0] + .1192 * c[1] + .9505 * c[2]) / 1.08883)
    return 116 * Y - 16, 500 * (X - Y), 200 * (Y - Z)
def ознаки(р):  # р: [(hex|None, одяг?, фактура?)] → (ознаки, бал, сектори)
    л = [(лчх(h), о, ф) for h, о, ф in р if h]; C = [math.hypot(x[0][1], x[0][2]) for x in л]; L = [x[0][0] for x in л]
    с = {int(math.degrees(math.atan2(x[0][2], x[0][1])) % 360 // 60) for x, c in zip(л, C) if c >= 15}
    о = dict(гучний=max(C, default=0) >= 40, контраст=bool(L) and max(L) - min(L) >= 50, фактура=any(x[1] and x[2] for x in л), багатобарвний=len(с) >= 3)
    return о, sum(о.values()), с
def річ(d):
    fb = d.get("fabric") if isinstance(d.get("fabric"), list) else [d.get("fabric")]
    return (None if d.get("color") in ("golden", "silvery", "pearly") or re.search("jewel|ring|brooch", d.get("type") or "") else d.get("hex"), not any(a in (d.get("type") or "x") for a in АКС), bool(d.get("shine") or d.get("pattern") or set(fb) & ТЕК))
зона = lambda h: math.hypot(*лчх(h)[1:]) < 15 or 60 <= math.degrees(math.atan2(лчх(h)[2], лчх(h)[1])) % 360 < 180  # нейтраль або жовто-зелено-блакитний сектор
цілі = lambda п: re.findall(r'(?:"hex": "|\\n\s+[а-яіїє\' ]+: )(#[0-9a-f]{6})', json.dumps([s for s in п["style_rules"] if "хема" in json.dumps(s, ensure_ascii=False) or "scheme_colours_by_kind" in json.dumps(s)], ensure_ascii=False))
def зібрати(сп):  # потік викликів → вирви: асемблі → ремонт (за набором речей) → вибір (за перетином із відповіддю ремонту)
    руки = []; наб = lambda o: frozenset(i["n"] for i in o["your_outfit"]["items"])
    for кр, п, в in сп:
        if not (п and в): continue
        if кр == "assembly": руки.append(dict(a=(п, в), r=None, c=None))
        elif кр == "repair":  # за набором речей; коли набір змінено кодом між складанням і ремонтом (ЗАМІР-Ш, ПІСЛЯ #539) — до останнього складання без ремонту
            зб = [x for x in руки[::-1] if наб(п["verdict"][0]) in {frozenset(o["items"]) for o in x["a"][1]["outfits"]}] or [x for x in руки[::-1] if x["r"] is None][:1]
            [x.update(r=(п, в)) for x in зб]
        elif кр == "choice": [x.update(c=(п, в)) for x in руки[::-1] if x["r"] and not x["c"] and наб(п["verdict"][0]) & {i for o in x["r"][1]["outfits"] for i in o["items"]}][:1]
    return руки
ВИР, ВИГ, СЛ, НЕВ, ЦН = [], [], re.compile(r"satin|lace|velvet|sequin|metallic|glossy|shine|patent|print|floral|embroider|silk|sheen"), [], {}  # вирви; вигадані образи рук 3–4; невідомі номери; цілі слотів схеми по нагодах
for f in sorted(x for x in glob.glob((ДАНІ or Р + "per_492") + "/*/вердикти.txt.gz") if ФІЛЬТР.search(x.split("/")[-2])):
    for в in json.load(gzip.open(f, "rt"))["прогони"][0]["вердикти"]:
        н = f.split("/")[-2][:None if ДАНІ else -2]; кл = [(c["крок"], дж(c["запит"]["текст"]), дж(c["відповідь_сира"])) for c in в["етапи"]["виклики"]]
        if str(в["рука"]) in "12": ВИР.append(("Ш" if ДАНІ else "В", н, int(в["рука"]), (зібрати(кл) or [dict(a=None, r=None, c=None)])[0])); НЕВ += [(н, в["рука"], x["підпис"]) for c in в["етапи"]["виклики"] for x in (c.get("розбір_блоків") or {}).get("невідомі_в_образах", [])]
        else: ВИГ.append((н, int(в["рука"]), [(None if i["slot"] in ("earrings", "bracelet", "necklace", "ring", "brooch", "jewelry") else i.get("color_hex"), i["slot"] in ("top", "bottom", "dress", "set", "outerwear"), bool(СЛ.search((i["name"] + i["details"]).lower()))) for i in кл[1][2]["items"]]))
for т in ([] if ДАНІ else sorted(glob.glob(Р + "zhp_a/*"))):
    сп = []
    for f in sorted(glob.glob(т + "/вікл/*ПАКЕТ*") + glob.glob(т + "/вікл/*ВЕРДИКТ*"), key=lambda p: int(re.search(r"seed3_(\d+)", p).group(1))):
        м = re.match(r"── ПРОМПТ[^\n]*\n(.*?)\n── ВІДПОВІДЬ[^\n]*\n(.*)", gzip.open(f, "rt").read(), re.S); п = дж(м.group(1)) if м else None
        if п: сп.append(("assembly" if "pool" in п else "choice" if re.match("ВИБІР|CHOICE", п["task"]["answer"]) else "repair", п, дж(м.group(2))))
    ВИР += [("Ж" + т[-1], т.split("/")[-1][:-2], k + 1, x) for k, x in enumerate(зібрати(сп))]
ФЕ, ЛІЧ, ПОЛ, ВАГ, РЯД, КОД, КОЛ = K.Counter(), K.Counter(), K.defaultdict(lambda: [0, 0, 0, 0]), [], [], [K.Counter(), K.Counter()], K.defaultdict(lambda: K.Counter())
ПРОП = []  # руки без ремонту чи вибору в потоці викликів (вибір на одному «образі» з 25 речей — ПІСЛЯ #539, ЗАМІР-Ш) — не рахуються, але названі
for с, н, р, x in ВИР:
    if not (x["a"] and x["r"] and x["c"]): ПРОП.append((н, р)); continue
    ап, ао = x["a"]; рп, ро = x["r"]; сп_, со = x["c"]; Д = {i["n"]: i for i in ап["pool"]}; Ц = ЦН[н] = цілі(ап)
    for o in рп["verdict"] + сп_["verdict"]: [Д.setdefault(i["n"], i) for i in o["your_outfit"]["items"]]
    пол = {re.sub(r"\D", "", o["id"]): o["pole"] for o in ао["outfits"]}; ід5 = {o["id"] for o in ро["outfits"]}
    бал = lambda ns: ознаки([річ(Д[n]) for n in ns if n in Д])[1]; ВР = {(o["your_outfit"]["id"], f["id"]): f["weight"] for o in рп["verdict"] for f in o["findings"] if "weight" in f}  # після ВИБ-1 вибір ваг не несе → вага з ремонту за id знахідки
    вг = lambda o, f: (f["weight"], "вибір") if "weight" in f else (ВР[o["your_outfit"]["id"], f["id"]], "ремонт") if (o["your_outfit"]["id"], f["id"]) in ВР else (0, "нема")
    вага = lambda o: sum(вг(o, f)[0] for f in o["findings"])
    фін = {}  # id ідеї → (бал після ремонту, блокери, обрано, вага, к-сть знахідок, набір речей)
    for o in сп_["verdict"]:
        ЛІЧ.update(("вага", вг(o, f)[1]) for f in o["findings"]); ns = [i["n"] for i in o["your_outfit"]["items"]]; ід = max(ро["outfits"], key=lambda q: len(set(q["items"]) & set(ns)) / len(set(q["items"]) | set(ns)))["id"]
        фін[ід] = (бал(ns), [b.get("code") for b in (o.get("structure") or {}).get("blockers", [])], o["your_outfit"]["id"] == со.get("chosen"), вага(o), len(o["findings"]), ns)
    ч = [Ф for Ф in фін.values() if Ф[2]][0]; б10 = 0; фк = K.Counter()
    for o in рп["verdict"]:
        ns = [i["n"] for i in o["your_outfit"]["items"]]; id_ = o["your_outfit"]["id"]; б = бал(ns); Ф = фін.get(id_); п_ = пол.get(re.sub(r"\D", "", id_))
        ЛІЧ["ідей", б >= 2] += 1; ЛІЧ["у5", б >= 2] += id_ in ід5; ПОЛ[п_][0] += 1; ПОЛ[п_][1] += id_ in ід5; ПОЛ[п_][2] += bool(Ф and Ф[2]); ПОЛ[п_][3] += б >= 2
        ЛІЧ["перехід", б >= 2, bool(Ф) and Ф[0] >= 2] += bool(Ф); ВАГ.append((id_ in ід5, вага(o)))
        for ст in {(s if isinstance(s, str) else next(iter(s))) for f in o["findings"] for s in f.get("statements", [])}: КОД[б >= 2][ст] += 1
        if б >= 2: б10 += 1; к = "відсіяна моделлю (10→5)" if not Ф else "блокер структури" if Ф[1] else "ремонт прибрав сміливість" if Ф[0] < 2 else "програла на виборі" if not Ф[2] else "обрана"; ФЕ[к] += 1; фк[к] += 1
    РЯД.append((с, н, р, б10, sum(Ф[0] >= 2 for Ф in фін.values()), ч[0], "|", *[f"{к.split()[0]} {v}" for к, v in фк.items()])); ЛІЧ["обране", ч[0] >= 2] += 1; ЛІЧ["ранг ваги", sorted(Ф[3] for Ф in фін.values()).index(ч[3])] += 1
    ЛІЧ["позиція", [o["your_outfit"]["id"] for o in сп_["verdict"]].index(со["chosen"])] += 1; ЛІЧ["облік зауважень у причині", bool(re.search(r"blocker|remark|finding|tension|fewest|lightest|mildest|lowest|checks?\b|blandness|excess|problems?|gate", со.get("why", ""), re.I))] += 1
    най = bool(re.search(r"fewest|milder|mildest|lightest|only light|lowest tension", со.get("why", ""), re.I)); ЛІЧ["твердить найменше"] += най; ЛІЧ["…але не найменше ні вагою ні числом"] += най and ч[3] > min(Ф[3] for Ф in фін.values()) and ч[4] > min(Ф[4] for Ф in фін.values())
    for o in ао["outfits"]:  # ВИРВА-968: оголошений хід складання → ремонт лишив у п'ятірці / змінив річ / відсіяв образ
        р_ = next((q for q in ро["outfits"] if re.sub(r"\D", "", q["id"]) == re.sub(r"\D", "", o["id"])), None)
        for дл in o.get("deliberate") or []: ЛІЧ["хід", o.get("pole"), "відсіяно" if not р_ else "лишено" if дл.get("item") in р_["items"] else "змінено"] += 1
    ЛІЧ["пул: ядро/решта", all(i.get("branch") == "core" for i in ап["pool"])] += 1; ЛІЧ["полюс break недоступний"] += "break" in ап.get("poles_unavailable", [])
    for гр, наб in (("пул", [[i["n"] for i in ап["pool"]]]), ("ідеї10", [[i["n"] for i in o["your_outfit"]["items"]] for o in рп["verdict"]]), ("фінал5", [Ф[5] for Ф in фін.values()]), ("обране", [ч[5]])):
        пр = [Д[n] for ns in наб for n in ns if n in Д and Д[n].get("hex") and річ(Д[n])[1] and Д[n].get("color") not in ("golden", "silvery")]; сек = lambda h: "н" if math.hypot(*лчх(h)[1:]) < 15 else int(math.degrees(math.atan2(лчх(h)[2], лчх(h)[1])) % 360 // 60)
        КОЛ[гр]["речей"] += len(пр); КОЛ[гр]["у зоні"] += sum(зона(d["hex"]) for d in пр); КОЛ[гр]["ΔE≤20 до цілі"] += sum(min((math.dist(лчх(d["hex"]), лчх(t)) for t in Ц), default=99) <= 20 for d in пр)
        КОЛ[гр]["секторів"] += len({сек(d["hex"]) for d in пр}); КОЛ[гр]["слів"] += len({d.get("color") for d in пр})
print("сер. нагода рука | сміливих у 10 | у 5 | бал обраного (0–4) | що сталося зі сміливими з 10"); [print(*r) for r in РЯД]
print("ідей смілива/решта", ЛІЧ["ідей", True], ЛІЧ["ідей", False], "| у5:", ЛІЧ["у5", True], ЛІЧ["у5", False], "| обране смілива:", ЛІЧ["обране", True], "з", len(ВИР), "| перехід (було,стало):", {(a, b): ЛІЧ["перехід", a, b] for a in (0, 1) for b in (0, 1)}, "\nзагибель сміливих R1:", dict(ФЕ))
print("полюс: ідей/у5/обрано/сміливих:", {p: tuple(v) for p, v in ПОЛ.items()}, "| вага знахідок у5/відсіяні: %.2f/%.2f" % tuple(sum(w for k, w in ВАГ if k == b) / sum(1 for k, _ in ВАГ if k == b) for b in (True, False)))
print("вибір: ранг ваги обраного (0=найлегший):", sorted((k[1], v) for k, v in ЛІЧ.items() if k[0] == "ранг ваги"), "| позиція у списку:", sorted((k[1], v) for k, v in ЛІЧ.items() if k[0] == "позиція"), "| облік зауважень у причині:", ЛІЧ["облік зауважень у причині", True], "з", len(ВИР), "| «найменше»:", ЛІЧ["твердить найменше"], "із них хибно:", ЛІЧ["…але не найменше ні вагою ні числом"])
print("знахідки (частка ідей) сміливі/решта:", {c: ("%.2f" % (КОД[True][c] / ЛІЧ["ідей", True]), "%.2f" % (КОД[False][c] / ЛІЧ["ідей", False])) for c in ("accessory_spends_chroma_budget", "loud_accent_on_low_contrast", "off_palette_colour_near_face", "accent_orphan")}, "| невідомі номери після ремонту:", НЕВ)
print("постачання: пул лише «ядро» у", ЛІЧ["пул: ядро/решта", True], "з", len(ВИР), "; полюс break недоступний у", ЛІЧ["полюс break недоступний"], "з", len(ВИР), "| колір (одяг):", {г: "речей %d · у зоні %.0f%% · ΔE≤20 до цілі %.0f%% · секторів/слів на вирву %.1f/%.1f" % (v["речей"], 100 * v["у зоні"] / v["речей"], 100 * v["ΔE≤20 до цілі"] / v["речей"], v["секторів"] / len(ВИР), v["слів"] / len(ВИР)) for г, v in КОЛ.items()})
ГР = [(h, ЦН[н]) for н, _, i in ВИГ for h, о, _ in i if h and о]  # одяг рук 3–4: колір і близькість до цілей слотів схеми тієї ж нагоди
print("руки 3–4 (вигадані): сміливих %d з %d" % (sum(ознаки(р)[1] >= 2 for _, _, р in ВИГ), len(ВИГ)), [(н, р, ознаки(i)[1]) for н, р, i in ВИГ], "| одяг у зоні %d, ΔE≤20 до цілі %d з %d" % (sum(зона(h) for h, _ in ГР), sum(min((math.dist(лчх(h), лчх(t)) for t in Ц_), default=99) <= 20 for h, Ц_ in ГР), len(ГР)))
print("вага знахідок у промпті вибору (звідки):", {k[1]: v for k, v in ЛІЧ.items() if k[0] == "вага"}, "| вага: нема в даних" if ЛІЧ["вага", "вибір"] + ЛІЧ["вага", "ремонт"] == 0 else "")
print("оголошені ходи складання → ремонт (полюс, доля): к-сть", sorted((k[1:], v) for k, v in ЛІЧ.items() if k[0] == "хід"))
if ПРОП: print("пропущено рук без повного ланцюга:", ПРОП)
