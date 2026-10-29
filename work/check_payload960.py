import re,base64,zipfile,io,pathlib,json,gzip,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
html=pathlib.Path('C:/tmp/zh960/site/index.html').read_text(encoding='utf-8')
payload=base64.b64decode(re.search(r'const МОДУЛІ_ПОКАЗУ = "([^"]+)"',html)[1])
z=zipfile.ZipFile(io.BytesIO(payload))
print('data entries',[n for n in z.namelist() if 'каталог' in n or 'збагачення' in n])
print('feed loader',z.read('feed.py')[:300].decode())
g=(root/'джерела/каталог_збагачення.json.gz').read_bytes()
entry=next(n for n in z.namelist() if n.startswith('каталог_збагачення'))
result=dict(unpacked_enrichment_present=(root/'джерела/каталог_збагачення.json').exists(),
 zipped_entry=entry,gzip_sha256=hashlib.sha256(g).hexdigest(),
 payload_entry_sha256=hashlib.sha256(z.read(entry)).hexdigest(),
 exact_gzip_bytes=z.read(entry)==g,
 code_sha='7c90a0093b5d7dc8587a90c541eaf11e23b9a3be')
(root/'аудит/живі_960/payload_3781.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
