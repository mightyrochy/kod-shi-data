from pathlib import Path
import collections, hashlib, json, re, subprocess, tempfile
root=Path('/tmp/liusterko-pachka-1310-1')
out=Path('/tmp/pachka-1310-evidence'); out.mkdir(exist_ok=True)
def git(*args): return subprocess.check_output(['git','-C',str(root),*args])
def blob(ref,path): return git('show',ref+':'+path)
base='8f22756364e060d4fc968671be11740d6aed8ceb'
heads={978:'994d15894ff2bd42dfd4b037fdd9dc58fd89dbd1',979:'094b3c32bd6d930822f1158be86647dbb1f2ac80',980:'6e3ee81373c7de53b5e181b27f316adf944c091f',981:'8b5680df215fd7447fc15c51644e9c7609965a57',982:'c0b84e61d835e863922a8ca58fae65ebcca416a3',983:'16295ef12cc4d786cbd0242997109cf063d7b357'}
full=git('rev-parse','HEAD').decode().strip()
assert full=='09ff6b7b5a46327666d633e1ba798f249941bb4d'
changed=set(git('diff','--name-only',base,'HEAD').decode().splitlines())
union=set(); own=[]
for n,sha in heads.items():
    assert git('rev-parse','source/'+str(n)).decode().strip()==sha
    subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',sha,'HEAD'],check=True)
    files=git('diff','--name-only',base,sha).decode().splitlines(); union.update(files)
    for p in files:
        if p in ['аудит/БЕКЛОГ.md','джерела/показ.html','аудит/передачі/2026-10-13_0050.md']: continue
        data=blob(sha,p); assert data==blob('HEAD',p),(n,p)
        own.append({'pr':n,'path':p,'sha256':hashlib.sha256(data).hexdigest()})
assert changed==union
board='аудит/БЕКЛОГ.md'
expected=blob(base,board).decode()
rows={979:5080,980:5030,982:5070,983:4941}
for n,i in rows.items():
    pattern=r'^\|\s*'+str(i)+r'\s*\|.*$'
    source=re.findall(pattern,blob(heads[n],board).decode(),re.M); assert len(source)==1
    expected,count=re.subn(pattern,lambda m:source[0],expected,flags=re.M); assert count==1
extra=[x for x in blob(heads[981],board).decode().splitlines(keepends=True) if re.match(r'^\|\s*502[0-7]\s*\|',x)]
assert len(extra)==8 and all('ВІДКРИТО' in x for x in extra)
base981=blob(base,board).decode(); src981=blob(heads[981],board).decode()
assert src981.replace(''.join(extra),'')==base981
anchor=src981.index(''.join(extra))
before=src981[:anchor]; after=src981[anchor+len(''.join(extra)):]
assert base981==before+after
left=expected[:len(before)]; right=expected[len(before):]
# Other source replacements alter lengths before insertion: retain the source's exact surrounding line.
following=after.splitlines(keepends=True)[0] if after else None
if following:
    assert expected.count(following)==1
    expected=expected.replace(following,''.join(extra)+following,1)
else: expected+=''.join(extra)
actual=blob('HEAD',board).decode(); assert expected==actual
ids=re.findall(r'^\|\s*(\d+)\s*\|',actual,re.M)
duplicates={k:v for k,v in collections.Counter(ids).items() if v>1}; assert not duplicates,duplicates
assert not re.search(r'^(<<<<<<<|=======|>>>>>>>)',actual,re.M)
row4944=re.findall(r'^\|\s*4944\s*\|.*$',actual,re.M)
assert row4944==re.findall(r'^\|\s*4944\s*\|.*$',base981,re.M)
handover='аудит/передачі/2026-10-13_0050.md'
old='ChatGPT — 5000–5199. Менеджерові вільні — **з 5204** (5202 — інформація для живого, 5203 — злито в #976).'
new='Нові знахідки — 5000–5199; вільний десяток менеджерові узгоджує координатор (5202 — інформація для живого, 5203 — злито в #976).'
source=blob(heads[978],handover).decode(); assert source.count(old)==1
assert source.replace(old,new)==blob('HEAD',handover).decode()
with tempfile.TemporaryDirectory(prefix='pachka-composition-') as d:
    work=Path(d); (work/'джерела').mkdir(); html=work/'джерела/показ.html'; html.write_bytes(blob(base,'джерела/показ.html'))
    for n in [979,983]:
        patch=git('diff','--binary',base,heads[n],'--','джерела/показ.html')
        subprocess.run(['git','apply','--unsafe-paths','-'],input=patch,cwd=work,check=True)
    assert html.read_bytes()==blob('HEAD','джерела/показ.html')
media=[p for p in changed if re.search(r'\.(png|jpe?g|webp|gif|svg|mp4)$',p,re.I)]; assert not media
for p in ['AGENTS.md','CLAUDE.md','аудит/ПРОДУКТ.md','каталог_повний.xml.gz','джерела/каталог_збагачення.json.gz','джерела/каталог_кадри.json.gz']:
    assert blob(base,p)==blob('HEAD',p)
result={'head':full,'main':base,'sources':heads,'source_owned_files':own,'changed_files':sorted(changed),'board_duplicate_ids':duplicates,'board_5020_5027':'дослівно source981, усі ВІДКРИТО','board_closed':rows,'board4944':'байтово з main, глобальне AA не закрито','show_html':'дослівна послідовна композиція diff979 + diff983','handover':'лише дослівний погоджений рядок55; фотоstatement збережено','new_media_product':len(media),'protected_blobs':'побайтово незмінні'}
(out/'композиція.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
