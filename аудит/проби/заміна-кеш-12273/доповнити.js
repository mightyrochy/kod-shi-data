/* Один відсутній обмін через незмінений локальний транспорт штатного стенда. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const {execFileSync} = require('child_process');
const {постЖСОН} = require('../обрив_моста.js');
const {ключЗапиту, записатиОбмін, ЗаписанийОбмін} = require('../записаний_обмін.js');

async function доповнити(помилка, сцена, вихід) {
  const запит = JSON.parse(fs.readFileSync(помилка, 'utf8'));
  if (запит.код !== 'REPLAY_STALE') throw new Error('Потрібен штатний незавершений запит');
  const паспорт = JSON.parse(fs.readFileSync(path.join(сцена, 'повтор.json'), 'utf8'));
  const тіло = запит.запит, модель = тіло.model;
  if (модель !== паспорт.змінні.MODEL) throw new Error('Модель відрізняється від записаної');
  if (тіло.messages.some(м => !Array.isArray(м.content) || м.content.some(б => б.type !== 'text')))
    throw new Error('Цей крок доповнює лише текстовий запит заміни');
  const тека = path.join(сцена, 'VIDPOVIDI', 'обмін');
  const архів = new ЗаписанийОбмін(тека), ключ = ключЗапиту(тіло);
  if (архів.записи.some(з => з.ключ === ключ)) throw new Error('Точна відповідь уже є; живий виклик зайвий');
  const номер = Math.max(...архів.записи.map(з => Number(path.basename(з.ім, '.json')))) + 1;
  fs.mkdirSync(вихід, {recursive: true});
  const зберегти = (ім, дані) => fs.writeFileSync(path.join(вихід, ім), JSON.stringify(дані, null, 1) + '\n');
  const gpu = () => execFileSync('nvidia-smi', ['--query-gpu=name,memory.total,memory.used',
    '--format=csv,noheader'], {encoding: 'utf8', windowsHide: true}).trim();
  const адреса = 'http://127.0.0.1:1234';
  const стан = await (await fetch(адреса + '/api/v0/models')).json();
  зберегти('моделі-до.json', стан);
  if (стан.data.some(м => м.state === 'loaded')) throw new Error('Інша завантажена модель: потрібен вільний GPU');
  const контекст = JSON.parse(паспорт.змінні.CTX)[модель];
  const завантаження = await постЖСОН(адреса + '/api/v1/models/load', {
    model: модель, context_length: контекст, flash_attention: true,
    offload_kv_cache_to_gpu: true, echo_load_config: true,
  });
  зберегти('завантаження.json', завантаження);
  if (завантаження.статус !== 200) throw new Error('Не завантажено модель: ' + завантаження.сире);
  const екземпляр = JSON.parse(завантаження.сире).instance_id;
  try {
    const код = fs.readFileSync(path.join(__dirname, '..', 'рв6_стенд.js'), 'utf8');
    const початок = код.indexOf('async function живоюМоделлю(');
    const кінець = код.indexOf('/* ── ОДИН ВИКЛИК МОДЕЛІ ЧЕРЕЗ', початок);
    if (початок < 0 || кінець < 0) throw new Error('Не знайдено транспорт штатного стенда');
    const журнал = [], запити = [], відповіді = [];
    const живою = vm.runInNewContext(код.slice(початок, кінець) + '\nживоюМоделлю;', {
      Date, process: {env: паспорт.змінні},
      ПРАВИЛА_РЕЧЕННЯМИ: false, КЛОД_ШВОМ: false, ШАР_ВИМКНЕНО: false,
      МОДЕЛЬ_МОВИ_СТЕНДУ: паспорт.змінні.MODEL_MOVA, МОДЕЛЬ_ЖИВА: модель,
      АДРЕСА_МОДЕЛІ: адреса + '/v1', СІД: паспорт.сід,
      ТЕМПЕРАТУРА: null, ТЕМПЕРАТУРА_МОВИ: null,
      ВИБІРКА_ЗАПИТУ: require('../вибірка_запиту.js'), ЖУРНАЛ_МОДЕЛІ: журнал,
      постЖСОН: async (url, дані, держак) => {
        запити.push(дані);
        зберегти('запит-lmstudio.json', дані);
        const р = await постЖСОН(url, дані, держак);
        відповіді.push(р);
        зберегти('відповідь-lmstudio.json', р);
        return р;
      },
    });
    const відеокарта = gpu(), початокUTC = new Date().toISOString();
    console.log('Живий виклик', запит.виклик, модель, 'sha256=' + ключ, відеокарта);
    зберегти('початок.json', {початокUTC, модель, контекст, відеокарта, ключ});
    const р = await живою(тіло, запит.тип, {});
    зберегти('модель.json', журнал);
    if (запити.length !== 1 || відповіді.length !== 1 || р.статус !== 200 || !р.текст)
      throw new Error('Один успішний живий виклик не підтверджено: ' + JSON.stringify(р));
    const відповідь = {status: 200, contentType: 'application/json', headers: {'x-model': модель},
      body: JSON.stringify({content: [{type: 'text', text: р.текст}],
        usage: {input_tokens: р.вхід, output_tokens: р.вихід}, stop_reason: р.стоп})};
    записатиОбмін(тека, номер, тіло, відповідь);
    записатиОбмін(path.join(вихід, 'обмін'), номер, тіло, відповідь);
    зберегти('результат.json', {початокUTC, кінецьUTC: new Date().toISOString(), модель,
      контекст, відеокарта, gpu_після: gpu(), ключ, виклик: запит.виклик, номер,
      живих_викликів: запити.length, с: р.с, текст: р.текст, стоп: р.стоп});
    console.log('Збережено точний обмін', номер, р.с, 'с:', р.текст);
  } finally {
    зберегти('вивантаження.json', await постЖСОН(адреса + '/api/v1/models/unload', {instance_id: екземпляр}));
  }
}

if (require.main === module) доповнити(...process.argv.slice(2)).catch(п => {
  console.error(п); process.exitCode = 1;
});
