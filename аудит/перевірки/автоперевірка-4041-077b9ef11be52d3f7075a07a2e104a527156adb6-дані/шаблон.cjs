const fs=require('fs'),path=require('path');
const root=path.resolve(process.argv[2],'джерела');
const h=require(path.join(root,'показ_шаблон.js'));
const html=h.підставитиШаблон(fs.readFileSync(path.join(root,'показ.html'),'utf8'),{
 __МОДУЛІ_ПОКАЗУ__:'офлайн',__ЗБІРКА_ПОКАЗУ__:'перевірка-4041',__ВІДБИТОК__:'перевірка-4041',
 __ФІД_ПОКАЗУ__:'каталог_повний.xml',__КАТАЛОГ_ПОКАЗУ__:'повний',__ДОВІДНИК_ПОКАЗУ__:h.прочитатиДовідникJSON(root)
});
fs.writeFileSync(process.argv[3],html);
