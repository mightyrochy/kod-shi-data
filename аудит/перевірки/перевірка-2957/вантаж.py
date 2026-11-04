"""Зіставити AST модуля голови з вантажем, де збирач вилучає докстрінги."""
import ast, base64, hashlib, io, json, pathlib, re, sys, zipfile
page,src=map(pathlib.Path,sys.argv[1:3])
html=page.read_text(encoding='utf-8')
encoded=re.search(r'МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"',html).group(1)
with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as z:
    packed=z.read('вибір_палітри.py')
original=(src/'вибір_палітри.py').read_bytes()
def tree(data):
    node=ast.parse(data)
    for x in ast.walk(node):
        body=getattr(x,'body',None)
        if isinstance(body,list) and len(body)>1 and isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str):
            x.body=body[1:]
    return ast.dump(node,include_attributes=False)
assert tree(packed)==tree(original)
assert b'Give each choice its reasons.' not in packed
print(json.dumps(dict(AST_без_докстрінгів_тотожний=True,sha256=hashlib.sha256(packed).hexdigest(),
                       html_sha256=hashlib.sha256(page.read_bytes()).hexdigest()),ensure_ascii=False,indent=2))
