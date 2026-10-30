"""Звіряє застосування свіжого обходу theoriginals з незмінністю записів бази."""
import gzip
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf8")
вибірки = []
for назва, sha in (("ДО", "560fa388e75fe10abe27145644d12d1be2266ab5"),
                   ("ПІСЛЯ", "a9d0c34898ac51ec8ea349b10b69ce9666c2210f")):
    дані = gzip.decompress(subprocess.check_output(["git", "show", sha + ":каталог_записи_v1.jsonl.gz"]))
    записи = [json.loads(р) for р in дані.splitlines()][1:]
    вибірка = {р["ід"]: р for р in записи if "theoriginals.com.ua" in р["адреса"]}
    вибірки.append(вибірка)
    print(назва, "theoriginals записів:", len(вибірка))
print("Повністю однакові записи за ід:", sum(вибірки[1].get(ід) == р for ід, р in вибірки[0].items()))
print("Нових ід:", len(вибірки[1].keys() - вибірки[0].keys()))
