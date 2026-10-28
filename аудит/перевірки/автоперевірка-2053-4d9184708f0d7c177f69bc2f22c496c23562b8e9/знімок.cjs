const {chromium} = require('playwright');
const fs = require('fs/promises');
const http = require('http');
const path = require('path');
(async () => {
  const root = process.cwd();
  const server = http.createServer(async (req, res) => {
    try {
      const name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      const file = path.resolve(root, '.' + (name === '/' ? '/index.html' : name));
      if (!file.startsWith(root + path.sep)) { res.writeHead(403); res.end(); return; }
      const content = await fs.readFile(file);
      const types = {'.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css'};
      res.writeHead(200, {'Content-Type': types[path.extname(file)] || 'application/octet-stream'});
      res.end(content);
    } catch (_) {res.writeHead(404); res.end();}
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe'});
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    page.on('pageerror', error => console.log('Помилка сторінки:', error.message));
    await page.route(/^https?:/, route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort());
    await page.goto('http://127.0.0.1:' + server.address().port, {waitUntil: 'networkidle', timeout: 30000});
    await page.screenshot({path: 'C:/Users/gemini/gemini-runs/w/review-2053-390x844.png'});
    console.log(await page.title());
    console.log('Знімок 390x844 з локального HTTP; зовнішню мережу заблоковано.');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
