"""Виконує лише потрібний розділ штатної батареї після відновлення фікстур."""
import ast,importlib.util,pathlib,sys


def main():
    """Виконує лише потрібний розділ штатної батареї після відновлення фікстур."""
    src=pathlib.Path(sys.argv[1]).resolve();sys.path.insert(0,str(src))
    path=src/'прилади/розділи_гейтів.py'
    spec=importlib.util.spec_from_file_location('гейти_голови',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    body=next(n for n in ast.parse(path.read_text('utf8')).body if isinstance(n,ast.FunctionDef) and n.name=='main').body
    def section(node,prefix):
        """Розпізнає заголовок розділу AST без виконання решти батареї."""
        return isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='print' and node.value.args and isinstance(node.value.args[0],ast.Constant) and str(node.value.args[0].value).startswith(prefix)
    start=next(i for i,n in enumerate(body) if section(n,'89.'))
    end=next(i for i,n in enumerate(body) if i>start and section(n,'90.'))
    exec(compile(ast.Module(body=body[start:end],type_ignores=[]),str(path),'exec'),module.__dict__)
    print('ПРОЙДЕНО',module.ok,'ВПАЛО',len(module.збої),'БЕЗ ВХОДУ',len(module.пропущено))
    return bool(module.збої or module.пропущено)


if __name__ == "__main__":
    sys.exit(main())
