"""БРИФ-1: сміливість ідей рук 1–2 — раунд 1 (10 образів, що пішли в ремонт), фінальні 5, обраний; колір обраного.
Міра ЗАМІР-В (`claude/zamir-vyrva`, `вирва_сміливості.py`) без її прив'язки до 30 вирв і до цілей слотів: смілива ідея — ≥2
з 4 ознак речей (гучний C*≥40, контраст L*≥50, фактура одягу, ≥3 кольорові сектори по 60° серед речей з C*≥15).
Запуск: python3 проби/бриф1_сміливість.py <база> [<база> …], база — теки <нагода>_В з вердикти.txt(.gz). Друкує факт."""
import gzip, json, glob, math, re, sys, os
ТЕК = {"satin", "lace", "guipure", "velvet", "velour", "patent_leather", "atlas", "openwork", "tweed", "boucle"}
АКС = ("bag", "jewel", "scarf", "belt", "headband", "shoes", "pumps", "loafers", "boots", "sandals", "sneakers", "mules", "flats", "plimsolls", "clutch", "tote", "ring", "kerchief", "hat", "glasses", "tights", "bracelet", "earring", "necklace", "brooch", "bow", "hair")
дж = lambda с: json.JSONDecoder().raw_decode(с[с.index("{"):])[0] if isinstance(с, str) and "{" in с else None
def лчх(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]; c = [((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c]; f = lambda u: u ** (1 / 3) if u > .008856 else 7.787 * u + 16 / 116
    X, Y, Z = f((.4124 * c[0] + .3576 * c[1] + .1805 * c[2]) / .95047), f(.2126 * c[0] + .7152 * c[1] + .0722 * c[2]), f((.0193 * c[0] + .1192 * c[1] + .9505 * c[2]) / 1.08883)
    return 116 * Y - 16, 500 * (X - Y), 200 * (Y - Z)
def річ(d):
    fb = d.get("fabric") if isinstance(d.get("fabric"), list) else [d.get("fabric")]
    return (None if d.get("color") in ("golden", "silvery", "pearly") or re.search("jewel|ring|brooch", d.get("type") or "") else d.get("hex"), not any(a in (d.get("type") or "x") for a in АКС), bool(d.get("shine") or d.get("pattern") or set(fb) & ТЕК))
def бал(рр):
    л = [(лчх(h), о, ф) for h, о, ф in map(річ, рр) if h]; C = [math.hypot(x[0][1], x[0][2]) for x in л]; L = [x[0][0] for x in л]
    с = {int(math.degrees(math.atan2(x[0][2], x[0][1])) % 360 // 60) for x, c in zip(л, C) if c >= 15}
    return (max(C, default=0) >= 40) + (bool(L) and max(L) - min(L) >= 50) + any(x[1] and x[2] for x in л) + (len(с) >= 3), len(с)
for база in sys.argv[1:]:
    р1 = ф5 = об = н10 = н5 = 0; кол = []
    for f in sorted(glob.glob(os.path.join(база, "*_В", "вердикти.txt*"))):
        вв = json.load(gzip.open(f, "rt") if f.endswith(".gz") else open(f))["прогони"][0]["вердикти"]
        for в in (в for в in вв if str(в["рука"]) in "12"):
            кл = [(c["крок"], дж(c["запит"]["текст"]), дж(c.get("відповідь_сира"))) for c in в["етапи"]["виклики"]]
            Д = {i["n"]: i for к, п, _ in кл if к == "assembly" and п for i in п.get("pool", [])}
            рем = [(п, в_) for к, п, в_ in кл if к == "repair" and п and в_]; виб = [(п, в_) for к, п, в_ in кл if к == "choice" and п and в_]
            for п, _ in рем + виб: [Д.setdefault(i["n"], i) for o in п["verdict"] for i in o["your_outfit"]["items"]]
            б = lambda ns: бал([Д[n] for n in ns if n in Д])
            if рем:
                р1 += sum(б([i["n"] for i in o["your_outfit"]["items"]])[0] >= 2 for o in рем[-1][0]["verdict"]); н10 += len(рем[-1][0]["verdict"])
                ф5 += sum(б(o["items"])[0] >= 2 for o in рем[-1][1]["outfits"]); н5 += len(рем[-1][1]["outfits"])
            if виб:
                o = next((o for o in виб[-1][0]["verdict"] if o["your_outfit"]["id"] == виб[-1][1].get("chosen")), None)
                if o:
                    ns = [i["n"] for i in o["your_outfit"]["items"]]; бб, сек = б(ns); об += бб >= 2
                    кол.append((f.split("/")[-2][:-2], в["рука"], бб, сек, sorted({str(Д[n].get("color")) for n in ns if n in Д and річ(Д[n])[1]})))
    print("%s: сміливих у раунді 1 %d з %d · у фінальних 5 %d з %d · обраних %d з %d" % (база.rstrip("/").split("/")[-1], р1, н10, ф5, н5, об, len(кол)))
    for к in кол: print("   ", к[0], "рука", к[1], "бал", к[2], "секторів", к[3], "кольори одягу", к[4])
