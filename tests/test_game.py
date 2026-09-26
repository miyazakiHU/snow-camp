"""Browser regression tests. --in-memory is an explicit offline test substitute.
The normal mode serves the real entry point and checks real browser storage.
No debug interface or test save is included in the published game.
"""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
import argparse, base64, hashlib, json, re, tempfile, threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
KEY = 'shiokaze_workshop_v3'
parser = argparse.ArgumentParser()
parser.add_argument('--in-memory', action='store_true')
parser.add_argument('--browser', default=None)
args = parser.parse_args()
html = (ROOT / 'index.html').read_text()
js = (ROOT / 'game.js').read_text()
hash_value = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
assert "'sha256-" + hash_value + "'" in html, 'CSP hash mismatch'
assert 'integrity="sha256-' + hash_value + '"' in html, 'SRI mismatch'
assert '__qa' not in js, 'Test hook leaked into production'
assert "connect-src 'none'" in html, 'Unexpected network policy'
assert not re.search(r'https?://|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|-----BEGIN .*PRIVATE KEY', js)

hook = """
window.__qa={get state(){return state},get meta(){return meta},get player(){return player},get mill(){return mill},get nodes(){return nodes},get gatherer(){return gatherer},get courier(){return courier},cfg,capacity,price,orderSize,orderActive,special,specialCash,solid,pathTo,resetRun,snapshot,validate,save,load,finish,showRoute,closePanel,render,project,get paused(){return paused},upgrades,
step(seconds){for(let x=0;x<seconds;x+=.025)update(Math.min(.025,seconds-x));},
go(x,z){inputStart();target={x,z};player.destKey='';},
teleport(x,z){player.x=x;player.z=z;target=null;player.destKey='';}};
"""
qa_js = js.rsplit('})();', 1)[0] + hook + '})();\n'
qa_hash = base64.b64encode(hashlib.sha256(qa_js.encode()).digest()).decode()
qa_html = re.sub(r'<script src="./game.js"[^>]*></script>', lambda _: '<script>' + qa_js + '</script>', html).replace(hash_value, qa_hash)
inline_html = re.sub(r'<script src="./game.js"[^>]*></script>', lambda _: '<script>' + js + '</script>', html)
results = []
errors = []
output = ROOT / 'test-results'
output.mkdir(exist_ok=True)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

