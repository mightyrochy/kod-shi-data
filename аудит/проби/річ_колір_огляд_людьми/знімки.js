// знімки.js — прогін сторінки огляду кольору на телефонах: знімки 390×844 кожного стану й пробний файл результатів.
// Запуск: node аудит/проби/річ_колір_огляд_людьми/знімки.js <адреса сторінки, для другого набору — з ?набір=sproba2> <тека знімків> <тека пробних файлів>
// Файл пробних: пробний-<ід набору>-<профіль>.txt
// Пристрої: Android Chrome — chromium з профілем Pixel 7, iPhone Safari — webkit з профілем iPhone 14; вікно 390×844, масштаб 1.
// Відповіді тут вигадані прогоном (за номером речі): це пробні дані, позначка «пробний-…», а не слово людей.
// «Фото невдалі» прогін ставить на речі 3 і 9 (у наборі із запасними — додаються дві запасні) і перевіряє перенесення
// відповідей давньої версії набору (до галерей і назв) — у свіжому контексті.
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
  return {А: м === 0 || м === 3 ? "п" : "н", Б: м === 1 ? "п" : м === 4 ? "з" : "н", назва: (н + зсув) % 2 ? "п" : "н", принт: маєПринт ? "з" : null};
}
const НЕВДАЛІ = [3, 9];
const ПЕРШЕ_ФОТО = "#галерея .кадр img";

