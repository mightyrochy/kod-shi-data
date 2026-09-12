# Н-V16-038: чий ID стоїть у сліді прийомів палітри (живий виклик моста).
# До правки: K-COL-03 ×4 і K-COL-08/10 приходять із поля `джерело` чужою порадою.
# Після: власні K-PAL-02…13, а цитата джерела має напрям «цитата джерела».
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "джерела"))
import bridge
d = dict(шкіра=["#deb295"], волосся=["#f1dbaa", "#dabf89", "#b09362"], очі="#759087",
         нагода="щоденне", місце="кафе", година=13, темп_c=18,
         зріст=168, вік=32, обхвати=dict(плечі=98, груди=92, талія=72, стегна=100))
j = json.loads(bridge.виклик("палітри", json.dumps(d, ensure_ascii=False)))
сл = j["слід_правил"]
пор = [z for z in сл if "прийом «" in (z.get("ярлик") or "")]
print("ID зі сліду прийомів:", sorted({z["правило"] for z in пор}))
for z in пор:
    print("  %-12s напрям=%-18s %s" % (z["правило"], z.get("напрям"), z["ярлик"]))
усі = sorted({z["правило"] for z in сл if z.get("правило")})
print("K-PAL у всьому сліді:", [x for x in усі if x.startswith("K-PAL")])
print("K-COL у всьому сліді:", [x for x in усі if x.startswith("K-COL")])