temp = tempfile.TemporaryDirectory()
serve = Path(temp.name)
for name, content in [('index.html', html), ('game.js', js), ('qa.html', qa_html)]:
    (serve / name).write_text(content)
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(serve)))
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = 'http://127.0.0.1:' + str(server.server_port)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=args.browser, headless=True,
        args=['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'])

    def new_page(mobile=False, qa=True, seed=None, software=False, blocked=False):
        context = browser.new_context(viewport={'width': 390 if mobile else 1280, 'height': 844 if mobile else 800}, has_touch=mobile, is_mobile=mobile)
        page = context.new_page()
        init = 'requestAnimationFrame=()=>0;' if qa else ''
        if software:
            init += "const originalContext=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(k,...a){return k==='webgl2'?null:originalContext.call(this,k,...a)};"
        if args.in_memory or blocked:
            init += "Object.defineProperty(window,'localStorage',{value:{data:" + json.dumps(seed or {}) + ",getItem(k){return this.data[k]??null},setItem(k,v){" + ("throw Error('storage denied');" if blocked else "this.data[k]=String(v);") + "},removeItem(k){delete this.data[k]}}});"
        elif seed:
            init += "if(!sessionStorage.seeded){for(const [k,v] of Object.entries(" + json.dumps(seed) + "))localStorage.setItem(k,v);sessionStorage.seeded='yes';}"
        if args.in_memory:
            page.evaluate(init or 'void 0')
        else:
            page.add_init_script(init or 'void 0')
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'favicon' not in m.text else None)
        if args.in_memory:
            page.set_content(qa_html if qa else inline_html)
        else:
            page.goto(origin + ('/qa.html' if qa else '/index.html'))
        return context, page

    def check(name, value):
        assert value, name
        results.append({'test': name, 'passed': True})

    for mobile in [False, True]:
        context, page = new_page(mobile, qa=False)
        page.wait_for_timeout(400)
        check('startup ' + ('mobile' if mobile else 'desktop'), page.locator('#error').is_hidden() and page.locator('#islandName').inner_text() != '')
        if not args.in_memory:
            check('WebGL initialized', page.evaluate("!!document.querySelector('#world').getContext('webgl2')"))
        page.screenshot(path=str(output / ('mobile.png' if mobile else 'desktop.png')))
        context.close()
    context, page = new_page(qa=False, software=True)
    check('Canvas fallback startup', page.locator('#error').is_hidden())
    context.close()

    context, page = new_page()
    check('fresh save valid', page.evaluate('__qa.validate(__qa.snapshot())'))
    value = page.evaluate("""()=>{let q=__qa,c=q.cfg();q.go(-3,-4);q.step(9);const collected=q.player.raw;q.go(c.drop.x,c.drop.z);q.step(15);const crafted=q.player.parts;q.go(c.sell.x,c.sell.z);q.step(10);q.go(c.cash.x,c.cash.z);q.step(8);return collected>0&&crafted>0&&q.state.money===q.state.sold*q.price();}""")
    check('walk, collect, craft, sell and collect revenue', value)
    check('inventory conservation', page.evaluate("""()=>{let q=__qa,s=q.state;return s.harvested===q.player.raw+q.player.parts+q.mill.raw+q.mill.parts+q.gatherer.raw+q.gatherer.parts+q.courier.raw+q.courier.parts+s.counter+s.sold+s.mission+s.specialProgress;}"""))
    value = page.evaluate("""()=>{let q=__qa,p=q.upgrades[0];q.teleport(p.x,p.z);q.go(p.x,p.z);q.step(.2);const before=q.state.money;q.step(.5);q.save();return before===72&&q.state.pack===0&&q.state.paid.pack>0&&q.state.money<72;}""")
    check('purchase dwell and partial payment', value)
    saved = page.evaluate('localStorage.getItem(' + json.dumps(KEY) + ')')
    c2, p2 = new_page(seed={KEY: saved})
    check('partial purchase survives load', p2.evaluate('__qa.state.paid.pack>0 && __qa.validate(__qa.snapshot())'))
    p2.evaluate('__qa.step(3)')
    check('no spending before input after load', json.loads(saved)['state']['money'] == p2.evaluate('__qa.state.money'))
    c2.close()
    page.evaluate('__qa.step(3)')
    check('purchase paid exactly once', page.evaluate('__qa.state.pack===1&&__qa.state.spent===40&&__qa.state.money===32'))
    page.evaluate('__qa.step(5)')
    check('standing cannot buy repeated levels', page.evaluate('__qa.state.pack===1&&Object.keys(__qa.state.paid).length===0'))
    check('money conservation', page.evaluate('__qa.state.money+__qa.state.till+__qa.state.specialTill+__qa.state.spent===__qa.state.earned+__qa.state.granted'))

    value = page.evaluate("""()=>{let q=__qa;q.resetRun(1,'none');const a={x:-3,z:4},b=q.nodes[0];function length(path){let p=a,n=0;for(let x of path){n+=Math.hypot(x.x-p.x,x.z-p.z);p=x}return n;}const before=length(q.pathTo(a,b));const closed=q.solid(-3,-1);q.upgrades.find(p=>p.id==='bridge').apply();return closed&&!q.solid(-3,-1)&&length(q.pathTo(a,b))<before*.7;}""")
    check('bridge changes traversability and route length', value)
    page.evaluate("__qa.state.gatherer=true;__qa.state.courier=true;__qa.teleport(7,7);__qa.step(100)")
    check('staff complete the production-to-sale loop', page.evaluate('__qa.state.earned>0'))
    check('staff save valid', page.evaluate('__qa.validate(__qa.snapshot())'))
    value = page.evaluate("""()=>{let q=__qa;q.resetRun(0,'none');q.state.mission=q.cfg().target-1;q.player.parts=1;q.teleport(q.cfg().repair.x,q.cfg().repair.z);q.step(3);const a=JSON.stringify(q.meta);q.finish();return q.state.done&&q.meta.completed[0]&&q.meta.unlocked.includes('cart')&&a===JSON.stringify(q.meta);}""")
    check('completion and reward idempotence', value)
    page.locator('#next').click()
    page.locator('[data-tool="cart"]').click()
    page.locator('#depart').click()
    check('route and selected tool persist while local economy resets', page.evaluate("__qa.state.island===1&&__qa.state.tool==='cart'&&__qa.state.pack===0&&__qa.state.money===20&&__qa.meta.completed[0]&&__qa.capacity()===24"))
    value = page.evaluate("""()=>{let q=__qa;q.resetRun(2,'press');q.player.parts=3;q.teleport(q.special.x,q.special.z);q.step(.5);const partial=q.state.specialProgress;q.state.elapsed=26;q.step(3);const held=q.state.specialProgress===partial;q.state.elapsed=45;q.player.parts=5;q.step(1);return partial===3&&held&&q.state.specialCount===1&&q.state.specialTill===8*q.price()*2&&q.state.specialProgress===0;}""")
    check('boat order progress survives closed window; reward paid once', value)
    page.evaluate('__qa.step(5)')
    check('boat completion is idempotent', page.evaluate('__qa.state.specialCount===1'))
    context.close()

    old = json.dumps({'state': {'version': 2, 'sound': False, 'money': 123}})
    context, page = new_page(seed={'snowcamp_direct_v2_1': old})
    check('legacy save retained with one-time tool recognition', page.evaluate("__qa.meta.legacy&&__qa.state.tool==='cart'&&__qa.meta.sound===false") and page.evaluate("localStorage.getItem('snowcamp_direct_v2_1')") == old)
    context.close()
    context, page = new_page(seed={KEY: '{invalid', KEY+'.backup': saved})
    check('corrupt primary save recovers backup', page.evaluate('__qa.validate(__qa.snapshot())&&__qa.state.paid.pack>0'))
    context.close()
    context, page = new_page(blocked=True)
    check('blocked storage does not prevent play', page.locator('#error').is_hidden() and '保存できません' in page.locator('#saveWarn').inner_text())
    context.close()

    context, page = new_page(mobile=True)
    before = page.evaluate('({x:__qa.player.x,z:__qa.player.z})')
    cdp = context.new_cdp_session(page)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':180,'y':650}]})
    cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':230,'y':610}]})
    page.evaluate('__qa.step(.5)')
    cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
    after = page.evaluate('({x:__qa.player.x,z:__qa.player.z})')
    check('touch drag moves character', before != after)
    page.evaluate('__qa.step(1)')
    check('touch release stops movement', page.evaluate('({x:__qa.player.x,z:__qa.player.z})') == after)
    page.locator('#menuBtn').click()
    paused_before = page.evaluate('__qa.state.elapsed')
    page.evaluate('__qa.step(4)')
    check('menu pauses simulation', page.evaluate('__qa.state.elapsed') == paused_before)
    page.locator('#resume').click()
    check('mobile viewport fits without horizontal overflow', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    context.close()
    check('no JavaScript or CSP console errors', not errors)
    browser.close()
server.shutdown()
temp.cleanup()
report = {'mode': 'in-memory with substitute storage' if args.in_memory else 'HTTP with browser storage', 'tests': results, 'errors': errors}
(output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
