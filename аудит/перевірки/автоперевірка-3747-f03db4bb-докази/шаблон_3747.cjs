const fs = require('fs'), path = require('path');
const root = path.resolve(process.argv[2]);
const m = require(path.join(root, 'джерела/показ_шаблон.js'));
const values = {__МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'перевірка-3747',
  __ВІДБИТОК__: 'f03db4bb', __ФІД_ПОКАЗУ__: 'каталог.xml', __КАТАЛОГ_ПОКАЗУ__: 'контроль фікстури RicaMare',
  __ДОВІДНИК_ПОКАЗУ__: fs.readFileSync(process.argv[4], 'utf8'),
  __ПРОМПТ_КОЛІР_ПОКАЗУ__: '', __ВИБІРКА_ПОКАЗУ__: '{}'};
let html = m.підставитиШаблон(fs.readFileSync(path.join(root, 'джерела/показ.html'),'utf8'), values);
html = html.replace(/<script[^>]*src="https:[^"]*"[^>]*><\/script>/g, '<script>window.loadPyodide=null;</script>');
fs.writeFileSync(process.argv[3], html);
console.log('Шаблон показу зібрано для офлайн-контролю рендера');
