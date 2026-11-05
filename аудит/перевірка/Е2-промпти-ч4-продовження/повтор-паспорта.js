/* Звіряє справжню функцію показу до й після на запиті справжнього збирача. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const корінь = path.resolve(__dirname, '../../..');
const файл = 'джерела/показ/паспорт.js';
const база = process.argv[2];
const до = execFileSync('git', ['show', `${база}:${файл}`], {cwd: корінь, encoding: 'utf8'});
const після = fs.readFileSync(path.join(корінь, файл), 'utf8');
const промпт = execFileSync('python', ['-c',
  "import sys; sys.path.insert(0, 'джерела'); import паспорт_нагоди as п; print(п.промпт_паспорта({}, 'На роботу, без декольте'))"],
  {cwd: корінь, encoding: 'utf8', env: {...process.env, PYTHONUTF8: '1'}}).trim();
const запит = JSON.parse(промпт);
assert.ok(JSON.stringify(запит).includes('відповідь_людині'));

async function прогін(текст, причина, фото, другаВідмова){
  const запити = [], входи = [];
  const контекст = {
    живийХідП: () => () => true,
    вхідМостаП: () => ({сценарій: {}, вимоги: 'На роботу', вето: {зони: ['декольте']}}),
    реплікиСценарію: () => [{хто: 'людина', текст: 'На роботу'}],
    текстРепліки: р => р.текст,
    новіФотоРечейП: () => фото,
    ПАСПОРТ_П: null, СТОРОНА_ФОТО_РЕЧІ_П: 1024, ВИБІРКА_П: {},
    фотоДляЗапитуП: async ф => ф,
    записатиВикликРозмовиП: () => {}, малюватиТокениП: () => {},
    модельП: async (п, ф) => {запити.push({п, ф}); return 'recorded response';},
    містП: async (ім, д) => {
      входи.push(д);
      if (д.json_моделі == null) return {промпт};
      const відмова = входи.length === 2 || другаВідмова;
      return {паспорт: {джерело: відмова && причина === 'json' ? 'плитки' : 'модель',
                       потрібен_повтор: відмова && причина === 'field'},
              помилка_формату: причина === 'json' ? 'invalid_json(line=1,col=1)' : ''};
    },
  };
  vm.createContext(контекст);
  vm.runInContext(текст.slice(текст.indexOf('async function паспортПоРозмовіП'),
    текст.indexOf('/* ДОВІДНИК ЖИВИМ ЕНДПОЙНТОМ')), контекст);
  await контекст.паспортПоРозмовіП();
  assert.equal(запити.length, 2);
  assert.equal(запити[0].п, промпт);
  for (const д of входи) assert.deepEqual(д.вето.зони, ['декольте']);
  for (const з of запити) assert.equal(з.ф, фото.length ? фото : null);
  return запити[1].п;
}

(async () => {
  for (const причина of ['json', 'field']) for (const фото of [[], [{ід: 'ф1', дані: 'photo'}]])
    for (const другаВідмова of [false, true]) {
      const старий = await прогін(до, причина, фото, другаВідмова);
      const новий = await прогін(після, причина, фото, другаВідмова);
      assert.ok(новий.startsWith(промпт));
      assert.ok(новий.length < старий.length);
      assert.match(новий.slice(промпт.length), причина === 'json' ? /invalid_json/ : /відповідь_людині/);
      console.log(`${причина}, фото=${фото.length}, друга відмова=${другаВідмова}: ${старий.length} → ${новий.length}; дві спроби, вето й фото збережені`);
    }
})().catch(п => {console.error(п); process.exitCode = 1;});
