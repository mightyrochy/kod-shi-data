"""Ч10: відношення й «та сама сім'я» (`колір_річ.відношення`, `та_сама_сім_я`) для речей, чиє вікно змінив
`вікно_з_кадром`, — проти всіх 477 речей із кадром іншого кольору й кожної 10-ї точки каталогу з виміром.

Запуск із джерела/ дерева: python3 <цей файл> <входи_кадру цього дерева .json.gz> <ids змінених .json> <вихід.json>."""
import gzip, json, sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
import колір_річ as КР

ТУТ = Path(__file__).resolve().parent
дані = json.load(gzip.open(sys.argv[1]))
змінені = set(json.load(open(sys.argv[2])))
речі = {r[0]: dict(id=r[0], колір_не_вимір=dict(вікно=r[1])) for r in дані["вікна_речей"]}
точки = [dict(id=і, lab=lab) for і, lab, *_ in json.load(gzip.open(ТУТ.parent / "річ_колір_межі_тон_20261105"
                                                                    / "каталог_точки.json.gz")) if lab][::10]
інші = list(речі.values()) + точки
вихід = []
for і in sorted(змінені):
    a = речі[і]
    for b in інші:
        вихід.append([і, b["id"], КР.відношення(a, b), КР.та_сама_сім_я(a, b)])
json.dump(вихід, open(sys.argv[3], "w"), ensure_ascii=False, default=str)
print("пар:", len(вихід))
