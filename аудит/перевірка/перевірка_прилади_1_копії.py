import os,re,sys
корінь=sys.argv[1]; інстр=set(open(sys.argv[2]).read().split())
P=[(re.compile(r"(cos|sin)\(\s*(math\.|_math\.)?radians\(\s*h"),"LCh→Lab"),
   (re.compile(r"(cos|sin)\(r\)"),"LCh→Lab(r)"),
   (re.compile(r"hypot\(\s*(a|lab\[1\]|a1|a2|lab\[:, :, 1\][^,]*)\s*,\s*(b|lab\[2\]|b1|b2|lab\[:, :, 2\])"),"хрома Lab→LCh"),
   (re.compile(r"atan2\(\s*(b|lab\[2\]|b1|b2)\s*,\s*(a|lab\[1\]|a1|a2)\s*\)"),"тон Lab→LCh"),
   (re.compile(r"def\s+(de00|d_ok|de2000|delta_e|to_oklab|lab_з_lch|_lab|lch)\s*\("),"визначення перетворення")]
for dp,dn,fn in os.walk(os.path.join(корінь,"джерела")):
  dn[:]=[d for d in dn if d not in("проби","прилади","node_modules","open-source-stylist","__pycache__")]
  for f in sorted(fn):
    if not f.endswith(".py") or f.startswith("тест_") or f=="колір_простір_перетворення.py": continue
    p=os.path.join(dp,f); r=os.path.relpath(p,корінь)
    for i,l in enumerate(open(p,encoding="utf-8",errors="ignore"),1):
      if l.lstrip().startswith("#"): continue
      for rx,why in P:
        if rx.search(l):
          print(("В" if f"{r}:{i}" in інстр else "ПОЗА"),f"{r}:{i}",why,"|",l.strip()[:90]); break
