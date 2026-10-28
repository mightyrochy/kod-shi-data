/* ── ЕКРАН ВИПАДКУ Й ПАКЕТ ВХІД-V1 ────────────────────────────────────────
   Таблиці нагод/місць/кодів — НЕ копія, а вивід `pipeline.довідник()`, який
   збирач підставляє сюди на місце плейсхолдера (Т-08 крок 3, Н-outfit-2-093).
   Доти тут стояв рукописний літерал, і він розійшовся з кодом на шести межах:
   жінка читала «Візьмемо: ошатність — …» з копії, а суд ішов за `outfit`.
   Тепер (наряд 3.7) смуги — лише щаблі драбини `формальність.ДРАБИНА`, слова —
   `pipeline.ДОВІДНИК_ПІДПИСИ`. Плитки, списки й слово ошатності беруть лише
   рядки з `плитка: true` (зріз для людини); повний перелік ключів лишається в
   таблиці, бо паспорт із чату може принести будь-який із них, і `знайти`
   мусить його впізнати. Вільні слова не тлумачаться тут: їх зводить у ключі
   ші у виклику 0 за тим самим довідником. */


function людяно(к){ return String(к||'').replace(/_/g,' '); }
/* Нагоди — плитки, не список: сім основних напрямків і «Інше» (НГ-5, власник 28.09 і 02.10:
   плитки — швидкий допоміжний вхід, «не мають бути громіздкими»); решту нагод — весілля,
   траур, церкву… — приносить розмова. Значки весілля й трауру лишаються для підсумку
   сценарію, коли таку нагоду поставила розмова. */
const ІКОНИ_НАГОД = {'щоденне':'день', 'робота':'робота', 'побачення':'побачення', 'свято':'свято',
  'театр':'театр', 'весілля_гість':'весілля', 'траур':'траур', 'спорт':'спорт', 'подорож':'подорож'};
/* «Інше» списку нагод «Оціни» — не ключ довідника: нагоду каже її слово в «Що хочеш знати?» (НГ-5) */
const ІНШЕ_ОЦІНКИ_П = 'інше';
const ОПАДИ = [['ні','Без опадів','сонце'], ['можливий_дощ','Можливий дощ','дощ'], ['дощ','Дощ','дощ'],
               ['сніг','Сніг','сніг']];
/* ВІДЧУТТЯ ПОГОДИ БЕЗ ГРАДУСІВ. З ПОГОДИ «надворі мороз» стає `погода_відчуття: frost` без
   числа (`темп_c` — None), а рядок «Коли й погода» читав лише поле градусів — типові +18 °C — і казав жінці
   протилежне її словам. Коди — `внутрішня_мова.ТАБЛИЦЯ["weather_feel"]`; підписи — сталі, як у плиток опадів. */
const ВІДЧУТТЯ_П = {frost: 'мороз', cold: 'холодно', cool: 'прохолодно', warm: 'тепло', hot: 'спекотно'};
/* підпис відчуття: те, що вона обрала плиткою (`сц-відчуття`), важить над паспортом; інакше — з паспорта, поки
   градусів вона не назвала (поле градусів типове); інакше null */
function ключВідчуттяП(){
  const рука = ($('сц-відчуття') || {}).value;
  if (ВІДЧУТТЯ_П[рука]) return рука;
  const п = типовеЧислоП('сц-темп') ? паспортКартки() : null;
  return (п && ВІДЧУТТЯ_П[п.погода_відчуття]) ? п.погода_відчуття : null;
}
function відчуттяКарткиП(){ return ВІДЧУТТЯ_П[ключВідчуттяП()] || null; }
/* Плитки відчуття в «Коли й погода» (п.9 — явний вибір дотиком, градусів знати не треба). Дотик ставить
   відчуття, знімає з поля градусів типове число (воно стає порожнім, як при слові паспорта) і виправляє паспорт
   моделі, що вже стоїть у стані (`ПАСПОРТ_П`): `сценарій.з_показу` віддає перевагу паспорту над плиткою, тож без
   цього «мороз» зі слів перебивав би її «холодно». Повторний дотик по обраному знімає вибір. */
function обратиВідчуттяП(ключ){
  const поле = $('сц-відчуття'), нове = (ключВідчуттяП() === ключ) ? '' : ключ;
  поле.value = нове; рукаТоркнуласьП('сц-відчуття');
  if (нове){ $('сц-темп').value = ''; подіяРукиП('темп_c', null); }
  малюватиПлитки(); малюватиКарткуСценарію(); зберегтиВипадок();
}
function позначитиВідчуттяП(){
  const к = ключВідчуттяП();
  document.querySelectorAll('#сц-відчуття-плитки .плитка').forEach(п => { п.classList.toggle('вибр', п.dataset.ключ === к); станВиборуП(п); });
}
/* «ХАЙ ОБЕРЕ СТИЛІСТКА» — СВІДОМИЙ ВИБІР, А НЕ ПОРОЖНЕЧА.
   Слова — ті самі, що на екрані палітри (аудит/ПРОДУКТ.md п.7: слова «ші» в текстах для
   людини нема). Різниця з палітрою одна й навмисна: там чип стоїть підсвіченим, коли
   вибору НЕМА, а тут ключ лягає в поле випадку й переживає повернення на екран — бо
   «я віддала це коду» і «я сюди не дійшла» мають виглядати по-різному. У міст ключ не
   їде ніколи: паспорт знає «невідомо», і саме його код і дістає. */
const СТИЛІСТКА_КЛЮЧ = 'стилістка', СТИЛІСТКА_СЛОВО = 'хай обере стилістка';
/* Рівні макіяжу — слова K-CLR-03 («помітний макіяж = +1 крок контрасту біля обличчя»)
   і R-MUA-04 («яскравий» уже тримає фокус на обличчі). Ключі читає `face_contrast`;
   `стилістка` ключем рівня НЕ Є і до `зібратиВхід` не доходить. */
const МАКІЯЖ = [...ДОВІДНИК.плитки_поради.makeup, [СТИЛІСТКА_КЛЮЧ, СТИЛІСТКА_СЛОВО, null]];
/* СТАНИ ПОЛЯ ГУБ — ЇХ ТРИ, І ВСІ ТРИ В ОДНОМУ `сц-губи-обрано`:
   '' — вона сюди не дійшла; `СТИЛІСТКА_КЛЮЧ` — свідомо віддала рішення коду;
   `ГУБИ_НАЗВАНО_П` — назвала відтінок (зі сходинки або своїм вибором кольору).
   КОДУ перші два стани дають те саме: `зібратиВхід` кольору не шле, і важіль
   K-CLR-03 бере крок контрасту сталим — поведінка не змінилась. ЖІНЦІ вони
   різні: показ памʼятає вибір, і рядок картки називає його словом. */
const ГУБИ_НАЗВАНО_П = '1';
const губиСтанП = ()=> (($('сц-губи-обрано')||{}).value || '');
const губиНазваноП = ()=> губиСтанП() === ГУБИ_НАЗВАНО_П;
/* ПРИКРАСИ З ЦИМ ОБРАЗОМ — шість слів рядка «Прикраси». Перші п'ять мусять збігатися з
   `паспорт_нагоди.ПРИКРАСИ_БАЖАННЯ` (мінус «інші»: це залишковий клас для слів РОЗМОВИ,
   рукою його не обирають — «без металу» рука каже словами «перли» або «етно»); слово,
   якого нема в тому переліку, `паспорт_нагоди` мовчки викине, і рядок перестане бути
   полем, лишившись на екрані. Шостий — свідоме «хай обере стилістка». */
/* МЕТА ОБРАЗУ — ДВІ ОСІ (рішення власника «3б»). Ключі — коди паспорта (`паспорт_нагоди`:
   «мета» — вісь уваги, «мета_важливо», «мета_зони»), слова й ноти — сталі написи показу. Нота каже, що плитка
   справді міняє (правило з входом у доборі чи суді, п.4). Доти — чотири плитки одним вибором: «Щоб личило» стало
   «Звично», «Не привертати уваги» — «Тихо», «Щоб дивились» — «Помітно», «Здаватись вищою» — «Довша лінія». */
const МЕТА_П = ДОВІДНИК.плитки_поради.goal;
const МЕТА_ВАЖЛИВО_П = ДОВІДНИК.плитки_поради.goal_extra;
const МЕТА_ЗОНИ_КЛЮЧ_П = 'зони', МЕТА_ЗОНИ_СЛОВО_П = 'Відвести погляд від…';
/* Зони — слова переліку `goal_zone`; родовий відмінок для рядка картки, називний — для чипа (сталі написи). */
const МЕТА_ЗОНИ_П = {живіт:'живота', стегна:'стегон', груди:'грудей', руки:'рук', ноги:'ніг',
  плечі:'плечей', декольте:'декольте', спина:'спини'};
const МЕТА_ЗОНИ_ЧИП_П = {живіт:'Живіт', стегна:'Стегна', груди:'Груди', руки:'Руки', ноги:'Ноги',
  плечі:'Плечі', декольте:'Декольте', спина:'Спина'};
let МЕТА_ЗОНИ_ВІДКРИТО_П = false;
function списокПоляП(ід){ return String(($(ід)||{}).value || '').split(',').map(x=>x.trim()).filter(Boolean); }
function метаСловомП(){
  const ч = [], у = (МЕТА_П.find(([к])=>к === ($('сц-мета')||{}).value) || [])[1];
  if (у) ч.push(у);
  списокПоляП('сц-мета-важливо').forEach(к=>{ const с = (МЕТА_ВАЖЛИВО_П.find(([кк])=>кк === к) || [])[1];
    if (с) ч.push(ч.length ? с.toLowerCase() : с); });
  const з = списокПоляП('сц-мета-зони').map(з=>МЕТА_ЗОНИ_П[з]).filter(Boolean);
  if (з.length) ч.push((ч.length ? 'відвести' : 'Відвести') + ' погляд від ' + з.join(' і '));
  return ч.join(' · ');
}
/* Запис до 15.10 (одна вісь) — на дві осі без втрат, як `паспорт_нагоди.мета_на_осі`: «вище» → «звично» +
   «довша лінія»; паспорт «приховати» із зоною без `мета_важливо` (тоді це була лише зона) → увага «невідомо». */
function метаНаОсіП(п){
  if (!п || typeof п !== 'object') return п;
  const новий = Array.isArray(п.мета_важливо);
  const важл = (п.мета_важливо || []).filter(к=>МЕТА_ВАЖЛИВО_П.some(([кк])=>кк === к));
  if (п.мета === 'вище'){ п.мета = 'лестити'; if (!важл.includes('вище')) важл.push('вище'); }
  else if (!новий && п.мета === 'приховати' && (п.мета_зони || []).some(з=>з in МЕТА_ЗОНИ_П)) п.мета = 'невідомо';
  if (новий || важл.length || п.мета != null) п.мета_важливо = важл;
  return п;
}
const ПРИКРАСИ_П = [...ДОВІДНИК.плитки_поради.jewelry, [СТИЛІСТКА_КЛЮЧ, СТИЛІСТКА_СЛОВО, null]];
/* ЗОНИ ВЕТО — ЧИПИ, А НЕ ЛИШЕ СЛОВА (Т-09). Словник закритий і мусить збігатися з
   `pipeline.ЗОНИ_ВЕТО`: чип, якого нема в тому списку, `bridge._застосувати_паспорт`
   мовчки викине, і межа перестане бути межею, лишившись на екрані. Гейт §126 звіряє
   ці два списки, бо вони написані різними мовами в різних файлах. */
const ЗОНИ_ВЕТО_П = ['декольте','спина','руки','плечі','ноги','живіт'];
/* ЗОНА ЛЮДСЬКОЮ ФРАЗОЮ. Плитка більше не
   зветься «Не відкривати», а «Не хочу» — і під цією назвою голе слово читається
   навиворіт: «Не хочу: ноги». Зона — це не частина тіла, від якої вона
   відмовляється, а ВІДКРИТА частина тіла. Той самий зворот уже пише рядок над
   образами («не відкриваємо ноги»), тут він просто іменником.
   КЛЮЧ НЕ МІНЯЄТЬСЯ: у `сц-вето-зони` й у паспорті лежить те саме слово, що й
   доти, — міняється лише те, що бачить жінка. */
const ЗОНА_ЛЮДИНІ_П = {декольте:'глибоке декольте', спина:'відкрита спина',
  руки:'відкриті руки', плечі:'відкриті плечі', ноги:'відкриті ноги',
  живіт:'відкритий живіт'};
