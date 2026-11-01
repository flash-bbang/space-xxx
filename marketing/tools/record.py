"""Record the SPACE XXX promo by driving the real game on a virtual clock.

python3 record.py preview   -> a few full-size stills in out/stills/
python3 record.py full      -> out/promo_silent.mp4 + out/events.json (timestamps for the sound track)
"""
import json, os, subprocess, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out'); os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
MODE = sys.argv[1] if len(sys.argv) > 1 else 'preview'
FPS = 30
DT = 1000 / FPS

CLOCK = r"""
(() => {
  let now = 0; const raf = []; const timers = []; let tid = 1;
  performance.now = () => now;
  window.requestAnimationFrame = cb => { raf.push(cb); return raf.length; };
  window.setTimeout = (cb, ms, ...a) => { const id = tid++; timers.push({id, at: now + (+ms || 0), cb: () => cb(...a)}); return id; };
  window.clearTimeout = id => { const i = timers.findIndex(t => t.id === id); if (i >= 0) timers.splice(i, 1); };
  window.setInterval = () => 0;
  window.__tick = ms => {
    now += ms;
    timers.sort((a, b) => a.at - b.at);
    while (timers.length && timers[0].at <= now){ const t = timers.shift(); try { t.cb(); } catch(e){ console.error(e); } }
    raf.splice(0).forEach(cb => { try { cb(now); } catch(e){ console.error(e); } });
  };
  window.__auto = 'off';
})();
"""

AUTO = r"""(() => {
  if (state !== 'play' || !mover || fx.boost > 0) return '';
  const top = stack[stack.length-1];
  const sp = speed * (fx.slow > 0 ? .55 : 1) * (fx.fast > 0 ? 2.6 : 1);
  if (window.__auto === 'perfect' && !mover.__near){ mover.__near = true; mover.x = top.x - mover.dir * 64; }   // start each slab close so the edit stays snappy
  if (window.__auto === 'perfect' && Math.abs(mover.x - top.x) < sp * 2.2){ mover.x = top.x; drop(false); return 'drop'; }
  return '';
})()"""

events, t_ms = [], 0.0

