import json, time, subprocess, os, sys
from cell import cell
N = 0; t0 = time.time(); lastcu = 0
HB = open("heartbeat.log", "a", encoding="utf-8")
while time.time() - t0 < 7200 + 900:
    ts = time.strftime("%H:%M:%S")
    try:
        r = cell("import json\nprint(json.dumps(LOG[%d:], ensure_ascii=False))" % N, wait=300)
        if r.get("timeout") or r.get("is_error") or r.get("exception"):
            HB.write(f"{ts} HB FAIL {json.dumps(r, ensure_ascii=False)[:400]}\n"); HB.flush()
        else:
            txt = "".join("".join(o.get("text", [])) for o in r["data"]["outputs"])
            new = json.loads(txt)
            HB.write(f"{ts} HB ok new={len(new)} secs={r['secs']}\n"); HB.flush()
            for rec in new:
                json.dump(rec, open(f"raw/{rec['i']:03d}_{rec['pr']}_r{rec['rep']}.json", "w", encoding="utf-8"), ensure_ascii=False)
            N += len(new)
    except Exception as e:
        HB.write(f"{ts} HB EXC {repr(e)[:300]}\n"); HB.flush()
    if time.time() - lastcu > 900:
        lastcu = time.time()
        out = subprocess.run(["powershell.exe", "-NoProfile", "-Command", "wsl -d Ubuntu -- bash /mnt/c/tmp/colab-mcp/usage.sh"], capture_output=True, text=True).stdout.replace("\n", " ")
        open("cu.log", "a").write(f"{ts} {out}\n")
    time.sleep(240)
