"""测试查询功能"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto('http://43.143.253.186/curv/login', wait_until='networkidle')
    page.fill('input[placeholder*="admin"]', 'admin')
    page.fill('input[type="password"]', 'admin123')
    page.click('button:has-text("登 录")')
    page.wait_for_url('**/dashboard', timeout=15000)
    page.goto('http://43.143.253.186/curv/analysis/trend', wait_until='networkidle')
    page.wait_for_timeout(2000)
    # 点击查询按钮
    page.click('button:has-text("查询")')
    page.wait_for_timeout(3000)
    page.screenshot(path=r'C:\银行经营\CURV\deploy\trend_query.png', full_page=True)
    print('saved')
    browser.close()