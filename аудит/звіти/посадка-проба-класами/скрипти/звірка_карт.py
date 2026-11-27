import json, glob
К="/home/user/kod-shi-data/"
сирі=json.load(open("/tmp/пс/склади_сирі.json")); карта=json.load(open("/tmp/пс/карта.json"))
def іди(с):
    return [карта["|".join([с["тека"],str(с["обмін"]),н])] for н in с["склад"]]
# картки N6
карти=[]
for ф in glob.glob(К+"аудит/звіти/ядро-образу-наново/приймання/хмара-sonnet/*/ядро/1/*/руки.jsonl"):
    for л in open(ф):
        for c in json.loads(л).get("картки") or []:
            if c.get("рука") in (1,2) and c.get("речі"):
                карти.append((ф.replace(К,"").rsplit("/",1)[0], c["рука"], c.get("вирок"), sorted(r["id"] for r in c["речі"])))
for ф in glob.glob(К+"аудит/проби/н2-доробка-90ded3b/с*/стан.json"):
    for c in json.load(open(ф))["картки"]:
        if c.get("рука") in (1,2) and c.get("речі"):
            карти.append((ф.replace(К,"").rsplit("/",1)[0], c["рука"], c.get("вирок") or (c.get("ядро") or {}).get("вирок"), sorted(r["id"] for r in c["речі"])))
карти=sorted(set((a,b,c,tuple(d)) for a,b,c,d in карти))
for т,рука,вирок,ід in карти:
    найкр=None
    for с in сирі:
        if с["тека"]!=т: continue
        ії=іди(с); збіг=sum(1 for x in ії if set(x)&set(ід))
        if not найкр or збіг>найкр[0]: найкр=(збіг,len(ід),с["обмін"],с["образ"],[x if len(x)!=1 else x[0] for x in ії])
    print(т.split("/")[-1], рука, вирок, "збіг", найкр[:4])
