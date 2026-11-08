/* `перекластиП('verdict_comment', …)` з показ/мовний_шар.js дерева <корінь> на записаних відповідях #38/#39 прогону
   (тека VIDPOVIDI), міст — справжній `мовний_шар.мова` того самого дерева (python), модель — записані відповіді. */
const fs = require('fs'), path = require('path'), vm = require('vm'), {spawnSync} = require('child_process');
const [корінь, тека] = process.argv.slice(2);
const c = vm.createContext({console, Date, МОДЕЛЬ_МОВИ_П: 'запис', ПАСПОРТ_П: null, ЧАТ_П: []});
vm.runInContext(fs.readFileSync(path.join(корінь, 'джерела/показ/мовний_шар.js'), 'utf8'), c);
const відп = н => fs.readFileSync(path.join(тека, fs.readdirSync(тека).find(ф => ф.startsWith('seed3_' + н + '_'))), 'utf8')
  .split('── ВІДПОВІДЬ')[1].split('──\n')[1].trim();
const черга = [відп(38), відп(39)];
c.містП = async (_, д) => {
  const р = spawnSync('python3', ['-W', 'ignore', '-c',
    'import sys;sys.path.insert(0,sys.argv[1]);import мовний_шар as М;print(М.мова(sys.stdin.read()))',
    path.join(корінь, 'джерела')], {input: JSON.stringify(д), encoding: 'utf8'});
  return JSON.parse(р.stdout);
};
c.модельМовиП = async () => черга.shift();
(async () => {
  const речі = [{id: 'ж-04103@sezone.ua', слот: 'верх'}, {id: 'ж-07291@rito.ua', слот: 'низ'}, {id: 'ж-09741@attico.ua', слот: 'взуття'}];
  const р = await c.перекластиП('verdict_comment', 'взуття не моє, хочу без каблука і без принта', {речі}, 'verdict.hand_1');
  console.log(JSON.stringify({внутрішня: р.внутрішня, запасна: р.запасна === undefined ? 'нема поля' : р.запасна,
    причина: р.запис.причина || null, незнайомі: р.запис.незнайомі || null, повтор: !!р.запис.повтор}));
})();
