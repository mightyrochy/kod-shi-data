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
  let застаріло = 0;
  let єРегрес = false;
  for (const сцена of сцени) {
    switch (сцена?.стан) {
      case 'застарів у main':
      case 'запис застарів': застаріло++; break;
      case 'регрес': єРегрес = true; break;
      case 'без регресу': break;
      default: throw new Error('Невідомий стан відтворення сцени: ' + сцена?.стан);
    }
  }
  const порівняно = сцени.length - застаріло;
  const рядок = порівняно
    ? `порівняно ${порівняно} з ${сцени.length}; застаріло ${застаріло}`
    : `порівняних сцен 0 з ${сцени.length}: відтворення нічого не виміряло; потрібні свіжі записи (нічний набір)`;
  console.log(рядок);
  if (process.env.GITHUB_STEP_SUMMARY) fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, рядок + '\n');
  return порівняно === 0 || єРегрес ? 1 : 0;
}

if (require.main === module) {
  try { process.exitCode = підбитиПідсумок(process.argv.slice(2)); }
  catch (помилка) { console.error(помилка.message); process.exitCode = 1; }
}
