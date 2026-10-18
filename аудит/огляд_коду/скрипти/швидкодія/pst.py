import pstats, sys
st = pstats.Stats(sys.argv[1])
def key(f, fn):
    return [k for k in st.stats if k[2]==fn and k[0].endswith(f)]
def callees(f, fn, n=10):
    for k in key(f, fn):
        v=st.stats[k]; print('== callees', k[0].split('/')[-1], k[2], 'ct=%.0f tt=%.0f nc=%d'%(v[3]*1000, v[2]*1000, v[1]))
        rows=[]
        for k2,v2 in st.stats.items():
            if k in v2[4]:
                c=v2[4][k]; rows.append((c[3]*1000, k2[0].split('/')[-1]+':'+str(k2[1])+':'+k2[2], c[1]))
        for r in sorted(rows, reverse=True)[:n]: print('   %8.0f  %s  ×%d'%r)
def callers(f, fn, n=10):
    for k in key(f, fn):
        v=st.stats[k]; print('== callers', k[0].split('/')[-1], k[2], 'ct=%.0f'%(v[3]*1000))
        rows=[(c[3]*1000, k2[0].split('/')[-1]+':'+str(k2[1])+':'+k2[2], c[1]) for k2,c in v[4].items()]
        for r in sorted(rows, reverse=True)[:n]: print('   %8.0f  %s  ×%d'%r)
for a in sys.argv[2:]:
    m, f, fn = a.split(':')
    (callers if m=='r' else callees)(f, fn)
