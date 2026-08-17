import { Card, Table, Button, message, Tag } from 'antd'

export default function AppRegulatory() {
  const reports = [
    { code: 'IRRBB_2026Q2', name: 'IRRBB 标准化报表（6 情景）', freq: '季度', last: '2026-06-30', format: 'Excel' },
    { code: 'G33_2026Q2', name: '利率风险计量表（G33）', freq: '季度', last: '2026-06-30', format: 'Excel' },
    { code: 'STRESS_2026Q2', name: '压力测试报告', freq: '季度', last: '2026-06-30', format: 'PDF' },
    { code: 'DAILY_20260817', name: '收益率曲线日报', freq: '日', last: '2026-08-17', format: 'Excel' },
  ]

  const irrbbResults = [
    { scenario: '平行 +200bp', delta_eve: '-15,200', eve_pct: '-15.2%', delta_nii: '+8,500', nii_pct: '+8.5%', status: 'warning' },
    { scenario: '平行 -200bp', delta_eve: '+12,800', eve_pct: '+12.8%', delta_nii: '-6,200', nii_pct: '-6.2%', status: 'success' },
    { scenario: '陡峭化', delta_eve: '-8,500', eve_pct: '-8.5%', delta_nii: '+3,200', nii_pct: '+3.2%', status: 'success' },
    { scenario: '平坦化', delta_eve: '-7,200', eve_pct: '-7.2%', delta_nii: '+2,800', nii_pct: '+2.8%', status: 'success' },
    { scenario: '短端利率 ↑', delta_eve: '-5,800', eve_pct: '-5.8%', delta_nii: '+1,500', nii_pct: '+1.5%', status: 'success' },
    { scenario: '短端利率 ↓', delta_eve: '+4,200', eve_pct: '+4.2%', delta_nii: '-1,800', nii_pct: '-1.8%', status: 'success' },
  ]

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>📤 监管报送</div>

      <Card title="监管报表" extra={
        <Button type="primary" onClick={() => message.success('已生成全部报表（演示）')}>📤 一键生成本期报表</Button>
      }>
        <Table
          rowKey="code"
          dataSource={reports}
          pagination={false}
          columns={[
            { title: '报表编码', dataIndex: 'code', render: (v) => <code>{v}</code> },
            { title: '报表名称', dataIndex: 'name' },
            { title: '频度', dataIndex: 'freq', render: (v) => <Tag color="purple">{v}</Tag> },
            { title: '最近生成', dataIndex: 'last' },
            { title: '格式', dataIndex: 'format', render: (v) => <Tag color="blue">{v}</Tag> },
            { title: '操作', render: () => <Button type="primary" size="small">下载</Button> },
          ]}
        />
      </Card>

      <Card title="IRRBB 监管 6 情景结果" style={{ marginTop: 16 }}>
        <Table
          rowKey="scenario"
          dataSource={irrbbResults}
          pagination={false}
          columns={[
            { title: '情景', dataIndex: 'scenario' },
            { title: 'ΔEVE（万元）', dataIndex: 'delta_eve' },
            { title: 'ΔEVE/EVE', dataIndex: 'eve_pct' },
            { title: 'ΔNII（万元）', dataIndex: 'delta_nii' },
            { title: 'ΔNII/NII', dataIndex: 'nii_pct' },
            { title: '监管阈值 ±15%', render: (_, r) => (
              <Tag color={r.status === 'success' ? 'green' : 'orange'}>
                {r.status === 'success' ? '✓ 达标' : '⚠ 预警'}
              </Tag>
            )},
          ]}
        />
      </Card>
    </div>
  )
}