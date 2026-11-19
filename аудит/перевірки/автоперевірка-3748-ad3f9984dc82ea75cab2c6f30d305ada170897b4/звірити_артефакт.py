import ast,base64,io,json,pathlib,re,sys,zipfile

class Виконуване(ast.NodeTransformer):
    def visit_Expr(self,node):
        if isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
            return None
        return self.generic_visit(node)
    def visit_Pass(self,node):
        return None

html=pathlib.Path(sys.argv[1]).read_text('utf8')
root=pathlib.Path(sys.argv[2])
payload=re.search(r'const МОДУЛІ_ПОКАЗУ = "([A-Za-z0-9+/=]+)"',html).group(1)
normalize=Виконуване()
diff=[];count=0
with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload))) as z:
    for name in z.namelist():
        if not name.endswith('.py'): continue
        count+=1
        before=normalize.visit(ast.parse(z.read(name)))
        after=normalize.visit(ast.parse((root/'джерела'/name).read_bytes()))
        if ast.dump(before,include_attributes=False)!=ast.dump(after,include_attributes=False): diff.append(name)
print(json.dumps(dict(модулів=count,розбіжності_виконуваного_AST=diff),ensure_ascii=False,indent=2))
assert not diff
