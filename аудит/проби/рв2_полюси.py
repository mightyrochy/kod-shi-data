# РВ-2 З-5: ід полюсів у ПАКЕТ_V1 (`pipeline.ПОЛЮСИ_ОБРАЗУ`) проти enum
# `протокол.ОБРАЗИ_V1.образи[].полюс`: чотири з шести не проходять схему.
# Запуск: python3 аудит/проби/рв2_полюси.py
import sys, os, json
ДЖ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "джерела")
sys.path.insert(0, ДЖ); os.chdir(ДЖ)
import bridge as B, протокол as P

вх = json.load(open("стенд_вх.json", encoding="utf-8"))
п = json.loads(json.loads(B.виклик("запити", json.dumps(dict(вх, варіантів=10), ensure_ascii=False)))["руки"]["1"])
# П-2: пакет несе ід полюсів англійським дротом (`poles[].id`), відповідь — `outfits[].pole`
іди = [x["id"] for x in п["poles"]]
дозволені = set(P.ЗНАЧЕННЯ_ВІДПОВІДІ_EN["полюс"].values())
print("ПАКЕТ_V1.poles[].id =", іди)
print("enum OUTFITS_V1.pole =", sorted(дозволені))
print("ід поза enum:", [i for i in іди if i not in дозволені])
сх = P.СХЕМИ["ОБРАЗИ_V1"]
for ід in іди:
    об = P.з_дроту_en(dict(version="1", outfits=[dict(id="o1", items=["#1·00"], pole=ід)]), сх)
    print("відповідь із полюсом «%s»: помилки схеми %s" % (ід, P.перевірити(сх, об)))
