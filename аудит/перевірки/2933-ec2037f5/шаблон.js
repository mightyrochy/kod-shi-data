const fs = require('fs'), path = require('path');
const [,, root, out] = process.argv;
const dir = path.join(root, 'джерела');
const {підставитиШаблон, прочитатиДовідникJSON} = require(path.join(dir, 'показ_шаблон.js'));
const html = підставитиШаблон(fs.readFileSync(path.join(dir, 'показ.html'), 'utf8'), {
  __МОДУЛІ_ПОКАЗУ__: 'офлайн', __ЗБІРКА_ПОКАЗУ__: 'перевірка-2933',
  __ВІДБИТОК__: 'перевірка-2933', __ФІД_ПОКАЗУ__: 'каталог_brief.xml',
  __КАТАЛОГ_ПОКАЗУ__: 'офлайн', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(dir)
});
fs.writeFileSync(out, html);
