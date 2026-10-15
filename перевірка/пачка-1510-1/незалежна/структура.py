import collections, json, re, subprocess
from pathlib import Path
r=Path('/workspace/scratch/pachka-1510-1/repo')
g=lambda *a: subprocess.check_output(['git',*a],cwd=r)
head='c80bea14f73505903d1b99c77b746c45acb34c45'; base='531ce082f573d225d444952207930095d2e260fc'
sources={'5191':'84d7d2af5bcbaa1f8414621d537bafc250173668','5193':'3d1789c3dba1eb612bc71111226f719011e00475','3541':'291a51b9b5ee0f4c6717b12d6194a7c68ff959b5'}
assert g('rev-parse','HEAD').decode().strip()==head
for sha in [base,*sources.values()]: subprocess.run(['git','merge-base','--is-ancestor',sha,head],cwd=r,check=True)
board='аудит/БЕКЛОГ.md'; before=g('show',base+':'+board).splitlines(keepends=True); after=g('show',head+':'+board).splitlines(keepends=True)
rowid=lambda line: (re.match(rb'^\|\s*(\d+)\s*\|',line) or [None,None])[1]
assert len(before)==len(after)
ids=collections.Counter(rowid(x) for x in after if rowid(x)); oldids=collections.Counter(rowid(x) for x in before if rowid(x))
assert ids==oldids and max(ids.values())==1
assert [x for x in before if rowid(x) not in {k.encode() for k in sources}]==[x for x in after if rowid(x) not in {k.encode() for k in sources}]
for key,sha in sources.items():
 old=next(x for x in before if rowid(x)==key.encode()); new=next(x for x in after if rowid(x)==key.encode())
 assert new==next(x for x in g('show',sha+':'+board).splitlines(keepends=True) if rowid(x)==key.encode())
 assert len(old.split(b'|'))==len(new.split(b'|')) and all(x.strip() in y for x,y in zip(old.split(b'|'),new.split(b'|')))
 assert '**ВІДКРИТО**'.encode() in new
paths=g('diff','--name-only','-z',base,head).decode().strip('\0').split('\0')
expected=['джерела/'+x+'.py' for x in ['дріт_моделі','міст_відповіді','повнота_образу','протокол']]+['джерела/проби/прийняття_3541.py']
assert set(paths)=={board,*expected,'джерела/проби/тип_джерела_5191.py','джерела/проби/назва_джерела_5193.py'}
for p in expected: assert g('show',head+':'+p)==g('show',sources['3541']+':'+p)
for key,name,lines in [('5191','тип',33),('5193','назва',40)]:
 p=f'джерела/проби/{name}_джерела_{key}.py'; assert g('show',head+':'+p)==g('show',sources[key]+':'+p)
 assert len((r/p).read_text().splitlines())==lines
subprocess.run(['git','diff','--check',base,head],cwd=r,check=True)
print(json.dumps(dict(голова=head,база=base,предки=list(sources.values()),рядків_дошки=len(ids),дублів=0,змінені_рядки=list(sources),чужі_байти_цілі=True,історичні_клітинки_цілі=True,усі_рядки_відкриті=True,всі_8_файлів_дорівнюють_точним_джерелам=True,медіа_у_main=0),ensure_ascii=False,indent=2))
