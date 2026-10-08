"""Isolated headless Chromium/Pyodide 0.26.4; only versioned CDN reads allowed."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path('/workspace/liusterko-hypergraph-gpt-e70c3c3')
BASE='https://cdn.jsdelivr.net/pyodide/v0.26.4/full/'

async def main():
    source=(ROOT/'prototypes/model.py').read_text().split("\nif __name__==")[0]
    requests=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=await browser.new_page(viewport={'width':390,'height':844})
        async def route(r):
            url=r.request.url
            if r.request.method=='GET' and url.startswith(BASE):
                requests.append(url)
                local=Path('/tmp/liusterko-pyodide-0.26.4')/url[len(BASE):]
                if local.is_file():
                    await r.fulfill(path=str(local),headers={'Access-Control-Allow-Origin':'*'})
                else:
                    await r.abort()
            else: await r.abort()
        await page.route('**/*',route)
        await page.set_content('<!doctype html><html><body>Isolated CPU research</body></html>')
        await page.add_script_tag(url=BASE+'pyodide.js')
        result=await page.evaluate('''async ({source,base}) => {
            const start=performance.now();
            const py=await loadPyodide({indexURL:base});
            const load_ms=performance.now()-start;
            py.runPython(source);
            const result=JSON.parse(py.runPython('json.dumps(run(), ensure_ascii=False)'));
            return {pyodide_version:py.version, python_version:py.runPython('import sys; sys.version'),
                    load_ms, user_agent:navigator.userAgent, viewport:[innerWidth,innerHeight], result};
        }''',{'source':source,'base':BASE})
        result['network_requests']=requests
        result['limits']='Desktop headless Chromium; mobile viewport only, not a physical mobile performance test. Versioned CDN assets predownloaded with urllib and served by route interception after direct script loading failed.'
        (ROOT/'evidence/browser_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='result' and k!='network_requests'}))
        print(json.dumps(result['result']['benchmark']))
        await browser.close()

if __name__=='__main__': asyncio.run(main())
