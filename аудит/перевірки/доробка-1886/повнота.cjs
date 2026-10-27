/* Записаний ж2: справжні промпт, розбір і показ; підмінена лише модель. */
const fs = require('fs'), vm = require('vm'), cp = require('child_process'), assert = require('assert');
const path = require('path'), root = path.resolve(__dirname, '../../..');
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, 'вхід.json'), 'utf8'));
const before = process.argv[2];
const source = before ? cp.execFileSync('git', ['show', before + ':джерела/показ/мовний_шар.js'], {cwd: root, encoding: 'utf8'})
  : fs.readFileSync(path.join(root, 'джерела/показ/мовний_шар.js'), 'utf8');
async function run(mode) {
  const calls = [];
  const ctx = vm.createContext({МОДЕЛЬ_МОВИ_П: 'підмінена', console});
  ctx.містП = async (_, input) => {
    const py = before ? 'import sys, subprocess, types; М=types.ModuleType("попередній_шар"); exec(compile(subprocess.check_output(["git","show",sys.argv[1]+":джерела/мовний_шар.py"]),"попередній_шар.py","exec"),М.__dict__); print(М.мова(sys.stdin.read()))'
      : 'import sys, мовний_шар as М; print(М.мова(sys.stdin.read()))';
    const result = cp.spawnSync('python', ['-c', py, ...(before ? [before] : [])],
      {cwd: path.join(root, 'джерела'), input: JSON.stringify(input), encoding: 'utf8', env: {...process.env, PYTHONIOENCODING: 'utf-8'}});
    assert.equal(result.status, 0, result.stderr);
    const answer = JSON.parse(result.stdout);
    if (input.повідомлення) calls.push(answer);
    return answer;
  };
  vm.runInContext(source, ctx);
  ctx.модельМовиП = async () => {
    if (mode === 'записана') return fixture.ж2.відповідь_моделі;
    if (mode === 'без_тексту') return '';
    const rows = calls.at(-1).розмітка;
    return JSON.stringify(Object.fromEntries(rows.filter((_, i) => mode === 'часткова' && i % 2 === 0)
      .map(row => [row.ключ, 'Я ще не маю потрібних відомостей.'])));
  };
  const result = await ctx.повідомленнямП(fixture.ж2.вхід, 'hand_2.code_unknowns');
  assert(calls.length > 0);
  assert(result.записи.every(z => !String(z.причина).startsWith('layer_failed')));
  const missing = result.заяви.filter(row => row.стан !== 'translated');
  const keys = result.заяви.map(row => row.ключ);
  assert.equal(keys.length, 19); assert.equal(new Set(keys).size, 19);
  for (const row of missing) assert(result.записи.some(z => z.без_відповіді.includes(row.ключ)));
  for (const row of result.заяви) assert.equal(row.показано, true);
  assert.equal(Object.keys(result.тексти).length, Object.keys(fixture.ж2.вхід).length);
  console.log(mode, 'перекладено', keys.length - missing.length, '/', keys.length, 'явно без тексту', missing.length);
  assert.equal(missing.length, mode === 'часткова' ? 4 : mode !== 'записана' || before ? 19 : 0);
  if (mode === 'записана') {
    if (!before) assert(result.записи[0].нотатки.includes('missing_commas_read'));
  }
}
(async () => { for (const mode of ['часткова', 'порожня', 'без_тексту', 'записана']) await run(mode); })()
  .catch(e => { console.error(e); process.exitCode = 1; });
