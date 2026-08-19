"""截图 AnalysisSpread 利差形态页面"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1400})
    page.goto('http://43.143.253.186/curv/login', wait_until='networkidle')
    page.fill('input[placeholder*="admin"]', 'admin')
    page.fill('input[type="password"]', 'admin123')
    page.click('button:has-text("登 录")')
    page.wait_for_url('**/dashboard', timeout=15000)
    page.goto('http://43.143.253.186/curv/analysis/spread', wait_until='networkidle')
    page.wait_for_timeout(4000)
    # 强制点查询按钮（用 form submit 避免时序问题）
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(5000)
    page.screenshot(path=r'C:\银行经营\CURV\deploy\spread_page.png', full_page=True)
    print('saved')
    browser.close()