async function відповісти(сторінка, в) {
  for (const мітка of ["А", "Б"]) await сторінка.click(`.свотч[data-мітка="${мітка}"] [data-в="${в[мітка]}"]`);
  await сторінка.click(`#назва [data-в="${в.назва}"]`);
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
  await сторінка.waitForSelector(ПЕРШЕ_ФОТО);
  await сторінка.waitForFunction((с) => document.querySelector(с).complete, ПЕРШЕ_ФОТО);
  await знімок("03-річ-порожня");

  /* галерея: гортання (як пальцем — прокрутка стрічки) і кнопка «›» — на першій речі з кількома фото */
  const [зКадрами, кадрів] = await сторінка.evaluate(() => { const р = набір.речі.find((р) => р.галерея.length > 1); return [р.номер, р.галерея.length]; });
  if (зКадрами !== 1) {
    стверд((await сторінка.textContent("#номер-кадру")) === "фото 1 з 1" && (await сторінка.locator("#кадр-вперед").count()) === 0, "одне фото — без гортання");
    await сторінка.click("#до-сітки");
    await сторінка.click(`#сітка [data-н="${зКадрами}"]`);
    await сторінка.waitForSelector(ПЕРШЕ_ФОТО);
  }
  стверд((await сторінка.textContent("#номер-кадру")) === "фото 1 з " + кадрів, "лічильник фото");
  await сторінка.evaluate(() => { const с = document.getElementById("стрічка"); с.scrollTo({left: с.clientWidth}); });
  await сторінка.waitForFunction(() => document.getElementById("номер-кадру").textContent.startsWith("фото 2 "));
  await сторінка.waitForFunction(() => document.querySelector('.кадр[data-кадр="1"] img').complete);
  await знімок("03а-галерея-друге-фото");
  await сторінка.click("#кадр-вперед");
  await сторінка.waitForFunction(() => document.getElementById("номер-кадру").textContent.startsWith("фото 3 ") || document.getElementById("кадр-вперед").disabled);
  await сторінка.click("#кадр-назад");
  await сторінка.waitForFunction(() => document.getElementById("номер-кадру").textContent.startsWith("фото 2 "));

  /* збільшення фото: те саме фото, що в галереї; «›» у шапці; подвійний дотик */
  await сторінка.click('.кадр[data-кадр="1"] img');
  await сторінка.waitForSelector("#збільшення:not([hidden])");
  стверд((await сторінка.textContent("#збільшення-кадри .підпис-кадру")) === "2/" + кадрів, "збільшення відкрило друге фото");
  await пауза(300);
  const поле = await сторінка.locator("#збільшення-поле").boundingBox();
  await сторінка.mouse.dblclick(поле.x + поле.width * 0.5, поле.y + поле.height * 0.4);
  await знімок("04-збільшення-фото");
  await сторінка.click('#збільшення-кадри [data-кадр="вперед"]');
  await сторінка.click('#збільшення-кадри [data-кадр="назад"]');
  await сторінка.click('#збільшення-кадри [data-кадр="назад"]');
  await сторінка.click("#збільшення-закрити");
  await сторінка.waitForSelector("#номер-кадру");
  await сторінка.waitForFunction(() => document.getElementById("номер-кадру").textContent.startsWith("фото 1 "));
  if (зКадрами !== 1) { await сторінка.click("#до-сітки"); await сторінка.click('#сітка [data-н="1"]'); await сторінка.waitForSelector(ПЕРШЕ_ФОТО); }

  /* перша річ: відповіді, простір, колір */
  await відповісти(сторінка, {А: "п", Б: "н", назва: "н", принт: null});
  await знімок("05-річ-з-відповідями");
  await сторінка.evaluate(() => document.getElementById("назва").scrollIntoView({block: "center"}));
  await знімок("05а-назва-відтінку");
  await сторінка.click('.свотч[data-мітка="А"] [data-в="н"]');
  await сторінка.click('#назва [data-в="п"]');
  await підібрати(сторінка, 0, false);
  await знімок("06-простір-один-колір");
  await сторінка.mouse.move(1, 1);
  await сторінка.click("#простір-другий");
  await пауза(200);
  await знімок("07-простір-два-кольори");
  await сторінка.click("#простір-готово");
  await сторінка.waitForSelector(".підібрані .латка");
  await знімок("08-річ-з-кольором");

  /* усі речі за вигаданими відповідями; на 3-й і 9-й — «фото невдалі»; на 12-й — закрили й відкрили */
  const основних = await сторінка.evaluate(() => набір.речі.length);
  const запасних = await сторінка.evaluate(() => (набір.запасні || []).length);
  const всього = основних + Math.min(НЕВДАЛІ.length, запасних);
  for (let і = 0; і < всього; і++) {
    const н = await сторінка.evaluate((і) => черга()[і].номер, і);
    await сторінка.waitForSelector("#лічба");
    const лічба = await сторінка.textContent("#лічба");
    стверд(і < основних ? лічба.startsWith("Річ " + н + " з ") : лічба.startsWith("Запасна річ " + н + " · "), "порядок речей на " + (і + 1) + ": " + лічба);
    if (НЕВДАЛІ.includes(н)) {
      if (н === НЕВДАЛІ[0]) await знімок("08а-річ-перед-фото-невдалі");
      await сторінка.click("#фото-невдалі");
      await сторінка.waitForSelector("#без-відповідей");
      стверд((await сторінка.locator(".свотч").count()) === 0, "з «фото невдалі» інших відповідей нема");
      if (н === НЕВДАЛІ[0]) await знімок("08б-фото-невдалі");
      await сторінка.click("#далі");
      continue;
    }
    if (і === основних) { await сторінка.waitForSelector(ПЕРШЕ_ФОТО); await знімок("16-запасна-річ"); }
    const маєПринт = (await сторінка.locator("#принт").count()) > 0;
    const в = відповідіДляРечі(н, маєПринт, профіль);
    if (н > 1) await відповісти(сторінка, в);
    else { await сторінка.click('.свотч[data-мітка="А"] [data-в="п"]'); await сторінка.click('.свотч[data-мітка="Б"] [data-в="н"]'); await сторінка.click('#назва [data-в="п"]'); if (маєПринт) await сторінка.click('#принт [data-в="з"]'); }
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
      стверд((await сторінка.locator("#сітка .готово").count()) === 12 - НЕВДАЛІ.length, "після перезапуску лишилось 10 готових");
      стверд((await сторінка.locator("#сітка .невдалі-річ").count()) === НЕВДАЛІ.length, "і дві з «фото невдалі»");
      стверд((await сторінка.locator("#сітка .запасна").count()) === Math.min(НЕВДАЛІ.length, запасних), "запасні в черзі");
      await сторінка.click('#сітка [data-н="3"]');
      await сторінка.waitForSelector("#без-відповідей");
      await сторінка.click('#до-сітки');
      await сторінка.click('#сітка [data-н="1"]');
      await сторінка.waitForSelector(ПЕРШЕ_ФОТО);
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
  стверд(результат.формат === "огляд-кольору/2" && результат.запасних === Math.min(НЕВДАЛІ.length, запасних), "формат 2 і запасні");
  стверд(результат.відповіді.filter((в) => в.фото_невдалі).map((в) => в.річ).join() === НЕВДАЛІ.join(), "«фото невдалі» у файлі");
  стверд(результат.відповіді.every((в) => в.фото_невдалі || в.назва), "назва судиться в кожній речі без «фото невдалі»");
  const файлПробний = path.join(текаПробних, "пробний-" + результат.набір + "-" + профіль.назва + ".txt");
  const [завантаження] = await Promise.all([сторінка.waitForEvent("download").catch(() => null), сторінка.click("#поділитися")]);
  if (завантаження) { await завантаження.saveAs(файлПробний); }
  else fs.writeFileSync(файлПробний, текст);
  await пауза(200);
  await знімок("15-після-поділитися");
  const збережено = fs.readFileSync(файлПробний, "utf8");
  стверд(збережено === текст, "файл і текст однакові");

  /* незавершений набір: результат недоступний */
  await сторінка.evaluate(() => { const к = Object.keys(localStorage)[0]; const с = JSON.parse(localStorage[к]); delete с.відповіді["5"]; localStorage[к] = JSON.stringify(с); });
  await сторінка.reload();
  await сторінка.waitForSelector("#сітка, #галерея, #поділитися");

  /* перенесення з давньої версії набору: свотчі й підібране переносяться, назва — ні */
  const давній = await сторінка.evaluate(() => (набір.відбитки_давні || [])[0]);
  if (давній) {
    const к2 = await браузер.newContext(параметри);
    const с2 = await к2.newPage();
    с2.on("pageerror", (е) => помилки.push(String(е)));
    await с2.goto(адреса);
    await с2.waitForSelector("#позначка");
    await с2.evaluate((давній) => {
      const відп = {};
      for (const р of набір.речі) відп[р.номер] = {св: {А: "п", Б: "н"}, слово: "п", підібрано: р.номер === 2 ? ["#336699"] : []};
      localStorage.clear();
      localStorage.setItem("ohliad-koloru:" + набір.id + ":" + давній, JSON.stringify({позначка: "пробний-давній", відповіді: відп, поточна: 0, екран: "сітка"}));
    }, давній);
    await с2.reload();
    await с2.waitForSelector("#перенесено");
    await с2.evaluate(() => window.scrollTo(0, 0));
    await пауза(250); await с2.screenshot({path: path.join(знімки, "17-перенесено-з-давньої-версії.png")});
    await с2.click("#почати");
    await с2.waitForSelector(ПЕРШЕ_ФОТО);
    стверд((await с2.locator(".свотч .обрано").count()) === 2 && (await с2.locator("#назва .обрано").count()) === 0, "свотчі перенесено, назву — ні");
    await к2.close();
  }
  стверд(помилки.length === 0, "помилки сторінки: " + помилки.join("; "));
  await браузер.close();
  console.log(профіль.назва, "ок, файл:", збережено.length, "знаків");
}

(async () => { for (const п of ПРОФІЛІ) await прогін(п); })().catch((е) => { console.error(е); process.exit(1); });
