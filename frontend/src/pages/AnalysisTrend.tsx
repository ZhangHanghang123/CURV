import { useState } from 'react'
import { Card, Form, Select, InputNumber, Button, Statistic, Row, Col, message } from 'antd'
import { analysisApi } from '../api'
import ReactECharts from 'echarts-for-react'

export default function AnalysisTrend() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)

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
              initialValues={{ curve_code: 'cnb_treasury_yield', tenor: '10Y', days: 365 }}>
          <Form.Item name="curve_code" label="曲线">
            <Select style={{ width: 180 }} options={[
              { value: 'cnb_treasury_yield', label: '中债国债' },
              { value: 'cnb_policy_fin', label: '国开债' },
              { value: 'shibor_curve', label: 'Shibor' },
            ]} />
          </Form.Item>
          <Form.Item name="tenor" label="期限">
            <Select style={{ width: 120 }} options={[
              { value: '1Y', label: '1Y' }, { value: '3Y', label: '3Y' },
              { value: '5Y', label: '5Y' }, { value: '10Y', label: '10Y' }, { value: '30Y', label: '30Y' },
            ]} />
          </Form.Item>
          <Form.Item name="days" label="天数">
            <InputNumber min={30} max={2000} style={{ width: 100 }} />
          </Form.Item>
          <Form.Item><Button type="primary" loading={loading} htmlType="submit">查询</Button></Form.Item>
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