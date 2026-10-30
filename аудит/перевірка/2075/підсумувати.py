"""Звести лише факти власних завершених запусків; порожній вхід не є прийманням."""
import collections
import json
from pathlib import Path

тут = Path(__file__).resolve().parent


def прочитати(ім):
    """JSON із PowerShell допускає BOM; машинні журнали його не потребують."""
    return json.loads((тут / ім).read_text("utf-8-sig"))


а, б = [прочитати(ім + "-власні.json") for ім in ("ДО", "ПІСЛЯ")]
сцени = [прочитати(ім + "-стенд.json") for ім in ("ДО", "ПІСЛЯ")]
assert сцени[0]["ід"] == сцени[1]["ід"]
відмінності = {}
for ім in сцени[0]["знімок"]:
    до, після = [с["знімок"][ім] for с in сцени]
    різне = []
    def обхід(x, y, шлях=""):
        """Списки обходити за індексом, щоб не дублювати всі чеклісти за однієї зміни."""
        if isinstance(x, dict) and isinstance(y, dict):
            for к in sorted(x.keys() | y.keys()):
                обхід(x.get(к), y.get(к), шлях + "/" + к)
        elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
            for i, (а_, б_) in enumerate(zip(x, y)):
                обхід(а_, б_, шлях + "/" + str(i))
        elif x != y:
            різне.append(dict(шлях=шлях, до=x, після=y))
    обхід(до["суд"], після["суд"])
    правила = [dict(с["суд"]["знахідки_правила"]) for с in (до, після)]
    зміни_правил = {к: [правила[0].get(к, 0), правила[1].get(к, 0)]
                    for к in правила[0].keys() | правила[1].keys()
                    if правила[0].get(к, 0) != правила[1].get(к, 0)}
    assert not any(к.startswith(("K-PAL", "K-WEA")) for к in зміни_правил)
    відмінності[ім] = dict(пул=[до["запити"]["пул"], після["запити"]["пул"]],
                           зміни_правил=зміни_правил, суд=різне)
(тут / "стенд-відмінності.json").write_text(json.dumps(відмінності, ensure_ascii=False, indent=2), "utf-8")
без_входу = [sum(sum(с["суд"]["без_входу_кольору"].values()) for с in з["знімок"].values()) for з in сцени]
підсумок = dict(каталог=[а["каталог"], б["каталог"]],
    сцен=len(відмінності), однакові_id=True, без_входу=без_входу,
    зміни_правил={к: с["зміни_правил"] for к, с in відмінності.items() if с["зміни_правил"]},
    мірило=прочитати("мірило-каталогу.json"))
for ім in ("батарея.json", "доповнення.json", "фінальна-батарея.json"):
    if (тут / ім).exists():
        р = прочитати(ім)
        підсумок[ім] = dict(команд=len(р), коди=dict(collections.Counter(з["код"] for з in р)),
                           ненульові=[з["назва"] for з in р if з["код"]])
(тут / "підсумок.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), "utf-8")
print(json.dumps({к: в for к, в in підсумок.items() if к != "мірило"}, ensure_ascii=False, indent=2))
