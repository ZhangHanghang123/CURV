import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag } from 'antd'
import { dashboardApi, ratesApi } from '../api'
import ReactECharts from 'echarts-for-react'

export default function Dashboard() {
  const [kpi, setKpi] = useState<any>({})
  const [curve, setCurve] = useState<any>({ tenors: [], rates: [] })

  useEffect(() => {
    dashboardApi.getOverview().then((res: any) => setKpi(res.data.kpi || {}))
    ratesApi.getCurve('cnb_treasury_yield', '2026-08-17').then((res: any) => setCurve(res.data))
  }, [])

  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: curve.tenors || [] },
    yAxis: { type: 'value', name: '%' },
    series: [{
      name: '中债国债',
      data: curve.rates || [],
      type: 'line',
      smooth: true,
      lineStyle: { width: 2 },
      itemStyle: { color: '#722ed1' },
      areaStyle: { opacity: 0.15 },
    }],
  }

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>📈 总览看板</div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}><Card><Statistic title="曲线总数" value={kpi.curve_count || 0} /></Card></Col>
        <Col span={4}><Card><Statistic title="数据源" value={kpi.source_count || 0} /></Card></Col>
        <Col span={4}><Card><Statistic title="期限点" value={kpi.tenor_count || 0} /></Card></Col>
        <Col span={4}><Card><Statistic title="情景" value={kpi.scenario_count || 0} /></Card></Col>
        <Col span={4}><Card><Statistic title="采集成功率" value={kpi.success_rate || 0} suffix="%" /></Card></Col>
        <Col span={4}><Card><Statistic title="10Y 国债" value={kpi.rate_10y || '-'} suffix="%" valueStyle={{ color: '#722ed1' }} /></Card></Col>
      </Row>
      <Row gutter={16}>
        <Col span={16}>
          <Card title="核心曲线快照（2026-08-17 中债国债）">
            <ReactECharts option={option} style={{ height: 360 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="关键指标">
            <p>10Y-1Y 利差: <b style={{ color: '#1677ff' }}>{kpi.spread_10y_1y_bp || '-'} bp</b></p>
            <p>最新交易日: <b>{kpi.rate_10y_date || '-'}</b></p>
            <p>最新曲线: <b>{kpi.latest_date || '-'}</b></p>
          </Card>
        </Col>
      </Row>
    </div>
  )
}