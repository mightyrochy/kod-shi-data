import base64,hashlib,io,json,pathlib,re,subprocess,sys,zipfile
src=pathlib.Path('/workspace/scratch/liusterko-4622/джерела');sys.path.insert(0,str(src));import build_артефакт as B
artifact=pathlib.Path('/workspace/scratch/4622-proof/round2-native/index.html');html=artifact.read_text()
payload=base64.b64decode(re.search(r'const МОДУЛІ_ПОКАЗУ\s*=\s*"([^"]+)"',html).group(1));z=zipfile.ZipFile(io.BytesIO(payload))
items={}
for name in z.namelist():
 if name.endswith('.py'):
  frozen=subprocess.check_output(['git','show','03759fd671272d6353dedd671dd528ea049a0003:джерела/'+name],cwd=src)
  assert (src/name).read_bytes()==frozen,name
  assert z.read(name)==B._стрип(str(src/name)),name
  items[name]=hashlib.sha256(z.read(name)).hexdigest()
# Фактична функція UI відповідає штатній чистці frozen показ.html.
frozen_ui=subprocess.check_output(['git','show','03759fd671272d6353dedd671dd528ea049a0003:джерела/показ.html'],cwd=src).decode()
clean=B._чистка_показу(frozen_ui)
fragment=re.search(r'function застосуватиПаспортДоЕкрана\(п\)\{.*?\n\}',clean,re.S).group(0)
assert fragment in html
manifest=json.loads(pathlib.Path('/workspace/scratch/4622-proof/round2-native/source-identity.json').read_text())
assert hashlib.sha256(artifact.read_bytes()).hexdigest()==manifest['html_sha256']
for name,expected in manifest['files'].items():
 assert hashlib.sha256((artifact.parent/name).read_bytes()).hexdigest()==expected,name
result={'sourceSHA':'03759fd671272d6353dedd671dd528ea049a0003','sourceURI':'git:03759fd671272d6353dedd671dd528ea049a0003:джерела','artifact':str(artifact),'html_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'payload_sha256':hashlib.sha256(payload).hexdigest(),'all_zip_python_modules_equal_frozen_standard_strip':len(items),'ui_function_equal_frozen_standard_strip':True,'actor_manifest_hashes_verified':len(manifest['files']),'model_calls':0}
pathlib.Path('/workspace/scratch2/review4622-round2/identity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
