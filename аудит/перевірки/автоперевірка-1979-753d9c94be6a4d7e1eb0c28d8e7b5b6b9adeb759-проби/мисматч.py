import json, gzip, sys
from collections import Counter
for ім in ("base", "head"):
    д = json.loads(gzip.decompress(open(ім + ".json.gz", "rb").read()))
    с = Counter()
    for п in д:
        гг = {г["схема"]: г["зразки"] for г in п["гілки"]}
        for г, пк in zip(п["гілки"], п["пакет"]):
            if пк["базова"] != г["схема"]:
                с[(пк["базова"], "однаково" if гг.get(пк["базова"]) == г["зразки"] else "різне")] += 1
    print(ім, dict(с))
