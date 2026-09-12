# РВ-2 З-5: ід полюсів у ПАКЕТ_V1 (`pipeline.ПОЛЮСИ_ОБРАЗУ`) проти enum
# `протокол.ОБРАЗИ_V1.образи[].полюс`: чотири з шести не проходять схему.
# Запуск: python3 аудит/проби/рв2_полюси.py
import sys, os, json
ДЖ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "джерела")
sys.path.insert(0, ДЖ); os.chdir(ДЖ)
import bridge as B, протокол as P

вх = json.load(open("стенд_вх.json", encoding="utf-8"))
п = json.loads(json.loads(B.виклик("запити", json.dumps(dict(вх, варіантів=10), ensure_ascii=False)))["руки"]["1"])
іди = [x["ід"] for x in п["полюси"]]
print("ПАКЕТ_V1.полюси[].ід =", іди)
print("enum ОБРАЗИ_V1.полюс   =", P.ПОЛЮСИ)
print("ід поза enum:", [i for i in іди if i not in P.ПОЛЮСИ])
об = dict(версія="1", образи=[dict(ід="о1", речі=["#1·00"], полюс=іди[1])])
print("відповідь із полюсом «%s»: помилки схеми %s" % (іди[1], P.перевірити(P.СХЕМИ["ОБРАЗИ_V1"], об)))
