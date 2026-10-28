"""Перевіряє старий читач і стару стелю новими сценаріями в окремому клоні."""
from pathlib import Path
import subprocess
import sys


def main():
    """Тимчасово повертає два файли бази; завжди відновлює кандидат після виміру."""
    tree = Path(sys.argv[1]).resolve()
    assert tree != Path.cwd().resolve()
    folder = Path(__file__).resolve().parent
    files = ['аудит/адаптери/gemini/' + name for name in ('claude_run.ps1', 'queue_lanes.ps1')]
    saved = {name: (tree / name).read_bytes() for name in files}
    try:
        for name in files:
            (tree / name).write_bytes(subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=tree))
        command = [sys.executable, str(folder.parents[0] / 'доробка-1969/прогнати_стенди.py'), str(tree),
                   str(folder / 'до'), 'сценарії_звіту.sh']
        result = subprocess.run(command)
        assert result.returncode == 1, 'ДО має довести розбіжність із мірилом'
    finally:
        for name, data in saved.items():
            (tree / name).write_bytes(data)


if __name__ == '__main__':
    main()
