"""Зняти стартову сторінку призначеної голови у Chromium 390×844."""
import functools
import http.server
import pathlib
import sys
import threading
from playwright.sync_api import sync_playwright

root = pathlib.Path(sys.argv[1]).resolve()
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(root)))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
        page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        page.goto(f"http://127.0.0.1:{server.server_port}/index.html", wait_until="commit")
        page.locator("body").wait_for(state="visible")
        page.screenshot(path=str(pathlib.Path(__file__).parent / "голова_390.png"))
        print("Знімок: Chromium, 390×844, index.html призначеної голови")
        browser.close()
finally:
    server.shutdown()
    thread.join()
    server.server_close()
