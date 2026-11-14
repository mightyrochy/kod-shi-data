"""Відтворення незалежної перевірки #3707; перший аргумент — тека з base3707, pr3707, до.html та після.html."""

def головна():
    import sys
    if len(sys.argv)<3:
        raise SystemExit("Потрібна тека робочих дерев і кеш Pyodide")
    import os, sys, json, hashlib, subprocess, time, platform
    from pathlib import Path
    
    root=Path(sys.argv[1]).resolve()
    head=root/'pr3707'
    helper=head/'джерела'/'прилади'/'знімок_мосту_pyodide.js'
    inputs=head/'аудит'/'проби'/'Збирання-запити-час'/'входи'
    results=[]
    def cpu():
        raw=subprocess.check_output(['node','-e','const o=require("os");process.stdout.write(JSON.stringify(o.cpus()))'],text=True,encoding='utf8')
        cores=json.loads(raw)
        return {'модель':cores[0]['model'],'idle':sum(c['times']['idle'] for c in cores),'total':sum(sum(c['times'].values()) for c in cores)}
    for version,page in [('ДО',root/'до.html'),('ПІСЛЯ',root/'після.html')]:
        for scene in sorted(inputs.glob('*.jsonl.gz')):
            output=root/'час3707'/version/scene.name.removesuffix('.jsonl.gz')
            output.mkdir(parents=True,exist_ok=True)
            cmd=['node',str(helper),str(page),str(Path(sys.argv[2]).resolve()),str(scene),str(output)]
            cpu_before=cpu()
            with (output/'процес.log').open('w',encoding='utf8') as log:
                p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            cpu_after=cpu()
            assert p.returncode==0,(cmd,p.returncode)
            timing=json.loads((output/'час.json').read_text('utf8'))
            assert timing['версія_pyodide']=='0.26.4',timing['версія_pyodide']
            call=next(x for x in timing['виклики'] if x[1]=='запити')
            line=next(x for x in (output/'знімок.jsonl').read_text('utf8').splitlines() if json.loads(x).get('н')==call[0])
            data=json.loads(line)
            response=data.get('результат')
            assert isinstance(response,dict),data
            assert not response.get('помилка') and response.get('пул_речей',0)>0,response
            table=(response.get('мета') or {}).get('таблиця_каталогу') or {}
            assert table.get('стан')=='вжито',table
            result={'збірка':version,'сцена':scene.name.removesuffix('.jsonl.gz'),'запити_с':round(call[2]/1000,3),'sha':hashlib.sha256(line.encode('utf8')).hexdigest(),'помилка':data.get('помилка'),'pyodide':timing['версія_pyodide'],'вхід_sha256':hashlib.sha256(scene.read_bytes()).hexdigest()}
            result.update(пул_речей=response['пул_речей'],таблиця_каталогу=table['стан'])
            result.update(процесор=cpu_before['модель'],завантаження_процесора_відсотків=round(100*(1-(cpu_after['idle']-cpu_before['idle'])/(cpu_after['total']-cpu_before['total'])),1))
            results.append(result)
            (root/'час3707.json').write_text(json.dumps(results,ensure_ascii=False,indent=1),encoding='utf8')
            print(json.dumps(result,ensure_ascii=False),flush=True)
            assert result['помилка'] is None,result
    for scene in sorted({x['сцена'] for x in results}):
        a,b=[x for x in results if x['сцена']==scene]
        assert a['sha']==b['sha'],(a,b)
    print('Три сцени: вихід ДО й ПІСЛЯ збігається до байта',flush=True)


if __name__=="__main__":
    головна()
