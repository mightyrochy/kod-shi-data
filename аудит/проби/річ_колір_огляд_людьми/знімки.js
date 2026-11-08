// знімки.js — прогін сторінки огляду кольору на телефонах: знімки 390×844 кожного стану й пробний файл результатів.
// Запуск: node аудит/проби/річ_колір_огляд_людьми/знімки.js <адреса сторінки> <тека знімків> <тека пробних файлів>
// Пристрої: Android Chrome — chromium з профілем Pixel 7, iPhone Safari — webkit з профілем iPhone 14; вікно 390×844, масштаб 1.
// Відповіді тут вигадані прогоном (за номером речі): це пробні дані, позначка «пробний-…», а не слово людей.
const {chromium, webkit, devices} = require("playwright");
const fs = require("fs");
const path = require("path");

const [адреса = "http://localhost:8077/", текаЗнімків = "знімки", текаПробних = "пробні"] = process.argv.slice(2);
const ПРОФІЛІ = [
  {назва: "android-chrome", рушій: chromium, пристрій: "Pixel 7", позначка: "пробний-android"},
  {назва: "iphone-safari", рушій: webkit, пристрій: "iPhone 14", позначка: "пробний-iphone"},
];
const пауза = (мс) => new Promise((р) => setTimeout(р, мс));
const стверд = (умова, текст) => { if (!умова) throw new Error("не вийшло: " + текст); };

/* вигадані відповіді пробного прогону: залежать лише від номера речі */
function відповідіДляРечі(н, маєПринт, профіль) {
  const зсув = профіль.назва.startsWith("iphone") ? 1 : 0;
  const м = (н + зсув) % 6;
  return {А: м === 0 || м === 3 ? "п" : "н", Б: м === 1 ? "п" : м === 4 ? "з" : "н", слово: (н + зсув) % 2 ? "п" : "н", принт: маєПринт ? "з" : null};
}

async function відповісти(сторінка, в) {
  for (const мітка of ["А", "Б"]) await сторінка.click(`.свотч[data-мітка="${мітка}"] [data-в="${в[мітка]}"]`);
  await сторінка.click(`#слово [data-в="${в.слово}"]`);
  if (в.принт) await сторінка.click(`#принт [data-в="${в.принт}"]`);
}

async function підібрати(сторінка, зсув, другий) {
  await сторінка.click("#відкрити-простір");
  await сторінка.waitForSelector("#простір:not([hidden])");
  await пауза(150);
  const поле = await сторінка.locator("#поле").boundingBox();
  await сторінка.mouse.move(поле.x + поле.width * (0.3 + зсув), поле.y + поле.height * 0.4);
  await сторінка.mouse.down();
  await сторінка.mouse.move(поле.x + поле.width * (0.4 + зсув), поле.y + поле.height * 0.5, {steps: 4});
  await сторінка.mouse.up();
  const смуга = await сторінка.locator("#смуга").boundingBox();
  await сторінка.mouse.click(смуга.x + смуга.width * (0.2 + зсув), смуга.y + смуга.height / 2);
  if (другий) {
    await сторінка.click("#простір-другий");
    await сторінка.mouse.click(поле.x + поле.width * 0.25, поле.y + поле.height * 0.7);
  }
  await пауза(120);
}

