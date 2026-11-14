/* Справжні Python-читач, повтор і злиття; замінено лише відповіді моделі. */
const fs = require('fs'), path = require('path'), Module = require('module');
const root = path.resolve(__dirname, '../../../..'), source = path.join(root, 'джерела');
const file = path.join(source, 'тест_показу.js'), code = fs.readFileSync(file, 'utf8');
const mod = new Module(file); mod.filename = file; mod.paths = Module._nodeModulePaths(source);
mod._compile(code.slice(0, code.indexOf('(async () => {')) + '\nmodule.exports={сторінка,моваПітона,чекатиСтарт};', file);
(async () => {
  const {сторінка, моваПітона, чекатиСтарт} = mod.exports;
  for (const хибний of [false, true]){
    const {w, помилки} = сторінка({url:'https://example.test/'}); await чекатиСтарт(w);
    const промпти = [];
    w._міст = async (_, д) => моваПітона(д);
    w._модель = async п => { промпти.push(п); return промпти.length === 1 || хибний
      ? '{"1":"Перша." "2":"Друга."}' : '{"1":"Тримай сумку в руці.","2":"Носи жакет розстебнутим."}'; };
    w.eval('містП=(...а)=>window._міст(...а); модельМовиП=(...а)=>window._модель(...а);');
    const вих = await w.eval("мовоюП({опис:'Hold the bag in your hand.', порада:'Wear the jacket open.'}, 'schema')");
    console.log(JSON.stringify({хибний, викликів:промпти.length, повтор:промпти[1]?.split('ТЕКСТИ:')[0].split('Розбіжність попередньої відповіді:')[1], вих, помилки}));
    w.close();
  }
})().catch(error => { console.error(error); process.exitCode=1; });
