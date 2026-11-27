/* Зводить завершені частини приймання в один вердикт CI. */
const fs = require('node:fs');

/** Рахує сцени зі звітів усіх частин і друкує вердикт у журналі та підсумку CI. */
function підбитиПідсумок(файли) {
  if (!файли.length) throw new Error('Вжиток: node підсумок_відтворення.js <звіт частини> ...');
  const сцени = файли.flatMap(файл => {
    const звіт = JSON.parse(fs.readFileSync(файл, 'utf8'));
    if (!Array.isArray(звіт)) throw new Error('Нема списку сцен у звіті частини: ' + файл);
    return звіт;
  });
  const неВиміряно = [];
  const відмови = [];
  const безЗміниПродукту = process.env.REPLAY_PRODUCT === 'false';
  let єРегрес = false;
  for (const сцена of сцени) {
    switch (сцена?.стан) {
      case 'застарів у main': неВиміряно.push(сцена); break;
      case 'запис застарів':
        if (безЗміниПродукту) відмови.push(`${сцена.сцена} — застарілий запис у PR без зміни продукту`);
        else if (сцена.різниця_запиту?.length) неВиміряно.push(сцена);
        else відмови.push(`${сцена.сцена} — застарілий запис, зміна запиту не доведена`);
        break;
      case 'регрес': єРегрес = true; break;
      case 'без регресу': break;
      default: throw new Error('Невідомий стан відтворення сцени: ' + сцена?.стан);
    }
  }
  const застаріло = неВиміряно.length + відмови.length;
  const порівняно = сцени.length - застаріло;
  const заголовок = порівняно
    ? `порівняно ${порівняно} з ${сцени.length}; застаріло ${застаріло}`
    : `порівняних сцен 0 з ${сцени.length}: відтворення нічого не виміряло; потрібні свіжі записи (нічний набір)`;
  const рядки = [заголовок];
  for (const сцена of неВиміряно) {
    const причина = сцена.стан === 'застарів у main' ? сцена.стан : 'PR змінив запит';
    рядки.push(`- ${сцена.сцена} — не виміряно (${причина})`);
  }
  for (const відмова of відмови) рядки.push(`- ${відмова}`);
  const приклад = сцени.find(сцена => сцена.різниця_запиту?.length);
  if (приклад) {
    рядки.push(`\nЗапит ДО → ПІСЛЯ (${приклад.сцена}, виклик ${приклад.виклик})`, '');
    for (const {поле, до, після} of приклад.різниця_запиту) рядки.push(`    ${поле}: ${до} → ${після}`);
  }
  const вивід = рядки.join('\n');
  console.log(вивід);
  if (process.env.GITHUB_STEP_SUMMARY) fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, вивід + '\n');
  return !сцени.length || єРегрес || відмови.length ? 1 : 0;
}

if (require.main === module) {
  try { process.exitCode = підбитиПідсумок(process.argv.slice(2)); }
  catch (помилка) { console.error(помилка.message); process.exitCode = 1; }
}
