import hashlib,json,pathlib,re,subprocess,sys
repo=pathlib.Path('/workspace/scratch/4944-aa-next/repo');root=pathlib.Path('/workspace/scratch/4944-aa-next-evidence');sys.path.insert(0,str(repo/'джерела'));from build_артефакт import _чистка_показу
out=[]
for stage,sha in [('before','0ccb8dbfa1b97ab3ac2ed189139a7bcfbe9ba3bc'),('after','824243ed89fd75b04a9c96552784a51ab6a39888')]:
 raw=subprocess.check_output(['git','show',sha+':джерела/показ.html'],cwd=repo).decode();template=_чистка_показу(raw);built=(root/stage/'index.html').read_text();chunks=[c for c in re.split(r'__[А-ЯІЇЄҐA-Z_]+__',template) if c];at=0
 for c in chunks:
  pos=built.find(c,at);assert pos>=0,(stage,len(c),c[:80]);at=pos+len(c)
 out.append({'stage':stage,'head':sha,'source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'built_sha256':hashlib.sha256(built.encode()).hexdigest(),'template_fragments':len(chunks),'matched':len(chunks)})
(root/'provenance.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
