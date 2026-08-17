import { Card, Table, Tag, Button, message } from 'antd'

export default function AppFTP() {
  const data = [
    { tenor: '活期', base: 1.45, deposit: 0, depositFTP: 1.45, loan: null, loanFTP: null, bill: null, billFTP: null },
    { tenor: '3M', base: 1.58, deposit: 5, depositFTP: 1.63, loan: 80, loanFTP: 2.38, bill: 15, billFTP: 1.73 },
    { tenor: '1Y', base: 1.77, deposit: 10, depositFTP: 1.87, loan: 95, loanFTP: 2.72, bill: 25, billFTP: 2.02 },
    { tenor: '3Y', base: 2.05, deposit: 15, depositFTP: 2.20, loan: 120, loanFTP: 3.25, bill: 40, billFTP: 2.45 },
    { tenor: '5Y', base: 2.15, deposit: 20, depositFTP: 2.35, loan: 135, loanFTP: 3.50, bill: 45, billFTP: 2.60 },
  ]

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>💰 FTP 定价</div>
      <Card title="FTP 定价表（基于 2026-08-17 中债国债曲线）" extra={
        <Button type="primary" onClick={() => message.success('已发布到 FTP 系统（演示）')}>📤 发布到 FTP 系统</Button>
      }>
        <Table
          rowKey="tenor"
          dataSource={data}
          pagination={false}
          columns={[
            { title: '期限', dataIndex: 'tenor', width: 80 },
            { title: '基准曲线', dataIndex: 'base', width: 100, render: (v) => `${v}%` },
            { title: '存款加点(bp)', dataIndex: 'deposit', width: 120 },
            { title: '存款 FTP', dataIndex: 'depositFTP', width: 120, render: (v) => <b style={{ color: '#1677ff' }}>{v}%</b> },
            { title: '贷款加点(bp)', dataIndex: 'loan', width: 120 },
            { title: '贷款 FTP', dataIndex: 'loanFTP', width: 120, render: (v) => v ? <b style={{ color: '#ff4d4f' }}>{v}%</b> : '-' },
            { title: '票据加点(bp)', dataIndex: 'bill', width: 120 },
            { title: '票据 FTP', dataIndex: 'billFTP', width: 120, render: (v) => v ? <b style={{ color: '#fa8c16' }}>{v}%</b> : '-' },
          ]}
        />
      </Card>
    </div>
  )
}