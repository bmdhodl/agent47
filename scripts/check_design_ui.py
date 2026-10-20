"""Browser checks for maintained BMD surfaces, with local-only synthetic data."""
import functools
import http.server
import json
import sys
import tempfile
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/playwright"

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

def check_page(page, name, url):
    checks = []
    for width in (375, 768, 1440):
        page.set_viewport_size({"width": width, "height": 900})
        page.goto(url, wait_until="networkidle")
        page.locator(".bmd-mark").first.wait_for()
        assert page.locator(".bmd-mark").first.evaluate("el => el.complete && el.naturalWidth > 0"), name
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (name, width, "overflow")
        body = page.locator("body")
        assert body.evaluate("el => getComputedStyle(el).fontSize") == "16px", name
        assert body.evaluate("el => getComputedStyle(el).backgroundColor") == "rgb(10, 10, 10)", name
        small = page.evaluate("""() => [...document.querySelectorAll('p,small,summary,button,th,td,figcaption')]
          .filter(e=>e.getClientRects().length && parseFloat(getComputedStyle(e).fontSize)<14)
          .map(e=>({tag:e.tagName,cls:e.className,size:getComputedStyle(e).fontSize}))""")
        assert not small, (name, width, "small text", small)
        contrast = page.evaluate("() => {\n const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const ctx=canvas.getContext('2d');\n const rgb=value=>{ctx.clearRect(0,0,1,1);ctx.fillStyle=value;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].map((n,i)=>i===3?n/255:n)};\n const blend=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));\n const luminance=c=>c.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);\n const failures=[];const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);\n while(walker.nextNode()) { const node=walker.currentNode,el=node.parentElement;if(!node.textContent.trim()||!el.getClientRects().length||['SCRIPT','STYLE'].includes(el.tagName))continue;\n  const style=getComputedStyle(el);if(style.visibility==='hidden')continue;\n  let bg=[10,10,10],layers=[];for(let e=el;e;e=e.parentElement)layers.push(rgb(getComputedStyle(e).backgroundColor));\n  for(const layer of layers.reverse())bg=blend(layer,bg);\n  const color=blend(rgb(style.color),bg),a=luminance(color),b=luminance(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);\n  const size=parseFloat(style.fontSize),large=size>=24||(size>=18.66&&parseInt(style.fontWeight)>=700),required=large?3:4.5;\n  if(ratio+.03<required)failures.push({tag:el.tagName,cls:el.className,ratio:+ratio.toFixed(2),required});\n }\n return failures;\n}")
        assert not contrast, (name, width, "contrast", contrast)
        page.keyboard.press("Tab")
        first = page.evaluate("document.activeElement.tagName")
        if page.locator("a,button,summary").count():
            assert first != "BODY", (name, "keyboard focus")
        page.screenshot(path=str(OUTPUT / f"{name}-{width}.png"), full_page=True)
        checks.append({"width":width,"overflow":False,"logo_loaded":True})
    page.emulate_media(reduced_motion="reduce")
    page.reload(wait_until="networkidle")
    running = page.evaluate("document.getAnimations().filter(a=>a.playState==='running').length")
    assert not running, (name, "reduced motion")
    page.evaluate("document.documentElement.style.zoom='2'")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (name, "200 percent zoom overflow")
    page.evaluate("document.documentElement.style.zoom='1'")
    words = page.locator('main,article').first.inner_text() if page.locator('main,article').count() else body.inner_text()
    return {"surface":name,"checks":checks,"reduced_motion":True,"zoom_200_percent":True,
            "visible_words":len(words.split()),"count_method":"rendered innerText of main/article; navigation excluded when present"}

def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bmd-design-ui-") as temporary:
        folder=Path(temporary)
        cases=fixtures(folder)
        handler=functools.partial(QuietHandler,directory=str(folder))
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        results=[]
        try:
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch()
                page=browser.new_page()
                errors=[]
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.route('**/api/**', lambda route: route.fulfill(status=503,content_type='application/json',body='{"error":"Fixture service unavailable"}'))
                for name,path in cases:
                    results.append(check_page(page,name,f'http://127.0.0.1:{server.server_port}/{path}'))
                extra_checks(page)
                assert not errors,errors
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
        (OUTPUT/'coverage.json').write_text(json.dumps({'surfaces':results,'human_review':'separate; not established by automated checks'},indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'passed':True,'surfaces':len(results),'viewports':[375,768,1440]}))

def fixtures(folder):
    import shutil
    sys.path.insert(0,str(ROOT/'sdk'))
    from agentguard.reporting import render_incident_report
    shutil.copytree(ROOT/'site',folder,dirs_exist_ok=True)
    cases=[(p.relative_to(folder).as_posix().replace('/','-').removesuffix('.html'),p.relative_to(folder).as_posix()) for p in folder.rglob('*.html') if p.name!='security.html']
    for name,events in [('incident-empty',[]),('incident-error',[{'kind':'event','name':'guard.budget_exceeded','data':{'message':'Fixture limit exceeded'},'error':None}])]:
        path=name+'.html'
        (folder/path).write_text(render_incident_report(events,output_format='html'),encoding='utf-8')
        cases.append((name,path))
    return cases

def extra_checks(page):
    pass

if __name__ == "__main__":
    main()
