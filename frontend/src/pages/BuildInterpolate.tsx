import { useState, useEffect } from 'react'
import { Card, Form, Select, Input, Button, Table, Tag, message } from 'antd'
import { buildApi, curvesApi } from '../api'

export default function BuildInterpolate() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [curveOptions, setCurveOptions] = useState<{value: string, label: string}[]>([])

  // 加载曲线列表
  useEffect(() => {
    const fetchCurves = async () => {
      try {
        const res = await curvesApi.listDefinitions()
        if (res.data?.code === 0 && Array.isArray(res.data.data)) {
          setCurveOptions(res.data.data.map((c: any) => ({
            value: c.code,
            label: c.name || c.code
          })))
        }
      } catch (e) {
        console.error('加载曲线列表失败', e)
      }
    }
    fetchCurves()
  }, [])

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      const res: any = await buildApi.interpolate({
        curve_code: values.curve_code,
        trade_date: values.trade_date,
        target_tenors: values.target_tenors.split(',').map((s: string) => s.trim()),
        method: values.method,
      })
      setResult(res.data)
      message.success('插值完成')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '插值失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>📐 曲线插值</div>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish}
              initialValues={{
                curve_code: 'cnb_treasury_yield', trade_date: '2026-08-17',
                target_tenors: '2Y, 4Y, 8Y, 12Y, 25Y', method: 'pchip',
              }}>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Form.Item name="curve_code" label="曲线" style={{ minWidth: 200 }}>
              <Select options={curveOptions} showSearch allowClear placeholder="选择曲线" />
            </Form.Item>
            <Form.Item name="trade_date" label="日期" style={{ minWidth: 150 }}>
              <Input placeholder="YYYY-MM-DD" />
            </Form.Item>
            <Form.Item name="target_tenors" label="目标期限（逗号分隔）" style={{ minWidth: 350, flex: 1 }}>
              <Input placeholder="如 2Y, 4Y, 8Y" />
            </Form.Item>
            <Form.Item name="method" label="方法" style={{ minWidth: 150 }}>
              <Select options={[
                { value: 'pchip', label: 'PCHIP（推荐）' },
                { value: 'cubic_spline', label: '三次样条' },
                { value: 'linear', label: '线性' },
                { value: 'log_linear', label: '对数线性' },
              ]} />
            </Form.Item>
            <Form.Item label=" "><Button type="primary" loading={loading} htmlType="submit">执行插值</Button></Form.Item>
          </div>
        </Form>
      </Card>

      {result && (
        <Card title="插值结果" style={{ marginTop: 16 }}>
          <Table
            size="small"
            dataSource={result.target_tenors.map((t: string, i: number) => ({
              tenor: t, rate: result.rates[i].toFixed(4),
            }))}
            pagination={false}
            rowKey="tenor"
            columns={[
              { title: '目标期限', dataIndex: 'tenor' },
              { title: '插值利率 (%)', dataIndex: 'rate', render: (v) => <Tag color="purple">{v}%</Tag> },
            ]}
          />
        </Card>
      )}
    </div>
  )
}