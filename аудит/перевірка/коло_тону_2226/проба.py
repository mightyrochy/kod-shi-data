import json, sys, random, collections as K; sys.path.insert(0, ".")
import bridge as B, стенд_знімок as СЗ, colorspace as cs, колір_річ as КР, колір_відношення as КВ
B.виклик("запити", json.dumps(dict(json.load(open("стенд_вх.json", encoding="utf-8")), сценарій=СЗ.СЦЕНАРІЇ["офіс·18°C"], випадок="офіс"), ensure_ascii=False))
кат = B.каталог_останнього_пакета()
U, k = КВ.ПОХИБКА_ТОНУ, КВ.ВАГА_ТОНУ_ХРОМИ
# 1) тип запису проти того, що читає _похибка
Т = K.Counter()
for r in кат:
    з = КР.запис_кольору(r)
    if з is None: Т[(r.get("колір_тип"), "нема запису")] += 1; continue
    Т[(r.get("колір_тип"), "точка" if з["дуга"] is not None and з["дуга"][0]==з["дуга"][1] else "не точка" if з["дуга"] is not None else "дуга None")] += 1
print("тип × що бачить _похибка:"); [print("  ", k_, v) for k_, v in sorted(Т.items(), key=str)]
def вер(a, b, кл, u):
    КВ.ПОХИБКА_ТОНУ, КВ.ВАГА_ТОНУ_ХРОМИ = u, (k if u else 0.0)
    try: return КР.відношення(a, b, кл)
    finally: КВ.ПОХИБКА_ТОНУ, КВ.ВАГА_ТОНУ_ХРОМИ = U, k
виміри = [r for r in кат if r.get("колір_тип") == "вимір" and r.get("lab")]
Cx = lambda r: cs.lch(tuple(r["lab"]))[1]
кол = [r for r in виміри if Cx(r) >= 12]
print("вимірів", len(виміри), "з C*>=12", len(кол))
р = random.Random(int(sys.argv[1])); N = int(sys.argv[2])
Л = K.Counter(); зм = []
for _ in range(N):
    a, b = р.choice(кол), р.choice(кол)
    if a is b: continue
    до, піс = вер(a, b, "same_hue", 0.0), вер(a, b, "same_hue", U)
    Л[(до, піс)] += 1
    hа, hб = cs.lch(tuple(a["lab"]))[2], cs.lch(tuple(b["lab"]))[2]
    дк = КР.кут_на_колі(hа, hб)
    if до != піс: зм.append(dict(a=[a["id"], a["назва"], cs.hex_з_lab(a["lab"])], b=[b["id"], b["назва"], cs.hex_з_lab(b["lab"])], дк=round(дк,1), до=до, піс=піс))
    else: зм.append(dict(a=[a["id"], a["назва"], cs.hex_з_lab(a["lab"])], b=[b["id"], b["назва"], cs.hex_з_lab(b["lab"])], дк=round(дк,1), до=до, піс=піс, незм=1))
print(dict(Л))
json.dump(зм, open(sys.argv[3], "w"), ensure_ascii=False)
