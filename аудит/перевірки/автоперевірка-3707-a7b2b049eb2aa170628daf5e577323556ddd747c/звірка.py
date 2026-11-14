"""Відтворення незалежної перевірки #3707; перший аргумент — тека з base3707, pr3707, до.html та після.html."""

def головна():
    import sys
    if len(sys.argv)<2:
        raise SystemExit("Потрібна тека робочих дерев")
    import importlib.util, sys, random, math, json, time
    from pathlib import Path
    
    root=Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root / 'pr3707' / 'джерела'))
    def load(name, filename):
        spec = importlib.util.spec_from_file_location(name, root / 'base3707' / 'джерела' / filename)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    
    import колір_тон as new
    old = load('тон_до', 'колір_тон.py')
    rng = random.Random(3707)
    points = [(rng.uniform(-8,108), rng.uniform(-145,145), rng.uniform(-145,145)) for _ in range(600)]
    points += [(L,a,b) for L in (0,50,100) for a in (-128,0,127) for b in (-128,0,127)]
    delta = 0.0
    count = 0
    for point in points:
        for error in (0,1.5,4):
            a = old._ваги(point,error,True)
            b = new._ваги(point,error,True)
            for x,y in zip(a[0]+a[1], b[0]+b[1]):
                delta = max(delta, abs(x-y)/max(1,abs(x)))
                assert math.isclose(x,y,rel_tol=1e-11,abs_tol=1e-11), (point,error,x,y)
            assert sorted(range(len(a[0])), key=lambda i:a[0][i]) == sorted(range(len(b[0])), key=lambda i:b[0][i]), (point,error,a,b)
            count += 1
    print(json.dumps({'ядра':count,'розбіжностей':0,'макс_похибка':delta},ensure_ascii=False),flush=True)
    
    import фід_добір as fd
    before = load('добір_до', 'фід_добір.py')
    count = 0
    for i in range(600):
        lo,hi=sorted((rng.uniform(0,100),rng.uniform(0,100)))
        cl,ch=sorted((rng.uniform(0,100),rng.uniform(0,100)))
        window=(lo,hi,cl,ch,None if i%3==0 else (rng.uniform(0,360),rng.uniform(0,360)))
        q=dict(L_min=rng.uniform(0,50),L_max=rng.uniform(50,100),C_min=rng.uniform(0,40),C_max=rng.uniform(40,100),h_from=rng.uniform(0,360),h_to=rng.uniform(0,360))
        if i%5==0: q.update(нейтраль=True,b_min=-5,b_max=12)
        if i%7==0: q['метал']='gold'
        if i%11==0: q['очі_запис']={'L':(20,80),'C':(0,40),'дуга':(30,120)}
        # Очі мають власний контракт запису; перевіряємо готові фікстури сім'ї окремо.
        q.pop('очі_запис',None)
        before.ЧАСТКА_КЕШ.clear(); fd.ЧАСТКА_КЕШ.clear()
        a=before.частка_вікна(window,q)
        b=fd.частка_вікна(window,q)
        assert a==b,(window,q,a,b)
        assert b==fd.частка_вікна(window,q,ключі=(fd.ключ_вікна(window),fd.ключ_запиту(q)))
        count+=1
    print(json.dumps({'вікна':count,'розбіжностей':0},ensure_ascii=False),flush=True)
    
    import selection_policy as sp
    bs=load('сорт_до','selection_policy.py')
    for seed in range(20):
        shared={'L_min':0,'L_max':100,'дуга':[0,360]}
        rows=[(rng.random(), {'id':str(i)},shared) for i in range(200)]
        assert bs.порядок(rows,seed,'проба')==sp.порядок(rows,seed,'проба')
    print('Сортування: 20 наборів × 200 кандидатів, розбіжностей 0',flush=True)


if __name__=="__main__":
    головна()
