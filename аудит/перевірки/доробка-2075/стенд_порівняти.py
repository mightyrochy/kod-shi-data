"""Порівняти суд на тих самих id й окремо показати зміни добору."""
import collections
import json
from pathlib import Path


def різниця(до, після, шлях=""):
    """Повернути змінені листки без друку всіх незмінених чеклістів."""
    if до == після:
        return []
    if isinstance(до, dict) and isinstance(після, dict) and до.keys() == після.keys():
        return [р for к in до for р in різниця(до[к], після[к], шлях + "/" + к)]
    if isinstance(до, list) and isinstance(після, list) and len(до) == len(після):
        return [р for і, (а, б) in enumerate(zip(до, після)) for р in різниця(а, б, шлях + "/" + str(і))]
    return [dict(шлях=шлях, до=до, після=після)]


def головна():
    """Зберегти повні відмінності й перевірити незмінність K-PAL/K-WEA та id."""
    тека = Path(__file__).resolve().parent
    до, після = [json.loads((тека / (р + "-стенд.json")).read_text(encoding="utf-8")) for р in ("ДО", "ПІСЛЯ")]
    assert до["ід"] == після["ід"]
    вих, кольору = {}, collections.Counter()
    for ім, а in до["знімок"].items():
        б = після["знімок"][ім]
        суд_до, суд_після = а["суд"], б["суд"]
        лд, лп = [dict(с["знахідки_правила"]) for с in (суд_до, суд_після)]
        зміни = {к: [лд.get(к, 0), лп.get(к, 0)] for к in лд.keys() | лп.keys() if лд.get(к) != лп.get(к)}
        assert not any(к.startswith(("K-PAL", "K-WEA")) for к in зміни), зміни
        вих[ім] = dict(пул=[а["запити"]["пул"], б["запити"]["пул"]], зміни_правил=зміни,
                      суд=різниця(суд_до, суд_після))
        for р, с in (("ДО", суд_до), ("ПІСЛЯ", суд_після)):
            кольору[р] += sum(с["без_входу_кольору"].values())
        print(ім, "правила:", зміни, "змінених листків суду:", len(вих[ім]["суд"]))
    (тека / "стенд-відмінності.json").write_text(json.dumps(dict(сцени=вих, без_входу=кольору),
        ensure_ascii=False, indent=2), encoding="utf-8")
    print("Окреме охоплення без входу кольору:", dict(кольору))


if __name__ == "__main__":
    головна()
