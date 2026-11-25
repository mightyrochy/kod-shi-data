import json, sys
for сц in sys.argv[1:]:
    с = json.load(open(f"/tmp/n2/live/типове/{сц}/стан.json"))
    к = next((к for к in с["картки"] if к.get("рука") == 1), None)
    я = (к or {}).get("ядро") or {}
    print("==", сц, "готово", с["готово"], "успіх", с["успіх"], "карток_dom", с.get("карток_dom"))
    print("  рука1: образ", я.get("образ"), "вирок", я.get("вирок"), "збій", я.get("збій"), "речей", len(я.get("речі", [])),
          "опис_без_фото", (к or {}).get("опис_без_фото"), "невідоме", [н["код"] for н in я.get("невідоме", [])][:8])
    збої = [з for з in с["ядро"]["звіт"] if "збій" in з or з.get("заява") in ("request_limit_exceeded",)]
    print("  збої ядра:", json.dumps(збої, ensure_ascii=False)[:600])
    print("  заяви:", sorted({з.get("заява") for з in с["ядро"]["звіт"] if з.get("заява")}))
