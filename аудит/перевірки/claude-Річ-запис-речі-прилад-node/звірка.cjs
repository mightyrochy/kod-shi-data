// Звіряє старий вхід (один JSON) з новим (рядки) після прочитати_вхід: побайтно JSON.stringify.
const fs = require('fs'), zlib = require('zlib');
const {прочитати_вхід} = require(process.argv[2]);
const тека = process.argv[3]; let n = 0, різних = 0;
for (let і = 0; fs.existsSync(`${тека}/старий_${і}.json.gz`); і++) {
  const н = в => { if (в.селектори) в.селектори = Object.fromEntries(Object.entries(в.селектори).sort()); return JSON.stringify(в); };
  const старий = н(JSON.parse(zlib.gunzipSync(fs.readFileSync(`${тека}/старий_${і}.json.gz`)).toString('utf8')));
  const рядки = zlib.gunzipSync(fs.readFileSync(`${тека}/новий_${і}.ndjson.gz`)).toString('utf8').split('\n').filter(Boolean);
  const новий = н(прочитати_вхід(рядки));
  n++; if (старий !== новий) { різних++; console.log('різний', і, старий.length, новий.length); }
}
console.log('входів', n, 'різних', різних);