async function прогін(профіль) {
  const знімки = path.join(текаЗнімків, профіль.назва);
  fs.mkdirSync(знімки, {recursive: true});
  fs.mkdirSync(текаПробних, {recursive: true});
  const браузер = await профіль.рушій.launch();
  const параметри = Object.assign({}, devices[профіль.пристрій], {viewport: {width: 390, height: 844}, screen: {width: 390, height: 844}, deviceScaleFactor: 1, acceptDownloads: true});
  const контекст = await браузер.newContext(параметри);
  let сторінка = await контекст.newPage();
  const помилки = [];
  сторінка.on("pageerror", (е) => помилки.push(String(е)));
  const знімок = async (ім) => { await пауза(250); await сторінка.screenshot({path: path.join(знімки, ім + ".png")}); };

  await сторінка.goto(адреса);
  await сторінка.waitForSelector("#позначка");
  await знімок("01-початок");
  await сторінка.fill("#позначка", "Оля Іванова Петрівна");
  await сторінка.click("#почати");
  стверд((await сторінка.textContent("#помилка-позначки")).length > 0, "довге ім'я має відхилятися");
  await сторінка.fill("#позначка", "a@b.ua");
  await сторінка.click("#почати");
  стверд((await сторінка.textContent("#помилка-позначки")).length > 0, "пошта має відхилятися");
  await знімок("02-початок-помилка");
  await сторінка.fill("#позначка", профіль.позначка);
  await сторінка.click("#почати");
  await сторінка.waitForSelector("#фото-речі");
  await сторінка.waitForFunction(() => document.getElementById("фото-речі").complete);
  await знімок("03-річ-порожня");

  /* збільшення фото: подвійний дотик */
  const фото = await сторінка.locator("#фото-речі").boundingBox();
  await сторінка.click("#фото-речі");
  await сторінка.waitForSelector("#збільшення:not([hidden])");
  await пауза(300);
  const поле = await сторінка.locator("#збільшення-поле").boundingBox();
  await сторінка.mouse.dblclick(поле.x + поле.width * 0.5, поле.y + поле.height * 0.4);
  await знімок("04-збільшення-фото");
  await сторінка.click("#збільшення-закрити");

  /* перша річ: відповіді, простір, колір */
  await відповісти(сторінка, {А: "п", Б: "н", слово: "н", принт: null});
  await знімок("05-річ-з-відповідями");
  await сторінка.click('.свотч[data-мітка="А"] [data-в="н"]');
  await сторінка.click('#слово [data-в="п"]');
  await підібрати(сторінка, 0, false);
  await знімок("06-простір-один-колір");
  await сторінка.mouse.move(1, 1);
  await сторінка.click("#простір-другий");
  await пауза(200);
  await знімок("07-простір-два-кольори");
  await сторінка.click("#простір-готово");
  await сторінка.waitForSelector(".підібрані .латка");
  await знімок("08-річ-з-кольором");

  /* усі речі за вигаданими відповідями; на 12-й — закрили й відкрили */
  const всього = await сторінка.evaluate(() => набір.речі.length);
  for (let і = 0; і < всього; і++) {
    const н = і + 1;
    await сторінка.waitForSelector("#лічба");
    стверд((await сторінка.textContent("#лічба")).startsWith("Річ " + н + " "), "порядок речей на " + н);
    const маєПринт = (await сторінка.locator("#принт").count()) > 0;
    const в = відповідіДляРечі(н, маєПринт, профіль);
    if (н > 1) await відповісти(сторінка, в);
    else { await сторінка.click('.свотч[data-мітка="А"] [data-в="п"]'); await сторінка.click('.свотч[data-мітка="Б"] [data-в="н"]'); await сторінка.click('#слово [data-в="п"]'); if (маєПринт) await сторінка.click('#принт [data-в="з"]'); }
    const А = н === 1 ? "п" : в.А, Б = н === 1 ? "н" : в.Б;
    const потрібен = А !== "п" && Б !== "п" && !(А === "з" && Б === "з");
    if (н > 1 && потрібен) {
      await сторінка.waitForSelector(".вимога");
      if (н === 7) { await сторінка.locator("#колір-речі").scrollIntoViewIfNeeded(); await знімок("09-річ-колір-обов-язковий"); }
      await підібрати(сторінка, (н % 5) / 20, н % 7 === 0);
      if (н === 7) await знімок("10-простір-колір-обов-язковий");
      await сторінка.click("#простір-готово");
    }
    if (н === 12) {
      await сторінка.click("#до-сітки");
      await знімок("11-сітка-посередині");
      await сторінка.close();
      сторінка = await контекст.newPage();
      сторінка.on("pageerror", (е) => помилки.push(String(е)));
      await сторінка.goto(адреса);
      await сторінка.waitForSelector("#сітка");
      await знімок("12-після-закриття-й-відкриття");
      стверд((await сторінка.locator("#сітка .готово").count()) === 12, "після перезапуску лишилось 12 готових");
      await сторінка.click('#сітка [data-н="1"]');
      await сторінка.waitForSelector("#фото-речі");
      стверд((await сторінка.locator(".свотч .обрано").count()) === 2, "відповіді першої речі на місці");
      стверд((await сторінка.locator(".підібрані .латка").count()) === 2, "обидва підібрані кольори на місці");
      await знімок("13-перша-річ-після-відкриття");
      await сторінка.click('#до-сітки');
      await сторінка.click('#сітка [data-н="12"]');
      await сторінка.waitForSelector("#далі");
    }
    await сторінка.click("#далі");
  }
  await сторінка.waitForSelector("#поділитися");
  стверд(await сторінка.locator("#поділитися").isEnabled(), "поділитися доступне, коли відповіли на всі");
  await знімок("14-результат");
  const текст = await сторінка.inputValue("#текст-результату");
  const результат = JSON.parse(текст);
  стверд(результат.відповіді.length === всього && результат.позначка === профіль.позначка && результат.пробний === true, "файл має всі речі й позначку");
  const [завантаження] = await Promise.all([сторінка.waitForEvent("download").catch(() => null), сторінка.click("#поділитися")]);
  if (завантаження) { await завантаження.saveAs(path.join(текаПробних, "пробний-" + профіль.назва + ".txt")); }
  else fs.writeFileSync(path.join(текаПробних, "пробний-" + профіль.назва + ".txt"), текст);
  await пауза(200);
  await знімок("15-після-поділитися");
  const збережено = fs.readFileSync(path.join(текаПробних, "пробний-" + профіль.назва + ".txt"), "utf8");
  стверд(збережено === текст, "файл і текст однакові");

  /* незавершений набір: результат недоступний */
  await сторінка.evaluate(() => { const к = Object.keys(localStorage)[0]; const с = JSON.parse(localStorage[к]); delete с.відповіді["5"]; localStorage[к] = JSON.stringify(с); });
  await сторінка.reload();
  await сторінка.waitForSelector("#сітка, #фото-речі, #поділитися");
  стверд(помилки.length === 0, "помилки сторінки: " + помилки.join("; "));
  await браузер.close();
  console.log(профіль.назва, "ок, файл:", збережено.length, "знаків");
}

(async () => { for (const п of ПРОФІЛІ) await прогін(п); })().catch((е) => { console.error(е); process.exit(1); });
