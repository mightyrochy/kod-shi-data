/* Додаткове питання після записаної розмови. Виконує незмінену функцію показу зі збірки;
   міст Python справжній; виклик моделі справжній. Це проба каналу, не другий прогін сцени. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const {spawnSync} = require('child_process');
const [build, output, historyFile, python] = process.argv.slice(2);
const html = fs.readFileSync(path.join(build, 'index.html'), 'utf8');
const start = html.indexOf('async function помічникП(');
const end = html.indexOf('\n}', start) + 2;
if (start < 0 || end < start) throw Error('Функцію показу не знайдено');
const question = 'Що я казала про зал на початку?';
const history = JSON.parse(fs.readFileSync(historyFile, 'utf8'));
const evidence = {питання: question, історія: history, функція: html.slice(start, end)};
const context = vm.createContext({
  ЧАТ_П: [...history, {хто: 'людина', текст: question}],
  довідкаП: () => '', станДляШі: () => ({екран: 'палітра'}), моваТекстуП: () => 'English',
  містП: async (name, input) => {
    if (name !== 'помічниця') throw Error(name);
    const result = spawnSync(python, [path.join(__dirname, 'помічниця_після.py'), '--міст'],
      {input: JSON.stringify(input), encoding: 'utf8', windowsHide: true});
    if (result.status !== 0) throw Error(result.stderr);
    if (input.розмова) evidence.вхід_моста = input;
    return JSON.parse(result.stdout);
  },
  модельП: async prompt => {
    evidence.промпт = JSON.parse(prompt);
    const request = {model: 'qwen/qwen3.5-9b', messages: [{role: 'user', content: prompt}],
      max_tokens: 1000, temperature: 0, reasoning_effort: 'none'};
    evidence.запит = request;
    const response = await fetch('http://127.0.0.1:1235/v1/chat/completions', {
      method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(request)});
    evidence.http = response.status;
    evidence.відповідь = await response.json();
    if (!response.ok) throw Error(JSON.stringify(evidence.відповідь));
    return evidence.відповідь.choices[0].message.content;
  }
});
(async () => {
  try {
    vm.runInContext(html.slice(start, end), context);
    evidence.результат = await vm.runInContext('помічникП(' + JSON.stringify(question) + ')', context);
    const carried = evidence.вхід_моста.розмова;
    evidence.всі_репліки_дослівно = JSON.stringify(carried) === JSON.stringify(history);
    if (!evidence.всі_репліки_дослівно) process.exitCode = 1;
  } catch (error) { evidence.помилка = String(error); process.exitCode = 2; }
  fs.writeFileSync(output, JSON.stringify(evidence, null, 1) + '\n');
  console.log(JSON.stringify({http: evidence.http, реплік: history.length,
    всі_репліки_дослівно: evidence.всі_репліки_дослівно, результат: evidence.результат,
    помилка: evidence.помилка}));
})();
