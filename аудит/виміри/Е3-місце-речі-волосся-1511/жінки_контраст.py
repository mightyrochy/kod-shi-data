# Контраст стенд-жінок і батареї: python3 жінки_контраст.py <тека джерел>
import sys, os, json, glob
d = os.path.abspath(sys.argv[1]); sys.path.insert(0, d); os.chdir(d)
import міст_вхід as МВ, outfit as O, батарея_входи as Б
база = json.load(open("стенд_вх.json", encoding="utf8"))
рядки = []
for ш in sorted(glob.glob("../аудит/проби/жінки/*.json")):
    ж = json.load(open(ш, encoding="utf8"))
    for дж in ("uncontrolled", "model_hex"):
        F = МВ.features(dict(база, шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source=дж))[0]
        к = O.контраст_особи(F, дж); рядки.append((os.path.basename(ш), дж, к.get("доступно"), к.get("рівень")))
for н, р in Б.БАТАРЕЯ:
    F = МВ.features(dict(база, **р, source="uncontrolled"))[0]
    к = O.контраст_особи(F, "uncontrolled"); рядки.append(("батарея: " + н, "uncontrolled", к.get("доступно"), к.get("рівень")))
for р in рядки: print(*р, sep=" | ")
print("доступно uncontrolled:", sum(1 for р in рядки if р[1] == "uncontrolled" and р[2]), "з", sum(1 for р in рядки if р[1] == "uncontrolled"))
