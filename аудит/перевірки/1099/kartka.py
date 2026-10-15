import sys, os, json, copy, collections
sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
import оцінка_образу as О
d0 = json.load(open(sys.argv[2])); е = d0["прогони"][0]["вердикти"][0]["етапи"]
d = dict(d0["спільне"]["вхід_прогону"], речі=е["речі"]["речі"], пікселі={}, сценарій_оцінки=е.get("сценарій_екрана") or {})
d.pop("каталог", None); О._виміри = lambda *а, **к: copy.deepcopy(е["суд"]["речі"])
суд = О.суд(d); н = О.невідоме_для_моделі(суд)
print(len(н), json.dumps(sorted(str(x.get("code") or x.get("код") or x.get("input") or x) if isinstance(x,dict) else str(x) for x in н), ensure_ascii=False))
