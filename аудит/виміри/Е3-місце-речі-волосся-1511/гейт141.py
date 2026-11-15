# Гейт 141 на особі: python3 гейт141.py <тека джерел> <номер особи БАТАРЕЇ>
import sys, os, json
d = os.path.abspath(sys.argv[1]); sys.path.insert(0, d); os.chdir(d)
import gate_reach as GR, ід_правил as ІП, bridge as B
шість = {"R-CHEV-06", "R-CHEV-07", "R-CHEV-12", "R-CHEV-13", "R-PC-03", "R-TYP-04"}
р = dict(GR.БАТАРЕЯ[int(sys.argv[2])][1])
def ід(драп):
    x = dict(р); x.update(source="uncontrolled", зріст=168, вік=32, обхвати=dict(плечі=98, груди=92, талія=72, стегна=100),
                          самозвіт=dict(метал="золото", барви="приглушені"), випадок="прогін", гілка=0,
                          намір="conventional", сценарій=GR.НАГОДИ[0])
    F, T, зр, kw = B._збірка(x)
    п = B._пакет(F, T, зр, kw, драп=драп)
    return set(ІП.бази_в_тексті(json.dumps({k: v for k, v in п.items() if k != "обмеження"}, ensure_ascii=False, default=str))), F
з, F = ід(dict(метал="золото", білий="вершковий")); без, _ = ід(None)
import face_features as FF
к = FF._контраст(F, "uncontrolled")
print(GR.БАТАРЕЯ[int(sys.argv[2])][0], "| з картками:", sorted(шість & з), "| без:", sorted(шість & без), "| контраст:", к.get("доступно"), к.get("рівень"))
