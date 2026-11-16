import importlib,sys,pathlib,subprocess,ast,json,time
sys.path.insert(0,'джерела/прилади');m=importlib.import_module('корінь_річ_кадр_варіант')
target=pathlib.Path('джерела/прилади/корінь_е2_збій_без_сліду.py').resolve();old=subprocess.check_output(['git','show','3a1edf232e1:'+target.relative_to(pathlib.Path.cwd()).as_posix()],encoding='utf8');parse=m.розібрати
result={}
for mode in ('голова','до'):
 if mode=='до':m.розібрати=lambda p:ast.parse(old) if pathlib.Path(p).resolve()==target else parse(p)
 places=m.головна('.')[0];js=m.скан_js('.')[2]
 result[mode]={'python':[dict(файл=p.файл,рядок=p.рядок,пункт=p.пункт,чому=p.чому) for p in places],'js':js}
 print(mode,json.dumps(result[mode],ensure_ascii=False),flush=True)
 pathlib.Path(__file__).with_name('кадр-повний.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
