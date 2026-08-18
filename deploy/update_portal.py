"""更新 portal 加 CURV 卡片"""
with open('/var/www/portal/index.html') as f:
    c = f.read()

# 1. 加 CURV 主题样式
new_styles = """
  .theme-curv { --theme: #6b4c8a; }
  .theme-curv .enter-btn { background: linear-gradient(135deg, #6b4c8a, #4a3360); }
  .theme-curv h2 { color: #4a3360; }
"""
c = c.replace(
    '  .theme-almt h2 { color: #2c5b40; }',
    '  .theme-almt h2 { color: #2c5b40; }\n' + new_styles,
    1
)

# 2. 加 CURV 模块卡片
curv_card = """
      <a href="/curv/" class="module-card theme-curv">
        <img class="seal" src="/design/curv_icon.png" alt="CURV" onerror="this.style.display='none'" />
        <h2>收益率曲线管理</h2>
        <div class="en-name">CURV · 曲</div>
        <div class="desc">银行经营基准曲线数据底座<br/>11 条曲线 · 智能构建引擎<br/>多 Agent 工作流 + 智能对话</div>
        <ul class="features">
          <li>中债/国开/信用/货币市场曲线</li>
          <li>NS/NSS 拟合 · PCHIP 插值</li>
          <li>敏感度 · 情景 · 压力测试</li>
          <li>FTP 定价 · 估值核算 · 监管报送</li>
        </ul>
        <span class="enter-btn">进 入 模 块</span>
      </a>
"""
old_end = """<span class="enter-btn">进 入 模 块</span>
      </a>
    </div>"""
new_end = """<span class="enter-btn">进 入 模 块</span>
      </a>
""" + curv_card + """    </div>"""
c = c.replace(old_end, new_end, 1)

with open('/var/www/portal/index.html', 'w') as f:
    f.write(c)
print('DONE, total theme-curv:', c.count('theme-curv'))