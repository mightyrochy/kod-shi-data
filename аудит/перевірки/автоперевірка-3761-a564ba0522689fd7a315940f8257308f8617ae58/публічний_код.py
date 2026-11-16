"""Звіряє змінені файли продукту поза демонстраційними блоками __main__."""
import ast
import subprocess

база, голова = "2f49c2c9b9752451ee26207518f7d0dcc1ad79ff", "a564ba0522689fd7a315940f8257308f8617ae58"
def імпортований_код(ref, файл):
    дерево = ast.parse(subprocess.check_output(["git", "show", ref + ":" + файл]).decode("utf-8"))
    дерево.body = [в for в in дерево.body if not (isinstance(в, ast.If) and
        ast.dump(в.test) == ast.dump(ast.parse('__name__ == "__main__"', mode="eval").body))]
    return ast.dump(дерево)
for файл in ["джерела/areas.py", "джерела/pipeline.py", "джерела/суд_образу.py"]:
    assert імпортований_код(база, файл) == імпортований_код(голова, файл)
    print(файл, "імпортований код ДО = ПІСЛЯ")
assert not subprocess.check_output(["git", "diff", "--name-only", база, голова, "--", "джерела/показ", "джерела/показ.html", "джерела/показ.css"])
print("Файли показу: змін немає")
