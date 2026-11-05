/* Стенд повернення людини на примірку: справжня модель сегментації в Chromium.

   Запуск:  node стенд_повернення.js <фото> [тека_медіапайп] [тека_виводу]
     <фото>            — фото людини на повний зріст; лише з диска, у репозиторій не кладеться;
     [тека_медіапайп]  — локальні копії файлів `ФАЙЛИ_СЕГМЕНТАЦІЇ_П` під їхніми іменами
                         (vision_bundle.mjs, wasm/…, selfie_multiclass_256x256.tflite);
                         без неї файли йдуть із мережі тими самими адресами й відбитками;
     [тека_виводу]     — куди покласти кадри примірки й повернення для очей.

   Справжнього генератора тут нема: «кадр примірки» стенд робить із її фото так, як його
   псує генератор, — масштаб і зсув кадру, інші пропорції, зсув тону шкіри, — і дві примірки
   паспорта: зміна кольору (одяг іншого кольору) і зміна крою (новий рукав і комір
   поверх шкіри). Друкує, скільки пікселів її частин поза новою річчю дорівнюють фото ДО і
   ПІСЛЯ повернення, і чи нова річ лишилась із кадру примірки. */
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');

const [фото, текаМП, текаВих] = process.argv.slice(2);
if (!фото){ console.error('потрібне фото: node стенд_повернення.js <фото> [тека_медіапайп] [тека_виводу]'); process.exit(2); }
const модуль = fs.readFileSync(path.join(__dirname, 'показ', 'повернення.js'), 'utf8');

/* У сторінці: синтетичний кадр примірки, повернення, лічба. */
async function проба(вид){
  const о = await класиКадруП(await сегментаторП(), ФОТО.тип, ФОТО.дані);
  const К = {тло: 0, волосся: 1, тіло: 2, обличчя: 3, одяг: 4};
  /* генератор: кадр ширший на 12 %, людина менша на 8 % і зсунута; тон шкіри теплішає */
  const м = 0.92, зх = 0.09 * о.ш, зу = 0.03 * о.в, ш = Math.round(о.ш * 1.12), в = о.в;
  const п = document.createElement('canvas'); п.width = ш; п.height = в;
  const кт = п.getContext('2d');
  const дж = document.createElement('canvas'); дж.width = о.ш; дж.height = о.в;
  const дп = new ImageData(new Uint8ClampedArray(о.пікс), о.ш, о.в);
  /* новий крій: рукав і комір — одяг поверх шкіри тіла в смузі під обличчям */
  let низОбличчя = 0;
  for (let і = 0; і < о.кл.length; і++) if (о.кл[і] === К.обличчя) низОбличчя = Math.max(низОбличчя, Math.floor(і / о.ш));
  const новаРіч = new Uint8Array(о.кл.length);
  for (let і = 0; і < о.кл.length; і++){
    const у = Math.floor(і / о.ш), к = о.кл[і];
    const нова = к === К.одяг || (вид === 'крій' && к === К.тіло && у > низОбличчя + 0.02 * о.в);
    новаРіч[і] = нова ? 1 : 0;
    /* інший колір речі — перестановка каналів: яскравість і складки лишаються, як у генератора */
    const rgb = [0, 1, 2].map(с => о.пікс[і * 4 + с]);
    for (let с = 0; с < 3; с++){
      let в_ = rgb[с];
      if (нова) в_ = к === К.одяг ? rgb[(с + 2) % 3] : [40, 90, 160][с];
      else if (к === К.тіло || к === К.обличчя) в_ = в_ * [1.08, 1.0, 0.92][с];
      дп.data[і * 4 + с] = в_;
    }
  }
  дж.getContext('2d').putImageData(дп, 0, 0);
  кт.fillStyle = '#808080'; кт.fillRect(0, 0, ш, в);
  кт.drawImage(дж, зх, зу, о.ш * м, о.в * м);
  const кадр = п.toDataURL('image/png');
  const р = await повернутиЛюдинуП(Promise.resolve({о}), {media_type: 'image/png', data: кадр.split(',')[1]}, false);
  if (!р.кадр) return {вид, звіт: р.звіт};
  /* лічба на рамці повернення: її частини поза новою річчю — рівні фото?; нова річ — з примірки? */
  const [рх, ру, рш, рв] = р.звіт.рамка;
  const б = await createImageBitmap(await (await fetch(р.кадр)).blob());
  const кп = document.createElement('canvas'); кп.width = рш; кп.height = рв;
  const ккт = кп.getContext('2d'); ккт.drawImage(б, 0, 0);
  const пв = ккт.getImageData(0, 0, рш, рв).data;
  /* ДО — кадр примірки, покладений на її фото справжнім (відомим стендові) суміщенням */
  const пд = document.createElement('canvas'); пд.width = о.ш; пд.height = о.в;
  const пдк = пд.getContext('2d'); пдк.drawImage(п, -зх / м, -зу / м, ш / м, в / м);
  const пдо = пдк.getImageData(0, 0, о.ш, о.в).data;
  const л = {частин: 0, до_рівні: 0, після_рівні: 0, до_відхил: 0, після_відхил: 0, нової: 0, нова_з_примірки: 0};
  for (let у = 0; у < рв; у++) for (let х = 0; х < рш; х++){
    const іо = (у + ру) * о.ш + х + рх, ів = у * рш + х, к = о.кл[іо];
    const різн = (а, і) => Math.max(...[0, 1, 2].map(с => Math.abs(а[і * 4 + с] - о.пікс[іо * 4 + с])));
    /* нова річ — з примірки: повернений піксель ближчий до кадру примірки, ніж до її фото */
    const доПримірки = Math.max(...[0, 1, 2].map(с => Math.abs(пв[ів * 4 + с] - пдо[іо * 4 + с])));
    if (новаРіч[іо]){ л.нової++; if (доПримірки <= різн(пв, ів)) л.нова_з_примірки++; continue; }
    if (к !== К.волосся && к !== К.тіло && к !== К.обличчя) continue;
    л.частин++;
    const рд = різн(пдо, іо), рп = різн(пв, ів);
    л.до_відхил += рд; л.після_відхил += рп;
    if (рд === 0) л.до_рівні++;
    if (рп === 0) л.після_рівні++;
  }
  return {вид, звіт: р.звіт, лічба: л, кадр_примірки: кадр, кадр_повернення: р.кадр};
}

