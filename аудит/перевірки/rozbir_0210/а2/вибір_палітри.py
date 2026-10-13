"""А2: що код прочитав у кольорах жінки і що обрала стилістка (схема, основа, гама, причини) — по кожному прогону."""
import json, gzip, glob, os, sys
Т = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for d in sorted(glob.glob(Т + "/ж*_*/")):
    if not os.path.getsize(d + "вердикти.txt.gz"): continue   # ж8_робота_плиткою: стенд кінчає сценарій плитки до карток, вердиктів нема
    D = json.load(gzip.open(d + "вердикти.txt.gz", "rt")); сп = D["спільне"]
    e = D["прогони"][0]["спільне"]["етапи"]["прогін"]["вибір_палітри"]
    try: q = json.loads(e["виклик"]["запит"]["текст"]); a = json.loads(e["виклик"]["відповідь_сира"])
    except Exception: q, a = {}, {}
    p = q.get("person") or {}; c = p.get("contrast") or {}; u = p.get("undertone") or {}
    f = lambda k: "%s L%s C%s" % ((p.get(k) or {}).get("family"), (p.get(k) or {}).get("lightness"), (p.get(k) or {}).get("chroma"))
    b = {x["id"]: x for x in q.get("bases") or []}; ба = b.get(a.get("base")) or {}
    сх = [s["scheme"] for s in q.get("schemes") or []]
    print("%-28s контраст %s/%.0f · підтон %s(%s) · очі %s · вол %s · шкіра %s · метал %s" % (os.path.basename(d.rstrip("/")), c.get("level"), c.get("light_dark_gap") or 0, u.get("class"), u.get("from"), f("eyes"), f("hair"), f("skin"), p.get("metal")))
    print("   основи[%d]: %s" % (len(b), ", ".join("%s/%s/L%s/%s" % (x["colour"], x["temperature"][:4], x["lightness"], x["saturation"][:3]) for x in list(b.values())[:8])))
    print("   L* основ: %s · схеми: %s" % (sorted({x["lightness"] for x in b.values()}), ">".join(сх)))
    print("   ОБРАЛА: схема=%s %s · основа=%s(ранг %s, %s L%s %s) %s · гама=%s · обрано пальцем: схема=%s основа=%s · пал_база=%s" % (a.get("scheme"), a.get("scheme_reasons"), a.get("base"), ба.get("rank"), ба.get("colour"), ба.get("lightness"), ба.get("saturation"), a.get("base_reasons"), a.get("saturation"), сп.get("пал_схема_обрана"), сп.get("пал_база_обрана"), сп.get("пал_база")))
    if e.get("знахідки") or e.get("відхилено"): print("   СУД ВИБОРУ:", json.dumps(e.get("знахідки"), ensure_ascii=False)[:300], e.get("відхилено"))
