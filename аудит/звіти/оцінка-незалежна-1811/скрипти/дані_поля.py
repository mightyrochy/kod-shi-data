import pickle, collections, sys
к = pickle.load(open("/tmp/скрипти_звірки/дані/каталог.pkl","rb"))
кл = collections.Counter(k for r in к for k in r)
print(len(к)); print(sorted(кл.items(), key=lambda x:-x[1]))
r = к[0]
for k in ("слот","тип","тип_джерело","колір_тип","колір_не_вимір","lab","hex","крій","крій_джерело","довжина_рівень","посадка","обхвати_виробу","колір_джерело","запис_речі"):
    print(k, repr(r.get(k))[:300])
