import subprocess, json, re, hashlib, gzip
from pathlib import Path
R='/workspace/kod-shi-data'
B='7c90a0093b5d7dc8587a90c541eaf11e23b9a3be'
H='cfbe2671b868cdcf124d25bd3d1c895fc14055fe'
S=['52fc8503656b13369ad538ec30d920701cf45dfe','4d60cce0ecadca38252b11f934c874b871bb8bf7']
def git(*args): return subprocess.check_output(['git','-C',R,*args])
def tree(ref):
    out={}
    for row in git('ls-tree','-rz',ref).split(b'\0'):
        if row:
            meta,path=row.split(b'\t'); mode,kind,sha=meta.split();out[path.decode()]=(mode.decode(),kind.decode(),sha.decode())
    return out
ts=[tree(r) for r in [B,H,*S]];base,head,s994,s995=ts
expected=dict(base)
for source in [s994,s995]:
    for path in set(base)|set(source):
        if path=='аудит/БЕКЛОГ.md':continue
        if source.get(path)!=base.get(path):
            if path in source:expected[path]=source[path]
            else:expected.pop(path,None)
expected['аудит/БЕКЛОГ.md']=head['аудит/БЕКЛОГ.md']
assert expected==head, 'Unexpected or lost blobs'
for source in S: assert subprocess.run(['git','-C',R,'merge-base','--is-ancestor',source,H]).returncode==0
newcommits=git('rev-list',H,'^'+B).decode().splitlines()
assert len(newcommits)==4 and set(S)<=set(newcommits)
merges=[x for x in newcommits if len(git('show','-s','--format=%P',x).split())==2]
assert len(merges)==2
boards=[git('show',r+':аудит/БЕКЛОГ.md').decode() for r in [B,H,*S]]
line=lambda t,n:next(x for x in t.splitlines(keepends=True) if re.match(r'^\|\s*'+str(n)+r'\s*\|',x))
expected_board=boards[0].replace(line(boards[0],4944),line(boards[2],4944))
for n in range(5191,5195):
    b,s=line(boards[0],n),line(boards[3],n)
    bc,sc=b.split('|'),s.split('|')
    changed=[i for i in range(len(bc)) if bc[i]!=sc[i]]
    assert changed==[5], (n,changed)
    expected_board=expected_board.replace(b,s)
assert boards[1]==expected_board, 'Unexpected board bytes'
rows=re.findall(r'^\|\s*(\d+)\s*\|',boards[1],re.M)
oldrows=re.findall(r'^\|\s*(\d+)\s*\|',boards[0],re.M)
assert len(rows)==len(set(rows))==1305 and rows==oldrows
assert not re.search(r'^(<<<<<<<|=======|>>>>>>>)',boards[1],re.M)
assert all('ВІДКРИТО' in line(boards[1],n) and 'ЗАКРИТО' not in line(boards[1],n) for n in [4944,5191,5192,5193,5194])
files=[]
for p in sorted(set(base)|set(head)):
    if base.get(p)!=head.get(p):files.append(p)
assert len(files)==13
assert len([p for p in files if p.startswith('джерела/дані_5191_5194/')])==7
assert len([p for p in files if p.startswith('джерела/проби/')])==4
assert 'джерела/показ.html' in files
assert not any(re.search(r'\.(png|jpe?g|webp|gif|svg|mp4)$',p,re.I) for p in files)
data=[]
for p in files:
    if not p.startswith('джерела/дані_5191_5194/'):continue
    b=git('show',H+':'+p); raw=gzip.decompress(b) if p.endswith('.gz') else b;v=json.loads(raw)
    assert raw==(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
    if p.endswith('.gz'):assert b[4:8]==b'\0'*4
    data.append({'path':p,'blob':head[p][2],'compressed_sha256':hashlib.sha256(b).hexdigest(),'json_sha256':hashlib.sha256(raw).hexdigest(),'json_bytes':len(raw)})
result={'head':H,'base':B,'sources':S,'tree_blob_count':len(head),'unchanged_main_blobs':len(head)-13,'changed_files':files,'normal_merges':merges,'source_heads_are_ancestors':True,'exact_source_owned_blobs':True,'all_other_main_blobs_unchanged':True,'board_rows':len(rows),'board_row_order_ids_preserved':True,'board_whole_bytes_exact_combination':True,'open_rows':[4944,5191,5192,5193,5194],'new_main_images':0,'data':data}
Path('/tmp/qa999-integration/composition.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