const зонаЛюдині = з => ЗОНА_ЛЮДИНІ_П[з] || з;
function зониВето(){
  return (($('сц-вето-зони')||{}).value||'').split(',').map(з=>з.trim()).filter(Boolean);
}

/* ── ЧИПИ ВЕТО ВСІХ П'ЯТИ КАТЕГОРІЙ, А НЕ ЛИШЕ ЗОН (Т-08 крок 4) ───────────
   Зони — закритий словник (`pipeline.ЗОНИ_ВЕТО`), і чип там ПЕРЕМИКАЧ. Типи,
   тканини, принти й кольори приходять вільними словами з паспорта: їх звела зі
   слів жінки модель, і закритого списку під них нема. Тому чип там ЗНІМАЄ межу,
   а не ставить: нове слово вона каже в чаті або пише в полі «своїми словами», а
   от почуте помилково («без підборів», коли йшлося про підбори на весіллі
   сестри) мусить зніматись одним дотиком — інакше межа, якої вона не ставила,
   мовчки ріже пул.
   ЩО САМЕ ЗНІМАЄТЬСЯ, ВИДНО НА ЕКРАНІ. Доти ці чотири списки жили лише всередині
   паспорта: `bridge._застосувати_паспорт` розгортав їх у `жорстке_ні` (абсолютний
   фільтр composer), а жінка не бачила ні слова з них. */
const КАТЕГОРІЇ_ВЕТО_П = [['типи','речі'], ['тканини','тканини'],
                          ['принти','принти'], ['кольори','кольори']];
let ЗНЯТІ_ВЕТО_П = [];
const _ключВетоП = (к, з)=> к + '\u00b7' + String(з).trim().toLowerCase();
function почиститиВетоП(п){
  if (!п || !п.вето) return п;
  /* ДОТИК ЗНІМАЄ МЕЖУ В ОБОХ ПЕРЕЛІКАХ: `вето` — усе, що стиліст
     почув (його й малює картка), `вето_тверде` — те, що код тримає. Почистити
     лише перший означало б лишити зняте діяти на пул. */
  [п.вето, п.вето_тверде].forEach(сп=>{
    if (!сп) return;
    ['типи','тканини','принти','кольори','зони'].forEach(к=>{
      if (Array.isArray(сп[к]))
        сп[к] = сп[к].filter(з=>ЗНЯТІ_ВЕТО_П.indexOf(_ключВетоП(к, з)) < 0);
    });
  });
  return п;
}
/* ── РОЗМОВА — ОДНА НА ВЕСЬ ПОКАЗ (інтерфейс v4.2) ───────────────────────────
   ПРИНЦИП. Поле розмови стоїть у панелі внизу на КОЖНОМУ екрані, і стрічка одна.
   На сценарії поле розгорнуте завжди, а стрічка переїжджає В САМ ЕКРАН
   (`розмістити_стрічку`): там розмова — головна річ. Деінде поле згорнуте в
   пілюлю з останньою відповіддю; тап розгортає стрічку й поле. Що з написаним
   робиться — залежить від того, де людина:
   · на екрані сценарію її слова — замовлення: вони йдуть у виклик 0 і стають
     паспортом (`pipeline.СХЕМА_ПАСПОРТА`), картка сценарію перемальовується з
     нього, а відповідь моделі (`відповідь_людині` + `питання_людині`) — у
     стрічку. Той самий виклик дістає ДОВІДКУ про застосунок і СТАН екрана, тож
     питання про інтерфейс на цьому екрані теж має відповідь;
   · деінде (профіль, знайомство, палітра, образи, очікування) її слова — це
     питання до помічниці, яка знає застосунок цілком (`ШІ_ДОВІДКА`) і бачить,
     що заповнено (`станДляШі`). Паспорт вона НЕ чіпає.
   Репліки несуть `тема`: «сценарій» або «довідка». У виклик 0 їде лише розмова
   про сценарій — питання «навіщо обхват голови» не має ставати вимогою до образу.

   ЧОГО ТУТ НЕМА НАВМИСНО: тлумачення вільних слів. Сторінка не здогадується, що
   «в ресторані» — це `місце=ресторан_районний`; ключі зводить модель за тим самим
   `довідник()`, з якого намальовані плитки. Показ лише ставить те, що вже стало
   ключем, і мовчить про те, що ним не стало. */
/* ── БЕЗ МЕЖІ РЕПЛІК, АЛЕ ЗІ СТЕЛЕЮ ПРОМПТА ──────────
   Межі реплік нема навмисно (16.09: чат — головний вхід), і вона не з'явилась: розмова
   не обривається й на сотому ході. Росла інша річ — ДОВЖИНА ЗАПИТУ: виклик 0 віз усю
   стрічку сценарію дослівно (`паспортПоРозмовіП.історія`), тож 413 від мосту
   (`СТЕЛЯ_ВХОДУ_СИМВ`) і квота були питанням часу. Стеля тепер стоїть окремим полем і не
   тут, а там, де промпт складається: `паспорт_нагоди.ВІКНО_РОЗМОВИ` — останні репліки
   дослівно плюс зведення старших (суть старших ходів уже несе `паспорт_досі`). Виміряно
   `проби/вікно_розмови_164.py`: 30 ходів 4569 → 3661 токенів, 100 ходів 9784 → 3757,
   далі не росте. Це число реплік НЕ обмежує — не плутати одне з одним. */
const ЧАТ_ЛІМІТ_П = 1e9; /* чат — головний вхід, без ліміту реплік */
let ЧАТ_П = [];                    // [{хто:'людина'|'ші', текст, тема:'сценарій'|'довідка', голосом?}] — одна стрічка
/* Мовний шар: теми поради, які стилістка запропонувала останнім ходом, —
   контекст для перекладача наступної репліки: коротка відповідь («так», «золото»)
   стосується саме їх. Новий чи відновлений сценарій їх скидає. */
let ОСТАННІ_ТЕМИ_П = [];
/* ЧИ ЦЮ РЕПЛІКУ НАДИКТОВАНО. Прапорець ставить голос, знімає
   порожнє поле: продиктоване й стерте рукою — це вже не диктування. У журнал
   він їде на САМІЙ репліці (`чат`), а не колонкою: надиктувати можна одну з трьох. */
let ЧАТ_ГОЛОСОМ_П = false;
let ВИПАДОК_ЗМІНЕНО_П = true;      // чи торкались екрана після останнього паспорта
/* хід плиток мовної моделі (НП-в5, `хідПлитокП`): обіцянка під ключ плиток і її запис для звіту */
const ХІД_ПЛИТОК_П = {ключ: null, обіцянка: null, таймер: null};
/* КАРТ-1: паспорт, зібраний із ходу плиток у фоні (число ошатності мовної моделі), щоб картка сценарію не чекала
   «Зібрати образи». Живе рівно доти, доки плитки ті самі (`ключ` = `ключПлитокП()`). */
let ПАСПОРТ_ПЛИТОК_П = null;
let ЗАПИС_ПЛИТОК_П = null;
const ПОЛЯ_ХОДУ_ПЛИТОК_П = ['formality', 'formality_branch', 'part_of_day', 'reserved_colour', 'open_zones'];
let ВИПАДОК_ПІДТВЕРДЖЕНО_П = false;
let ШІ_РОЗГОРНУТО = false;         // поза сценарієм: стрічка й поле розгорнуті з пілюлі
let КАРТКА_РУКОЮ = false;          // людина попросила показати картку сценарію, поки в ній порожньо
const ФОТО_Є = {портрет:false, зріст:false};   // що лежить у слотах — для рядка стану ші
const темаРепліки = р => (р && р.тема) || 'сценарій';

function людськихРеплікП(){ return ЧАТ_П.filter(р=>р.хто === 'людина').length; }
function реплікиСценарію(){ return ЧАТ_П.filter(р=>темаРепліки(р) === 'сценарій'); }

/* ── ФОТО РЕЧІ В РОЗМОВІ ─────────────────
   «Потрібно в головний діалог додати можливість додавання фото речей. Щоб людина
   могла запитати, чи підійде мені ця річ і з чим її носити.» Фото лежить НА
   ТЕЛЕФОНІ — у самій репліці стрічки, тож його несуть ті самі чернетка й бібліотека
   сценаріїв, що вже несуть розмову (`станСценарію`), і окремого сховища нема.
   Зменшується тим самим `блобВБазу`, що й фото для приміряння (довга сторона 1568,
   JPEG, стеля символів). У модель воно їде лише у виклику: у виклику 0 (стилістка
   бачить річ) і в описі образу; у звіт вердиктів їде лише його ід і розмір. */
let ФОТО_ВКЛАДЕНІ_П = [];          // фото ще не надісланої репліки: [{ід, тип, дані, ширина, висота}]
const ПИТАННЯ_ФОТО_П = 'Чи підійде мені ця річ і з чим її носити?';   // коли вона шле фото без слів
/* мітка нагоди, яку код підставив для речі з фото, — та сама, що `паспорт_нагоди.ТИПОВА_НАГОДА_РЕЧІ` */
const ТИПОВА_НАГОДА_РЕЧІ_П = 'типово для речі з фото';
/* та сама мітка, що `паспорт_нагоди.ТИПОВЕ_ПОЛЕ_ФОРМИ` (В-2) */
const ТИПОВЕ_ПОЛЕ_ФОРМИ_П = 'типове_форми';
function фотоРозмовиП(){ return ЧАТ_П.flatMap(р=>(р && р.фото) || []); }
function фотоЗаІдП(ід){ return фотоРозмовиП().find(ф=>ф.ід === ід) || null; }
function фотоТієїРеплікиП(ід){ return ((ЧАТ_П.find(р=>р && (р.фото || []).some(ф=>ф.ід === ід)) || {}).фото) || []; }
/* ЇЇ РІЧ НА КАРТЦІ, В ОПИСІ Й ПРИМІРЯННІ — байти з телефона, з репліки, що принесла
   фото в розмову. ЗВІДКИ — каже викликач: ід «ф1» живе в межах однієї розмови, і в
   новому сценарії «ф1» — вже інше фото. Картка й приміряння читають знімок сценарію
   своїх карток (`фотоКартокП`), збирання — стрічку, з якої воно почалось (`ЗБ.фото_чат`).
   У картку байти не пишуться. */
function фотоВласноїРечіП(ід, чат){
  if (!ід) return null;
  return (чат || ЧАТ_П).flatMap(р=>(р && р.фото) || []).find(ф=>ф && ф.ід === ід && ф.дані) || null;
}
const фотоКартокП = () => ((П || {}).сценарій_знімок || {}).чат || ЧАТ_П;
const урлФотоП = ф => ф ? ('data:' + (ф.тип || 'image/jpeg') + ';base64,' + ф.дані) : '';
const блокФотоП = ф => ({type:'image', source:{type:'base64', media_type: ф.тип || 'image/jpeg', data: ф.дані}});
/* ФОТО ЗАКРІПЛЕНИХ РЕЧЕЙ — ОДНАКОВО ВСІМ ЧОТИРЬОМ РУКАМ (п.6 наряду): руки
   різняться кодом, а не тим, що жінка принесла. Одне фото — одне зображення, навіть коли
   з нього названо кілька речей. Без закріпленої речі — null, і виклик той самий, що доти. */
function фотоЗакріпленихП(паспорт, чат){
  const ф = [];
  ((паспорт || {}).речі_з_фото || []).filter(р=>р && р.закріплена && р.фото).forEach(р=>{
    const о = фотоВласноїРечіП(р.фото, чат); if (о && !ф.includes(о)) ф.push(о);
  });
  return ф.length ? ф : null;
}
function наступнийІдФотоП(){
  const н = фотоРозмовиП().concat(ФОТО_ВКЛАДЕНІ_П)
    .map(ф=>parseInt(String(ф.ід || '').replace(/^ф/, ''), 10)).filter(x=>isFinite(x));
  return 'ф' + ((н.length ? Math.max(...н) : 0) + 1);
}
/* Репліка для журналу й звіту: фото — ідентифікатором і розміром, без байтів.
   Звіт копіюють у повідомлення власнику, і мегабайти base64 там — не інформація. */
