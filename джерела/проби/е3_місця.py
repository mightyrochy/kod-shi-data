"""Звірка множин файл · пункт · функція з двох виводів приладу кореня."""
import ast, collections, pathlib, re, subprocess, sys


def місця(текст, коміт=None):
    """Прив'язати рядки приладу до функцій відповідного дерева."""
    вих, дерева = collections.Counter(), {}
    for рядок in текст.splitlines():
        збіг = re.match(r'(п\S+) · (.*?):(\d+) ·', рядок)
        if not збіг:
            continue
        пункт, файл, номер = збіг.groups()
        файл = файл.replace('\\', '/')
        if файл not in дерева:
            код = (subprocess.check_output(['git', 'show', коміт + ':' + файл]).decode('utf-8')
                   if коміт else pathlib.Path(файл).read_text(encoding='utf-8'))
            дерева[файл] = ast.parse(код)
        функції = [n for n in ast.walk(дерева[файл]) if isinstance(n, ast.FunctionDef)
                   and n.lineno <= int(номер) <= n.end_lineno]
        функція = min(функції, key=lambda n: n.end_lineno - n.lineno).name if функції else 'модуль'
        вих[файл, пункт, функція] += 1
    return вих


def main():
    """Відхилити нові місця або незняті місця файлу погоди."""
    до = місця(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'), sys.argv[3])
    після = місця(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
    нові = після - до
    погода = sum(v for k, v in після.items() if k[0] == 'джерела/суд_погода.py')
    print('місць', sum(до.values()), '→', sum(після.values()), 'нових', sum(нові.values()), 'погода', погода)
    assert sum(після.values()) <= 150 and not нові and погода == 0


if __name__ == '__main__':
    main()
