import json, sys, random, collections as K; sys.path.insert(0, ".")
import bridge as B, стенд_знімок as СЗ, колір_річ as КР, колір_відношення as КВ
B.виклик("запити", json.dumps(dict(json.load(open("стенд_вх.json", encoding="utf-8")), сценарій=СЗ.СЦЕНАРІЇ["офіс·18°C"], випадок="офіс"), ensure_ascii=False))
кат = [r for r in B.каталог_останнього_пакета() if r.get("колір_тип") in ("вимір", "інтервал")]
U, k = КВ.ПОХИБКА_ТОНУ, КВ.ВАГА_ТОНУ_ХРОМИ
def вер(a, b, кл, u):
    КВ.ПОХИБКА_ТОНУ, КВ.ВАГА_ТОНУ_ХРОМИ = u, (k if u else 0.0)
    try: return КР.відношення(a, b, кл)
    finally: КВ.ПОХИБКА_ТОНУ, КВ.ВАГА_ТОНУ_ХРОМИ = U, k
р = random.Random(5); Л = K.Counter(); слово = K.Counter()
ід = lambda r: r.get("колір_назва") or r.get("колір_слово")
for _ in range(int(sys.argv[1])):
    a, b = р.choice(кат), р.choice(кат)
    if a is b: continue
    т = "×".join(sorted(x["колір_тип"] for x in (a, b)))
    for кл in ("same_hue", "near_hue", "adjacent"):
        до, піс = вер(a, b, кл, 0.0), вер(a, b, кл, U)
        if до != піс: Л[(т, кл, до, піс)] += 1
for x, v in sorted(Л.items()): print(x, v)
