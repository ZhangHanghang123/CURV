"""Playwright 脚本：注入调试代码看 dashboard 实际拿到的 data"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path(r"C:\银行经营\CURV\deploy")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page = await ctx.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text[:500]}"))
        page.on("pageerror", lambda e: console_logs.append(f"[ERROR] {e}"))

        # 登录
        await page.goto("http://43.143.253.186/curv/", wait_until="domcontentloaded")
        await page.locator("input[placeholder*='用户']").fill("admin")
        await page.locator("input[type='password']").fill("admin123")
        await page.get_by_role("button", name="登 录").click()
        await page.wait_for_url("**/curv/dashboard", timeout=15000)
        await asyncio.sleep(6)

        # 在浏览器中执行 JS，看 React 内部状态（但 React 状态无法直接访问）
        # 检查 localStorage token
        token = await page.evaluate("() => localStorage.getItem('token')")
        user = await page.evaluate("() => localStorage.getItem('user')")
        print(f"Token: {token[:30] if token else 'None'}...")
        print(f"User: {user}")

        # 提取 KPI 实际显示数值
        stats = await page.locator(".ant-statistic").all()
        print(f"\nKPI 显示值:")
        for s in stats:
            try:
                title = await s.locator(".ant-statistic-title").text_content()
                value = await s.locator(".ant-statistic-content-value").text_content()
                print(f"  {title}: {value}")
            except Exception as e:
                print(f"  err: {e}")

        # 直接 fetch API 验证 token 是否有效
        api_test = await page.evaluate("""
            async () => {
                const token = localStorage.getItem('token');
                const r = await fetch('/curv/api/dashboard', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                const j = await r.json();
                return { status: r.status, code: j.code, hasData: !!j.data, kpi_curve: j.data?.kpi?.curve_count };
            }
        """)
        print(f"\n浏览器内 fetch API 结果: {api_test}")

        # 触发一次 React 刷新按钮（强制重新加载数据）
        try:
            await page.get_by_text("刷新").click()
            await asyncio.sleep(3)
        except Exception as e:
            print(f"点击刷新失败: {e}")

        # 再看 KPI
        stats2 = await page.locator(".ant-statistic").all()
        print(f"\n刷新后 KPI 显示值:")
        for s in stats2[:6]:
            try:
                title = await s.locator(".ant-statistic-title").text_content()
                value = await s.locator(".ant-statistic-content-value").text_content()
                print(f"  {title}: {value}")
            except Exception:
                pass

        print(f"\n=== Console 日志 ({len(console_logs)} 条) ===")
        for log in console_logs[:30]:
            print(f"  {log}")

        await page.screenshot(path=str(OUT / "dashboard_diag.png"), full_page=True)
        await browser.close()


asyncio.run(main())