import fs from 'fs';
const сир = fs.readFileSync('/home/user/kod-shi-data/джерела/worker.js','utf-8')
  .replace(/export\s*\{\s*worker_default as default\s*\}\s*;?/, 'const М = worker_default;')
  .replace(/^export default/m, 'const М =');
fs.writeFileSync('/tmp/_мод.mjs', сир + '\nexport {М};');
const {М} = await import('/tmp/_мод.mjs');
const в = await М.fetch(new Request('https://w.workers.dev/', {method:'GET'}), {});
if (в.status !== 200) throw new Error('GET віддав ' + в.status);
fs.writeFileSync('/tmp/_стор.html', await в.text());
