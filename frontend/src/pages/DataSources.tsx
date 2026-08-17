import { useEffect, useState } from 'react'
import { Card, Table, Tag } from 'antd'
import { curvesApi } from '../api'

export default function DataSources() {
  const [data, setData] = useState<any[]>([])

  useEffect(() => {
    curvesApi.getDataSources().then((res: any) => setData(res.data))
  }, [])

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>🔌 数据源配置</div>
      <Card>
        <Table
          rowKey="code"
          dataSource={data}
          pagination={{ pageSize: 20 }}
          columns={[
            { title: '编码', dataIndex: 'code', width: 220, render: (v) => <code>{v}</code> },
            { title: '名称', dataIndex: 'name', width: 220 },
            { title: '类型', dataIndex: 'source_type', width: 100, render: (v) => <Tag color="blue">{v}</Tag> },
            { title: '提供方', dataIndex: 'provider', width: 120 },
            { title: '频率', dataIndex: 'frequency', width: 100 },
            { title: 'Cron', dataIndex: 'cron_expr', width: 130 },
            { title: '最近采集', dataIndex: 'last_run_time', width: 180 },
            { title: '状态', dataIndex: 'last_run_status', width: 100, render: (v) => (
              <Tag color={v === 'success' ? 'green' : v === 'failed' ? 'red' : 'orange'}>{v || '-'}</Tag>
            )},
          ]}
        />
      </Card>
    </div>
  )
}