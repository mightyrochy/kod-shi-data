import gzip, json, sys, re, collections as C
for ш in sys.argv[1:]:
    print("==", ш.split("/")[-2])
    for i,l in enumerate(gzip.open(ш,"rt",encoding="utf-8")):
        t=l
        if "Build outfits for her case" not in t: continue
        m=re.search(r'\\?"colouring\\?"\s*:\s*\{.{0,700}', t)
        print(i, (m.group(0)[:600] if m else "colouring нема"))
        break
    n=0; ст=C.Counter()
    for l in gzip.open(ш,"rt",encoding="utf-8"):
        if "Build outfits for her case" in l:
            n+=1; ст.update(re.findall(r'\\?"status\\?"\s*:\s*\\?"(\w+)', l[:200000])[:6] and [tuple(re.findall(r'withheld|measured|model_hex|portrait', l))[:0]] or [])
    print("запитів складання", n)
