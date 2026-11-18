import sys, os, shutil, subprocess, yaml
дерево, yml = sys.argv[1], sys.argv[2]
d = yaml.safe_load(open(os.path.join(дерево, yml), encoding="utf-8"))
for job, j in d["jobs"].items():
    for s in j.get("steps", []):
        w = s.get("with") or {}
        if "sparse-checkout" in w:
            шляхи = w["sparse-checkout"].split()
            т = f"/tmp/г/теки/{os.path.basename(дерево)}-{job}"
            shutil.rmtree(т, ignore_errors=True)
            for ш in шляхи:
                os.makedirs(os.path.dirname(os.path.join(т, ш)), exist_ok=True)
                shutil.copy(os.path.join(дерево, ш), os.path.join(т, ш))
            р = subprocess.run(["python3","-I","джерела/прилади/документ_без_коду.py","--самоперевірка"], cwd=т, capture_output=True, text=True)
            print(job, шляхи, "код", р.returncode, (р.stdout+р.stderr).strip().splitlines()[-1:])
