"""Зберігає повний стандартний прогін показу голови без зміни таймаутів."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    """Запускає штатну батарею та фіксує код завершення."""
    звіт = Path(__file__).resolve().parent
    корінь = звіт.parents[2]
    назва = 'показ'
    команда = ['node', 'джерела/тест_показу.js']
    if '--повільний-шов' in sys.argv:
        назва = 'показ-повільний-шов'
        команда = ['node', '-e', """
const fs=require('fs'),path=require('path'),Module=require('module');
const file=path.resolve('джерела/тест_показу.js');
let source=fs.readFileSync(file,'utf8');
for (const [before,after] of [['timeout: 10000','timeout: 60000'],['ліміт = 8000','ліміт = 60000']]){
  if (source.split(before).length!==2) throw new Error('Змінилась форма таймауту: '+before);
  source=source.replace(before,after);
}
const test=new Module(file,module); test.filename=file; test.paths=Module._nodeModulePaths(path.dirname(file));
test._compile(source,file);
"""]
    with (звіт / (назва + '.txt')).open('w', encoding='utf-8') as вихід:
        код = subprocess.run(команда, cwd=корінь,
                             env=dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8'),
                             stdout=вихід, stderr=subprocess.STDOUT).returncode
    (звіт / (назва + '-код.txt')).write_text(str(код) + '\n', encoding='utf-8')
    print(назва + ': ' + str(код), flush=True)
    return код


if __name__ == '__main__':
    sys.exit(main())
