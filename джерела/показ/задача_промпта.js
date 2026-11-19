/* ЗАДАЧА ПРОМПТА — ОДНЕ ВИЗНАЧЕННЯ (Е2-межі п.4). Мітки «answer» з ім'ям задачі в «task» нема: від неї модель загортала
   відповідь, і її несуть лише руки 3–4 (власник 16.10, рядок 6201; рішення 14417). Задачу називає форма самого
   промпта — ключі «answer_schema» (останнім ключем чи в «task»), дані чи роль. Читачі — журнал стадій (`показ/міст.js`,
   `стадіяВикликуП`) і стенд (`аудит/проби/види_речей.js`, `відповідьЗадачі`, через `require`): доти кожен тримав свій
   перелік, і стенд розійшовся з кодом (14432, 14438). Ім'я — латинкою, як мітка, що стояла в промпті
   (`протокол.НАЗВИ_ВІДПОВІДІ_EN`); перекладачки входу — `verdict_comment`, `question`, `review_items_fix`.
   Без DOM і без розбору тексту: на вході — уже розібраний обʼєкт промпта. */
/* порядок — пріоритет: ремонт має й «chosen», і «outfits», а він — складання/ремонт */
const ЗАДАЧІ_ЗА_СХЕМОЮ_П = [['outfits', 'OUTFITS_V1'], ['chosen', 'CHOICE_V1'], ['verdict', 'OUTFIT_REVIEW_V1'],
  ['ratings', 'ITEM_RATINGS_V1'], ['winners', 'TOURNAMENT_V1'], ['fixes', 'COMPLETION_V1'],
  ['how_to_wear', 'DESCRIPTION_V1'], ['need', 'ХІД_РОЗМОВИ'], ['invite_topics', 'ПОРАДА_ХОДУ'],
  ['actions', 'review_items_fix'], ['skin', 'PORTRAIT_COLOURS'], ['item_type', 'CATALOG_PARSE_V3'],
  ['подія', 'ПАСПОРТ'], ['scheme', 'PALETTE_CHOICE'], ['is_outfit', 'ITEM_LIST']];
const ЗАДАЧІ_ЗА_ДАНИМИ_П = [['her_comment', 'verdict_comment'], ['her_question', 'question']];
const ЗАДАЧІ_ЗА_РОЛЛЮ_П = [[/^Photo 1 is a woman/, 'TRY_ON_IMAGE'], [/ Help her with /, 'APP_ANSWER'],
  [/ She has asked you /, 'LOOK_ANSWER'], [/^You are a personal stylist/, 'OUTFIT_TEXT']];
function задачаПромптаП(об){
  if (!об || typeof об !== 'object') return null;
  const з = об.завдання || об.task;
  if (!з || typeof з !== 'object') return null;
  const м = з.відповідь || з.answer;
  if (typeof м === 'string' && м) return м;
  if (!об.task) return null;
  const с = об.answer_schema || об.task.answer_schema;
  const схема = !!(с && typeof с === 'object' && !Array.isArray(с));
  const є = к => схема && к in с;
  /* Рядок 6450: оцінка образу — скелет наприкінці; її схема має «verdict», а допит на її місці — лише «answer»
     з хвостом «now» (ті самі дані: «outfit», «check») — обидва звуться OUTFIT_REVIEW_V1 */
  if (об.answer_schema && об.outfit && об.check && (є('verdict') || об.now)) return 'OUTFIT_REVIEW_V1';
  /* речі на фото має схема з «items» і дані «photos» */
  if (є('items') && об.photos) return 'PHOTO_ITEMS';
  if (схема && Object.keys(с).join() === 'update') return 'ХІД_ПЛИТОК';
  const зс = ЗАДАЧІ_ЗА_СХЕМОЮ_П.find(([к]) => є(к));
  if (зс) return зс[1];
  const зд = ЗАДАЧІ_ЗА_ДАНИМИ_П.find(([к]) => к in об);
  if (зд) return зд[1];
  const зр = ЗАДАЧІ_ЗА_РОЛЛЮ_П.find(([р]) => р.test(String(об.task.role || '')));
  return зр ? зр[1] : null;
}
if (typeof module === 'object' && module && module.exports) module.exports = {задачаПромптаП};
