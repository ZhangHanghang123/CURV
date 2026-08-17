import { useState } from 'react'
import { Card, Form, Select, Input, InputNumber, Button, Table, Tag, Row, Col, Statistic, message } from 'antd'
import { analysisApi } from '../api'
import ReactECharts from 'echarts-for-react'

export default function RiskKRD() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const res: any = await analysisApi.krd({
        curve_code: values.curve_code,
        portfolio_value: values.portfolio_value,
      })
      setData(res.data)
      message.success('KRD 计算完成')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '计算失败')
    } finally {
      setLoading(false)
    }
  }

  const option = data ? {
    tooltip: {},
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: Object.keys(data.krd_vector || {}) },
    yAxis: { type: 'value', name: 'KRD (年)' },
    series: [{
      name: 'KRD', data: Object.values(data.krd_vector || {}), type: 'bar',
      itemStyle: { color: '#722ed1' },
    }],
  } : null

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>🎯 关键利率久期（KRD）</div>
      <Card>
        <Form form={form} layout="inline" onFinish={onFinish}
              initialValues={{ curve_code: 'cnb_treasury_yield', portfolio_value: 10000 }}>
          <Form.Item name="curve_code" label="曲线">
            <Select style={{ width: 180 }} options={[
              { value: 'cnb_treasury_yield', label: '中债国债' },
              { value: 'cnb_policy_fin', label: '国开债' },
            ]} />
          </Form.Item>
          <Form.Item name="portfolio_value" label="组合价值（万）">
            <InputNumber style={{ width: 150 }} min={1} />
          </Form.Item>
          <Form.Item><Button type="primary" loading={loading} htmlType="submit">计算 KRD</Button></Form.Item>
        </Form>
      </Card>

      {data && (
        <>
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={8}><Card><Statistic title="总 DV01（1bp 冲击）" value={data.total_dv01} suffix="元"
              valueStyle={{ color: '#722ed1' }} /></Card></Col>
            <Col span={16}>
              <Card title="KRD 向量分布">
                <ReactECharts option={option!} style={{ height: 280 }} />
              </Card>
            </Col>
          </Row>
          <Card style={{ marginTop: 16 }} title="明细">
            <Table
              size="small"
              dataSource={Object.entries(data.krd_vector || {}).map(([t, k]) => ({
                tenor: t, krd: k, pv01: data.pv01_vector?.[t],
              }))}
              pagination={false}
              rowKey="tenor"
              columns={[
                { title: '关键期限', dataIndex: 'tenor' },
                { title: 'KRD（年）', dataIndex: 'krd', render: (v) => v ? <Tag color="purple">{v}</Tag> : '-' },
                { title: 'PV01（元）', dataIndex: 'pv01', render: (v) => v ? v.toFixed(2) : '-' },
              ]}
            />
          </Card>
        </>
      )}
    </div>
  )
}