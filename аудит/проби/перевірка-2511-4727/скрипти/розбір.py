import json, sys, os, collections
for сц in sys.argv[1:]:
    д = f"/tmp/n2/live/{сц}"
    print("==", сц, open(д+"/час.txt").read().replace("\n"," "))
    if not os.path.exists(д + "/стан.json"): print("  нема стану"); continue
    рядки = [json.loads(л) for л in open(д + "/обміни.jsonl")] if os.path.exists(д + "/обміни.jsonl") else []
    for р in рядки:
        u = р.get("usage") or {}
        вх = sum((u.get(k) or 0) for k in ("input_tokens","cache_read_input_tokens","cache_creation_input_tokens"))
        if вх > 15000 or р['статус'] != 200:
            print(f"  {р['тип'][:28]:28} {р['статус']} вхід={вх} фото={р.get('фото')} не_дійшло={р.get('фото_не_дійшло')} вікно={[v.get('contextWindow') for v in (р.get('modelUsage') or {}).values()]} пом={str(р.get('помилка'))[:60]}")
    с = json.loads(open(д+"/стан.json").read())
    я = с.get("ядро") or {}
    звіт = я.get("звіт") or []
    лч = collections.Counter((з.get("заява") or ("збій:"+str((з.get("збій") or {}).get("вид")) if з.get("збій") else "?")) for з in звіт)
    print("  заяви:", dict(лч))
    for з in звіт:
        if з.get("заява") in ("bad_record",) : print("   bad_record", з.get("річ"), [x.get("поле") if isinstance(x,dict) else x for x in (з.get("збої") or [])][:4])
        if з.get("збій"): print("   збій", з.get("крок"), json.dumps(з["збій"], ensure_ascii=False)[:300])
        if з.get("заява")=="pool_rows_trimmed": print("   trim", з.get("крок"), з.get("скільки"), з.get("межі"))
    for i,к in enumerate(с.get("картки") or []):
        if not к: continue
        кя = к.get("ядро") or {}
        print(f"  картка[{i}] рука={кя.get('рука')} образ={кя.get('образ')} вирок={кя.get('вирок')} речей={len(кя.get('речі') or [])} без_опису={bool(к.get('без_опису'))} опис_без_фото={к.get('опис_без_фото')} невідоме={[з.get('код') for з in (кя.get('невідоме') or [])]}")
    print("  діагноз:", str(с.get("діагноз"))[:300])
