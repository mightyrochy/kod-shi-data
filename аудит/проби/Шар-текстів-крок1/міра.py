import json, re, sys, glob, os
ІД = re.compile(r"[\w-]+@[\w.-]+\.(?:ua|com|net|store|shop)")
for д in sys.argv[1:]:
    ч = json.load(open(os.path.join(д, "чат.json")))
    ші = [з for з in ч if з.get("хто") == "ші"]
    print("##", os.path.basename(д))
    for з in ші:
        print("  ТЕКСТ:", з.get("текст"))
        for н in з.get("невідоме") or []: print("  ЗА КНОПКОЮ:", н)
        for м in з.get("мова_шару") or []:
            if м.get("напрям") == "out":
                print("  out: причина=%s повтор=%s відкинуто=%s не_сказано=%s" % (
                    м.get("причина"), (м.get("повтор") or {}).get("причина"),
                    [(в.get("чому"), в.get("зняте")) for в in м.get("відкинуто") or []], м.get("не_сказано")))
    for ф in sorted(glob.glob(os.path.join(д, "обміни", "*_запит.json"))):
        т = open(ф).read()
        print("  %s: ід крамниці %d" % (os.path.basename(ф), len(ІД.findall(т))))
