import os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
    pg = b.new_page(viewport={'width': 360, 'height': 640}, device_scale_factor=3)
    pg.goto('file://' + os.path.abspath('rec.html')); pg.wait_for_timeout(500)
    pg.evaluate("document.getElementById('endcard').hidden = false")
    pg.wait_for_timeout(200)
    pg.screenshot(path='out/endcard.png')
    b.close()
