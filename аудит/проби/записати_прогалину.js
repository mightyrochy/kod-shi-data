/* Записує відсутній текстовий виклик локальною моделлю; прибирає лише власний екземпляр. */
const fs = require('fs'), path = require('path'), {execFileSync} = require('child_process');
const вибірка = require('./вибірка_запиту.js');
const {записатиОбмін, ключЗапиту} = require('./записаний_обмін.js');

async function виконати() {
  const [вхід, вихід] = process.argv.slice(2);
  if (!вхід || !вихід) throw Error('Потрібні файл відсутнього запиту й тека запису');
  const {запит} = JSON.parse(fs.readFileSync(вхід, 'utf8'));
  if (!запит || запит.messages.some(м => !Array.isArray(м.content) || м.content.some(б => б.type !== 'text')))
    throw Error('Прилад приймає лише записаний текстовий запит');
  const база = 'http://127.0.0.1:1234';
  const api = async (суфікс = '', тіло) => {
    const r = await fetch(база + '/api/v1/models' + суфікс, {
      method: тіло ? 'POST' : 'GET', headers: {'content-type': 'application/json'},
      body: тіло ? JSON.stringify(тіло) : undefined, signal: AbortSignal.timeout(300000)});
    const v = await r.json();
    if (!r.ok || v.error) throw Error(JSON.stringify(v));
    return v;
  };
  const до = await api();
  if (до.models.some(м => м.loaded_instances.length)) throw Error('Сервер тримає чужу модель');
  fs.mkdirSync(вихід, {recursive: true});
  const доказ = {початок: new Date().toISOString(), sha: execFileSync('git', ['rev-parse', 'HEAD'], {encoding: 'utf8'}).trim(),
    ключ: ключЗапиту(запит), до};
  let власний;
  try {
    const контекст = запит.model.startsWith('qwen/') ? 57344 : 16384;
    доказ.завантаження = await api('/load', {model: запит.model, context_length: контекст, parallel: 1, echo_load_config: true});
    власний = доказ.завантаження.instance_id;
    if (!власний || доказ.завантаження.status !== 'loaded') throw Error('Не завантажено екземпляр');
    const стан = await api();
    const екземпляр = стан.models.flatMap(м => м.loaded_instances).find(е => е.id === власний);
    if (!екземпляр || екземпляр.config.context_length !== контекст || екземпляр.config.parallel !== 1)
      throw Error('Не підтверджено контекст і parallel=1');
    доказ.запит_транспорту = {model: запит.model, messages: запит.messages, max_tokens: запит.max_tokens || 4000,
      stream: false, ...вибірка(запит, false, {сід: 3, темп: null, темпМови: null}), reasoning_effort: 'none'};
    console.log('Живий виклик: ' + доказ.ключ);
    const r = await fetch(база + '/v1/chat/completions', {method: 'POST', headers: {'content-type': 'application/json'},
      body: JSON.stringify(доказ.запит_транспорту), signal: AbortSignal.timeout(300000)});
    доказ.http = {status: r.status, headers: Object.fromEntries(r.headers), body: await r.text()};
    if (!r.ok) throw Error('Модель: HTTP ' + r.status);
    const дані = JSON.parse(доказ.http.body), вибір = дані.choices?.[0];
    if (!вибір || typeof вибір.message?.content !== 'string') throw Error('Нема текстової відповіді');
    const відповідь = {status: r.status, contentType: 'application/json', body: JSON.stringify({
      content: [{type: 'text', text: вибір.message.content}],
      usage: {input_tokens: дані.usage?.prompt_tokens || 0, output_tokens: дані.usage?.completion_tokens || 0},
      stop_reason: вибір.finish_reason === 'length' ? 'max_tokens' : 'end_turn'})};
    записатиОбмін(вихід, 1, запит, відповідь);
    console.log('Записано: HTTP ' + r.status + ', finish_reason=' + вибір.finish_reason);
  } finally {
    if (власний) доказ.вивантаження = await api('/unload', {instance_id: власний});
    доказ.після = await api();
    доказ.кінець = new Date().toISOString();
    fs.writeFileSync(path.join(вихід, 'джерело.json'), JSON.stringify(доказ, null, 1) + '\n');
  }
}
виконати().catch(е => {console.error(е); process.exitCode = 2;});
