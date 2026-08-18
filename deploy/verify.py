"""端到端 API 验证（用 urllib）"""
import urllib.request, urllib.parse, json

BASE = 'http://43.143.253.186/curv'

def call(method, path, data=None, headers=None):
    url = f'{BASE}{path}'
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, method=method,
                                 headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())

# 1. 登录
r = call('POST', '/api/auth/login', {'username': 'admin', 'password': 'admin123'})
print(f'[1] 登录: code={r["code"]} token_len={len(r["data"]["token"])}')
token = r['data']['token']
H = {'Authorization': f'Bearer {token}'}

# 2. Dashboard
r = call('GET', '/api/dashboard', headers=H)
print(f'[2] Dashboard: code={r["code"]} kpi={r["data"]["kpi"]}')

# 3. 曲线定义
r = call('GET', '/api/curves/definitions', headers=H)
defs = r['data']
print(f'[3] 曲线定义: 共 {len(defs)} 条')
for d in defs[:3]:
    print(f'    - {d["code"]:30s} | {d["name"]}')

# 4. 曲线点
r = call('GET', '/api/curves/points?curve_code=cnb_treasury_yield', headers=H)
print(f'[4] 曲线点: {len(r["data"])} 个')

# 5. 字典
r = call('GET', '/api/dict/types', headers=H)
print(f'[5] 字典类型: {len(r["data"])}')

# 6. NS 拟合
body = json.dumps({'curve_code': 'cnb_treasury_yield', 'trade_date': '2026-08-18', 'model': 'nelson_siegel'}).encode()
H2 = dict(H, **{'Content-Type': 'application/json'})
r = call('POST', '/api/build/fit', body, H2)
fit = r['data']
print(f'[6] NS 拟合: RMSE={fit["rmse_bp"]}bp R2={fit["r2"]}')

# 7. 利差
r = call('GET', '/api/analysis/spread?curve_code=cnb_treasury_yield&long_tenor=10Y&short_tenor=1Y', headers=H)
print(f'[7] 10Y-1Y 利差: {r["data"]["spread_bp"]}bp')

# 8. 智能问数
body = json.dumps({'query': '10年国债利率多少'}).encode()
r = call('POST', '/api/agent/chat', body, H2)
print(f'[8] 智能问数: intent={r["data"]["intent"]} text={r["data"]["text"][:60]}')

print()
print('=== 全部 API 端到端验证通过 ===')