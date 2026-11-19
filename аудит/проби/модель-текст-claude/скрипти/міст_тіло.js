// Тіло, яке міст шле Anthropic: код моста (`джерела/worker_джерело.js`, ПРОВАЙДЕРИ[claude-].запит) без змін.
// Запуск: node міст_тіло.js <worker_джерело.js> [CLAUDE_EFFORT моста, типово — як у мосту без змінної]
// stdin: JSONL {id, запит(рядок тіла сторінки)}; stdout: JSONL {id, тіло}. Змінну середовища CLAUDE_EFFORT
// не читає навмисно: сесія Claude Code ставить її собі (/effort), і тіло вийшло б не тим, що в мосту.
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8').replace(/^export default\s*\{/m, 'var __воркер = {');
const ctx = {console}; vm.createContext(ctx);
vm.runInContext(src + '\n;this.ПРОВАЙДЕРИ = ПРОВАЙДЕРИ; this.СТЕЛЯ = СТЕЛЯ_ВИХОДУ;', ctx);
const пров = ctx.ПРОВАЙДЕРИ.find(x => x.префікс === 'claude-');
for (const l of fs.readFileSync(0, 'utf8').split('\n').filter(Boolean)) {
  const {id, запит} = JSON.parse(l); const т = JSON.parse(запит);
  т.max_tokens = Math.min(Number(т.max_tokens) || ctx.СТЕЛЯ, ctx.СТЕЛЯ);
  // каскад моста ставить першу форму мислення (`пров.думки`), якщо вона в провайдера є
  const форми = пров.думки ? пров.думки(process.argv[3]) : [];
  т._думки = форми.length ? форми[0] : null;
  process.stdout.write(JSON.stringify({id, тіло: пров.запит(т)}) + '\n');
}
