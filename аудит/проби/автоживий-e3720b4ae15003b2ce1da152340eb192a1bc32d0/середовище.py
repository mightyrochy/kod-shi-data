"""Зберігає передстартові факти без запуску чи зміни чужих служб."""
import datetime
import json
from pathlib import Path
import subprocess
import urllib.request

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
facts = {"час_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "cwd": str(ROOT), "команди": [], "http": []}

def command(args):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")
    facts["команди"].append({"команда": args, "rc": p.returncode,
                           "stdout": p.stdout, "stderr": p.stderr})
    return p

command(["git", "rev-parse", "HEAD", "origin/main"])
command(["git", "merge-base", "--is-ancestor", "6e452693807de1dc8d6e6a30dd5c861f1826d101", "origin/main"])
p = command(["netstat", "-ano", "-p", "tcp"])
facts["команди"][-1]["stdout"] = "\n".join(line for line in p.stdout.splitlines()
    if any(":" + str(port) + " " in line for port in (1234, 1235, 8000, 8188)))
command(["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv"])
command(["whoami"])
node = Path(r"C:\Users\gemini\tools\node-v24.22.1-win-x64\node.exe")
facts["файли"] = {str(p): p.exists() for p in [node,
    Path(r"C:\Users\gemini\kod-shi-test-node\node_modules\playwright\package.json"),
    Path(r"C:\Users\gemini\AppData\Local\ms-playwright\chromium-1248\chrome-win64\chrome.exe"),
    Path(r"C:\Users\gemini\tools\python-3.12.1\python.exe"),
    Path(r"C:\Users\gemini\pyodide\pyodide.js")]}
if node.exists():
    command([str(node), "--version"])
for path in ("/lmstudio-greeting", "/api/v1/models"):
    url = "http://127.0.0.1:1234" + path
    item = {"метод": "GET", "url": url}
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            item.update(status=response.status, body=response.read().decode("utf-8"))
    except Exception as error:
        item.update(status=None, error=repr(error), причина=repr(getattr(error, "reason", None)))
    facts["http"].append(item)
facts["живий_rc"] = None
facts["живий_стартував"] = False
(OUT / "середовище.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"http": facts["http"], "файли": facts["файли"],
                  "команди": [{"команда": c["команда"], "rc": c["rc"],
                                "stdout": c["stdout"]} for c in facts["команди"]]},
                 ensure_ascii=False, indent=2))
raise SystemExit(2 if any(i.get("status") != 200 for i in facts["http"]) else 0)
