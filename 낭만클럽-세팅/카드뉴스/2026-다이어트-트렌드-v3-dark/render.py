# -*- coding: utf-8 -*-
"""카드뉴스 index.html -> output/slide_01~07.png (1080x1350, device_scale_factor=2 고해상도) 추출."""
import os
import pathlib
import subprocess
import sys

# playwright 미설치 시 자동 설치 (패키지 + Chromium 바이너리)
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

url = pathlib.Path(BASE, "index.html").as_uri()
SLIDES = 7

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 1080, "height": 1350},
        device_scale_factor=2,
    )
    page.goto(url, wait_until="networkidle")
    page.evaluate("() => document.fonts.ready")  # Pretendard/JetBrains Mono 로드 대기

    for i in range(SLIDES):
        page.evaluate(f"setSlide({i})")
        page.wait_for_timeout(400)
        out_path = os.path.join(OUT, f"slide_{i + 1:02d}.png")
        page.locator("#card-container").screenshot(path=out_path)
        print(f"saved {out_path}")

    browser.close()

print("done")
