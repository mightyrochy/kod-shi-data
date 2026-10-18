import pstats,sys,re
n=sys.argv[1]
s=pstats.Stats(f'logs/prof_{n}.bin'); s.sort_stats('cumtime')
import io
o=io.StringIO(); s.stream=o; s.print_stats(15)
t=o.getvalue()
print(f'--- cProfile {n}: ',re.search(r'function calls.*',t).group(0))
for l in t.splitlines()[5:]:
    if l.strip(): print(l[:170])
# importtime
tot=0; top=[]
for l in open(f'logs/imp_{n}.txt',errors='replace'):
    m=re.match(r'import time:\s+(\d+) \|\s+(\d+) \| (\s*)(\S+)',l)
    if m: 
        tot+=int(m.group(1)); top.append((int(m.group(2)),int(m.group(1)),m.group(4),len(m.group(3))))
print(f'importtime: modules={len(top)} sum self={tot/1e6:.2f}s')
top.sort(reverse=True)
print('top10 cumulative(ms) self(ms):',[(m[2],round(m[0]/1000),round(m[1]/1000)) for m in top[:10]])