/* ЧИ РЕПЛІКУ НАДИКТОВАНО. Стоїть в ОБОХ переписувачах репліки —
   журнальному (`реплікаБезБайтівП`) і чернетковому (`реплікаЗФотоП`): власник
   читає позначку у звіті, а жінка не має губити її при перезавантаженні. Ключ
   кладеться, лише коли він правда: `false` у кожній репліці — це шум у звіті,
   який власник читає рядок за рядком. */
const голосомУРепліку = (р, к) => { if (р.голосом) к.голосом = true; return к; };
function реплікаБезБайтівП(р){
  const к = голосомУРепліку(р, {хто: р.хто, текст: р.текст, тема: темаРепліки(р)});
  if ((р.мова_шару || []).length) к.мова_шару = р.мова_шару;   // мовний шар: було → стало
  if (р.опис_фото) к.опис_фото = р.опис_фото;                  // П-1: запит і відповідь «речі з фото»
  if ((р.фото || []).length) к.фото = р.фото.map(ф=>({ід: ф.ід, ширина: ф.ширина, висота: ф.висота}));
  return к;
}
/* Репліка для чернетки й бібліотеки: фото з байтами — інакше після перезавантаження
   мініатюри й річ для виміру зникли б. */
function реплікаЗФотоП(р){
  const к = голосомУРепліку(р, {хто: р.хто, текст: р.текст, тема: темаРепліки(р)});
  if ((р.мова_шару || []).length) к.мова_шару = р.мова_шару;
  if (р.опис_фото) к.опис_фото = р.опис_фото;
  if (р.порада_питанням) к.порада_питанням = true;             // «Можна не відповідати…» не зникає після перезавантаження
  if ((р.фото || []).length) к.фото = р.фото.filter(ф=>ф && ф.дані)
    .map(ф=>({ід: ф.ід, тип: ф.тип || 'image/jpeg', дані: ф.дані, ширина: ф.ширина, висота: ф.висота}));
  return к;
}
function малюватиВкладенняП(){
  const к = $('чат-вкладення'); if (!к) return;
  к.innerHTML = '';
  ФОТО_ВКЛАДЕНІ_П.forEach((ф, i)=>{
    const в = ел('div', 'вкладення');
    const і = ел('img'); і.src = 'data:' + (ф.тип || 'image/jpeg') + ';base64,' + ф.дані; і.alt = 'фото речі'; в.appendChild(і);
    const геть = ел('button'); геть.type = 'button'; геть.title = 'Прибрати фото'; геть.setAttribute('aria-label', 'Прибрати фото');
    геть.appendChild(іконка('хрестик'));
    геть.onclick = ()=>{ ФОТО_ВКЛАДЕНІ_П.splice(i, 1); малюватиВкладенняП(); малюватиЧатП(); };
    в.appendChild(геть); к.appendChild(в);
  });
}
async function додатиФотоРечіП(е){
  const ф = [...((е.target && е.target.files) || [])].filter(x=>x && /^image\//.test(x.type || 'image/'));
  const ст = $('чат-стан');
  for (const файл of ф){
    try{
      const б = await блобВБазу(файл);
      ФОТО_ВКЛАДЕНІ_П.push({ід: наступнийІдФотоП(), тип: б.тип || 'image/jpeg', дані: б.дані,
                           ширина: б.ширина || null, висота: б.висота || null});
    }catch(err){ if (ст) ст.textContent = 'Фото не прочиталось: ' + String(err).slice(0, 120); }
  }
  try{ е.target.value = ''; }catch(_){}
  малюватиВкладенняП(); малюватиЧатП();
  const п = $('чат-поле'); if (п) try{ п.focus(); }catch(_){}
}

/* ЇЇ СЛОВА ПРО ВИПАДОК — ЦЕ Й КАНАЛ ВИМОГ. Із v4 окремого поля «своїми словами»
   нема: слова живуть у розмові, і в міст вони їдуть звідси — інакше жінка, яка
   все сказала стилістові, їхала б у міст із порожніми вимогами: блок «ВИМОГИ
   ЛЮДИНИ» не з'явився б, `brief.послаблення` мовчав би, а `малюватиМежіП` не
   відрізнив би «слів не було» від «слова були, меж нема». Довідкові питання сюди
   не входять: «навіщо обхват голови» — не вимога до образу. */
/* РЕПЛІКИ — НОВИМ РЯДКОМ, А НЕ ПРОБІЛОМ: межа репліки — межа речення для моделі,
   що їх читає. У чаті крапку в кінці не ставлять, і «…, без підборів» + «В мене світлі джинси
   кльош…» склеювались в одне речення: її власні джинси ставали її ж «межею». Код її слів не
   читає (Ч-4): словник заперечень, що різав їх по [.!?;\n], знято. */
function словаЛюдиниП(){
  return реплікиСценарію().filter(р=>р.хто === 'людина').map(р=>(р.текст||'').trim()).filter(Boolean).join('\n');
}

/* ── ЩО ПОМІЧНИЦЯ ЗНАЄ ПРО ЗАСТОСУНОК (П-4) ─────────────────────
   Довідка живе в самій сторінці, бо описує саме її: екрани, елементи, що з чим робить код.
   Правиться разом із розміткою. АНГЛІЙСЬКОЮ: вона їде в промпт функціональної моделі
   (`міст_помічниця`, поле `app`; аудит/ПРОДУКТ.md п.12) — без ID правил, без чисел, яких людині не
   показують, і без прикладів її фраз (збирач промптів їх забороняє: 25.09 MamayLM вигадувала
   факти прямо з прикладів промпта). Доти тут стояв той самий зміст українською (723 слова,
   ~80 фраз у лапках), і його дописував до промпта сам показ, повз збирач.
   НАПИСИ ЕКРАНА — КЛЮЧАМИ `{…}`: `довідкаП` ставить на їхнє місце «напис» з `написиДовідкиП`.
   Сталі написи інтерфейсу лишаються в показі (п.12), а помічниця називає кнопку тими словами,
   що в неї на екрані. */
const ШІ_ДОВІДКА = `ABOUT. Lyusterko is a stylist in the browser. From her colours (skin, hair and eyes, read from her portrait), four girths (shoulders, bust, waist, hips) with her height, and her case (where she is going), the code picks four outfits from a catalogue of Ukrainian shops, checks them against style rules and shows them with photos and prices; she judges each one, and her verdicts stay on her phone. Everything personal (photos, measurements, colours, cases, outfits, verdicts) is kept in this phone's browser; a model receives only what it needs for one answer.

NAVIGATION. Four tabs at the bottom: {tab_case} (the main screen: the chat with the stylist and the case card), {tab_outfits} (the latest outfits; from there {all_outfits} opens the outfit library and the verdict log; before any outfits exist the tab leads straight to the library), {tab_review} (photos of what she is wearing now → a verdict on her own outfit) and {tab_profile}. The current tab is marked with two gold dots. The chat field: on an empty case it is a large sheet in the middle of the screen; once the chat has started, a window above the tabs; on other screens it is folded into a pill with the last answer, and a tap unfolds it. During onboarding and while outfits are being built there are no tabs; onboarding has {back} and {next} at the bottom. The word {logo} at the top also leads to the main screen, and the circle on the right of the header switches between day and night on every screen. On a laptop (a wide screen) the same four sections form a rail on the left together with {new_case_rail}, {saved} and the list of saved cases; the chat field sits under the chat and the case card to the right of it (on the profile, the photos are on the right). Edits are made in a sheet that rises from the bottom: it has {done}, and a tap on the dimmed background closes it.

ONBOARDING — three steps, once, while there is no profile yet. Step 1 {step_about}: the portrait (as soon as it is added, the skin, hair and eye colours are read automatically; {read_colours} reads them again; {other_way} lets her copy the request into any chat assistant and paste its answer back), a full-length photo (needed only to try an outfit on her), a name or pseudonym (the profile is called by it in the list of people and in the verdict record) and consent to record shades together with verdicts. Step 2 {step_face}: three pairs of fields next to her face — gold or silver, pure white or milky white, warm or cool neutrals ({no_difference} is a full answer) — and whether her own colouring is bright or muted. These answers narrow the temperature of the palette when the photo cannot establish it; the step can be skipped and done later. Step 3 {step_figure}: shoulders, bust, waist and hips in cm at the widest point over underwear, and height; the code derives the figure type from them. {done} creates the profile and opens the case screen.

PROFILE (tab) — rows, each showing what is already there: {row_photo} (portrait and full length), {row_colours} (three swatches: skin, hair, eyes), {row_name} (and consent), {step_face} (her answers), {row_girths} (four numbers and height), {row_extra} (all optional: high hip, knee, calf and ankle refine the fit on the legs and hips; foot length in mm and head girth in cm check shoe and hat sizes), {row_people} ({whose_profile} switches between people and {new_profile} adds one: several people can use one phone, each with her own data). A tap on a row opens its editor as a sheet with the same fields as in onboarding. What is still missing for building is labelled in gold.

CASE — the main screen; the one main thing on it is the chat. Before the chat starts, under the question {where_going} there is a letter sheet: she writes into it, as to a friend, where she is going, when, what the weather is, what she wants and does not want; below it are three example beads (a tap puts the example into the field without sending it) and {fill_by_hand} (shows an empty case card). From her words the stylist builds the case passport: event, occasion, place, formality, hour, temperature, precipitation, requirements and limits. The messages form a thread, and under the last answer lies the case card with rows: {row_occasion} ({occasions}), {row_place} ({places}), {row_formality} (the step of dress for this outing — home, everyday, neat, smart, strict, evening dress or ceremonial — set by whose standard holds there, not by the hour or the event's name; a dress code chosen by hand overrides it), {row_when} (hour, temperature, {precipitation}, wind, de-icing chemicals on the roads), {row_makeup} ({makeup_levels}; for the last two also a lip colour — noticeable makeup gives the outfit one more step of contrast near the face, bold makeup already holds the focus on the face; {stylist_chooses} hands this decision to the code on purpose; the lip colour is chosen from a ladder of shades split into those recommended for her and the rest, each with its reason, next to {own_shade} and {stylist_chooses} for the colour itself), {row_jewelry} ({jewelry} or {stylist_chooses}: the code matches gold and silver against the metal of the items and removes the opposite metal from the pick, no jewellery removes jewellery altogether, and pearls cannot be told from ethnic pieces because shops do not say so — the code says this in its report), {row_dont_want} ({zones} — a hard limit, not a wish: the code removes such items from the pick itself; limits the stylist heard in her words go here too — items, fabrics, prints, colours: the card row names only what the code actually holds, which is colours and what she refused in her own words, and the rest of what was heard is shown in the sheet, where a tap removes something heard by mistake) and {row_palette} (opens a separate screen). A tap on a row opens its editor as a sheet with tiles and lists; after a manual edit the passport is rebuilt from the whole chat before building. Grey values are defaults: she has not chosen there. The card also has the question {all_right} ({yes} confirms, {fix} returns to the field), the button {build} (it needs read colours, four girths and height, and an occasion or a description in her own words; the button says what is missing, and a hint with {to_profile} appears at the top of the screen) and {save_case} (into the library, with a name; an opened saved case can be updated with {update} or saved with {save_as_new}). When the stylist does not know something (for example, how formal), quick-answer beads from the reference tables appear above the field, and a tap sends the answer.
ITEM PHOTOS: next to {send}, both in the letter sheet and in the chat field, there is a photo button — she can add one or several photos of an item (her own, or one she is thinking of buying) and ask whether it suits her and what to wear it with; a photo without words means exactly that question. The photo is shown as a thumbnail in her message; it stays on the phone with the case draft and is saved with the case in the library; a model receives it only within a call. The stylist names the item (what it is, colour, cut, length, fabric, whose it is), and the code measures its colour from the photo itself and decides whether the item suits her — it suits, it suits with a condition (for example, away from the face, with her neutral near the face), or another one would be better — and why; the stylist only retells this verdict. If she has not named an occasion, the item is judged for an ordinary day, and this is said. {build} puts the item from the photo into every outfit and picks the rest around it; on the card it stands with its photo and the mark {your_item} (or {item_from_photo}), without a shop or price, and {total} does not count it. An item that does not suit her can still be built with — the card says in one line what softens it.
AN ITEM IN WORDS: she can also describe her own item without a photo; the stylist adds it to the case, and the code puts it into every outfit in the same way. Its colour then comes from her words, not from a measurement, and the card says so in the list of what the code does not know. Such a sentence, or a wish for an outfit with that item, written on any other screen, the code itself puts into the case chat and says it was added to the case; other questions outside the case do not go into building.
VOICE: next to the photo button there is a microphone — here in the chat and on the outfit card under the verdict field. The first tap starts recording and the second stops it; while she speaks, the text appears in the field at once and is appended to what is already written, so she can correct it by hand. It goes nowhere by itself: {send} sends the message, {record_verdict} records the verdict. The voice is recognised not by Lyusterko but by the browser's service (Google in Chrome, Apple on iPhone), and the sound goes to it; only the text it returns lands in the field. Where recognition is unavailable or the microphone is blocked, the button says so and suggests the microphone on the phone's keyboard, which types into the same field. The owner's report shows that a comment or a message was dictated.
At the top of the screen are {saved} (a list: a tap opens a case, {delete} needs two taps) and {new_case} (a clean screen). An unsaved draft survives a page reload.

PALETTE — a separate screen, opened from the {row_palette} row of the card. It is computed from her colours, so it needs read colours; the colour maths starts here, and the first time it takes up to a minute. Gamut ({gamut_options}), base — the main colour the outfit stands on ({stylist_chooses} lets the code pick; {recommended} marks the code's recommendation), and colour scheme — the branches legitimate for her colouring; without a choice the code takes the first. At the top is {to_case}.

BUILDING takes two to three minutes, longer the first time (an environment of about 15 MB loads). Without the access token (the owner's link ending with #token) neither the chat nor building works.
WAITING SCREEN: a loom weaving cloth in the colours of the chosen palette (the base as the thread, the accent as towel stripes) and four windows that clear up with the stages of building: the code gathers candidates, a model composes outfits, the code checks them, a model picks and describes them from photos of the chosen items. The chat field works here too.

OUTFITS (tab): four cards, one per screen, in random order. A card has a collage of item photos, the list of items with shop links and prices, {total}, {why_look}, {how_to_wear} and {try_on} (draws her in these items from her full-length photo; it costs a model call; a picture can also be added by hand). The verdict: {will_wear} ({wear_options}) → {yours_or_pretty} → the main part: a large field for her impressions in her own words, typed or dictated, under a question that follows her two answers (before them it reads {verdict_question}; after them it asks what makes the outfit hers, what is missing for it to be hers, or what is in the way and what the outfit should have been) → optionally, below the field, one tap on short words, the same for every verdict ({aspect_options}): {aspects_plus} after «as it is» with «hers» or no second answer, {aspects_minus} otherwise; and the mark {not_this} on the item that is wrong → {record_verdict}. Above the cards: {change_case} returns to the main screen, {build_again} gives four new outfits for the same case, {all_outfits} opens the library, and {open_case} restores the case the outfit was built from.
LIBRARY ({all_outfits}): the built outfits grouped by case; a tap opens an outfit again, and judging it again adds a new record while the previous one stays. Below is the verdict log of this phone with {copy_verdicts} to pass them to the owner. If there are latest outfits, {latest_outfits} is at the top.`;
/* НАПИСИ ЕКРАНА ДЛЯ ДОВІДКИ — ті самі, що в розмітці. Переліки плиток беруться з таблиць, з
   яких їх малює сам екран (`ДОВІДНИК`, `ОПАДИ`, `МАКІЯЖ`, `ПРИКРАСИ_П`, `ЗОНИ_ВЕТО_П`, `ГАМИ`,
   `ВЕРДИКТ_П`, `АСПЕКТИ_ВЕРДИКТУ_П`, `ПИТАННЯ_ПОЛЯ_П`), тож розійтися з ним вони не можуть. Кожен ключ довідки мусить мати напис,
   і кожен напис — стояти в довідці (тест показу, розділ помічниці). */
function написиДовідкиП(){
  const плитки = с => (с || []).filter(х => х && х.плитка).map(х => х.підпис);
  const безСтилістки = с => с.filter(х => х[0] !== СТИЛІСТКА_КЛЮЧ).map(х => х[1]);
  return {
    tab_case: 'Сценарій', tab_outfits: 'Образи', tab_review: 'Оцінити', tab_profile: 'Профіль',
    all_outfits: 'Усі образи ›',
    back: 'Назад', next: 'Далі', logo: 'люстерко', new_case_rail: 'Новий сценарій', saved: 'Збережені',
    new_case: 'Новий', delete: 'видалити', done: 'Готово', send: 'Надіслати',
    step_about: 'Про тебе', read_colours: 'Зчитати кольори з портрета',
    other_way: 'Інший шлях — через будь-який чат-помічник', step_face: 'Що тобі до лиця',
    no_difference: 'не бачу різниці', step_figure: 'Фігура',
    row_photo: 'Фото', row_colours: 'Твої кольори', row_name: "Ім'я", row_girths: 'Обхвати і зріст',
    row_extra: 'Розширені виміри', row_people: 'Люди на цьому телефоні', whose_profile: 'Чий це профіль',
    new_profile: 'Новий профіль', where_going: 'Куди ти збираєшся?', fill_by_hand: 'Або заповнити рукою',
    row_occasion: 'Нагода', occasions: плитки((ДОВІДНИК || {}).нагоди), row_place: 'Де',
    places: плитки((ДОВІДНИК || {}).місця), row_formality: 'Ошатність', row_when: 'Коли й погода',
    precipitation: ОПАДИ.map(о => о[1]), row_makeup: 'Макіяж', makeup_levels: безСтилістки(МАКІЯЖ),
    stylist_chooses: СТИЛІСТКА_СЛОВО, own_shade: 'свій відтінок', row_jewelry: 'Прикраси',
    jewelry: безСтилістки(ПРИКРАСИ_П), row_dont_want: 'Не хочу', zones: ЗОНИ_ВЕТО_П.map(зонаЛюдині),
    row_palette: 'Палітра', all_right: 'Усе правильно?', yes: 'так', fix: 'поправити',
    build: 'Зібрати образи', to_profile: 'До профілю', save_case: 'Зберегти сценарій', update: 'Оновити',
    save_as_new: 'Зберегти як новий', your_item: 'твоя річ', item_from_photo: 'річ з фото',
    record_verdict: 'Записати вердикт', gamut_options: ГАМИ,
    recommended: 'радимо', to_case: '← До сценарію', total: 'Разом', why_look: 'Чому цей образ',
    how_to_wear: 'Як це носити', try_on: 'Приміряти на себе', will_wear: 'Вдягнеш?',
    wear_options: ВЕРДИКТ_П.map(ч => ч.ярлик),
    yours_or_pretty: 'Це саме твоє — чи просто гарний образ?', verdict_question: ПИТАННЯ_ПОЛЯ_П.start,
    aspects_plus: АСПЕКТИ_МІТКА_П.plus, aspects_minus: АСПЕКТИ_МІТКА_П.minus,
    aspect_options: АСПЕКТИ_ВЕРДИКТУ_П.map(ч => ч.ярлик), not_this: ЗАМІНА_П.дія, change_case: 'Змінити сценарій',
    build_again: 'Зібрати ще раз', open_case: 'Відкрити сценарій цього образу',
    copy_verdicts: 'Скопіювати всі вердикти', latest_outfits: '← Останні образи'};
}
/* Довідка з написами на місцях ключів: напис — у «лапках», перелік — через кому. Ключ без
   напису лишається `{ключем}` — його ловить тест, а не мовчазна дірка в тексті. */
function довідкаП(){
  const н = написиДовідкиП(), лапки = т => '«' + т + '»';
  return ШІ_ДОВІДКА.replace(/\{([a-z_]+)\}/g, (ц, к) => !(к in н) ? ц
    : (Array.isArray(н[к]) ? н[к].map(лапки).join(', ') : лапки(н[к])));
}

/* ПІДКАЗКА В ПОЛІ — ЗАПРОШЕННЯ, А НЕ ІМ'Я: на сценарії поле саме ставить
   головне питання; деінде — коротке «спитай про…». Коротше за ширину поля. */
const ПІДКАЗКИ_ШІ = {
  'сценарій':   'Напиши стилістці…',
  'старт':      'Щось незрозуміло? Спитай',
  'профіль':    'Спитай про будь-яке поле',
  'палітра':    'Спитай про кольори',
  'сценарії':   'Спитай про сценарії',
  'очікування': 'Можна питати, поки тчеться',
  'образи':     'Спитай про ці образи',
  'бібліотека': 'Спитай про образи',
  'інше':       'Спитай стилістку'};
/* підказка в АРКУШІ ЛИСТА — на порожньому сценарії, замість пояснення під заголовком */
/* ЗАПРОШЕННЯ ПИТАННЯМ — ПОРАДА (п.9): модель запрошує розповісти питанням, і код його пропускає
   (`мовний_шар.суд_частин`); що відповідати не мусить, каже цей сталий напис під бульбашкою, а не модель. */
const ПОРАДА_НЕОБОВʼЯЗКОВА_П = 'Можна не відповідати — образи зберуться й так.';
const ПІДКАЗКА_ЛИСТА = 'Напиши, як подрузі: куди йдеш, коли, яка погода, чого хочеш і чого не хочеш. Я складу сценарій, а ти поправиш, що треба.';

/* Приклади під аркушем листа — живі речення, якими вона б і написала сама, без
   напису над ними (власник: підписи читались як замітки девелопера).
   Тап вписує речення в поле й не шле — слово лишається за нею. */
const ПРИКЛАДИ_СЦЕНАРІЮ = ['Іду на побачення в ресторан, увечері. Обіцяють дощ',
                           'Завтра презентація для клієнта в офісі',
                           'Прогулянка з дитиною в парку, +8 і вітер'];

/* Палітра словами — з ВИБОРУ, без Pyodide: підпис основи запамʼятовується в
   момент дотику (`словоПалітри`), тож рядок є і на щойно відкритому сценарії. */
/* Коротко для рядка картки: лише те, що вона обрала; нічого — «хай обере стилістка». */
function палітраКоротко(){
  const вк = ВИБІР.вибір_кольору || {}, сл = ВИБІР.слова || {}, ч = [];
  if (вк.база) ч.push('основа: ' + (сл.база || String(вк.база).split('·')[0]));
  if (ВИБІР.гілка != null || ВИБІР.схема) ч.push('схема: ' + (сл.схема || (ВИБІР.схема ? String(ВИБІР.схема).replace(/_/g, ' ') : 'гілка ' + ВИБІР.гілка)));
  if (вк.насиченість) ч.push('гама: ' + вк.насиченість);
  return ч.join(' · ');
}
function малюватиПалітруКоротко(){
  const е = $('пал-коротко'); if (!е) return;
  const к = палітраКоротко();
  е.textContent = к || 'хай обере стилістка'; е.classList.toggle('типово', !к);
}
function словоПалітри(к, з){
  const с = Object.assign({}, ВИБІР.слова); if (з) с[к] = з; else delete с[к];
  ВИБІР.слова = Object.keys(с).length ? с : null;
}
/* Дотик до палітри — зміна сценарію: позначити, записати чернетку, перерахувати. */
function змінаПалітриП(){ позначитиЗміну(); малюватиПалітруКоротко(); зберегтиЧернетку(); оновитиПалітруП(); }

/* ── КАРТКА СЦЕНАРІЮ: рядки «що зрозуміло», редактори під ними (v4.2) ──────
   Те, що стилістка зрозуміла, лежить на видноті рядками; тап по рядку відкриває
   під ним ТІ САМІ плитки й списки, що й доти, — форма не зникла, вона перестала
   стояти стіною. Значення сірим («типово») — там її вибору ще нема. */
/* ── ПЛИТКА КАЖЕ ЛИШЕ МЕЖУ ─────────────────────
   ЩО ЦЕ ЛАГОДИТЬ. Плитка показувала ВСЕ почуте одним списком, тим самим жирним
   шрифтом. Жінка, яка попросила «можна яскравий верх — куртку чи жакет, не
   темного кольору», читала в картці «блейзер, куртка, темні кольори» — тобто що
   її куртку заборонено. Код так не вважає: межею він тримає саме «темні
   кольори» (`вето_тверде`), а куртку й блейзер лишає в пулі. Над
   картками образів рядок уже казав правду («Твої межі враховано: темні
   кольори») — картка казала інше, і вірили картці.
   ДЖЕРЕЛО ПРАВДИ ОДНЕ Й ТЕ САМЕ, ЩО В ШВА: `вето_тверде` паспорта. Другий
   перелік у JS розійшовся б із ним на першій же правці.
   ЗОНА — ТЕЖ ЛИШЕ ЧИННА. Тут стояло «ЗОНИ — ЗАВЖДИ МЕЖА:
   їх жінка натискає чипом сама, це не почуте слово». Тепер це вже
   неправда: зону кладе й модель, і `вето_тверде` тримає її лише з опорою в словах
   чи з чипа. А плитка казала «Не хочу: ноги» й аркуш показував чип «ноги» обраним
   під написом «Тверда межа, а не побажання: обране тут стилістка прибирає з добору сама»
   — при `вето_тверде.зони: []` у тому самому файлі вердиктів (прохід
   тестувальниці 24.09, З-2). Тобто жінка читала, що її ноги — тверда межа, а код
   у цьому ж прогоні її свідомо не тримав. Джерело правди тут те саме, що в шва.
   СЛОВО БЕЗ ЧИТАЧА (`без_читача`) межею не стоїть — його ніхто не застосовує,
   тож із рядка воно просто зникає. Старий збережений паспорт поля `вето_тверде`
   не має — тоді поводимось як доти: усе почуте лишається в межах.
   ПРО ПОЧУТЕ НА КАРТЦІ НЕ СКАЗАНО НІЧОГО, І РЯДКА «НЕ ХОЧУ» НЕМА (ПОКАЗ-1, слово власника 02.10): «Це зайве…
   Мовна модель в діалозі і так відповідає повністю, що вона зрозуміла». Заборони лишаються в паспорті. */
/* МІСЦЕ СЛОВАМИ. Плитка місця — сталий напис показу (п.7); місце поза плитками (церква,
   школа, ресторан_високий…) — слова мовної моделі з паспорта (`місце_слова`), коли вона написала їх при саме цьому
   місці, а коли ні — сталий напис довідника (`ПІДПИСИ_НЕ_ПЛИТКИ`, `слова` у рядку): місце з кодом не лишається
   без рядка «Де». Ключа (`церква_служба`) людина не бачить (п.12): ні слів моделі, ні напису довідника — null,
   і рядок мовчить. */
function словаМісцяП(м){
  if (!м) return null;
  if (м.плитка) return м.підпис;
  const п = [паспортКартки(), ПАСПОРТ_П].find(х => х && х.місце === м.ключ && String(х.місце_слова || '').trim());
  return п ? String(п.місце_слова).trim() : (м.слова ? м.підпис : null);
}
let ПОРОЖНІ_ВІДКРИТО_П = false;   // рядок «Додати» картки відкрив порожні рядки (до нового сценарію)
/* пора паспорта (код `внутрішня_мова` part_of_day) → слово рядка «Коли й погода» — ті самі слова, що в швидких
   відповідях про годину */
const ПОРА_СЛОВОМ_П = {ранок: 'вранці', день: 'вдень', вечір: 'ввечері', ніч: 'вночі'};
function малюватиКарткуСценарію(){
  const к = $('сц-картка'); if (!к) return;
  малюватиПитанняНагодиП();
  const пост = (ід, текст, типово)=>{ const е = $(ід); if (!е) return; е.textContent = текст; е.classList.toggle('типово', !!типово); };
  const н = знайти(ДОВІДНИК.нагоди, $('сц-нагода').value);
  const мОбране = $('сц-місце').value, мк = місцеКартки(), ош = ошатністьДжерело();
  const кл = знайти(ДОВІДНИК.коди, $('сц-дрес').value);
  /* нагода, яку код підставив для речі з фото, стоїть сірим і з причиною */
  const нТип = !н && ПАСПОРТ_П && (ПАСПОРТ_П.джерело_полів || {}).нагода === ТИПОВА_НАГОДА_РЕЧІ_П
    ? знайти(ДОВІДНИК.нагоди, ПАСПОРТ_П.нагода) : null;
  пост('зн-нагода', н ? н.підпис : (нТип ? нТип.підпис + ' — ' + ТИПОВА_НАГОДА_РЕЧІ_П : 'не обрано'), !н);
  /* «ТИПОВО» — ЛИШЕ ТАМ, ДЕ ВИБОРУ СПРАВДІ НЕ БУЛО (КАРТ-1).
     Місце, яке вона назвала словами чи зрозуміла модель, плиткою не є, тож у `<select id="сц-місце">`
     його нема — правду про вибір дає `місцеКартки`: паспорт каже «рука» або «розмова», і саме воно
     вирішує. Типове місце нагоди стоїть сірим, а коли суперечить числу чи частині дня моделі, — «не обрано». */
  /* МІСЦЕ СЛОВАМИ: плитка — своїм написом, місце поза плитками — словами мовної моделі
     (`словаМісцяП`), ключа людина не бачить. Типове місце нагоди стоїть, лише поки саме дає слово ошатності
     (числа моделі нема); при числі моделі воно нічого на картці не вирішує — це здогад коду («Урочистий зал»
     над вечіркою в подруги), і рядок мовчить разом з іншими порожніми (нижче). */
  const деСл = мк.м && !(мк.типово && числоМоделіКартки()) ? словаМісцяП(мк.м) : null;
  пост('зн-місце', деСл ? деСл + (мк.типово ? ' — типово для нагоди' : '') : '', мк.типово);
  /* ошатність: названий код чи щабель числа моделі; без числа моделі — «не обрано» (наряд 3.7) */
  пост('зн-дрес', ош ? ош.слово : 'не обрано', !ош || ош.від === 'модель');
  /* Пілюля «Надворі» не каже +18 °C, коли паспорт каже «мороз»: типове число з неї знято, а відчуття стоїть
     підказкою (`placeholder`, слово те саме, що в рядку картки); рука впише число — воно її. Відчуття зникло —
     типове число повертається. Читачі поля бачать порожнє типове поле як «не називала» (`картка_запиту`). */
  const пТемп = $('сц-темп'), відчПілюлі = відчуттяКарткиП();
  if (пТемп){
    if (типовеЧислоП('сц-темп')){
      if (відчПілюлі && пТемп.value === ТИПОВІ_ПОЛЯ_ВИПАДКУ['сц-темп']) пТемп.value = '';
      else if (!відчПілюлі && пТемп.value === '') пТемп.value = ТИПОВІ_ПОЛЯ_ВИПАДКУ['сц-темп'];
    }
    if (відчПілюлі) пТемп.placeholder = відчПілюлі; else пТемп.removeAttribute('placeholder');
    /* Слово відчуття ширше за поле 44 px і різалося до «мо»: поле росте за довжиною слова, поки порожнє */
    пТемп.style.width = (відчПілюлі && !пТемп.value) ? (відчПілюлі.length * 0.66 + 0.6).toFixed(2) + 'em' : '';
  }
  let г = parseInt($('сц-година').value), т = температураП(), хвКартки = хвилиниП();
  const оп = $('сц-опади').value;
  const вт = $('сц-вітер').value, рг = $('сц-реагенти').value;
  /* ПОКАЗ-1: година з ходу плиток. Поле екрана, якого вона не торкалась, стоїть на типових 11:00, а
     фоновий хід плиток уже зрозумів годину (театр — 20:00) — картка читає її з того самого паспорта, з якого
     бере число ошатності (`паспортКартки`), доки поле типове; рука й назване нею слово важать над паспортом. */
  const пК = типовеЧислоП('сц-година') ? паспортКартки() : null;
  let гЗПаспорта = false;
  if (пК && пК.година != null && isFinite(пК.година) && (пК.джерело_полів || {}).година !== ТИПОВЕ_ПОЛЕ_ФОРМИ_П){
    г = parseInt(пК.година); хвКартки = пК.хвилини > 0 ? пК.хвилини : 0; гЗПаспорта = true;
  }
  /* Пора без годинника («субота ввечері») стоїть у паспорті порою, а не годиною — рядок каже її пору
     словом плитки швидкої відповіді, а годинника, якого вона не називала, не малює */
  const пораК = (пК && !гЗПаспорта && ПОРА_СЛОВОМ_П[пК.пора]) || null;
  /* Відчуття з її слів стоїть замість типових градусів, а не поруч із ними */
  const відч = відчуттяКарткиП();
  позначитиВідчуттяП();
  /* шматки рядка парами [текст, типове] — типове стоїть сірим і тоді, коли решту рядка назвала вона */
  /* Вшита година форми (11:00) — не її слово, і на картці вечірки «Коли — 11:00, мороз» казало про ранок, якого
     вона не називала (правила беруть вечір). Поки години в її словах нема (рука не торкалась, паспорт її не дав і порою
     не замінив), рядок її не друкує; поле й число лишаються в редакторі того ж рядка і в правилах (п.9). */
  const годинаВшита = типовеЧислоП('сц-година') && !гЗПаспорта && !пораК;
  const коли = [пораК ? [пораК, false] :
                [isFinite(г) && !годинаВшита ? String(г).padStart(2, '0') + ':' + String(хвКартки).padStart(2, '0') : null,
                 типовеЧислоП('сц-година') && !гЗПаспорта],
                [відч || (isFinite(т) ? (т > 0 ? '+' : '') + т + ' °C' : null),
                 !відч && типовеЧислоП('сц-темп')],
                [оп ? ({нема:'без опадів', можливий_дощ:'можливий дощ', дощ:'дощ', сніг:'сніг'}[оп] || оп) : null,
                 false],
                [вт !== '' ? ({'0':'безвітря', '1':'помірний вітер', '2':'сильний вітер'}[вт] || null) : null, false],
                [рг === '1' ? 'реагенти на дорогах' : null, false]].filter(([ш]) => ш);
  /* ── СІРИМ — ТЕ, ЧОГО ВОНА НЕ НАЗИВАЛА (В-13, розбір 1/8) ───────
     Доти сірість знімалась від самої появи паспорта від моделі
     (`ПАСПОРТ_П.джерело === 'модель'`), хоч до години й температури вона не
     торкалась: рядок казав чорним «Коли й погода — 11:00, +18 °C» про день, про
     який вона не сказала ні слова. Тепер сірість міряє те, що й мусила: чи хоч
     що-небудь у цьому рядку назвала вона сама. Число не ховаємо й не замикаємо
     (п.9) — воно видне й клікабельне тим самим дотиком. */
  const _типЧисла = Object.keys(ПОЛЯ_ТИПОВІ_ЧИСЛА).every(і=>типовеЧислоП(і));
  const колиСірим = _типЧисла && !пораК && !відч && !оп && вт === '' && рг !== '1';
  пост('зн-коли', коли.map(([ш]) => ш).join(', ') || 'не вказано', колиСірим);
  /* «Коли й погода — 11:00, +18 °C, дощ» чорним казало б, що 11:00 і +18 °C назвала вона, а
     назвала вона лише дощ. Типовий шматок не ховаємо (В-13) — він стоїть сірим поруч із її словами. */
  if (!колиСірим && коли.some(([, тип]) => тип)){
    const е = $('зн-коли'); е.textContent = '';
    коли.forEach(([ш, тип], і) => { if (і) е.appendChild(document.createTextNode(', '));
                                    е.appendChild(ел('span', тип ? 'типово' : null, ш)); });
  }
  /* макіяж — тими ж словами, що на плитках; колір губ поруч, коли його названо.
     «Хай обере стилістка» — обране слово, і сірим воно НЕ стоїть: вибір є. */
  const мкР = ($('сц-макіяж')||{}).value, мкП = (МАКІЯЖ.find(([к])=>к === мкР) || [])[1];
  /* Губи — той самий поділ: «не дійшла» мовчить, а «хай обере стилістка» стоїть
     у рядку так само видимо, як названий відтінок. */
  const гб = (!мкР || мкР === 'нюд' || мкР === СТИЛІСТКА_КЛЮЧ) ? ''
           : губиНазваноП() ? ', губи ' + $('сц-губи').value
           : губиСтанП() === СТИЛІСТКА_КЛЮЧ ? ', губи — ' + СТИЛІСТКА_СЛОВО : '';
  пост('зн-макіяж', мкР ? (мкР === СТИЛІСТКА_КЛЮЧ ? СТИЛІСТКА_СЛОВО : мкП + гб) : '', !мкР);
  /* прикраси — те саме: слово плитки; порожнечу ховає рядок «Додати» нижче */
  const прР = ($('сц-прикраси')||{}).value, прП = (ПРИКРАСИ_П.find(([к])=>к === прР) || [])[1];
  пост('зн-прикраси', прР ? (прР === СТИЛІСТКА_КЛЮЧ ? СТИЛІСТКА_СЛОВО : прП) : '', !прР);
  /* мета — слово, яке почула стилістка (або яке жінка обрала дотиком) */
  const мтП = метаСловомП(), мтР = мтП;
  пост('зн-мета', мтР ? мтП : '', !мтР);
  /* ПОРОЖНІ РЯДКИ — ЗА КНОПКОЮ (п.9): рядок, про який вона нічого не сказала, не стоїть «не вказано»;
     його назва йде в рядок «Додати», і дотик до нього відкриває всі такі рядки (`ПОРОЖНІ_ВІДКРИТО_П`). */
  const назвиПорожніх = [];
  [['зн-місце', !деСл], ['зн-макіяж', !мкР], ['зн-прикраси', !прР], ['зн-мета', !мтР]].forEach(([ід, пусто])=>{
    const ряд = $(ід) && $(ід).closest('.ряд-паспорта'); if (!ряд) return;
    ряд.hidden = пусто && !ПОРОЖНІ_ВІДКРИТО_П;
    if (ряд.hidden) назвиПорожніх.push(ряд.firstElementChild.textContent.toLowerCase());
  });
  { const ще = $('сц-ще'); if (ще){ ще.hidden = !назвиПорожніх.length; $('зн-ще').textContent = назвиПорожніх.join(', '); } }
  малюватиПалітруКоротко();
  /* картка видима, щойно є що показати, або коли людина попросила її сама */
  const єЩось = !!(ПАСПОРТ_П || $('сц-нагода').value || мОбране || $('сц-дрес').value || оп || зониВето().length
                   || мкР || прР || мтР || СЦ.ід || КАРТКА_РУКОЮ);
  к.hidden = !єЩось;
  const р = $('сц-рукою-ряд'); if (р) р.style.display = єЩось ? 'none' : '';
  /* Поки сценарію нема, «Зберегти» й «Новий» нічого не означають: лишається
     «Збережені» — єдине, що на порожньому екрані має сенс. */
  { const нв = $('сц-новий'); if (нв) нв.hidden = !(єЩось || СЦ.ід || ЧАТ_П.length); }
}
/* Чого бракує в профілі — вгорі сценарію з посиланням, а не лише словами на кнопці. */
function малюватиУвагуП(){
  const е = $('сц-увага'); if (!е) return;
  const бракує = чогоБракує().filter(б=>/кольори|обхвати/.test(б));
  е.innerHTML = '';
  if (!бракує.length){ е.hidden = true; return; }
  е.appendChild(ел('span', null, 'Твої кольори й мірки допоможуть підібрати образи, що тобі пасують. У профілі ще потрібні ' + бракує.join(' і ') + '.'));
  const б = ел('button', 'текст', 'До профілю'); б.type = 'button';
  б.onclick = ()=>відкритиПрофіль(бракує[0].indexOf('кольори') >= 0 ? 'кол-блок' : 'мір-блок');
  е.appendChild(б); е.hidden = false;
}

/* Стрічка розмови ОДНА, а місць два: на сценарії вона стоїть в екрані (там
   розмова — головна річ), деінде — у панелі, де її можна згорнути. Переносимо
   той самий вузол, а не тримаємо дві копії: дві розійшлися б на першій правці. */
function розмістити_стрічку(){
  const с = $('чат-стрічка'), інл = $('сц-розмова'), док = $('ші-стрічка');
  const ціль = (РЕЖИМ === 'сценарій' && інл) ? інл : док;
  if (с && ціль && с.parentNode !== ціль) ціль.appendChild(с);
}

/* СТАН ДЛЯ ПОМІЧНИЦІ — ФАКТИ, А НЕ РЕЧЕННЯ (П-4, аудит/ПРОДУКТ.md п.12). Де вона й що вже є — тими
   ключами й значеннями, що їх має сам код; дріт моделі (англійські ключі, коди внутрішньої мови)
   складає `міст_помічниця.стан`. Доти тут код складав рядки українською («кольори зчитано;
   обхвати: бракує — …», «картка сценарію: … 11:00 [типове_форми]»), і вони їхали в промпт
   функціональної моделі повз збирач.
   ЧЕТВЕРТИЙ ЧИТАЧ ВШИТОГО ЧИСЛА ФОРМИ (Л-3б-2, В-2 і В-13): поля сценарію — ті самі, що
   `зібратиВхід().сценарій`, разом із `типові_поля` (що вона не називала, а код поставив сам).
   Значення лишається — число на картці вона бачить, і помічниця не має заперечувати те, що в
   неї перед очима; а що з такими полями робити, каже рядок входу оголошення (`form_defaults`). */
function станДляШі(){
  const акт = ПРОФІЛІ.find(п=>п.ід === АКТИВНИЙ);
  const число = ід => { const v = parseFloat(($(ід) || {}).value); return isFinite(v) && v > 0 ? v : null; };
  const основні = ['плечі','груди','талія','стегна'];
  let сценарій = {};
  try{ сценарій = зібратиВхід().сценарій || {}; }catch(e){ console.warn('стан для помічниці без полів сценарію:', e); }
  const вк = ВИБІР.вибір_кольору || {};
  return {
    екран: РЕЖИМ, крок: РЕЖИМ === 'старт' ? ЕКРАН + 1 : null,
    профіль: {назва: (акт && акт.назва) || null, профілів: ПРОФІЛІ.length, створено: !!ПРОФІЛЬ_СТВОРЕНО,
              кольори: !!КОЛІР.шкіра, зріст: число('мр-зріст'),
              обхвати: Object.fromEntries(ПОЛЯ_ОБХВАТІВ.map(([і, к]) => [к, число(і)])),
              аксесуарні: зібратиАксесуарні(),
              що_до_лиця: ['метал','білий','нейтралі','барви'].filter(к=>ДРАП[к]).length,
              фото: {портрет: !!ФОТО_Є.портрет, зріст: !!ФОТО_Є.зріст}},
    сценарій: {назва: СЦ.назва || null, збережений: !!СЦ.ід, змінено: !!СЦ.змінено,
               паспорт: ВИПАДОК_ПАСПОРТА_П || випадокРядком() || null,
               підтверджено: !!(ВИПАДОК_ПАСПОРТА_П && ВИПАДОК_ПІДТВЕРДЖЕНО_П),
               поля: сценарій, зони: зониВето()},
    палітра: {основа: вк.база || null, схема: ВИБІР.схема || null, гама: вк.насиченість || null},
    /* чого бракує для збирання — ті самі умови, що `чогоБракує`, ключами, а не рядком кнопки */
    бракує: [].concat(КОЛІР.шкіра && КОЛІР.волосся && КОЛІР.очі ? [] : ['кольори'],
                      число('мр-зріст') ? [] : ['зріст'],
                      ПОЛЯ_ОБХВАТІВ.filter(([і, к]) => основні.includes(к) && !число(і)).map(([, к]) => к),
                      єВипадокП() ? [] : ['нагода']),
    образів: (П && П.картки) ? П.картки.length : 0,
    збережених: СЦН_ЛІЧБА};
}

/* ── ДОВІДКА ПРО ЗАСТОСУНОК У ВИКЛИК 0 БІЛЬШЕ НЕ ЙДЕ (В-10, розбір 1/8; рішення
   власника «прибрати», ПЕРЕДАЧА §0) ─────────────────────────────────────────────
   Доти `додатокДоПаспортаП()` дописував до КОЖНОГО виклику 0 шапку «КРІМ ПАСПОРТА»,
   усю `ШІ_ДОВІДКА` (10 859 симв., 80 фраз у лапках) і `станДляШі()`: 6 041 симв.
   промпта збирача проти 11 290 симв. додатка — довідка займала 55–63 % виклику.
   Ціна не в байтах: `збирач_промптів` прямо забороняє приклади-фрази («ЗАБОРОНЕНО»),
   бо на проході 25.09 MamayLM вигадувала факти просто з прикладів промпта, — а
   довідка приносила їх повз збирач у кожен виклик.
   ПИТАННЯ ПРО ЗАСТОСУНОК НЕ ЛИШАЄТЬСЯ БЕЗ ВІДПОВІДІ: у нього свій виклик —
   `помічникП`, і довідку зі станом несе саме він (промпт — `міст_помічниця`, П-4). Куди йде
   репліка, вирішує мовний шар (`внутрішня.question`); у гілці без шару репліка поза
   сценарієм і так іде в `помічникП` (Ч-4: код її слів не читає). */

/* Помічниця поза сценарієм: промпт — зі збирача англійською (`міст_помічниця`, П-4), виклик —
   тієї самої типової моделі, вихід — текст. Мова відповіді — `моваТекстуП`: English із мовним
   шаром (текст жінці пише мовна модель — `мовоюП` чи перекладач репліки), Ukrainian без нього. */
/* ЗАПОБІЖНИК ОБІЦЯНКИ: поза сценарієм сказане в збирання не йде, тож відповідь
   помічниці з «врахуємо» / «запам'ятаю» / «додам до образу» — неправда, і жінка її не бачить:
   замість неї — де це написати. Промпт це теж забороняє, але промпт — побажання моделі.
   П-4: з мовним шаром помічниця пише англійською (внутрішня мова, п.12), тож та сама обіцянка
   ловиться й англійською — у сирій відповіді, ще до перекладу. */
const ОБІЦЯНКА_П = new RegExp('врахуємо|врахую|врахована|врахуються|запам.ятаю|запам.ятала|збережу|'
  + 'візьм(у|емо) до уваги|додам (до|в|у) образ|'
  + "\\b(I|we)(['’]ll| will| shall)(\\s+\\w+){0,2}\\s+(remember|take\\b[^.!?]{0,40}\\binto account|"
  + 'keep\\b[^.!?]{0,30}\\bin mind|add\\b[^.!?]{0,40}\\b(outfit|look)s?\\b)', 'i');
const ЧЕСНО_ДЕ_ПИСАТИ_П = 'Тут я лише відповідаю на питання — у збирання образів ці слова не йдуть, і пообіцяти, '
  + 'що їх буде враховано, я не можу. Щоб річ чи побажання потрапили в образи, напиши це на екрані «Сценарій» — '
  + 'там я додам це до сценарію.';
const моваТекстуП = () => МОДЕЛЬ_МОВИ_П ? 'English' : 'Ukrainian';
async function помічникП(текст, мова){
  const розмова = ЧАТ_П.slice(-9, -1).map(р=>({хто: р.хто, текст: String(р.текст || '').replace(/\s+/g, ' ').slice(0, 400)}));
  const р1 = await містП('помічниця', {питання: String(текст || ''), довідка: довідкаП(), стан: станДляШі(),
                                       розмова, мова_тексту: мова || моваТекстуП()});
  if (!р1 || р1.помилка || !р1.промпт) throw new Error((р1 && р1.помилка) || 'bridge_no_prompt: helper');
  return String(await модельП(р1.промпт) || '').trim();
}

/* ── ЇЇ ПИТАННЯ ПРО ОБРАЗ — СТИЛІСТЦІ З ФОТО Й РЕЧАМИ (М-1, розбір 8/8) ─────────────
   З мовним шаром питання йшло помічниці про застосунок — без фото, речей і вердикту коду,
   і на «чи підійде ця спідниця?» вона казала «я не бачу фото». Тепер перекладач називає,
   про що питання (`question_about`); про образ — сюди: ендпойнт `стилістка` (промпт зі
   збирача, `міст_стилістка`) бачить її речі з паспорта з вердиктом коду й випадок, а
   фото її речей їдуть блоками — найновіше першим (його `вмістити_запит_П` не знімає ніколи),
   боком `СТОРОНА_ФОТО_РЕЧІ_П`, як у кожному виклику над її річчю; стелю моста тримає сам
   `модельП` (наряд Л-2), а що він зменшив чи зняв — у `вміщення`.
   «CASE» — КОДАМИ ПАСПОРТА (п.12): міст бере сам паспорт і сценарій і складає випадок
   тими самими кодами, що опис картки; рядок `ВИПАДОК_ПАСПОРТА_П` (фраза коду українською) сюди не їде.
   Повертає {текст, фото: скільки фото поїхало, вміщення}; збій — кидає (причину пише викликач). */
async function стилісткаП(питання, мова){
  const речі = ((ПАСПОРТ_П || {}).речі_з_фото || []).filter(р => р && р.ід);
  const сирі = [];
  речі.slice().reverse().forEach(р => { const ф = р.фото ? фотоЗаІдП(р.фото) : null;
                                        if (ф && ф.дані && !сирі.includes(ф)) сирі.push(ф); });
  const фото = сирі.length ? await фотоДляЗапитуП(сирі, СТОРОНА_ФОТО_РЕЧІ_П) : [];
  const р1 = await містП('стилістка', {питання: String(питання || ''), речі,
                                       паспорт: ПАСПОРТ_П || null, сценарій: вхідМостаП().сценарій || null,
                                       фото_речей: фото.map(ф => ф.ід),
                                       мова_тексту: мова || моваТекстуП()});
  if (!р1 || р1.помилка || !р1.промпт) throw new Error((р1 && р1.помилка) || 'bridge_no_prompt: stylist');
  const вміщення = {};
  const сира = await модельП(р1.промпт, фото, null, null, вміщення);
  const р2 = await містП('стилістка', {відповідь_моделі: сира});
  if (!р2 || р2.помилка) throw new Error((р2 && р2.помилка) || 'bridge_no_answer: stylist');
  if (!р2.відповідь) throw new Error('stylist_no_answer: ' + (р2.причина || 'empty'));
  return {текст: р2.відповідь, фото: фото.length - ((вміщення.знято || []).length), вміщення};
}

function ростиПоле(поле){
  if (!поле) return;
  поле.style.height = 'auto';
  const лист = !!поле.closest('#сц-лист');
  поле.style.height = Math.max(лист ? 160 : 56, Math.min(поле.scrollHeight || 44, лист ? 320 : 160)) + 'px';
}
/* Панель унизу міняє висоту (поле росте, пілюля чи стрічка, вкладки то є, то
   нема), а відступ під нею стояв константою й накривав низ сторінки. */
/* ── МІСЦЕ ПІД ПАНЕЛЛЮ ──────────────────────────────────────────
   ЩО ЦЕ ЛАГОДИТЬ. `#ніг` — `position:fixed; bottom:0` зі ЗМІННОЮ висотою: поле
   росте, стрічка розгортається, зʼявляються швидкі відповіді, рядок стану, рядок
   голосу, мініатюри фото, вкладки то є, то нема. Місце під нею дає лише
   `body.paddingBottom`. Розійдуться — головна кнопка («Зібрати образи» в картці
   сценарію) лишається ПІД панеллю, і жінка на телефоні до неї не долистає:
   сторінка вже на дні. Куратор зловив це тричі з десяти прогонів
   (`subtree intercepts pointer events`; Playwright гортав і повторював 30 с).

   ДВІ ПОМИЛКИ, І ОБИДВІ — «спитати не в панелі».
   (1) Виклик стояв у двох місцях (`малюватиЧатП` і `oninput` поля), а висоту
       міняє десяток інших подій. Тепер висоту стереже сама панель —
       `ResizeObserver`; де його нема (jsdom), лишаються прямі виклики.
   (2) Умову «панель у колонці, відступ не потрібен» питали в МЕДІА-ЗАПИТУ
       (`широко()`), а не в панелі. Ширина вже ≥ 900, а вузол ще в `body` і ще
       `fixed` — і відступ уже знято. Виміряно на зібраній сторінці: на 1280×720
       до першого `режим()` панель лежить у BODY, `position: fixed`, класу
       `широко` на `<html>` ще нема, а `запас` під кнопкою — мінус 92 px.
       Тепер питаємо ОБЧИСЛЕНИЙ `position` самої панелі: `fixed` — місце
       потрібне, будь-що інше (у колонці вона `sticky`) — ні. */
function відступПідПанель(){
  const п = $('ніг'); if (!п) return;
  const тіло = document.body;
  /* Панель, яка стоїть у потоці колонки (ноутбук), місця під собою не просить —
     і це видно з неї самої, а не з ширини вікна. */
  let фікс = true;
  try{ фікс = getComputedStyle(п).position === 'fixed'; }catch(e){}
  const h = фікс ? (п.offsetHeight || 0) : 0;
  тіло.style.paddingBottom = h ? (h + 20) + 'px' : '';
  тіло.style.setProperty('--під-панеллю', h + 'px');
}
/* Сторож висоти: одне спостереження на всю сторінку, ставиться при першому
   виклику. Без нього кожна нова зміна вмісту панелі знову вимагала б памʼятати
   про відступ — а саме на цьому пам'ять і підвела. */
let СТОРОЖ_ПАНЕЛІ = null;
function стерегтиПанель(){
  if (СТОРОЖ_ПАНЕЛІ || typeof ResizeObserver !== 'function') return;
  const п = $('ніг'); if (!п) return;
  СТОРОЖ_ПАНЕЛІ = new ResizeObserver(()=>відступПідПанель());
  СТОРОЖ_ПАНЕЛІ.observe(п);
}
function перемкнутиРедактор(ід){
  /* Редактор рядка відкривається АРКУШЕМ знизу (v5), а не акордеоном у картці:
     картка лишається списком, а правка — вікном над ним. Рівно один за раз. */
  const е = $(ід); if (!е) return;
  const ряд = document.querySelector('.ряд-паспорта[data-редактор="' + ід + '"]');
  if (АРКУШ && АРКУШ.вузол === е){ закритиАркуш(); return; }
  /* Перший ручний вхід замінює приклади карткою ще до відкриття аркуша:
     його кнопки вже нема. Тоді місце повернення — відповідний рядок картки. */
  const активний = document.activeElement;
  const відкривач = активний !== document.body && активний.getClientRects().length ? активний : ряд;
  відкритиАркуш((ряд && ряд.dataset.назва) || '', е, {відкривач, після: ()=>{ малюватиКарткуСценарію(); }});
  if (ряд) ряд.classList.add('відкрито');
  /* Сходинку помад рахує код, і рахує її Pyodide — тож відкриття редактора саме
     й є моментом, коли її треба просити. Доти тут не було чого просити: кольори
     давав браузер. */
  if (ід === 'ред-макіяж') малюватиМакіяж();
  if (ід === 'ред-мета') малюватиМетуОбразу();
}
function малюватиПрикладиП(){
  const к = $('сц-приклади'); if (!к) return;
  к.innerHTML = '';
  if (ЧАТ_П.length || ПАСПОРТ_П || КАРТКА_РУКОЮ || РЕЖИМ !== 'сценарій') return;
  ПРИКЛАДИ_СЦЕНАРІЮ.forEach(т=>{
    const ч = ел('button', 'приклад', т); ч.type = 'button';
    ч.onclick = ()=>{ const п = $('чат-поле'); if (!п) return; п.value = т; ростиПоле(п); п.focus(); if (window.малюватиЧатП) малюватиЧатП(); };
    к.appendChild(ч);
  });
}
/* Поле одне: на порожньому сценарії воно живе в аркуші листа посеред екрана,
   деінде — в панелі. Переносимо ВУЗОЛ, а не копіюємо: текст, фокус і обробники
   лишаються. */
function розмістити_поле(){
  const в = $('чат-ввід'); if (!в) return false;
  const лист = (РЕЖИМ === 'сценарій' && !ЧАТ_П.length && !ПАСПОРТ_П && !КАРТКА_РУКОЮ);
  const місце = лист ? $('сц-лист-місце') : $('ші-поле-місце');
  if (місце && в.parentNode !== місце) місце.appendChild(в);
  /* Рядок голосу — ЗА полем, тим самим переносом: інакше «Слухаю…» лишалось би
     в панелі, поки поле стоїть в аркуші листа, і жінка читала б його не там. */
  const г = $('чат-голос');
  if (г && місце && г.previousElementSibling !== в) місце.insertBefore(г, в.nextSibling);
  const л = $('сц-лист'); if (л) л.hidden = !лист;
  return лист;
}
/* ШВИДКІ ВІДПОВІДІ: паспорт каже, чого стилістка ще не знає (`невідомо`), а
   довідник дає слова. Тап шле слово як репліку — тим самим шляхом, що й
   написане рукою, тож наступну відповідь і паспорт складає та сама модель. */
const ШВИДКІ_ВІДПОВІДІ = {
  'дрес_код': ()=>(ДОВІДНИК.коди||[]).filter(о=>о.плитка).map(о=>о.підпис.toLowerCase()),
  'місце':    ()=>(ДОВІДНИК.місця||[]).filter(о=>о.плитка).map(о=>о.підпис.toLowerCase()),
  'нагода':   ()=>(ДОВІДНИК.нагоди||[]).filter(о=>о.плитка).map(о=>о.підпис.toLowerCase()),
  'опади':    ()=>['без опадів', 'дощ', 'сніг'],
  'година':   ()=>['вранці', 'вдень', 'ввечері']};
function малюватиШвидкіП(){
  const к = $('сц-швидкі'); if (!к) return;
  к.innerHTML = '';
  if (РЕЖИМ !== 'сценарій' || !ПАСПОРТ_П || !ЧАТ_П.length || ЧАТ_П[ЧАТ_П.length - 1].хто !== 'ші') return;
  const поле = (ПАСПОРТ_П.невідомо || []).find(п=>ШВИДКІ_ВІДПОВІДІ[п]);
  if (!поле) return;
  const слова = ШВИДКІ_ВІДПОВІДІ[поле]().filter(Boolean).slice(0, 7);
  if (!слова.length) return;
  слова.concat(['на твій розсуд']).forEach(т=>{
    const ч = ел('span', 'чип', т); ч.setAttribute('role', 'button'); ч.tabIndex = 0;
    const дія = ()=>{ const п = $('чат-поле'); if (!п || п.disabled) return; п.value = т; слатиЧатП(); };
    ч.onclick = дія;
    ч.onkeydown = e=>{ if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); дія(); } };
    к.appendChild(ч);
  });
}
function малюватиЧатП(){
  const с = $('чат-стрічка'); if (!с) return;
  розмістити_стрічку();
  const лист = розмістити_поле();
  с.innerHTML = '';
  ЧАТ_П.forEach(р=>{
    const фото = (р.хто !== 'ші' && р.фото || []).filter(ф=>ф && ф.дані);
    if (!фото.length){
      const б = ел('div', 'репліка ' + (р.хто === 'ші' ? 'ші' : 'вона'), р.текст);
      if (р.хто === 'ші' && р.порада_питанням) б.appendChild(ел('span', 'порада-нота', ПОРАДА_НЕОБОВʼЯЗКОВА_П));
      с.appendChild(б); return; }
    /* ФОТО РЕЧІ В ЇЇ РЕПЛІЦІ: мініатюри над словами; без слів — лише фото */
    const б = ел('div', 'репліка вона');
    const ряд = ел('div', 'фото-репліки');
    фото.forEach(ф=>{ const і = ел('img'); і.src = 'data:' + (ф.тип || 'image/jpeg') + ';base64,' + ф.дані;
                      і.alt = 'фото речі'; і.dataset.фото = ф.ід; ряд.appendChild(і); });
    б.appendChild(ряд);
    if (String(р.текст || '').trim()) б.appendChild(document.createTextNode(р.текст));
    с.appendChild(б);
  });
  const є = ЧАТ_П.length > 0, дім = (РЕЖИМ === 'сценарій');
  /* На сценарії поле розгорнуте завжди (в аркуші листа або в панелі), стрічка —
     в екрані. Деінде — пілюля з останньою відповіддю; тап розгортає стрічку й поле. */
  const розгорнуто = дім || ШІ_РОЗГОРНУТО;
  /* НА ЕКРАНІ ОЦІНКИ ПАНЕЛІ СТИЛІСТКИ НЕМА (Л-6): питання про її образ ставиться під
     карткою оцінки, де модель бачить фото й суд коду. Пілюля тут вела б його помічниці
     застосунку без фото — рівно та вада, з якої почався наряд (В-2, В-3). */
  const оц = (РЕЖИМ === 'оцінка');
  const піл = $('ші-пілюля'), арк = $('ші-аркуш'), ввід = $('чат-ввід');
  if (піл){
    піл.hidden = розгорнуто || оц;
    const о = ЧАТ_П.slice().reverse().find(р=>р.хто === 'ші');
    const т = $('ші-пілюля-текст'); if (т) т.textContent = о ? String(о.текст || '').replace(/\s+/g, ' ') : 'Спитати стилістку';
  }
  if (арк){ арк.hidden = оц || !(розгорнуто && !дім); if (!арк.hidden){ const стр = $('ші-стрічка'); if (стр) стр.scrollTop = стр.scrollHeight; } }
  if (ввід) ввід.hidden = оц || !розгорнуто;
  const поле = $('чат-поле'), кн = $('чат-слати');
  const вичерпано = людськихРеплікП() >= ЧАТ_ЛІМІТ_П;
  if (поле){ поле.disabled = вичерпано; поле.placeholder = лист ? ПІДКАЗКА_ЛИСТА : (ПІДКАЗКИ_ШІ[РЕЖИМ] || ПІДКАЗКИ_ШІ.інше); }
  if (кн){ кн.disabled = вичерпано; кн.classList.toggle('порожньо', !(поле && поле.value.trim()) && !ФОТО_ВКЛАДЕНІ_П.length); }
  /* Фото речі йде в замовлення (виклик 0), тож кнопка стоїть там, де репліка стає
     замовленням: на сценарії — в аркуші листа й у панелі. Деінде репліка — питання
     до помічниці про застосунок, і фото речі там нема куди прийняти. */
  { const фк = $('чат-фото'); if (фк) фк.hidden = !дім;
    const фв = $('чат-фото-вхід'); if (фв) фв.disabled = вичерпано; }
  if (!дім && ФОТО_ВКЛАДЕНІ_П.length){ ФОТО_ВКЛАДЕНІ_П = []; малюватиВкладенняП(); }
  /* ГОЛОС — НА ВІДМІНУ ВІД ФОТО, НА ВСІХ ЕКРАНАХ: питання до
     помічниці теж пишуть словами, і диктувати їх можна так само. Закривається
     мікрофон лише разом із полем, коли повідомлення вичерпано: тоді писати нікуди,
     і це не мертва кнопка (п.9), а закритий увесь ввід — чому, каже `#чат-стан`. */
  { const мк = $('чат-мікрофон'); if (мк) мк.disabled = вичерпано; }
  малюватиПрикладиП();
  малюватиШвидкіП();
  /* заголовок-питання потрібен лише до першого слова */
  { const в = $('сц-вступ'); if (в) в.style.display = лист ? '' : 'none'; }
  малюватиУвагуП();
  малюватиКарткуСценарію();
  малюватиЗрозумілаП();
  відступПідПанель();
}
/* Панель унизу міняє висоту (поле росте, ряд дій то є, то нема), а відступ під
   нею стояв константою — і на сценарії панель накривала назву сценарію. */