(async () => {
  const б = await chromium.launch();
  const стор = await б.newPage();
  if (текаМП){
    const назви = {'vision_bundle.mjs': 'vision_bundle.mjs', 'vision_wasm_internal.js': 'wasm/vision_wasm_internal.js',
      'vision_wasm_internal.wasm': 'wasm/vision_wasm_internal.wasm', 'selfie_multiclass_256x256.tflite': 'selfie_multiclass_256x256.tflite'};
    await стор.route(/cdn\.jsdelivr\.net|storage\.googleapis\.com/, маршрут => {
      const ім = маршрут.request().url().split('/').pop();
      маршрут.fulfill({path: path.join(текаМП, назви[ім] || ім),
        headers: {'access-control-allow-origin': '*', 'content-type': ім.endsWith('.wasm') ? 'application/wasm' : 'application/octet-stream'}});
    });
  }
  await стор.setContent('<!doctype html><meta charset="utf-8"><body>');
  await стор.addScriptTag({content: модуль});
  const тип = /\.png$/i.test(фото) ? 'image/png' : 'image/jpeg';
  await стор.evaluate(([т, д]) => { window.ФОТО = {тип: т, дані: д}; }, [тип, fs.readFileSync(фото).toString('base64')]);
  await стор.addScriptTag({content: 'window.проба = ' + проба.toString()});
  for (const вид of ['колір', 'крій']){
    const р = await стор.evaluate(в => window.проба(в), вид);
    const л = р.лічба;
    console.log(вид + ' · звіт ' + JSON.stringify(р.звіт));
    if (!л) continue;
    const ч = (а, б_) => (100 * а / Math.max(1, б_)).toFixed(1) + ' %';
    console.log(вид + ' · її частини поза новою річчю: ' + л.частин + ' px; рівні фото ДО ' + ч(л.до_рівні, л.частин)
      + ' → ПІСЛЯ ' + ч(л.після_рівні, л.частин) + '; середнє відхилення ДО ' + (л.до_відхил / л.частин).toFixed(1)
      + ' → ПІСЛЯ ' + (л.після_відхил / л.частин).toFixed(1) + '; нова річ із примірки ' + ч(л.нова_з_примірки, л.нової));
    if (текаВих){
      for (const [ім, у] of [['примірка', р.кадр_примірки], ['повернення', р.кадр_повернення]])
        fs.writeFileSync(path.join(текаВих, вид + '_' + ім + '.png'), Buffer.from(у.split(',')[1], 'base64'));
    }
  }
  await б.close();
})().catch(е => { console.error(е); process.exit(1); });
