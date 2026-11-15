# ДО/ПІСЛЯ: ID шести правил приобличчевої індукції в пакеті моделі (метод гейта 141 розділи_гейтів)
import sys, json; sys.path.insert(0, ".")
import bridge as B, gate_reach as GR, ід_правил as ІП
ШІСТЬ = ("R-CHEV-06", "R-CHEV-07", "R-CHEV-12", "R-CHEV-13", "R-PC-03", "R-TYP-04")
def шляхи(о, ш=""):
    if isinstance(о, dict):
        for к, v in о.items(): yield from шляхи(v, ш + "/" + str(к))
    elif isinstance(о, list):
        for i, v in enumerate(о): yield from шляхи(v, ш + "[%d]" % i)
    elif isinstance(о, str):
        for і in ШІСТЬ:
            if і in о: yield і, ш
for драп in (None, dict(метал="золото", білий="вершковий")):
    d = dict(GR.БАТАРЕЯ[0][1]); d.update(source="uncontrolled", зріст=168, вік=32,
        обхвати=dict(плечі=98, груди=92, талія=72, стегна=100), самозвіт=dict(метал="золото", барви="приглушені"),
        випадок="прогін", гілка=0, намір="conventional", сценарій=GR.НАГОДИ[0])
    F, T, зр, kw = B._збірка(d); п = B._пакет(F, T, зр, kw, драп=драп)
    тіло = {k: v for k, v in п.items() if k != "обмеження"}
    ід = ІП.бази_в_тексті(json.dumps(тіло, ensure_ascii=False, default=str))
    є = [і for і in ШІСТЬ if і in ід]
    print("драп", bool(драп), "ID %d із 6:" % len(є), є)
    ш = sorted({(і, p.split("[")[0][:90]) for і, p in шляхи(тіло)})
    print("  де:", ш[:8])
