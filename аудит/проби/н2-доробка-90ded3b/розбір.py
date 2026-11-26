import json, sys, os
for сц in sys.argv[1:]:
    д = f"/tmp/n2/live/типове/{сц}"
    if not os.path.exists(д + "/стан.json"): print(сц, "нема стану"); continue
    с = json.load(open(д + "/стан.json"))
    print("==", сц, "ключі:", list(с)[:12])
    рядки = [json.loads(л) for л in open(д + "/обміни.jsonl")] if os.path.exists(д + "/обміни.jsonl") else []
    for р in рядки:
        u = р.get("usage") or {}
        вх = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        мu = р.get("modelUsage") or {}
        вікно = {к: v.get("contextWindow") for к, v in мu.items()}
        print(f"  {р['тип'][:40]:40} {р['статус']} вхід={вх} стеля={р.get('стеля_сторінки')} фото={р.get('фото')} вікно={вікно} помилка={str(р.get('помилка'))[:60]}")