/* «Я ЗРОЗУМІЛА ТАК: …» — ТОЙ САМИЙ РЯДОК, ЩО ПОЇДЕ В ШАПКУ ОБРАЗІВ І В ЖУРНАЛ
   (`випадокРядком`, вона бере паспорт першим). Кнопки не міняють даних: «так»
   знімає питання, «поправити» повертає курсор у чат. Підтвердження — не мовчазна
   згода: доти паспорт узагалі не показувався жінці до збирання. */
function малюватиЗрозумілаП(){
  const е = $('сц-зрозуміла'); if (!е) return;
  const рядок = ВИПАДОК_ПАСПОРТА_П || '';
  /* Підтверджене питання зникає: картка вище й є відповідь. Доти тут стояв
     ПОВТОРНИЙ переказ випадку словами — те саме, що в рядках картки, двічі. */
  if (!рядок || ВИПАДОК_ПІДТВЕРДЖЕНО_П){ е.style.display = 'none'; е.textContent = ''; return; }
  е.innerHTML = '';
  е.appendChild(ел('span', null, 'Усе правильно?'));
  {
    const так = ел('button', 'текст', 'так'); так.type = 'button';
    так.onclick = ()=>{ ВИПАДОК_ПІДТВЕРДЖЕНО_П = true; малюватиЗрозумілаП(); малюватиКарткуСценарію(); };
    const поп = ел('button', 'текст', 'поправити'); поп.type = 'button';
    поп.onclick = ()=>{
      const п = $('чат-поле'), ст = $('чат-стан');
      if (п && !п.disabled){ ШІ_РОЗГОРНУТО = true; малюватиЧатП(); п.focus(); if (ст) ст.textContent = 'Скажи, що не так, — я перепишу паспорт.'; }
      else if (ст) ст.textContent = 'Повідомлення вичерпано — поправ плитки й списки нижче.';
    };
    е.appendChild(так); е.appendChild(поп);
  }
  е.style.display = 'flex';
}

