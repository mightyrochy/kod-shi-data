/* Е2-межі п.3 класу — запасна порада після невдалого повтору (рішення менеджера 30.10, рядки 9860, 10082).
   Записані ходи корпусу (`проби/дані/картка_запиту.json`) → справжній шов `мова` (паспорт_з) → ходи, де суд п.9 зняв
   пораду й шов планує повтор (`ремонт_поради`). Кожен такий хід — через справжній `порадоюП` показу двома збоями
   повтору: «знято» — модель повторює ту саму ваду (запрошення ходу ще раз, без нього — порожня відповідь), «збій» —
   виклик моделі кидає. Лічить ходи, де після повтору поради жінка не бачить (теми порожні, тексту поради нема), і
   звіряє запасну: теми — з дозволених, до трьох, ще не дані; `поради_дані` їх містить; текст проходить сторожа мови.
   Запуск (з кореня): node джерела/проби/е2_запасна_порада.js; ДО — E2_SOURCES=<тека джерел бази>. Код 1 — є втрати. */
const fs = require('fs'), path = require('path'), vm = require('vm'), {spawnSync} = require('child_process');
const root = path.resolve(__dirname, '../..'), src = process.env.E2_SOURCES || path.join(root, 'джерела');
const py = (код, дані) => {
  const r = spawnSync(process.env.PYTHON || 'python3', ['-X', 'utf8', '-c', код, src],
    {input: JSON.stringify(дані), encoding: 'utf8', maxBuffer: 64000000, cwd: path.join(root, 'джерела')});
  if (r.status) throw Error(r.stderr);
  return JSON.parse(r.stdout);
};
const МІСТ = 'import sys,io,contextlib;sys.path.insert(0,sys.argv[1])\nwith contextlib.redirect_stdout(io.StringIO()):' +
  ' import мовний_шар as М\nprint(М.мова(sys.stdin.read()))';
const ХОДИ = 'import sys,io,json,contextlib;sys.path.insert(0,sys.argv[1])\nwith contextlib.redirect_stdout(io.StringIO()):' +
  ' import мовний_шар as М\nвих=[]\nfor з in json.load(open("проби/дані/картка_запиту.json",encoding="utf8")):\n' +
  ' if з["вид"]!="розмова": continue\n п=М.прийняти_розмову(json.dumps(з["відповідь"],ensure_ascii=False))\n' +
  ' вих.append(dict(джерело=з["джерело"],слова=з["запит"].get("her_new_message",""),внутрішня=п.get("внутрішня") or {},' +
  'частини=п.get("частини") or {},теми=(з["відповідь"].get("invite_topics") or [])))\nprint(json.dumps(вих,ensure_ascii=False))';
async function main(){
  const ходи = py(ХОДИ, null);
  const міст = async (_, дані) => py(МІСТ, дані);
  const c = vm.createContext({console, Date, МОДЕЛЬ_МОВИ_П: 'запис', ПАСПОРТ_П: null, ЧАТ_П: [], містП: міст,
    вхідМостаП: () => ({сценарій: {}}), текстРепліки: р => р.текст});
  vm.runInContext(fs.readFileSync(path.join(src, 'показ/мовний_шар.js'), 'utf8'), c);
  const л = {ходів: ходи.length, з_повтором: 0}, вади = [];
  for (const вид of ['знято', 'збій']) Object.assign(л, {[вид + ': без поради']: 0, [вид + ': запасна']: 0});
  for (const х of ходи){
    const пш0 = await міст('мова', {паспорт_з: х.внутрішня, сценарій: {}, слова_розмови: [х.слова], частини: х.частини});
    if (!пш0.ремонт_поради) continue;
    л.з_повтором++;
    for (const вид of ['знято', 'збій']){
      const пш = JSON.parse(JSON.stringify(пш0)), хід = {запис: {}}, рем = пш.ремонт_поради;
      c.модельМовиП = async () => {
        if (вид === 'збій') throw Error('model_unavailable');
        return JSON.stringify(рем.запрошення ? {invite_topics: х.теми, invite: рем.запрошення} : {});
      };
      await c.порадоюП(пш, хід, х.слова);
      const теми = пш.теми_поради || [];
      if (!теми.length || !пш.запрошення){ л[вид + ': без поради']++; continue; }
      if (!хід.запис.ремонт_поради.запасна) continue;
      л[вид + ': запасна']++;
      const дані = пш0.паспорт.поради_дані || [];
      const чужі = теми.filter(т => !рем.дозволені.includes(т));
      const стан = typeof c.станТекстуЖінціП === 'function' ? c.станТекстуЖінціП(пш.запрошення) : 'translated';
      if (чужі.length || теми.length > 3 || !пш.текст.endsWith(пш.запрошення) || стан !== 'translated'
          || теми.length !== (пш.паспорт.поради_дані || []).length - дані.length)
        вади.push({джерело: х.джерело.slice(-70), вид, теми, чужі, стан, текст: пш.текст});
    }
  }
  const приклад = ходи.length && c.порадаШаблономП ? c.порадаШаблономП(['goal', 'makeup', 'jewelry']) : '';
  console.log(JSON.stringify(Object.assign(л, {вад_запасної: вади.length, приклад}), null, 1));
  вади.slice(0, 5).forEach(в => console.log(JSON.stringify(в)));
  const втрат = л['знято: без поради'] + л['збій: без поради'];
  console.log('втрат поради після повтору:', втрат, '· вад запасної:', вади.length);
  process.exitCode = втрат || вади.length ? 1 : 0;
}
main().catch(e => { console.error(e); process.exitCode = 1; });
