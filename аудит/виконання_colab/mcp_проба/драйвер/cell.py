import sys, json
from job import run
def cell(code, cid="lIYdn1woOS1n", wait=900):
    r = run("update_cell", {"cellId": cid, "content": code})
    if r.get("is_error"): return r
    return run("run_code_cell", {"cellId": cid}, wait)
if __name__ == "__main__":
    code = open(sys.argv[1], encoding="utf-8").read()
    r = cell(code)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:8000])
