"""Скрипт батареї (гейти, дим, тести, проба) під записувачем суддів в одному процесі.
Аргументи: <вихід.json.gz> <корінь дерева | -> <скрипт від джерела/> [його аргументи]."""
import os, pathlib, runpy, sys
ТУТ = pathlib.Path(__file__).resolve().parent
КОРІНЬ = (ТУТ.parents[1] if sys.argv[2] == '-' else pathlib.Path(sys.argv[2])).resolve()
СКРИПТ = КОРІНЬ / 'джерела' / sys.argv[3]
sys.path[:0] = [str(СКРИПТ.parent), str(КОРІНЬ / 'джерела'), str(ТУТ)]
os.chdir(КОРІНЬ / 'джерела')
import е3_судді_запис as З


def main():
    вихід = sys.argv[1]
    З.обгорнути()
    sys.argv = [str(СКРИПТ)] + sys.argv[4:]
    код = 0
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    except SystemExit as в:
        код = в.code
    З.записати(вихід, код=код)
    print('код скрипта', код)


if __name__ == '__main__':
    main()
