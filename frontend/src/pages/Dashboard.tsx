import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Spin, Tag, Progress, Space, Typography, Tooltip } from 'antd'
import {
  LineChartOutlined, DatabaseOutlined, FileTextOutlined, CheckCircleOutlined,
  RiseOutlined, FallOutlined, ApiOutlined,
  NodeIndexOutlined, MessageOutlined, BarChartOutlined,
  ClusterOutlined, LinkOutlined, ExperimentOutlined, PieChartOutlined,
  ReloadOutlined, StockOutlined, FundOutlined, ThunderboltOutlined,
  CalculatorOutlined, ScheduleOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { dashboardApi } from '../api'

const { Text, Title } = Typography

// CURV 吉祥物（与登录页同款）
function CurvMascot({ size = 44 }: { size?: number }) {
  return (
    <div
      style={{
        width: size, height: size, borderRadius: '50%',
        background: 'linear-gradient(135deg, #b37feb, #722ed1, #531dab)',
        boxShadow: '0 2px 12px rgba(114, 46, 209, 0.35)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        animation: 'curvPulse 2s ease-in-out infinite',
        transition: 'transform 0.15s',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.animation = 'none'; e.currentTarget.style.transform = 'scale(1.2)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.animation = 'curvPulse 2s ease-in-out infinite'; e.currentTarget.style.transform = 'scale(1)'; }}
    >
      <svg viewBox="0 0 64 64" width={size * 0.7} height={size * 0.7}>
        <path d="M6 18 Q14 8 22 14 T40 12 T58 18" fill="none" stroke="#FFF8E7" strokeWidth="2" strokeLinecap="round" style={{ animation: 'curvCurveWave 1.8s ease-in-out infinite' }} />
        <ellipse cx="32" cy="36" rx="20" ry="17" fill="#FFF8E7" stroke="#D4A574" strokeWidth="1.5" />
        <ellipse cx="13" cy="22" rx="5.5" ry="4.5" fill="#FFF8E7" stroke="#D4A574" strokeWidth="1.2" transform="rotate(-18, 13, 22)" />
        <ellipse cx="13" cy="22" rx="3" ry="2.5" fill="#FFE0C0" />
        <ellipse cx="51" cy="22" rx="5.5" ry="4.5" fill="#FFF8E7" stroke="#D4A574" strokeWidth="1.2" transform="rotate(18, 51, 22)" />
        <ellipse cx="51" cy="22" rx="3" ry="2.5" fill="#FFE0C0" />
        <path d="M16 20 Q13 10 10 8" fill="none" stroke="#8B6914" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="10" cy="8" r="2.5" fill="#D4A017" />
        <path d="M48 20 Q51 10 54 8" fill="none" stroke="#8B6914" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="54" cy="8" r="2.5" fill="#D4A017" />
        <ellipse cx="25" cy="31" rx="4.5" ry="5" fill="#fff" />
        <circle cx="26" cy="31" r="2.5" fill="#2c1810" />
        <circle cx="27" cy="30" r="1" fill="#fff" />
        <ellipse cx="39" cy="31" rx="4.5" ry="5" fill="#fff" />
        <circle cx="38" cy="31" r="2.5" fill="#2c1810" />
        <circle cx="39" cy="30" r="1" fill="#fff" />
        <circle cx="25" cy="31" r="7" fill="none" stroke="#722ed1" strokeWidth="1.2" />
        <circle cx="39" cy="31" r="7" fill="none" stroke="#722ed1" strokeWidth="1.2" />
        <ellipse cx="29" cy="39" rx="2" ry="1.5" fill="#D4A574" />
        <ellipse cx="35" cy="39" rx="2" ry="1.5" fill="#D4A574" />
        <path d="M27 43 Q32 46 37 43" fill="none" stroke="#D4A574" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    </div>
  )
}

function EmptyPlaceholder({ text }: { text: string }) {
  return <div style={{ textAlign: 'center', padding: '40px 0', color: '#bfbfbf', fontSize: 14 }}>{text}</div>
}

function MiniBarChart({ data, height = 120, color = '#1677ff', unit = '%' }: {
  data: { period: string; value: number }[]; height?: number; color?: string; unit?: string;
}) {
  if (!data.length) return <EmptyPlaceholder text="暂无趋势数据" />
  const max = Math.max(...data.map(d => d.value), 0.01)
  const min = Math.min(...data.map(d => d.value), 0)
  const range = max - min || 1
  // 间隔显示 x 轴日期，避免 30 天密集时日期标签重叠（保留首个和最后一个）
  const step = Math.max(1, Math.ceil(data.length / 7))
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height, paddingTop: 24, justifyContent: 'center', position: 'relative' }}>
      {data.map((item, idx) => {
        const showLabel = idx === 0 || idx === data.length - 1 || idx % step === 0
        return (
          <div key={item.period} style={{ textAlign: 'center', flex: 1, minWidth: 8, position: 'relative' }}>
            <Tooltip title={`${item.value}${unit}`}>
              <div style={{
                height: Math.max(4, ((item.value - min) / range) * (height - 50)),
                minWidth: 4,
                background: `linear-gradient(180deg, ${color}, ${color}66)`,
                borderRadius: '3px 3px 0 0',
                margin: '0 auto',
                cursor: 'pointer',
              }} />
            </Tooltip>
            <div style={{
              marginTop: 4,
              fontSize: 10,
              color: '#8c8c8c',
              whiteSpace: 'nowrap',
              visibility: showLabel ? 'visible' : 'hidden',
            }}>{item.period}</div>
          </div>
        )
      })}
    </div>
  )
}

