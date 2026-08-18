import { useEffect, useState, useMemo } from 'react'
import { Card, Form, Select, DatePicker, Button, Table, Tag, Row, Col, Statistic, message, Space } from 'antd'
import { analysisApi, curvesApi } from '../api'
import ReactECharts from 'echarts-for-react'
import dayjs, { Dayjs } from 'dayjs'

const CATEGORY_LABEL: Record<string, string> = {
  base: '基准', credit: '信用', money_market: '货币', policy: '政策',
  swap: '互换', fx: '外币', derived: '派生',
}
const CATEGORY_COLOR: Record<string, string> = {
  base: '#1677ff', credit: '#fa541c', money_market: '#13c2c2', policy: '#722ed1',
  swap: '#2f54eb', fx: '#eb2f96', derived: '#52c41a',
}

export default function AnalysisSpread() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [snapshot, setSnapshot] = useState<any>(null)   // 单日形态快照
  const [trend, setTrend] = useState<any>(null)         // 趋势时间序列
  const [curves, setCurves] = useState<any[]>([])

  // 加载所有曲线
  useEffect(() => {
    (async () => {
      try {
        const r: any = await curvesApi.listDefinitions()
        const list: any[] = (r?.data || r || []) as any[]
        const active = list.filter((c: any) => c.is_enabled !== 0)
        setCurves(active)
        // 默认选中 中债国债收益率曲线
        const defaultCode = active.find((c: any) => c.code === 'cnb_treasury_yield')?.code
          || active[0]?.code
        form.setFieldValue('curve_code', defaultCode)
      } catch (e) {
        console.error('加载曲线列表失败', e)
      }
    })()
  }, [])

  // 提交查询（同时拿单日快照 + 区间趋势）
  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const range = values.range as [Dayjs, Dayjs]
      const startDate = range[0].format('YYYY-MM-DD')
      const endDate = range[1].format('YYYY-MM-DD')

      // 单日快照：用 endDate
      const snapRes: any = await analysisApi.shapeMetrics({
        curve_code: values.curve_code,
        trade_date: endDate,
      })
      setSnapshot(snapRes.data || snapRes)

      // 区间趋势
      const trendRes: any = await analysisApi.shapeMetricsTrend({
        curve_code: values.curve_code,
        start_date: startDate,
        end_date: endDate,
      })
      setTrend(trendRes.data || trendRes)

      message.success('查询完成')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '查询失败')
    } finally {
      setLoading(false)
    }
  }

  // 曲线选项（按 category 分组）
  const curveOptions = useMemo(() => {
    const groups: Record<string, any[]> = {}
    curves.forEach(c => {
      const cat = c.category || 'base'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push({ value: c.code, label: c.name })
    })
    return Object.keys(groups).sort().map(cat => ({
      label: <span><Tag color={CATEGORY_COLOR[cat]} style={{ marginRight: 4 }}>{CATEGORY_LABEL[cat] || cat}</Tag></span>,
      title: CATEGORY_LABEL[cat] || cat,
      options: groups[cat],
    }))
  }, [curves])

  // 趋势图配置
  const trendOption = trend && trend.dates ? {
    tooltip: { trigger: 'axis' },
    legend: { top: 0, data: ['10Y-1Y 利差', '10Y-5Y 利差', '5Y-1Y 利差', '信用利差 AAA 5Y'] },
    grid: { left: 60, right: 30, top: 40, bottom: 60 },
    xAxis: { type: 'category', data: trend.dates, axisLabel: { fontSize: 9, interval: Math.floor(trend.dates.length / 10) } },
    yAxis: { type: 'value', name: 'bp' },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 20 }],
    series: [
      {
        name: '10Y-1Y 利差', type: 'line', smooth: true, showSymbol: false,
        lineStyle: { width: 2, color: '#1677ff' },
        itemStyle: { color: '#1677ff' },
        data: trend.series.spread_10y_1y,
        markLine: { silent: true, data: [{ yAxis: 0, lineStyle: { type: 'dashed', color: '#bfbfbf' } }] },
      },
      {
        name: '10Y-5Y 利差', type: 'line', smooth: true, showSymbol: false,
        lineStyle: { width: 1.5, color: '#fa8c16' },
        itemStyle: { color: '#fa8c16' },
        data: trend.series.spread_10y_5y,
      },
      {
        name: '5Y-1Y 利差', type: 'line', smooth: true, showSymbol: false,
        lineStyle: { width: 1.5, color: '#52c41a' },
        itemStyle: { color: '#52c41a' },
        data: trend.series.spread_5y_1y,
      },
      {
        name: '信用利差 AAA 5Y', type: 'line', smooth: true, showSymbol: false,
        lineStyle: { width: 1.5, color: '#722ed1', type: 'dashed' },
        itemStyle: { color: '#722ed1' },
        data: trend.series.credit_spread_aaa_5y,
      },
    ],
  } : null

  // 倒挂事件统计
  const inversionStats = useMemo(() => {
    if (!trend?.series?.inversion_flag) return { total: 0, days: 0 }
    const days = trend.series.inversion_flag.filter((x: any) => x === 1).length
    return { total: trend.dates?.length || 0, days }
  }, [trend])

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>📐 利差形态分析</div>
      <Card>
        <Form form={form} layout="inline" onFinish={onFinish}
              initialValues={{
                curve_code: 'cnb_treasury_yield',
                range: [dayjs().subtract(180, 'day'), dayjs()],
              }}>
          <Form.Item name="curve_code" label="曲线" style={{ minWidth: 280 }}>
            <Select
              placeholder="选择曲线（按分类分组）"
              showSearch
              optionFilterProp="label"
              options={curveOptions as any}
              filterOption={(input, option: any) => {
                const label = option?.label?.props?.children?.[1] || option?.label || ''
                return String(label).toLowerCase().includes(input.toLowerCase())
              }}
            />
          </Form.Item>
          <Form.Item name="range" label="日期范围">
            <DatePicker.RangePicker />
          </Form.Item>
          <Form.Item>
            <Button type="primary" loading={loading} htmlType="submit">查询</Button>
          </Form.Item>
          <Form.Item>
            <span style={{ color: '#8c8c8c', fontSize: 12 }}>
              共 {curves.length} 条曲线可选
            </span>
          </Form.Item>
        </Form>
      </Card>

      {/* 单日形态快照 */}
      {snapshot && snapshot.metrics && (
        <Card style={{ marginTop: 16 }} title={`形态指标快照 · ${snapshot.trade_date}`}>
          <Row gutter={16}>
            <Col span={6}><Card size="small"><Statistic title="10Y-1Y 利差" value={snapshot.metrics.spread_10y_1y ?? '-'} suffix="bp"
              valueStyle={{ color: '#1677ff' }} /></Card></Col>
            <Col span={6}><Card size="small"><Statistic title="10Y-5Y 利差" value={snapshot.metrics.spread_10y_5y ?? '-'} suffix="bp"
              valueStyle={{ color: '#fa8c16' }} /></Card></Col>
            <Col span={6}><Card size="small"><Statistic title="5Y-1Y 利差" value={snapshot.metrics.spread_5y_1y ?? '-'} suffix="bp"
              valueStyle={{ color: '#52c41a' }} /></Card></Col>
            <Col span={6}><Card size="small"><Statistic title="倒挂"
              value={snapshot.metrics.inversion ? '是 ⚠️' : '否 ✓'}
              valueStyle={{ color: snapshot.metrics.inversion ? '#ff4d4f' : '#52c41a' }} /></Card></Col>
          </Row>
          {snapshot.metrics.credit_spread_aaa_5y_bp !== undefined && (
            <Card size="small" style={{ marginTop: 12, background: '#f9f0ff' }}>
              <Statistic title="信用利差 AAA（5Y）" value={snapshot.metrics.credit_spread_aaa_5y_bp} suffix="bp"
                valueStyle={{ color: '#722ed1' }} />
            </Card>
          )}
        </Card>
      )}

      {/* 趋势图 */}
      {trend && trend.dates && trend.dates.length > 0 && (
        <>
          <Card style={{ marginTop: 16 }} title="利差形态趋势"
            extra={<Space>
              <span style={{ color: '#8c8c8c', fontSize: 12 }}>
                区间 {trend.start_date} ~ {trend.end_date}
              </span>
              <Tag color={inversionStats.days > 0 ? 'red' : 'green'}>
                倒挂天数: {inversionStats.days} / {inversionStats.total}
              </Tag>
            </Space>}>
            <ReactECharts option={trendOption!} style={{ height: 420 }} />
          </Card>

          {/* 关键指标汇总 */}
          <Card style={{ marginTop: 16 }} title="区间汇总统计">
            <Row gutter={16}>
              {[
                { name: '10Y-1Y 利差', key: 'spread_10y_1y', color: '#1677ff' },
                { name: '10Y-5Y 利差', key: 'spread_10y_5y', color: '#fa8c16' },
                { name: '5Y-1Y 利差', key: 'spread_5y_1y', color: '#52c41a' },
                { name: '信用利差 AAA 5Y', key: 'credit_spread_aaa_5y', color: '#722ed1' },
              ].map(s => {
                const arr = (trend.series[s.key] || []).filter((x: any) => x !== null) as number[]
                if (arr.length === 0) {
                  return (
                    <Col span={6} key={s.key}>
                      <Card size="small">
                        <Statistic title={s.name} value="-" />
                      </Card>
                    </Col>
                  )
                }
                const avg = arr.reduce((a, b) => a + b, 0) / arr.length
                const mx = Math.max(...arr)
                const mn = Math.min(...arr)
                return (
                  <Col span={6} key={s.key}>
                    <Card size="small">
                      <Statistic title={s.name} value={avg.toFixed(2)} suffix="bp"
                        valueStyle={{ color: s.color }}
                        prefix={<span style={{ fontSize: 12, color: '#8c8c8c' }}>均值</span>} />
                      <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 4 }}>
                        最大 {mx.toFixed(2)} · 最小 {mn.toFixed(2)} · {arr.length} 个交易日
                      </div>
                    </Card>
                  </Col>
                )
              })}
            </Row>
          </Card>
        </>
      )}
    </div>
  )
}