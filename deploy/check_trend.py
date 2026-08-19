"""验证 Dashboard 趋势图修复后的渲染效果"""
from playwright.sync_api import sync_playwright
import sys

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    # 登录
    page.goto('http://43.143.253.186/curv/login', wait_until='networkidle')
    page.fill('input[placeholder*="admin"]', 'admin')
    page.fill('input[type="password"]', 'admin123')
    page.click('button:has-text("登 录")')
    page.wait_for_url('**/dashboard', timeout=15000)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    # 滚动到趋势图区域
    page.evaluate('window.scrollTo(0, 200)')
    page.wait_for_timeout(1000)
    page.screenshot(path=r'C:\银行经营\CURV\deploy\trend_fix.png', full_page=False)
    print('saved: C:\\银行经营\\CURV\\deploy\\trend_fix.png')
    browser.close()