function HorizontalBar({ data, height = 200, maxLabelLen = 8 }: {
  data: { label: string; count: number; color: string }[]; height?: number; maxLabelLen?: number;
}) {
  if (!data.length) return <EmptyPlaceholder text="暂无数据" />
  const max = Math.max(...data.map(d => d.count), 1)
  const barH = Math.max(20, Math.min(28, (height - 40) / data.length))
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingTop: 8, height }}>
      {data.map((item, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Text style={{ fontSize: 12, width: 80, textAlign: 'right', flexShrink: 0, color: '#595959' }}>
            {item.label.slice(0, maxLabelLen)}
          </Text>
          <div style={{ flex: 1, background: '#f5f5f5', borderRadius: 4, overflow: 'hidden', height: barH }}>
            <div style={{
              height: '100%', width: `${(item.count / max) * 100}%`,
              background: item.color || '#1677ff',
              borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
              paddingRight: 8, minWidth: 28,
            }}>
              <Text style={{ color: '#fff', fontSize: 11, fontWeight: 600 }}>{item.count}</Text>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

const STATUS_COLOR: Record<string, string> = {
  success: 'success', failed: 'error', running: 'processing', partial: 'warning',
}
const STATUS_LABEL: Record<string, string> = {
  success: '成功', failed: '失败', running: '执行中', partial: '部分成功',
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any>({})
  const [refreshTime, setRefreshTime] = useState('')

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res: any = await dashboardApi.getOverview()
      // 兼容 axios 拦截器已解包/未解包两种情况
      const payload = res?.data?.kpi ? res.data : res
      console.log('[Dashboard] raw response keys:', Object.keys(res || {}))
      console.log('[Dashboard] payload keys:', Object.keys(payload || {}))
      console.log('[Dashboard] payload.kpi:', payload?.kpi)
      setData(payload || {})
      setRefreshTime(new Date().toLocaleTimeString('zh-CN'))
    } catch (e) {
      console.error('[Dashboard] API error:', e)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 120 }}>
      <Spin size="large" /><div style={{ marginTop: 16, color: '#8c8c8c' }}>加载曲线数据中...</div>
    </div>
  )

  const kpi = data.kpi || {}
  const statusDist = data.status_dist || {}
  const totalRuns = (statusDist.success || 0) + (statusDist.failed || 0) + (statusDist.running || 0)
  const successPct = totalRuns > 0 ? Math.round((statusDist.success || 0) / totalRuns * 100) : 0

  // 多曲线对比 option
  const colors = ['#1677ff', '#52c41a', '#fa8c16', '#722ed1']
  const snapshot = data.snapshot_curves || []
  const xLabels = ['1Y', '3Y', '5Y', '10Y']
  const snapshotOption = {
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { fontSize: 12 } },
    grid: { left: 50, right: 20, top: 36, bottom: 30 },
    xAxis: { type: 'category', data: xLabels, name: '期限', nameLocation: 'middle', nameGap: 24 },
    yAxis: { type: 'value', name: '%', nameTextStyle: { fontSize: 11 } },
    series: snapshot.map((c: any, idx: number) => ({
      name: c.name,
      type: 'line',
      smooth: true,
      symbolSize: 8,
      lineStyle: { width: 2, color: colors[idx % colors.length] },
      itemStyle: { color: colors[idx % colors.length] },
      data: xLabels.map(x => c.rates[x] ?? null),
    })),
  }

  return (
    <div style={{ height: 'calc(100vh - 64px)', overflowY: 'auto', padding: '0 24px 24px' }}>

      {/* 标题栏 */}
      <div style={{ marginBottom: 20, padding: '20px 0 0', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Title level={3} style={{ margin: 0 }}>曲线经营分析总览</Title>
            <a href="/curv/chat" title="AI曲线助手" style={{ display: 'inline-flex', textDecoration: 'none' }}>
              <CurvMascot size={44} />
            </a>
          </div>
          <Text type="secondary">
            覆盖 {kpi.curve_count || 0} 条曲线 · {kpi.source_count || 0} 个数据源 ·
            {kpi.rate_total?.toLocaleString() || 0} 条利率数据
          </Text>
        </div>
        <Space>
          {kpi.latest_date && <Text type="secondary" style={{ fontSize: 12 }}>最新数据: {kpi.latest_date}</Text>}
          {refreshTime && <Text type="secondary" style={{ fontSize: 12 }}>刷新于 {refreshTime}</Text>}
          <a onClick={loadData}><ReloadOutlined /> 刷新</a>
        </Space>
      </div>

      {/* ── KPI 第一行：核心资产 ── */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        {[
          { icon: <LineChartOutlined />, title: '在管曲线', value: kpi.curve_count, color: '#1677ff', bg: '#e6f4ff' },
          { icon: <DatabaseOutlined />, title: '数据源', value: kpi.source_count, color: '#52c41a', bg: '#f6ffed' },
          { icon: <NodeIndexOutlined />, title: '期限点（最新日）', value: kpi.tenor_count, color: '#fa8c16', bg: '#fff7e6' },
          { icon: <FileTextOutlined />, title: '利率数据总量', value: (kpi.rate_total || 0).toLocaleString(), color: '#722ed1', bg: '#f9f0ff' },
          { icon: <CheckCircleOutlined />, title: '采集成功率（7日）', value: `${successPct}%`, color: '#13c2c2', bg: '#e6fffb' },
          { icon: <StockOutlined />, title: '10Y 国债最新', value: kpi.rate_10y ? `${kpi.rate_10y}%` : '-', color: '#eb2f96', bg: '#fff0f6' },
        ].map(item => (
          <Col xs={12} sm={8} md={4} key={item.title}>
            <Card hoverable size="small" style={{ borderTop: `3px solid ${item.color}`, background: item.bg }}>
              <Statistic title={item.title} value={item.value}
                prefix={React.cloneElement(item.icon, { style: { color: item.color } })}
                valueStyle={{ color: item.color, fontSize: 22 }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── KPI 第二行：建模能力 ── */}
      <Row gutter={[12, 12]} style={{ marginBottom: 24 }}>
        {[
          { icon: <ClusterOutlined />, title: '派生曲线', value: kpi.derived_count, color: '#1677ff' },
          { icon: <ExperimentOutlined />, title: '压力情景', value: kpi.scenario_count, color: '#52c41a' },
          { icon: <CalculatorOutlined />, title: '拟合记录', value: kpi.fit_count, color: '#fa8c16' },
          { icon: <BarChartOutlined />, title: '形状指标', value: kpi.shape_count, color: '#722ed1' },
          { icon: <FundOutlined />, title: '回测报告', value: kpi.backtest_count, color: '#13c2c2' },
          { icon: <MessageOutlined />, title: '智能会话', value: kpi.session_count, color: '#eb2f96' },
        ].map(item => (
          <Col xs={12} sm={8} md={4} key={item.title}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic title={item.title} value={item.value}
                prefix={React.cloneElement(item.icon, { style: { color: item.color } })}
                valueStyle={{ color: item.color, fontSize: 20 }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── 趋势图 ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title={<Space><LineChartOutlined />10Y 国债收益率近30日趋势</Space>}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>cnb_treasury_yield</Text>}>
            <MiniBarChart data={data.trend_10y || []} height={150} color="#1677ff" unit="%" />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={<Space><BarChartOutlined />10Y-1Y 利差近30日趋势</Space>}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>期限利差（bp）</Text>}>
            <MiniBarChart data={data.spread_trend || []} height={150} color="#722ed1" unit="bp" />
          </Card>
        </Col>
      </Row>

      {/* ── 多曲线对比 + 利率排行 ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={14}>
          <Card title={<Space><StockOutlined />关键曲线对比（最新交易日）</Space>}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>国债 / 国开 / AAA企业债</Text>}>
            {snapshot.length > 0 ? (
              <ReactECharts option={snapshotOption} style={{ height: 280 }} />
            ) : <EmptyPlaceholder text="暂无多曲线数据" />}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title={<Space><RiseOutlined />10Y 利率排行</Space>}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>由高到低</Text>}>
            {data.top_rates?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {(data.top_rates || []).map((item: any) => (
                  <div key={item.curve_code} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '6px 12px',
                    background: item.rank % 2 === 1 ? '#fafafa' : '#fff',
                    borderRadius: 6,
                    borderLeft: `3px solid ${item.rank <= 3 ? '#722ed1' : '#d9d9d9'}`,
                  }}>
                    <Space>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                        width: 22, height: 22, borderRadius: '50%',
                        background: ['#f5222d', '#fa8c16', '#faad14', '#8c8c8c', '#8c8c8c'][item.rank - 1] || '#8c8c8c',
                        color: item.rank <= 3 ? '#fff' : '#595959', fontSize: 11, fontWeight: 700,
                      }}>
                        {item.rank}
                      </span>
                      <Text style={{ fontSize: 13 }}>{item.curve_name}</Text>
                    </Space>
                    <Text strong style={{ color: '#722ed1', fontSize: 14 }}>{item.value}%</Text>
                  </div>
                ))}
              </div>
            ) : <EmptyPlaceholder text="暂无排行数据" />}
          </Card>
        </Col>
      </Row>

      {/* ── 分布：曲线分类 + 数据源 + 期限 ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card title={<Space><PieChartOutlined />曲线分类分布</Space>}>
            <HorizontalBar
              data={(data.curve_category_dist || []).map((d: any) => ({
                label: d.label, count: d.count, color: d.color,
              }))}
              height={180} maxLabelLen={6}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title={<Space><ApiOutlined />数据源类型分布</Space>}>
            <HorizontalBar
              data={(data.source_type_dist || []).map((d: any) => ({
                label: d.label, count: d.count, color: d.color,
              }))}
              height={180} maxLabelLen={6}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title={<Space><NodeIndexOutlined />期限点覆盖度（最新日）</Space>}>
            <HorizontalBar
              data={(data.tenor_dist || []).slice(0, 10).map((d: any) => ({
                label: d.label, count: d.count, color: d.color || '#722ed1',
              }))}
              height={180} maxLabelLen={6}
            />
          </Card>
        </Col>
      </Row>

      {/* ── 采集状态 + 最近日志 ── */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={6}>
          <Card title={<Space><ScheduleOutlined />近7日采集状态</Space>}>
            <div style={{ padding: '8px 0' }}>
              <Progress type="dashboard" percent={successPct}
                strokeColor={{ '0%': '#722ed1', '100%': '#52c41a' }}
                size={140} format={() => `${statusDist.success || 0}/${totalRuns}`} />
              <div style={{ textAlign: 'center', marginTop: 8 }}>
                <Space size={4} wrap>
                  <Tag color="success">成功 {statusDist.success || 0}</Tag>
                  <Tag color="error">失败 {statusDist.failed || 0}</Tag>
                  <Tag color="processing">运行 {statusDist.running || 0}</Tag>
                </Space>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={18}>
          <Card title={<Space><DatabaseOutlined />最近采集日志</Space>}>
            <Table dataSource={data.recent_logs || []} rowKey={(_r, i) => `${i}`} pagination={false} size="small"
              locale={{ emptyText: '暂无采集日志' }}
              columns={[
                { title: '交易日', dataIndex: 'trade_date', width: 100, render: (v: string) => v || '-' },
                { title: '任务ID', dataIndex: 'task_id', width: 80 },
                { title: '数据源', dataIndex: 'source_id', width: 80 },
                { title: '记录数', dataIndex: 'record_count', width: 80,
                  render: (v: number) => <Text strong style={{ color: '#1677ff' }}>{v?.toLocaleString() || 0}</Text> },
                { title: '耗时', dataIndex: 'duration_ms', width: 80,
                  render: (v: number) => v ? `${v}ms` : '-' },
                { title: '状态', dataIndex: 'status', width: 90,
                  render: (v: string) => <Tag color={STATUS_COLOR[v] || 'default'}>{STATUS_LABEL[v] || v}</Tag> },
                { title: '开始时间', dataIndex: 'start_time', width: 160,
                  render: (v: string) => v ? v.replace('T', ' ').slice(0, 19) : '-' },
              ]} />
          </Card>
        </Col>
      </Row>

    </div>
  )
}
