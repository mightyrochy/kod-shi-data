/* Перевіряє обіцянку живого прогону, якщо приймання виявило застарілий запис. */
const fs = require('fs'), path = require('path');

function перевірити(тека, подія) {
  const підсумок = JSON.parse(fs.readFileSync(path.join(тека, 'підсумок.json'), 'utf8'));
  if (підсумок.some(р => р.стан === 'регрес')) throw new Error('Приймання виявило регрес');
  if (!підсумок.some(р => р.стан === 'запис застарів')) return;
  const опис = подія?.pull_request?.body || '';
  if (!/^\s*ЖИВИЙ ПІСЛЯ:[^\S\r\n]+\S[^\r\n]*$/m.test(опис))
    throw new Error('Запис застарів: в описі PR потрібний рядок ЖИВИЙ ПІСЛЯ: <сцена> — <питання>');
}

if (require.main === module) {
  try {
    const подія = process.env.GITHUB_EVENT_PATH
      ? JSON.parse(fs.readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8')) : null;
    перевірити(process.argv[2], подія);
    console.log('✔ приймання та опис PR узгоджені');
  } catch (помилка) { console.error(помилка.message); process.exitCode = 1; }
}
module.exports = {перевірити};
