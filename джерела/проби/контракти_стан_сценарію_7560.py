"""7560: фактичний JS writer двох ручних flags та локальний Python boundary."""
import ast, json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.chdir(Path(__file__).resolve().parents[1])
import audit_contracts as А
import міст_запити as М


def main():
    """Виконує справжній JS producer і Python reader, не піднімаючи показ."""
    код = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const текст=fs.readFileSync('показ.html','utf8');
const producer=текст.match(/function вхідСтануСценаріюП\(\)\{[\s\S]*?\n\}/)[0];
assert(текст.includes("містП('стан_сценарію', вхід)"));
const rows=[];
for(const плитки of [false,true]) for(const опади of [false,true]){
 const ctx={ВИПАДОК_ЗМІНЕНО_П:плитки,ОПАДИ_РУКОЮ_П:опади,
 ПАСПОРТ_П:{опади:'rain'},зібратиВхід:()=>({сценарій:{опади:'сніг'}})};
 rows.push(JSON.parse(vm.runInNewContext(producer+';JSON.stringify(вхідСтануСценаріюП())',ctx)));
}
console.log(JSON.stringify(rows));'''
    рядки = json.loads(subprocess.check_output(['node', '-e', код], text=True))
    for рядок in рядки:
        стан = json.loads(М.стан_сценарію(рядок))
        assert стан['код_плитки_опадів'] == ('сніг' if рядок['опади_рукою'] else 'дощ')
    текст = Path('міст_запити.py').read_text()
    ключі, блоки = А._декларація(ast.parse(текст))
    assert ключі == {'опади_рукою', 'плитки_змінено'} and not ключі & А.ЗОВНІШНІ
    А.МОДУЛІ = ['міст_запити']
    for джерело, очікувані in ((А._затерти_рядки(текст, блоки), ключі), (текст, set())):
        А._ОГОЛОШЕНІ.clear()
        А._джерело = lambda м: джерело
        сироти, _, записи, зовнішні, _ = А.поля()
        assert ключі & сироти.keys() == очікувані and not ключі & записи.keys()
    assert ключі <= зовнішні.keys()
    print('ПРОЙДЕНО 7560: actual JS→Python 4 стани; сироти2→0, декларація не writer')

if __name__ == '__main__': main()
