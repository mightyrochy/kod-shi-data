import json,re,sys
d=json.load(open(sys.argv[1])); з=0;н=0
for x in d:
    if x["k"][2]=="синій" or x["k"][4] not in ("нейтрали+акцент","контраст-мисматч"): continue
    m={a:b for a,b in re.findall(r"^\s+(верх|низ): (#[0-9a-f]{6})",x["t"],re.M)}
    if len(m)==2:
        н+=1; з+= m["верх"]==m["низ"]
print("верх==низ",з,"/",н)
