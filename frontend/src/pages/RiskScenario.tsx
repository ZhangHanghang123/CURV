import { useEffect, useState } from 'react'
import { Card, Form, Select, InputNumber, Button, Table, Tag, Row, Col, Statistic, message } from 'antd'
import { scenarioApi } from '../api'
import ReactECharts from 'echarts-for-react'

export default function RiskScenario() {
  const [scenarios, setScenarios] = useState<any[]>([])
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    scenarioApi.list().then((res: any) => {
      setScenarios(res.data)
      const s = res.data.find((x: any) => x.scenario_type === 'parallel' && x.shock_json.shock_bp === 100)
      if (s) form.setFieldsValue({ scenario_id: s.id, portfolio_value: 10000, duration: 5 })
    })
  }, [])

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const res: any = await scenarioApi.run({
        scenario_id: values.scenario_id,
        curve_code: 'cnb_treasury_yield',
        trade_date: '2026-08-17',
        portfolio_value: values.portfolio_value,
        duration: values.duration,
      })
      setData(res.data)
      message.success(`情景 ${res.data.scenario_name} 计算完成`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '计算失败')
    } finally {
      setLoading(false)
    }
  }

  const option = data?.shocked_curve ? {
    tooltip: { trigger: 'axis' },
    legend: { top: 0, data: ['原曲线', '冲击后'] },
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: Object.keys(data.shocked_curve) },
    yAxis: { type: 'value', name: '%' },
    series: [
      {
        name: '原曲线', data: [2.45, 1.85, 2.15, 2.45, 2.78, 1.45, 1.58, 1.65, 1.77, 1.95, 2.32, 2.62, 2.72].slice(0, Object.keys(data.shocked_curve).length),
        type: 'line', smooth: true, itemStyle: { color: '#1677ff' },
      },
      {
        name: '冲击后', data: Object.values(data.shocked_curve), type: 'line', smooth: true,
        itemStyle: { color: '#ff4d4f' },
      },
    ],
  } : null

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>🌪️ 情景模拟</div>
      <Card>
        <Form form={form} layout="inline" onFinish={onFinish}>
          <Form.Item name="scenario_id" label="情景">
            <Select style={{ width: 200 }} options={scenarios.map(s => ({ value: s.id, label: s.name }))} />
          </Form.Item>
          <Form.Item name="portfolio_value" label="组合（万）">
            <InputNumber style={{ width: 120 }} min={1} />
          </Form.Item>
          <Form.Item name="duration" label="久期（年）">
            <InputNumber style={{ width: 100 }} min={0.1} max={30} step={0.5} />
          </Form.Item>
          <Form.Item><Button type="primary" loading={loading} htmlType="submit">运行情景</Button></Form.Item>
        </Form>
      </Card>

      {data && (
        <>
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={6}><Card><Statistic title="组合原值" value={data.base_value} suffix="万" /></Card></Col>
            <Col span={6}><Card><Statistic title="PV 变化" value={data.pv_change} suffix="万" precision={2}
              valueStyle={{ color: data.pv_change < 0 ? '#ff4d4f' : '#52c41a' }} /></Card></Col>
            <Col span={6}><Card><Statistic title="NII 变化" value={data.nii_change} suffix="万" precision={2} /></Card></Col>
            <Col span={6}><Card><Statistic title="EVE 变化" value={data.eve_change} suffix="万" precision={2}
              valueStyle={{ color: data.eve_change < 0 ? '#ff4d4f' : '#52c41a' }} /></Card></Col>
          </Row>
          {option && (
            <Card title="冲击后曲线" style={{ marginTop: 16 }}>
              <ReactECharts option={option} style={{ height: 320 }} />
            </Card>
          )}
        </>
      )}
    </div>
  )
}