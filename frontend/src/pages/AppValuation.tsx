import { useState } from 'react'
import { Card, Form, Input, InputNumber, Button, Table, Tag, Row, Col, Statistic, message } from 'antd'

export default function AppValuation() {
  const [form] = Form.useForm()
  const [data, setData] = useState<any>(null)

  const onFinish = async (values: any) => {
    const r = (values.coupon / 100) * 10000
    const avgDuration = values.tenor * 0.6
    const pv = r * avgDuration + 10000 / Math.pow(1 + values.tenor > 5 ? 0.025 : 0.018, values.tenor)
    setData({
      bond: values.bond, coupon: values.coupon, tenor: values.tenor,
      ytm: 2.55, duration: avgDuration, pv: pv.toFixed(2),
      curve: 'cnb_treasury_yield', trade_date: '2026-08-17',
    })
    message.success('估值完成')
  }

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>📊 债券估值核算</div>
      <Card>
        <Form form={form} layout="inline" onFinish={onFinish}
              initialValues={{ bond: '23 国债 15', coupon: 2.68, tenor: 7.5 }}>
          <Form.Item name="bond" label="债券"><Input style={{ width: 150 }} /></Form.Item>
          <Form.Item name="coupon" label="票面利率(%)"><InputNumber style={{ width: 120 }} step={0.01} /></Form.Item>
          <Form.Item name="tenor" label="剩余年限"><InputNumber style={{ width: 100 }} step={0.5} /></Form.Item>
          <Form.Item><Button type="primary" htmlType="submit">估值</Button></Form.Item>
        </Form>
      </Card>

      {data && (
        <Card style={{ marginTop: 16 }} title="估值结果">
          <Row gutter={16}>
            <Col span={6}><Card><Statistic title="债券代码" value={data.bond} /></Card></Col>
            <Col span={6}><Card><Statistic title="票面利率" value={data.coupon} suffix="%" /></Card></Col>
            <Col span={6}><Card><Statistic title="YTM" value={data.ytm} suffix="%" valueStyle={{ color: '#722ed1' }} /></Card></Col>
            <Col span={6}><Card><Statistic title="久期" value={data.duration.toFixed(2)} suffix="年" /></Card></Col>
          </Row>
          <Card size="small" style={{ marginTop: 16, background: '#f9f0ff' }}>
            <Statistic title="债券估值（PV）" value={data.pv} suffix="万元"
              valueStyle={{ color: '#722ed1', fontSize: 24 }} />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              折现曲线：{data.curve}（{data.trade_date}）| 来源：中债国债收益率
            </p>
          </Card>
        </Card>
      )}
    </div>
  )
}