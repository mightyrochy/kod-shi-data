/* Незалежна проба мовного шару: справжній Python-шов і JS голови PR;
   модель замінена детермінованою відмовою 402 credits_exhausted. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const {spawnSync} = require('child_process');
const root = path.resolve(process.argv[2]), src = path.join(root, 'джерела');
let calls = 0;
const context = vm.createContext({console, МОДЕЛЬ_МОВИ_П: 'claude-sonnet-5-5',
  НАЛАШТУВАННЯ_РУШІЯ_П: {}, МАКС_ТОКЕНІВ_П: 4000,
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
  const result = await vm.runInContext(`повідомленнямП({рядок: {kind: 'card_occasion', statements: [
    {code: 'mourning_colour_word_only', item_ids: ['а'], choice: 'her', recipient: 'woman',
     source: 'catalogue', rank: {position: 1, rare: false},
     values: {item: {free_text: 'Сукня', lang: 'uk'}}}]}}, 'перевірка-кредитів')`, context);
  console.log(JSON.stringify({викликів_моделі: calls, текст_жінці: result.тексти,
    причини: result.записи.map(x => x.причина),
    журнал_збоїв_жінці: vm.runInContext('ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П', context)}, null, 2));
})().catch(e => {console.error(e); process.exitCode = 1;});
