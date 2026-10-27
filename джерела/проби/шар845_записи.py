"""Порівнює діагностику до й після поділу ключів на справжніх файлах вердиктів сцен."""
import json
import pathlib
import subprocess
import sys


def main():
    """Друкує лічбу відповідей і порожніх джерел без викликів моделей."""
    корінь = pathlib.Path(__file__).resolve().parents[2]
    сцени = {str(pathlib.Path(ш)): json.loads(pathlib.Path(ш).read_text(encoding="utf-8"))
             for ш in sys.argv[1:]}
    код = r'''
const fs = require('fs'), path = require('path');
const {джерелоШару, питаньЗВідповіддю} = require(path.resolve('аудит/проби/записи_шару.js'));
const сцени = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const [сцена, файл] of Object.entries(сцени)) for (const прогін of файл.прогони) for (const к of прогін.вердикти){
  if (!['1', '2'].includes(String(к.рука))) continue;
  const записи = (к.мова_шару || []).filter(з => /code_unknowns/.test(з.де || ''));
  const без = записи.flatMap(з => (з.без_відповіді || []).map(ключ => ({з, ключ})));
  const було = записи.reduce((н, з) => н + Object.keys(з.вихід || {}).filter(к => /^питання\./.test(к)).length
    + (з.чужою || []).filter(к => /^питання\./.test(к)).length, 0);
  const порожніх = без.filter(({з, ключ}) => !джерелоШару(з, ключ)).length;
  console.log(сцена, 'рука', к.рука, 'відповіли ДО → ПІСЛЯ:', було, '→', питаньЗВідповіддю(записи),
    'порожніх джерел ДО → ПІСЛЯ:', без.filter(({з, ключ}) => !(з.вхід || {})[ключ]).length, '→', порожніх);
  if ('питань_картці' in к) console.log('  повних відповідей разом із пам’яттю / питань для картки:',
    питаньЗВідповіддю(записи) + (к.питань_з_пам_яті || 0), '/', к.питань_картці);
  if (порожніх) process.exitCode = 1;
}
'''
    р = subprocess.run(["node", "-e", код], cwd=корінь, input=json.dumps(сцени), text=True)
    return р.returncode


if __name__ == "__main__":
    sys.exit(main())
