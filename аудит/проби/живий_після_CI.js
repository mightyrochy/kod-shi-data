/* Перевіряє обіцянку живого прогону, якщо приймання виявило застарілий запис. */
const fs = require('fs'), path = require('path');

function погоджено(опис) {
  return /^\s*ЖИВИЙ ПІСЛЯ:[^\S\r\n]+\S[^\r\n]*$/m.test(опис || '');
}

async function погодженняПушу(подія) {
  const sha = подія?.after, репозиторій = подія?.repository?.full_name;
  if (подія?.ref !== 'refs/heads/main' || !/^[0-9a-f]{40}$/.test(sha || '') ||
      репозиторій !== process.env.GITHUB_REPOSITORY) return false;
  if (подія.head_commit?.id === sha && погоджено(подія.head_commit.message)) return true;
  // Merge, squash і rebase прив'язують погодження до точної голови push, а не до сусіднього PR.
  const заголовки = {Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'};
  if (process.env.GITHUB_TOKEN) заголовки.Authorization = 'Bearer ' + process.env.GITHUB_TOKEN;
  for (let сторінка = 1; ; сторінка++) {
    const відповідь = await fetch(`${process.env.GITHUB_API_URL || 'https://api.github.com'}/repos/${репозиторій}/commits/${sha}/pulls?per_page=100&page=${сторінка}`,
      {headers: заголовки, signal: AbortSignal.timeout(30000)});
    if (!відповідь.ok) throw new Error('Не отримано погодження злитого PR: GitHub HTTP ' + відповідь.status);
    const запити = await відповідь.json();
    if (запити.some(пр => пр.merged_at && пр.merge_commit_sha === sha && пр.base?.ref === 'main' &&
        пр.base.repo?.full_name === репозиторій && пр.head?.repo?.full_name === репозиторій &&
        пр.user?.login === 'mightyrochy' && погоджено(пр.body))) return true;
    if (запити.length < 100) return false;
  }
}

async function перевірити(тека, подія) {
  const підсумок = JSON.parse(fs.readFileSync(path.join(тека, 'підсумок.json'), 'utf8'));
  if (підсумок.some(р => р.стан === 'регрес')) throw new Error('Приймання виявило регрес');
  if (!підсумок.some(р => р.стан === 'запис застарів')) return;
  const єПогодження = подія?.pull_request ? погоджено(подія.pull_request.body) : await погодженняПушу(подія);
  if (!єПогодження)
    throw new Error('Запис застарів: потрібний рядок ЖИВИЙ ПІСЛЯ: <сцена> — <питання> в описі PR або погодження для голови push');
}

if (require.main === module) {
  (async () => {
    const подія = process.env.GITHUB_EVENT_PATH
      ? JSON.parse(fs.readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8')) : null;
    await перевірити(process.argv[2], подія);
    console.log('✔ приймання та погодження живого прогону узгоджені');
  })().catch(помилка => { console.error(помилка.message); process.exitCode = 1; });
}
module.exports = {перевірити};
