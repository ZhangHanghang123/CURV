"""验证 AnalysisTrend 和 AnalysisSpread 自动查询"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1400})

    # 登录
    page.goto('http://43.143.253.186/curv/login', wait_until='networkidle')
    page.fill('input[placeholder*="admin"]', 'admin')
    page.fill('input[type="password"]', 'admin123')
    page.click('button:has-text("登 录")')
    page.wait_for_url('**/dashboard', timeout=15000)

    # 时序分析 - 不点查询
    page.goto('http://43.143.253.186/curv/analysis/trend', wait_until='networkidle')
    page.wait_for_timeout(4000)
    page.screenshot(path=r'C:\银行经营\CURV\deploy\auto_trend.png', full_page=True)
    print('trend saved')

    # 利差形态 - 不点查询
    page.goto('http://43.143.253.186/curv/analysis/spread', wait_until='networkidle')
    page.wait_for_timeout(4000)
    page.screenshot(path=r'C:\银行经营\CURV\deploy\auto_spread.png', full_page=True)
    print('spread saved')

    browser.close()