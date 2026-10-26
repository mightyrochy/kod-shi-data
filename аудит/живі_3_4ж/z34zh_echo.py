import json,glob,sys
for d in sorted(glob.glob('C:/tmp/z34zh_out/П7_1825/*/')):
    fs=glob.glob(d+'VIDPOVIDI/*вибір_палітри*')
    if not fs: print(d,'нема вибору'); continue
    t=open(fs[0],encoding='utf-8').read()
    p=json.loads(t.split('── ПРОМПТ')[1].split('\n',1)[1].split('── ВІДПОВІДЬ')[0].strip())
    e=p['person']['eyes']
    ec=[(b['id'],b['colour'],b['family']) for b in p['bases'] if b.get('eyes')=='echo']
    so=[(b['id'],b['colour'],b['family']) for b in p['bases'] if b.get('eyes')=='set_off']
    print(d.split('/')[-2], 'eyes',e, '\n   echo',ec,'\n   set_off',so)
    print('   відповідь:', t.split('── ВІДПОВІДЬ')[1].split('\n',2)[2][:260].strip())
