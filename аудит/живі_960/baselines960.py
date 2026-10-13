from pathlib import Path
import subprocess,json,gzip,hashlib
root=Path(__file__).resolve().parents[1]
def blob(ref,path): return subprocess.check_output(['git','show',ref+':'+path],cwd=root)
items=[('4948','origin/claude/zhyvi-26','аудит/живі_26/А/05_ж1_оціни_образ_6б'),
 ('4684-L','origin/claude/zhyvi-25','аудит/живі_25/А/04_ж1_оціни_образ_6б'),
 ('4825','origin/claude/zhyvi-25','аудит/живі_25/А/10_ж2_новорічна_мороз'),
 ('4105','origin/claude/zhyvi-26','аудит/живі_26/А/06_ж2_новорічна_мороз'),
 ('4622','origin/claude/zhyvi-25','аудит/живі_25/А/08_ж2_спорт_коментар'),
 ('3520','origin/claude/zhyvi-13','аудит/живі_13/А/08_ж7_мороз_без_відкритого'),
 ('5202','origin/main','аудит/живі_12/Б/08_ж1_оціни_образ_6б')]
data=[]
for row,ref,path in items:
 try:
  code=blob(ref,path+'/код.txt').decode().strip()
  data.append(dict(row=row,ref=ref,artifact_sha=subprocess.check_output(['git','rev-parse',ref],cwd=root,text=True).strip(),path=path,code=code))
 except subprocess.CalledProcessError as e: data.append(dict(row=row,path=path,error='archive_path_missing'))
src=root/'аудит/гг1_замір/входи.jsonl.gz'
gg=[json.loads(s) for s in gzip.decompress(src.read_bytes()).decode().splitlines() if s.strip()]
data.append(dict(row='ГГ1',path=str(src.relative_to(root)),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),records=len(gg),first_record_keys=list(gg[0]),runnable_paired_assignment=False))
data.append(dict(row='5201/4623',status='input-and-DO-gap; no substituted scene run'))
(root/'аудит/живі_960/baselines.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('baseline records',len(data),'GG inputs',len(gg))