def main():
    global t_ms
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--autoplay-policy=no-user-gesture-required'])
        page = browser.new_page(viewport={'width': 360, 'height': 640}, device_scale_factor=3)
        page.on('console', lambda m: m.type == 'error' and print('PAGE ERROR:', m.text))
        page.on('pageerror', lambda e: print('PAGE EXCEPTION:', e))
        page.add_init_script(CLOCK)
        page.goto('file://' + os.path.join(HERE, 'rec.html'))
        page.wait_for_timeout(300)

        ev = lambda code: page.evaluate('c => window.__G.ev(c)', code)
        cap = lambda html: page.evaluate('h => document.getElementById("cap").innerHTML = h', html)

        ff = None
        if MODE == 'full':
            tmp = os.path.join(OUT, 'promo_silent.tmp.mp4')
            ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                                   '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)

        state_seen = {'floors': 0, 'cut': ''}
        def frames(n, speed=1.0, still=None):
            global t_ms
            for i in range(n):
                r = page.evaluate('a => { window.__G.ev(a); window.__tick(%f); return window.__G.ev("[state, stack.length, combo, cutin ? cutin.kind + \':\' + cutin.t0 : \'\']"); }' % (DT * speed), AUTO)
                st, n_floors, combo, cut = r
                ts = round(t_ms / 1000, 3)
                if st == 'play' and n_floors > state_seen['floors']: events.append(['floor', ts, combo])
                state_seen['floors'] = n_floors
                if cut and cut != state_seen['cut']: events.append(['cutin_' + cut.split(':')[0], ts])
                state_seen['cut'] = cut
                if ff:
                    ff.stdin.write(page.screenshot(type='jpeg', quality=92))
                elif still and i == n - 1:
                    page.screenshot(path=os.path.join(OUT, 'stills', still + '.png'))
                t_ms += DT

        def mark(name): events.append([name, round(t_ms / 1000, 3)])

        # --- setup: quiet the random spawns so every beat happens on cue ---
        ev("""nick = '빵돌이'; nickEl.value = '빵돌이'; D.item = 0;
              window.__devTroll = devTroll; devTroll = function(){};""")

        # S0 hook: start screen
        page.evaluate("document.getElementById('cap').style.top = '58px'; document.querySelector('#start p').style.display = 'none'")
        cap('블록 쌓기 게임인데<br><em>자꾸 뭐가 방해함</em>')
        frames(54, still='s0_start')
        page.evaluate("document.getElementById('cap').style.top = ''")
        ev("startGame(); nextHz = 1e9; nextDropT = 1e12;")
        mark('start')

        # S1 perfect combo -> auto 3 floors
        page.evaluate("window.__auto = 'perfect'")
        cap('퍼펙트 5연속이면<br><em>3층 자동으로 쌓아줌</em>')
        frames(135, still='s1_combo')

        # S2 pigeon
        page.evaluate("window.__auto = 'off'")
        ev("mover = null; startHazard('pigeon'); hz.dir = 1; hz.x = -40; hz.tx = stack[stack.length-1].x + stack[stack.length-1].w*.62;")
        cap('근데 하늘에서<br><em>비둘기가 똥 싸고 감</em>')
        mark('pigeon')
        frames(100, still='s2_pigeon')
        ev("spawn();")

        # S3 neighbor throws a cat
        ev("mover = null; startHazard('ajussi'); hz.side = -1; hz.pr = PROJ[2];")
        cap('옆집 아저씨는<br><em>고양이를 던짐</em>')
        mark('ajussi')
        frames(150, still='s3_ajussi')
        ev("hz = null; spawn();")

        # S4 developer flips the screen
        page.evaluate("window.__auto = 'perfect'")
        ev("devTroll = window.__devTroll; devTroll(); fx.fast = 0; fx.flip = 3; cutin.sub = '화면 뒤집기 패치 적용합니다'; renderFx(); devTroll = function(){};")
        cap('잘하면 개발자가<br><em>화면을 뒤집어버림</em>')
        mark('dev')
        frames(120, still='s4_flip')

        # S5 gift box -> mine -> blackout
        page.evaluate("window.__auto = 'off'")
        ev("fx.flip = 0; renderFx(); drops.push({k:'gift', x:W*.5, y:110, vy:2.1, t:0});")
        cap('떨어지는 선물 상자?<br><em>먹어야지 ㅎㅎ</em>')
        frames(28)
        ev("""const d = drops.shift(), px = d.x + Math.sin(d.t/20)*14, wyP = toWorldY(d.y);
              lastTapItemT = performance.now(); lastHit = {kind:'mine', t:performance.now()};
              burstAt(px, wyP, 34, ['#ff8a65','#ffd36e','#2b2b33'], 8); shake = 10;
              blackout = performance.now() + 4000;
              cutin = {kind:'mine', text:'낚였다 ㅋㅋ', sub:'4초 동안 앞이 안 보여요', t0:performance.now(), dur:1500};""")
        cap('<em>지뢰였음 ㅋㅋㅋ</em>')
        mark('mine')
        frames(80, still='s5_mine')

        # S6 collapse
        ev("blackout = 0;")
        cap('')
        ev("const top = stack[stack.length-1]; mover.x = top.x + top.w + 12; drop(false); document.getElementById('doomT').textContent = '아 ㅋㅋ 이걸 처맞네';")
        mark('collapse')
        frames(100, still='s6_doom')

        # S7 jump to floor 119, then the 120th floor launches the rocket
        ev("""startGame(); nextHz = 1e9; nextDropT = 1e12; D.item = 0;
              for (let i = 0; i < 119; i++){ mover.x = stack[stack.length-1].x; drop(true); fx.boost = 0; }
              hz = null; cutin = null; drops = []; $('zone').classList.remove('on'); $('pop').classList.remove('on');
              cam = Math.max(0, stack.length*BH - H*0.42);""")
        cap('120층 찍으면<br><em>랜덤 점수만큼 우주로 발사</em>')
        frames(24)
        ev("showEnding = function(){}; mover.x = stack[stack.length-1].x; drop(true); flight.dest = 6; flight.score = 16241;")
        mark('launch')
        frames(66, still='s7_launch')
        cap('')
        n = 0
        while ev("flight.phase") != 'boom' and n < 400:   # flight runs at double speed until the crash
            frames(1, speed=2.0); n += 1
        page.screenshot(path=os.path.join(OUT, 'stills', 's7_warp.png')) if MODE != 'full' else None
        cap('<em>블랙홀 잭팟</em> ㅋㅋㅋ')
        mark('boom')
        frames(75, still='s7_boom')

        # S8 end card
        cap('')
        page.evaluate("document.getElementById('endcard').hidden = false")
        mark('endcard')
        frames(96, still='s8_end')

        if ff:
            ff.stdin.close(); code = ff.wait()
            if code == 0:
                os.replace(os.path.join(OUT, 'promo_silent.tmp.mp4'), os.path.join(OUT, 'promo_silent.mp4'))
            print('ffmpeg exit', code)
        json.dump({'duration': round(t_ms / 1000, 3), 'events': events}, open(os.path.join(OUT, 'events.json'), 'w'), ensure_ascii=False, indent=1)
        print('duration', round(t_ms / 1000, 2), 's,', len(events), 'events')
        browser.close()

main()
