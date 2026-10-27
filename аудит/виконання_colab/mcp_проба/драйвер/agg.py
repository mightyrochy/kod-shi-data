import json, glob, re, collections
rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob("raw/*.json"))]
ok = [r for r in rs if r["ok"]]; bad = [r for r in rs if not r["ok"]]
print("calls", len(rs), "ok", len(ok), "fail", len(bad))
for r in rs:
    m = re.search(r"ЧИСЛО_БЛОКУВАЛЬНИХ:\s*(\d+)", r.get("text", ""))
    v = re.search(r"ВЕРДИКТ:\s*(\w+)", r.get("text", ""))
    print(r["i"], r["pr"], "rep", r["rep"], "w", r["w"], r["clock"], r["secs"], "s", "ok" if r["ok"] else "FAIL " + r.get("err", "")[:150], v.group(1) if v else "-", m.group(1) if m else "-")
