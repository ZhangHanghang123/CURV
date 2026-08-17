import { useState } from 'react'
import { Card, Form, Select, Input, Button, Table, Tag, Statistic, Row, Col, message } from 'antd'
import { buildApi } from '../api'

export default function BuildFit() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const res: any = await buildApi.fit({
        curve_code: values.curve_code,
        trade_date: values.trade_date,
        model: values.model,
      })
      setResult(res.data)
      message.success(`拟合完成 RMSE=${res.data.rmse_bp}bp`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '拟合失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>⚙️ 曲线拟合（NS / NSS）</div>
      <Card>
        <Form form={form} layout="inline" onFinish={onFinish}
              initialValues={{ curve_code: 'cnb_treasury_yield', trade_date: '2026-08-17', model: 'nelson_siegel' }}>
          <Form.Item name="curve_code" label="曲线">
            <Select style={{ width: 200 }} options={[
              { value: 'cnb_treasury_yield', label: '中债国债' },
              { value: 'cnb_policy_fin', label: '国开债' },
              { value: 'cnb_corp_aaa', label: '企业债 AAA' },
              { value: 'shibor_curve', label: 'Shibor' },
            ]} />
          </Form.Item>
          <Form.Item name="trade_date" label="日期">
            <Input placeholder="YYYY-MM-DD" style={{ width: 150 }} />
          </Form.Item>
          <Form.Item name="model" label="模型">
            <Select style={{ width: 180 }} options={[
              { value: 'nelson_siegel', label: 'Nelson-Siegel' },
              { value: 'svensson', label: 'Svensson (NSS)' },
            ]} />
          </Form.Item>
          <Form.Item><Button type="primary" loading={loading} htmlType="submit">执行拟合</Button></Form.Item>
        </Form>
      </Card>

      {result && (
        <>
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={6}><Card><Statistic title="RMSE" value={result.rmse_bp} suffix="bp"
              valueStyle={{ color: result.rmse_bp <= 2 ? '#52c41a' : '#ff4d4f' }} /></Card></Col>
            <Col span={6}><Card><Statistic title="R²" value={result.r2} precision={4} /></Card></Col>
            <Col span={6}><Card><Statistic title="β₀ (水平)" value={result.params.beta0} precision={4} /></Card></Col>
            <Col span={6}><Card><Statistic title="β₁ (斜率)" value={result.params.beta1} precision={4}
              valueStyle={{ color: result.params.beta1 < 0 ? '#722ed1' : '#1677ff' }} /></Card></Col>
          </Row>
          <Card title="拟合参数详情" style={{ marginTop: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <h4>参数</h4>
                <Table
                  size="small"
                  dataSource={Object.entries(result.params).map(([k, v]) => ({ k, v }))}
                  pagination={false}
                  columns={[
                    { title: '参数', dataIndex: 'k' },
                    { title: '值', dataIndex: 'v', render: (v: any) => typeof v === 'number' ? v.toFixed(4) : v },
                  ]}
                />
              </Col>
              <Col span={12}>
                <h4>残差</h4>
                <Table
                  size="small"
                  dataSource={result.tenors.map((t: string, i: number) => ({
                    tenor: t, fitted: result.fitted[i].toFixed(4), residual_bp: result.residuals_bp[i],
                  }))}
                  pagination={false}
                  rowKey="tenor"
                  columns={[
                    { title: '期限', dataIndex: 'tenor' },
                    { title: '拟合值', dataIndex: 'fitted' },
                    { title: '残差(bp)', dataIndex: 'residual_bp', render: (v) => (
                      <Tag color={Math.abs(v) <= 5 ? 'green' : Math.abs(v) <= 10 ? 'orange' : 'red'}>{v}</Tag>
                    )},
                  ]}
                />
              </Col>
            </Row>
          </Card>
        </>
      )}
    </div>
  )
}