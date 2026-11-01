import sys, os, json
sys.path.insert(0, os.path.abspath("джерела"))
import каталог_розбір_прогін as P
куди, журнал = sys.argv[1], sys.argv[2]
стара = P.Годинник.записати
def записати(self, запис):
    with open(журнал, "a", encoding="utf-8") as ф:
        ф.write(json.dumps(запис, ensure_ascii=False) + "\n")
    return стара(self, запис)
P.Годинник.записати = записати
M = "mamaylm-gemma-3-12b-it-v2.0"
P.прогін(M, P.КР.МОВА, куди, 6, P.СІД, False, None, P.ПАРАЛЕЛЬНО, None, 0, True)
