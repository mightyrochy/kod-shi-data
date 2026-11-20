/* Незалежна проба перекладу прози картки (`перекластиТекстиКарткиП`) на голові PR #4407:
   справжній JS мовного шару й Python `мовний_шар.мова`, модель замінена детермінованою відмовою
   HTTP 402 credits_exhausted. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const {spawnSync} = require('child_process');
const root = path.resolve(process.argv[2]), src = path.join(root, 'джерела');
let calls = 0;
const context = vm.createContext({console, МОДЕЛЬ_МОВИ_П: 'claude-sonnet-5-5',
  НАЛАШТУВАННЯ_РУШІЯ_П: {}, МАКС_ТОКЕНІВ_П: 4000, ЧАТ_П: [],
  стадіяВикликуП: () => 'test', _оцінкаПромптаП: () => 100,
  містП: async (_, data) => {
    const r = spawnSync('python', ['-X', 'utf8', '-c',
      'import sys, мовний_шар; print(мовний_шар.мова(sys.argv[1]))', JSON.stringify(data)],
      {cwd: src, encoding: 'utf8'});
    if (r.status !== 0) throw new Error(r.stderr);
    return JSON.parse(r.stdout);
  }});
vm.runInContext(fs.readFileSync(path.join(src, 'показ', 'мовний_шар.js'), 'utf8'), context);
context.відмоваМоделі = async () => {
  calls++;
  throw new Error('HTTP 402 · {"error":{"type":"credits_exhausted","message":"немає кредитів"}}');
};
vm.runInContext('модельМовиП = відмоваМоделі', context);
(async () => {
  const card = {
    опис: 'A warm wool coat over a black dress.',
    як_носити: ['Wear belted.'],
    речі: [{id: 'а', назва: 'Wool coat'}]
  };
  context.card = card;
  const recs = await vm.runInContext(
    `перекластиТекстиКарткиП(card, 'card_prose', {'опис': card.опис, 'як_носити.0': card.як_носити[0]}, {опис: card.опис, задум: card.як_носити})`,
    context
  );
  console.log(JSON.stringify({
    викликів_моделі: calls,
    картка_опис: card.опис === undefined ? null : card.опис,
    як_носити: card.як_носити,
    причини_записів: recs.map(x => x.причина),
    журнал_збоїв_жінці: vm.runInContext('ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П', context)
  }, null, 2));
})().catch(e => {console.error(e); process.exitCode = 1;});
