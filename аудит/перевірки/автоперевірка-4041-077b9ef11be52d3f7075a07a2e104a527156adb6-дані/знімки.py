import base64,gzip,json,os,pathlib,subprocess,sys,urllib.request,xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

root=pathlib.Path(sys.argv[1]).resolve()
out=root/'перевірка4041'
os.environ['FOTO']='1'
photo=out/'ж-00049.jpg'
if not photo.exists():
    photo.write_bytes(urllib.request.urlopen('https://alot.com.ua/imgs/b827.jpg',timeout=40).read())
photo_data='data:image/jpeg;base64,'+base64.b64encode(photo.read_bytes()).decode()
with gzip.open(root/'source4041/каталог_повний.xml.gz') as f:
    for _,e in ET.iterparse(f,events=('end',)):
        if e.tag=='offer' and e.get('id')=='ж-00049':
            price=float(e.findtext('price')); itemurl=e.findtext('url'); break
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--disable-gpu'])
    for label,tree in [('до','base4041'),('після','source4041')]:
        html=out/(label+'.html')
        subprocess.run(['node',str(pathlib.Path(__file__).with_name('шаблон.cjs')),str(root/tree),str(html)],check=True)
        page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda e: errors.append(str(e)))
        page.route('**/*',lambda route: route.fulfill(content_type='text/html',body=html.read_text(encoding='utf-8'))
                   if route.request.url=='http://offline.local/' else route.abort())
        page.goto('http://offline.local/',wait_until='domcontentloaded')
        page.wait_for_function("typeof показатиСценарій === 'function'")
        page.wait_for_function("Екран.стан.запущено === true")
        text=page.evaluate('''() => {
          режим('сценарій');
          ПАСПОРТ_П={джерело:'модель',подія:'Весілля ввечері',нагода:'весілля_гість',місце:'весілля',
            пора:'вечір',ошатність:[7,9],зарезервований_колір:'near_white',
            джерело_полів:{нагода:'розмова',місце:'розмова',пора:'розмова',ошатність:'розмова'}};
          ВИПАДОК_ЗМІНЕНО_П=false; застосуватиПаспортДоЕкрана(ПАСПОРТ_П); показатиСценарій();
          const card=document.getElementById('сц-картка'); card.hidden=false; card.scrollIntoView({block:'start'});
          return card.innerText;
        }''')
        page.evaluate('''async () => {
          await document.fonts.ready;
          await new Promise(r => setTimeout(r, 300));
          режим('сценарій'); показатиСценарій();
          await new Promise(requestAnimationFrame);
          document.getElementById('сц-картка').scrollIntoView({block:'start'});
          await new Promise(requestAnimationFrame);
        }''')
        page.screenshot(path=str(out/(label+'_390x844.png')),animations='disabled')
        (out/(label+'_екран.json')).write_text(json.dumps({'FOTO':os.environ['FOTO'],'помилки':errors,'текст':text},ensure_ascii=False,indent=2),encoding='utf-8')
        print(label,'помилки',errors,'текст',text[:600],flush=True)
        cardtext=page.evaluate('''({photo,price,itemurl}) => {
          П={картки:[{рука:1,речі:[{id:'ж-00049',назва:'Біла сукня прямого крою з екошкіри',
            слот:'сукня',тип:'сукня',фото:photo,урл:itemurl,ціна:price}]}]};
          режим('образи'); const target=document.getElementById('картки');target.innerHTML='';
          target.appendChild(рендерКартку(0));
          підвʼязатиКартку(0);
          return target.innerText;
        }''',{'photo':photo_data,'price':price,'itemurl':itemurl})
        page.evaluate("async () => { await Promise.all([...document.querySelectorAll('#картки img')].map(i=>i.decode().catch(()=>{}))); document.getElementById('к-0').scrollIntoView({block:'start'}); await new Promise(requestAnimationFrame); }")
        page.screenshot(path=str(out/(label+'_річ_390x844.png')),animations='disabled')
        print(label,'картка речі',cardtext[:500],flush=True)
        page.close()
    browser.close()
