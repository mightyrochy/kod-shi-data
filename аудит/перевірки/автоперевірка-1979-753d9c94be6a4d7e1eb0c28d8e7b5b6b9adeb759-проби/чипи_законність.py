"""Зводить вади законності за кінцевим hex до того, що стоїть на чипах голови (persona, hex-трійка чипа)."""
import json, gzip, re, ast
from collections import Counter, defaultdict
вади = defaultdict(list)
for р in open("законність_head.txt", encoding="utf-8"):
    if р.startswith("ЛІК"): continue
    м = re.match(r"(\d+) \S+ \S+ \S+ \S+ (\S+) (\S+) (\S+) (\[.*?\]) \| hex: (.*) \| внутр: (.*)$", р.strip())
    і, кр, прийом, вид, hexи, суд, внутр = м.groups()
    вади[(int(і), tuple(ast.literal_eval(hexи)))].append((кр, прийом, вид, суд, внутр))
head = json.loads(gzip.decompress(open("head.json.gz", "rb").read()))
base = json.loads(gzip.decompress(open("base.json.gz", "rb").read()))
лік = Counter(); персони = defaultdict(set)
for п, б in zip(head, base):
    for г in п["гілки"]:
        к = (п["і"], tuple(г["зразки"]))
        if к in вади:
            було = any(list(к[1]) == [x["hex"] for x in q["кольори"]] for пк in б["пакет"] for q in (пк["поєднання"] or []))
            мітка = "нова трійка" if not було else "трійка бази"
            лік[(г["схема"], мітка)] += 1; персони[мітка].add(п["і"])
            print(п["і"], г["схема"], мітка, list(к[1]), вади[к][0][3])
print("ЧИПІВ з вадою за кінцевим hex:", {"|".join(к): v for к, v in лік.items()}, "персон:", {к: len(v) for к, v in персони.items()})
print("ЛІК усіх перших поєднань:", open("законність_head.txt", encoding="utf-8").read().split("ЛІК ")[-1].strip())
