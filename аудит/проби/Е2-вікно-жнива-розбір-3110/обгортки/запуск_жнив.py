import sys, os, json, urllib.request
sys.path.insert(0, os.getcwd())
import feed as F
_о = F.читати_yml
F.читати_yml = lambda ш, показ=True: _о(getattr(ш, "name", ш), показ)
ЖУРНАЛ = os.environ["USAGE_LOG"]
_u = urllib.request.urlopen
class Тee:
    def __init__(s, r, url, код): s.r, s.url, s.код = r, url, код
    def read(s, *a):
        d = s.r.read(*a)
        try:
            if "chat/completions" in s.url:
                u = (json.loads(d).get("usage") or {})
                open(ЖУРНАЛ, "a", encoding="utf-8").write(json.dumps({"prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens")}) + "\n")
        except Exception: pass
        return d
    def __enter__(s): s.r.__enter__(); return s
    def __exit__(s, *a): return s.r.__exit__(*a)
    def __getattr__(s, n): return getattr(s.r, n)
def urlopen(з, *a, **k):
    url = з if isinstance(з, str) else з.full_url
    try:
        return Тee(_u(з, *a, **k), url, 0)
    except urllib.error.HTTPError as e:
        if "chat/completions" in url:
            open(ЖУРНАЛ, "a", encoding="utf-8").write(json.dumps({"http_error": e.code, "тіло": e.read()[:300].decode("utf-8", "replace")}) + "\n")
        raise
urllib.request.urlopen = urlopen
import жнива_прогін as P
sys.argv = ["жнива_v2.py"] + sys.argv[1:]
P.main()
