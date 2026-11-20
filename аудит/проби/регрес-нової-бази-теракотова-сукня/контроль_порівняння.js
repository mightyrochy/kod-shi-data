// Контроль: стенд із правкою не сліпий — база з іншим входом/звіркою дає регрес, а справжня різниця у вхідних даних — «застарів».
const fs=require('fs'),path=require('path');
const {порівняти}=require(path.join(process.argv[2],'аудит/проби/храповик_записів.js'));
const тека=process.argv[3]; // f2_після/<сцена>
const після=JSON.parse(fs.readFileSync(path.join(тека,'звірки.json'),'utf8'));
const база=JSON.parse(fs.readFileSync(process.argv[4],'utf8'));
console.log('справжня база:', порівняти(база,після).стан);
const б2=JSON.parse(JSON.stringify(база)); б2.звірки[0].ід='0'.repeat(64);          // звірка бази зникла з прогону
console.log('база зі зниклою звіркою:', порівняти(б2,після).стан, порівняти(б2,після).регресії.length);
const п2=JSON.parse(JSON.stringify(після)); п2.звірки[1].зелена=false;                // звірка в прогоні почервоніла
console.log('прогін із червоною звіркою:', порівняти(база,п2).стан, порівняти(база,п2).регресії.length);
