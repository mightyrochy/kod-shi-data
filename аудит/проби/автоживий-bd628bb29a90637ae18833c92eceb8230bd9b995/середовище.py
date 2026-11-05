"""Перевірка готовності без запуску сервісів чи зміни чужих процесів."""
import datetime
import json
import pathlib
import shutil
import socket
import subprocess
import urllib.request

out = pathlib.Path(__file__).resolve().parent
result = {
    "час_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "sha_коду": "bd628bb29a90637ae18833c92eceb8230bd9b995",
    "запити": [],
}
for endpoint in ["/lmstudio-greeting", "/api/v1/models", "/v1/models"]:
    item = {"метод": "GET", "url": "http://127.0.0.1:1234" + endpoint}
    try:
        with urllib.request.urlopen(item["url"], timeout=10) as response:
            item.update({"http": response.status, "тіло": response.read().decode("utf-8")})
    except Exception as error:
        item.update({"помилка": repr(error), "http": None})
    result["запити"].append(item)
result["порти"] = {}
for port in [1234, 1235, 8000, 8188, 8765]:
    with socket.socket() as sock:
        sock.settimeout(1)
        result["порти"][str(port)] = sock.connect_ex(("127.0.0.1", port))
result["lms_у_PATH"] = shutil.which("lms")
result["власний_lms_існує"] = (pathlib.Path.home() / ".lmstudio/bin/lms.exe").exists()
result["інструменти"] = {
    path: pathlib.Path(path).exists()
    for path in [
        r"C:\Users\gemini\tools\node-v24.22.1-win-x64\node.exe",
        r"C:\Users\gemini\tools\python-3.12.1\python.exe",
        r"C:\Users\gemini\kod-shi-test-node\node_modules\playwright\package.json",
        r"C:\Users\gemini\pyodide\pyodide.js",
    ]
}
for name, command in [
    ("gpu", ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"]),
    ("netstat", ["netstat", "-ano"]),
]:
    proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    stdout = proc.stdout
    if name == "netstat":
        stdout = "\n".join(line for line in stdout.splitlines() if any(
            ":" + str(port) + " " in line for port in [1234, 1235, 8000, 8188, 8765]))
    result[name] = {"команда": command, "rc": proc.returncode, "stdout": stdout, "stderr": proc.stderr}
result["rc_готовності"] = 0 if all(item.get("http") == 200 for item in result["запити"]) else 2
(out / "середовище.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(result["rc_готовності"])
