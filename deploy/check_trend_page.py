"""截图 AnalysisTrend 时序分析页面"""
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
    page.wait_for_timeout(3000)
    page.screenshot(path=r'C:\银行经营\CURV\deploy\analysis_trend.png', full_page=False)
    print('saved')
    # 点开曲线下拉看分组
    page.click('text=曲线', force=False)
    page.wait_for_timeout(1500)
    page.screenshot(path=r'C:\银行经营\CURV\deploy\analysis_trend_dropdown.png', full_page=False)
    print('dropdown saved')
    browser.close()