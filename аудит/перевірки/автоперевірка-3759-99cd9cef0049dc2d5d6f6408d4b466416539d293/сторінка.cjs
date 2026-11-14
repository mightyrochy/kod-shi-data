const fs = require('fs');
const path = require('path');
const src = path.join(process.argv[2] ? path.resolve(process.argv[2]) : path.join(__dirname, 'pr3759'), 'джерела');
const out = process.argv[3] ? path.resolve(process.argv[3]) : path.join(__dirname, 'evidence3759');
const h = require(path.join(src, 'показ_шаблон.js'));
let html = h.підставитиШаблон(fs.readFileSync(path.join(src, 'показ.html'), 'utf8'), {
  __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'перевірка-3759', __ВІДБИТОК__: '3759',
  __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: h.прочитатиДовідникJSON(src)
});
html = html.replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^\"]*"[^>]*><\/script>/,
                    '<script>window.loadPyodide=null;</script>');
fs.mkdirSync(out, {recursive: true});
fs.writeFileSync(path.join(out, 'head.html'), html);
