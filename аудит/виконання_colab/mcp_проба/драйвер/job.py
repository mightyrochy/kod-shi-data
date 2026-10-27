import json, sys, os, time, glob
D = r"C:\tmp\colab-mcp\jobs"
def run(tool, args=None, wait=900):
    n = max([int(os.path.basename(f)[:3]) for f in glob.glob(D + r"\*.json") if not f.endswith(".out.json")] + [1]) + 1
    jf = f"{D}\{n:03d}.json"
    json.dump({"tool": tool, "args": args or {}}, open(jf + ".tmp", "w", encoding="utf-8"))
    os.replace(jf + ".tmp", jf)
    out = jf[:-5] + ".out.json"
    t0 = time.time()
    while not os.path.exists(out):
        if time.time() - t0 > wait: return {"timeout": True, "job": n}
        time.sleep(1)
    time.sleep(0.3)
    r = json.load(open(out, encoding="utf-8")); r["job"] = n; return r
if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}), ensure_ascii=False, indent=1)[:6000])
