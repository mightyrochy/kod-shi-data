const { chromium } = require('playwright');
const запуск = chromium.launch.bind(chromium);
chromium.launch = async (...аргументи) => {
  const браузер = await запуск(...аргументи);
  const закрити = браузер.close.bind(браузер);
  браузер.close = async (...параметри) => {
    for (const контекст of браузер.contexts()) {
      for (const сторінка of контекст.pages()) {
        if (сторінка.isClosed()) continue;
        await сторінка.evaluate(() => window.scrollTo(0, 0));
        await сторінка.screenshot({path: process.env.VIEWPORT_4366, fullPage: false});
        console.log('ЗНІМОК ВІКНА', JSON.stringify(сторінка.viewportSize()));
      }
    }
    return закрити(...параметри);
  };
  return браузер;
};
process.argv = [process.argv[0], ...process.argv.slice(2)];
require(process.argv[1]);
