"""截图 Dashboard 全页找信用利差单位"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto('http://43.143.253.186/curv/login', wait_until='networkidle')
    page.fill('input[placeholder*="admin"]', 'admin')
    page.fill('input[type="password"]', 'admin123')
    page.click('button:has-text("登 录")')
    page.wait_for_url('**/dashboard', timeout=15000)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    # 全页截图
    page.screenshot(path=r'C:\银行经营\CURV\deploy\dashboard_full3.png', full_page=True)
    # 滚动到底
    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    page.wait_for_timeout(1000)
    page.screenshot(path=r'C:\银行经营\CURV\deploy\dashboard_bottom.png', full_page=False)
    # 找包含"信用"或"利差"的元素
    elements = page.query_selector_all('text=/信用|利差/')
    print(f'找到 {len(elements)} 个匹配元素：')
    for e in elements[:20]:
        try:
            txt = e.inner_text()
            if txt:
                print(f'  - {txt[:60]}')
        except: pass
    browser.close()