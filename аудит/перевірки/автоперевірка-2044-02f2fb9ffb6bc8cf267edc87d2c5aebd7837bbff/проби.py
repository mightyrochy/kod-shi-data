"""Незалежні прицільні проби #2044: python проби.py <дерево> <режим>."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "джерела"))
import colorspace as CS
import колір_річ as KR
import композитор_слоти as KS
import verify as V

if sys.argv[2] == "сімя":
    import палітра_схеми as PS
    import фід_збагачення as FZ
    family = dict(роль="основа", дуга=(210, 340))
    r = dict(id="blue", слот="верх", назва="Синя сорочка", колір_назва="синій",
             lab=FZ.центр_вікна(V.ЛЕКСИКОН["синій"]),
             колір_не_вимір=dict(свідок="shop_word", слово="синій", вікно=V.ЛЕКСИКОН["синій"]))
    if hasattr(KR, "тип_кольору"):
        r.update(lab=None, колір_тип="інтервал")
    print("Роль за повним записом:", PS.сім_я_схеми(r, [family]))
    print("У каталозі:", PS._великі_у_каталозі(family, {r["id"]: r}))
    print("У тому самому пулі:", PS._великі_у_пулі(family, {"верх": [r]}, {r["id"]: r}))
    print("Площі/носії:", PS.площі_схеми([r], [family], за_ід={r["id"]: r}))
elif sys.argv[2] == "добір-металу":
    import palettes as PL
    cat = {r["id"]: r for r in json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))["каталог"]}
    ids = ["ж-07620@jecomestudio.com", "ж-07619@gepur.com"]
    gold = dict(слот="сережки", L_min=PL.ЗОЛОТО["L"][0], L_max=PL.ЗОЛОТО["L"][1],
                C_min=PL.ЗОЛОТО["C"][0], C_max=PL.ЗОЛОТО["C"][1],
                h_from=PL.ЗОЛОТО["дуга"][0], h_to=PL.ЗОЛОТО["дуга"][1], метал="золото")
    neutral = dict(слот="сережки", L_min=0, L_max=100, C_min=0, C_max=11, нейтраль=True)
    rows, note, _ = KS.кандидати_на_слот([cat[i] for i in ids], [gold, neutral], "сережки")
    print("Кандидати:", [r["id"] for r in rows])
    print("Нота:", note)
    if hasattr(KR, "тип_кольору"):
        print("Метал межами:", PL.метал_меж(cat[ids[0]], "сережки", cat[ids[0]].get("тип")))
elif sys.argv[2] == "метал-каталог":
    import palettes as PL
    import фід_добір as FD
    cat = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))["каталог"]
    hits = []
    for r in cat:
        if r.get("слот") not in PL.СЛОТИ_МЕТАЛУ:
            continue
        q = dict(слот=r["слот"], L_min=PL.ЗОЛОТО["L"][0], L_max=PL.ЗОЛОТО["L"][1],
                 C_min=PL.ЗОЛОТО["C"][0], C_max=PL.ЗОЛОТО["C"][1],
                 h_from=PL.ЗОЛОТО["дуга"][0], h_to=PL.ЗОЛОТО["дуга"][1], метал="золото")
        if hasattr(KR, "тип_кольору"):
            v = KR.вікно_речі(r)
            match = FD.описує_річ(r, q, вікно=v)
            point = KR.точка_кольору(r)
        else:
            v = (r.get("колір_не_вимір") or {}).get("вікно") or r.get("вікно")
            point = r.get("lab")
            match = bool(point) and FD.описує_річ(point, q, вікно=v)
        if match and (FD.частка_вікна(v, q) > 0 if v else FD.підходить(point, q)):
            hits.append(dict(id=r["id"], слово=bool(v)))
    print(json.dumps(dict(пройшли=len(hits), інтервали=sum(r["слово"] for r in hits), речі=hits), ensure_ascii=False))
elif sys.argv[2] == "сумісність":
    import outfit as O
    import фід_збагачення as FZ
    for r in [dict(lab=(50, 10, 20), колір_джерело="фото"),
              dict(lab=(50, 10, 20), колір_джерело="назва_вікно", вікно=V.ЛЕКСИКОН["синій"]),
              dict(hex="#ff0000", lab=CS.hx("#0000ff"), колір_тип="вимір"),
              dict(hex="#ff0000", lab=CS.hx("#0000ff"), колір_тип="невідомо")]:
        print("Сумісність:", KR.тип_кольору(r), KR.точка_кольору(r), KR.межі_кольору(r))
    r = dict(id="multi", слот="верх", hex="#ff0000", colors=[
        dict(lab=CS.hx("#ff0000"), coverage=.7, колір_тип="вимір"),
        dict(lab=CS.hx("#0000ff"), hex="#ffffff", coverage=.3, колір_тип="невідомо")])
    print("Сегменти:", [(KR.тип_кольору(e), KR.точка_кольору(e)) for e in O.елементи([r])])
elif sys.argv[2] == "каталог":
    import collections
    import outfit as O
    import композитор_річ as KP
    before, after = [{r["id"]: r for r in json.loads(Path(p).read_text(encoding="utf-8"))["каталог"]}
                     for p in sys.argv[3:5]]
    out = dict(до=len(before), після=len(after), втрачено_id=len(before.keys() - after.keys()),
               типи=dict(collections.Counter(map(KR.тип_кольору, after.values()))),
               невимір_з_lab=sum(bool(r.get("lab")) for r in after.values() if KR.тип_кольору(r) != "вимір"),
               сегментів=0, втрачено_точок=0, спотворено=0, максимум_de00=0)
    for r in after.values():
        if not r.get("colors") or r.get("слот") == "верхній_шар":
            continue
        es = O.елементи([KP.у_річ(r, r["слот"], {})])
        assert len(es) == len(r["colors"])
        for c, e in zip(r["colors"], es):
            a, b = KR.точка_кольору(c), KR.точка_кольору(e)
            if a:
                out["сегментів"] += 1
                out["втрачено_точок"] += b is None
                if b:
                    d = CS.de00(a, b)
                    out["спотворено"] += d > 1
                    out["максимум_de00"] = max(out["максимум_de00"], d)
            else:
                assert b is None and KR.межі_кольору(c) == KR.межі_кольору(e)
    print(json.dumps(out, ensure_ascii=False))
