import { useEffect, useState, useMemo } from 'react'
import { Card, Form, Select, InputNumber, Button, Statistic, Row, Col, message, Tag } from 'antd'
import { analysisApi, curvesApi } from '../api'
import ReactECharts from 'echarts-for-react'

const CATEGORY_LABEL: Record<string, string> = {
  base: '基准', credit: '信用', money_market: '货币', policy: '政策',
  swap: '互换', fx: '外币', derived: '派生',
}
const CATEGORY_COLOR: Record<string, string> = {
  base: '#1677ff', credit: '#fa541c', money_market: '#13c2c2', policy: '#722ed1',
  swap: '#2f54eb', fx: '#eb2f96', derived: '#52c41a',
}

export default function AnalysisTrend() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)
  const [curves, setCurves] = useState<any[]>([])
  const [curveTenors, setCurveTenors] = useState<string[]>([])

  // 加载所有曲线
  useEffect(() => {
    (async () => {
      try {
        const r: any = await curvesApi.listDefinitions()
        const list: any[] = (r?.data || r || []) as any[]
        const active = list.filter((c: any) => c.is_enabled !== 0)
        setCurves(active)
        if (active.length) {
          // 默认选中 中债国债收益率曲线，不存在则取第一条
          const defaultCode = active.find((c: any) => c.code === 'cnb_treasury_yield')?.code
            || active[0].code
          form.setFieldValue('curve_code', defaultCode)
          await onCurveChange(defaultCode)
        }
      } catch (e) {
        console.error('加载曲线列表失败', e)
      }
    })()
  }, [])

  // 切换曲线时加载该曲线的期限集
  const onCurveChange = async (code: string) => {
    try {
      const r: any = await curvesApi.getDefinition(code)
      const def = r?.data || r
      // tenor_set 可能是 JSON 字符串，需要 parse
      let rawTenors = def?.tenor_set
      if (typeof rawTenors === 'string') {
        try { rawTenors = JSON.parse(rawTenors) } catch { rawTenors = [] }
      }
      const tenors: string[] = Array.isArray(rawTenors) ? rawTenors : []
      const sorted = [...tenors].sort((a: string, b: string) => {
        const days = (s: string) => {
          const n = parseFloat(s)
          if (s.endsWith('Y')) return n * 365
          if (s.endsWith('M')) return n * 30
          if (s.endsWith('W')) return n * 7
          if (s.endsWith('D')) return n
          return n
        }
        return days(a) - days(b)
      })
      setCurveTenors(sorted)
      const defaultTenor = sorted.includes('10Y') ? '10Y' : sorted[sorted.length - 1] || ''
      form.setFieldsValue({ tenor: defaultTenor })
    } catch (e) {
      console.error('加载期限集失败', e)
      setCurveTenors([])
    }
  }

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const res: any = await analysisApi.trend({
        curve_code: values.curve_code,
        tenor: values.tenor,
        days: values.days,
      })
      setData(res.data)
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

  const option = data ? {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 20, bottom: 60 },
    xAxis: { type: 'category', data: data.dates, axisLabel: { fontSize: 9, interval: Math.floor(data.dates.length / 10) } },
    yAxis: { type: 'value', name: '%' },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 20 }],
    series: [{
      name: data.tenor, data: data.rates, type: 'line', smooth: true, showSymbol: false,
      lineStyle: { width: 1.5 }, itemStyle: { color: '#722ed1' }, areaStyle: { opacity: 0.1 },
    }],
  } : null

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>📈 时序走势分析</div>
      <Card>
        <Form form={form} layout="inline" onFinish={onFinish}
              initialValues={{ days: 365 }}>
          <Form.Item name="curve_code" label="曲线">
            <Select
              style={{ width: 280 }}
              placeholder="选择曲线（按分类分组）"
              showSearch
              optionFilterProp="label"
              options={curveOptions as any}
              onChange={(v) => onCurveChange(v as string)}
              filterOption={(input, option: any) => {
                const label = option?.label?.props?.children?.[1] || option?.label || ''
                return String(label).toLowerCase().includes(input.toLowerCase())
              }}
            />
          </Form.Item>
          <Form.Item name="tenor" label="期限">
            <Select
              style={{ width: 120 }}
              placeholder="选择期限"
              options={curveTenors.map(t => ({ value: t, label: t }))}
            />
          </Form.Item>
          <Form.Item name="days" label="天数">
            <InputNumber min={30} max={2000} style={{ width: 100 }} />
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

      {data && (
        <>
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={5}><Card><Statistic title="均值" value={(data.stats?.mean || 0).toFixed(3)} suffix="%" /></Card></Col>
            <Col span={5}><Card><Statistic title="最大值" value={(data.stats?.max || 0).toFixed(3)} suffix="%" valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
            <Col span={5}><Card><Statistic title="最小值" value={(data.stats?.min || 0).toFixed(3)} suffix="%" valueStyle={{ color: '#52c41a' }} /></Card></Col>
            <Col span={5}><Card><Statistic title="年化波动率" value={((data.stats?.annual_volatility || 0) * 100).toFixed(2)} suffix="%" /></Card></Col>
            <Col span={4}><Card><Statistic title="样本数" value={data.stats?.count || 0} /></Card></Col>
          </Row>
          <Card style={{ marginTop: 16 }} title="时序图">
            <ReactECharts option={option!} style={{ height: 400 }} />
          </Card>
        </>
      )}
    </div>
  )
}