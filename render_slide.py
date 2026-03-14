"""Script auxiliar — roda Playwright em processo separado (fix Windows asyncio)"""
import sys

html_path = sys.argv[1]
png_path = sys.argv[2]

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1080, "height": 1080})
    page.goto(f"file:///{html_path.replace(chr(92), '/')}")
    page.wait_for_timeout(2000)
    page.screenshot(path=png_path, full_page=False)
    browser.close()
