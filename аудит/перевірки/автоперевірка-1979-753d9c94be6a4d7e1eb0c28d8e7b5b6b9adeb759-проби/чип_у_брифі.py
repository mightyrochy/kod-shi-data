import json, gzip
from collections import Counter
for ім in ("base", "head"):
    д = json.loads(gzip.decompress(open(ім + ".json.gz", "rb").read()))
    if ім == "head": print("ключі брифу:", list(д[0]["пакет"][0]["бриф"].keys()))
    с = Counter()
    for п in д:
        for г, пк in zip(п["гілки"], п["пакет"]):
            if not пк["бриф"]: continue
            тексти = [" ".join(т["кольори"]) for т in пк["бриф"].get("поєднання", пк["бриф"].get("трійки", []))]
            є = any(all(h in т for h in г["зразки"]) for т in тексти)
            с[(г["схема"], "у брифі" if є else "нема в брифі")] += 1
    print(ім, sorted(с.items()))
