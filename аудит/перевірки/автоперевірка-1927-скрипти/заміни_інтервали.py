"""оцінка_образу.зміни_кроками: скільки речей каталогу проходять вартового `if not <точка> ...: continue` і скільки з
відкинутих мають членство вікна «так» у палітрі стенда (тобто були б кандидатами-замінами).
Аргументи: дерево знімок.json"""
import json, os, sys, collections as К
дж = os.path.abspath(os.path.join(sys.argv[1], "джерела")); зн = os.path.abspath(sys.argv[2]); os.chdir(дж); sys.path.insert(0, дж)
import оцінка_образу as ОО, річ_з_фото as РФ, palettes as ПЛ, колір_річ as КР
кат = json.load(open(зн, encoding="utf-8"))["каталог"]
F, T, d = ОО.профіль(json.load(open("стенд_вх.json", encoding="utf-8")))
П = ПЛ.палітра_практична(F)
вартовий = (lambda r: КР.точка_кольору(r)) if hasattr(КР, "тип_кольору") else (lambda r: r.get("lab"))
л, члени = К.Counter(), {}
for r in кат:
    if КР.межі_кольору(r) is None: continue
    т = "вимір" if КР.не_вимір(r) is None else "не вимір"
    у, _ = РФ.членство_вікна(r, П, члени)
    пройшов = bool(вартовий(r))
    л[(т, "пройшов вартового" if пройшов else "відкинутий", "у палітрі" if у == "так" else "ні")] += 1
for к in sorted(л): print(" · ".join(к), л[к])