/* ПЛИТКИ Й СПИСКИ ПЕРЕМАЛЬОВУЮТЬСЯ ЗІ СТАНУ ПАСПОРТА (Т-08 крок 4). Ключ, якого
   нема в довіднику, НЕ ставиться: інакше `сц-нагода` дістав би слово, якого суд
   не знає, і плитка світилась би порожньою, а рядок «Візьмемо: …» брехав би. */
function застосуватиПаспортДоЕкрана(п){
  if (!п) return;
  try{ return застосуватиПаспортДоЕкранаВтіло(чиннийПаспортП(п)); } finally {
    малюватиКарткуСценарію();
    завершитиДіюЯдра('паспорт', п);
  }
}
function застосуватиПаспортДоЕкранаВтіло(п){
  КАРТКА_ЗАПИТУ_П = JSON.parse(JSON.stringify(п.картка_запиту || карткаДавньогоПаспортаП(п)));
  ПОДІЇ_РУКИ_П = [];
  const став = (ід, знач)=>{ const е = $(ід);
    if (е && знач != null && знач !== '' && знач !== 'невідомо') е.value = знач; };
  /* ТИПОВА НАГОДА РЕЧІ З ФОТО на плитку не лягає: це не її вибір, а «звичайний
     день», на який код судить річ, поки нагоди не названо. Плитка лишається порожньою, а
     рядок картки каже «типово для речі з фото» (`малюватиКарткуСценарію`). */
  const _типова = ((п.джерело_полів || {}).нагода === ТИПОВА_НАГОДА_РЕЧІ_П);
  /* Відхилену нагоду знімаємо також із джерела наступного входу. */
  if (п.нагода == null && (п.джерело_полів || {}).нагода === 'occasion_part_conflict'
      && $('сц-нагода').value === 'спорт') $('сц-нагода').value = '';
  if (!_типова && знайти(ДОВІДНИК.нагоди, п.нагода)) став('сц-нагода', п.нагода);
  if (знайти(ДОВІДНИК.місця, п.місце)) став('сц-місце', п.місце);
  if (знайти(ДОВІДНИК.коди, п.дрес_код)) став('сц-дрес', п.дрес_код);
  /* 3.2-В: розмова й екран пишуть в один `ВИБІР`. Тому вхід стилістки
     бере тріаду так само, ніби вона торкнулася плитки; паспорт і запит більше не розходяться. */
  if (п.схема){
    ВИБІР.схема = п.схема;
    ВИБІР.гілка = null;
    словоПалітри('схема', п.схема.replaceAll('_', ' '));
    малюватиПалітруКоротко();
  }
  if (п.година != null && isFinite(п.година)){ став('сц-година', п.година); $('сц-хвилини').value = String(п.хвилини > 0 ? п.хвилини : 0); }
  if (п.темп_c != null && isFinite(п.темп_c)) став('сц-темп', п.темп_c);
  /* паспорт, що несе погоду (градуси чи відчуття), переписує плитку відчуття — як решту плиток */
  if (($('сц-відчуття') || {}).value && ((п.темп_c != null && isFinite(п.темп_c)) || ВІДЧУТТЯ_П[п.погода_відчуття])) $('сц-відчуття').value = '';
  /* ЧИСЛО З ЇЇ СЛІВ ПЕРЕСТАЄ БУТИ ТИПОВИМ (В-2). Поле сюди прийшло з паспорта, а
     паспорт каже, звідки воно: «рука» чи «розмова» — вона його назвала; мітка
     типового — ні, і тоді поле лишається типовим, хоч значення й перемальовано. */
  /* Точні коди паспорта беруться зі спільного погодного договору.
     «так» — лише сумісність старого входу; підписи й підмножина плиток сталі. */
  if (п.опади === 'ні') став('сц-опади', 'ні');
  else if (п.опади === 'так')
    став('сц-опади', (parseFloat($('сц-темп').value) <= 0) ? 'сніг' : 'дощ');
  /* М-5: паспорт мовної моделі несе її ТОНКЕ слово опадів (`мовний_шар.паспорт_з_шару`) — плитка бере
     найближче своє: сніг — сніг; дощ, злива, мокрий сніг — дощ (код однаково читає слово паспорта) */
  else if (['дощ', 'злива', 'мокрий_сніг', 'сніг'].includes(п.опади))
    став('сц-опади', п.опади === 'сніг' ? 'сніг' : 'дощ');
  /* «можливо дощ» — своєю плиткою, а не порожньою: інакше на картці його не було б */
  else if (п.опади === 'можливий_дощ') став('сц-опади', 'можливий_дощ');
  /* ── ЗОНА МОДЕЛІ НЕ СТАЄ ЧИПОМ ЖІНКИ ───────────────
     Поле `сц-вето-зони` — це те, з чого `зібратиВхід` бере «чипи», і коментар над
     ним каже прямо: «ЧИПИ — ТВЕРДЖЕННЯ ЛЮДИНИ, А НЕ ЗДОГАД МОДЕЛІ». Проте сюди
     клалась будь-яка зона з паспорта, зокрема та, яку вигадала модель: у вході
     наступного виклику стояло `"вето":{"зони":["ноги"]}`, і `паспорт_з_json`
     читав це як ЧИП — тобто здогад моделі повертався до коду з печаткою її руки
     й проходив гейт зон (прохід тестувальниці, З-2).
     Беремо лише ЧИННІ зони: те, що код справді тримає межею. Вони або її чип
     (тоді поле й так їх несло), або її слово — і в обох випадках це її
     твердження, а не здогад. Старий паспорт без `вето_тверде` — як доти. */
  const _тв = п.вето_тверде;
  const зони = ((_тв ? _тв.зони : (п.вето||{}).зони) || []).filter(з=>ЗОНИ_ВЕТО_П.indexOf(з) >= 0);
  if (зони.length) $('сц-вето-зони').value = зони.join(',');
  /* МАКІЯЖ — ПЛИТКА ЗІ СТАНУ ПАСПОРТА: той самий ключ і формат, що
     `сц.макіяж` у `зібратиВхід` ({рівень, губи?}); паспорт переписує плитку так само,
     як нагоду, а дотик рукою після паспорта переважає (`поля_рукою` у паспорті). */
  const мк = п.макіяж;
  if (мк && МАКІЯЖ.some(([к])=>к === мк.рівень)){
    став('сц-макіяж', мк.рівень);
    if (мк.рівень !== 'нюд' && /^#[0-9a-fA-F]{6}$/.test(мк.губи || '')){ $('сц-губи').value = мк.губи; $('сц-губи-обрано').value = ГУБИ_НАЗВАНО_П; }
  }
  /* ПРИКРАСИ — так само: паспорт переписує плитку, дотик рукою після
     паспорта переважає (`паспорт_нагоди.ПОЛЯ_ПЛИТОК` несе «прикраси» з 21.09).
     «невідомо» й «інші» плитки не мають: перше — мовчання, друге — залишковий клас
     слів розмови, і підставляти під нього чужу плитку означало б збрехати про вибір. */
  if (ПРИКРАСИ_П.some(([к])=>к === п.прикраси)) став('сц-прикраси', п.прикраси);
  /* МЕТА — так само (ПК-1): код мети зі слів жінки стає плиткою, дотик рукою після паспорта переважає */
  метаНаОсіП(п);
  if (МЕТА_П.some(([к])=>к === п.мета)) став('сц-мета', п.мета);
  /* Друга вісь і зони — так само, списками; порожній список у паспорті плиток не стирає */
  if (Array.isArray(п.мета_важливо) && п.мета_важливо.length) $('сц-мета-важливо').value = п.мета_важливо.join(',');
  if (Array.isArray(п.мета_зони) && п.мета_зони.length)
    $('сц-мета-зони').value = п.мета_зони.filter(з=>з in МЕТА_ЗОНИ_П).join(',');
  малюватиПлитки(); оновитиДіапазон();
  /* паспорт моделі з числом ошатності сам несе те, що дав би хід плиток (він і є джерелом картки та збирання) */
  зберегтиВипадок(п.джерело === 'модель' && Array.isArray(п.ошатність));
  ВИПАДОК_ЗМІНЕНО_П = false;
  малюватиКарткуСценарію();   // прапор знято — картка читає паспорт саме тепер
}
