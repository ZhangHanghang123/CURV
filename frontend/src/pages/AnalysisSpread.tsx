import { useState } from 'react'
import { Card, Form, Select, Input, Button, Table, Tag, Row, Col, Statistic, message } from 'antd'
import { analysisApi } from '../api'

export default function AnalysisSpread() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const res: any = await analysisApi.shapeMetrics({
        curve_code: values.curve_code,
        trade_date: values.trade_date,
      })
      setData(res.data)
      message.success('查询完成')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '查询失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>📐 形态指标</div>
      <Card>
        <Form form={form} layout="inline" onFinish={onFinish}
              initialValues={{ curve_code: 'cnb_treasury_yield', trade_date: '2026-08-17' }}>
          <Form.Item name="curve_code" label="曲线">
            <Select style={{ width: 180 }} options={[
              { value: 'cnb_treasury_yield', label: '中债国债' },
              { value: 'cnb_policy_fin', label: '国开债' },
            ]} />
          </Form.Item>
          <Form.Item name="trade_date" label="日期"><Input style={{ width: 150 }} /></Form.Item>
          <Form.Item><Button type="primary" loading={loading} htmlType="submit">查询</Button></Form.Item>
        </Form>
      </Card>

      {data && (
        <Card style={{ marginTop: 16 }} title="形态指标结果">
          <Row gutter={16}>
            <Col span={6}><Card><Statistic title="10Y-1Y 利差" value={data.metrics.spread_10y_1y || '-'} suffix="bp"
              valueStyle={{ color: '#1677ff' }} /></Card></Col>
            <Col span={6}><Card><Statistic title="10Y-5Y 利差" value={data.metrics.spread_10y_5y || '-'} suffix="bp" /></Card></Col>
            <Col span={6}><Card><Statistic title="5Y-1Y 利差" value={data.metrics.spread_5y_1y || '-'} suffix="bp" /></Card></Col>
            <Col span={6}><Card><Statistic title="倒挂" value={data.metrics.inversion ? '是 ⚠️' : '否 ✓'}
              valueStyle={{ color: data.metrics.inversion ? '#ff4d4f' : '#52c41a' }} /></Card></Col>
          </Row>
          {data.metrics.credit_spread_aaa_5y_bp !== undefined && (
            <Card size="small" style={{ marginTop: 16, background: '#f9f0ff' }}>
              <Statistic title="信用利差 AAA（5Y）" value={data.metrics.credit_spread_aaa_5y_bp} suffix="bp"
                valueStyle={{ color: '#722ed1' }} />
            </Card>
          )}
        </Card>
      )}
    </div>
  )
}