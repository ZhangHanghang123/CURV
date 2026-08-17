import { useEffect, useMemo, useState } from 'react'
import {
  Card, Table, Button, Modal, Form, Input, Select, InputNumber, Space, message, Popconfirm, Tag,
  Row, Col, Statistic, Tooltip, Empty, Alert,
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, EditOutlined, ReloadOutlined, SearchOutlined,
  BookOutlined, TagsOutlined, CheckCircleOutlined, StopOutlined,
} from '@ant-design/icons'
import { dictApi } from '../api'

export default function DictManagement() {
  const [types, setTypes] = useState<any[]>([])
  const [activeTypeId, setActiveTypeId] = useState<number | null>(null)
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [typeKeyword, setTypeKeyword] = useState('')
  const [dataKeyword, setDataKeyword] = useState('')

  // 类型 Modal
  const [typeModalOpen, setTypeModalOpen] = useState(false)
  const [typeEditing, setTypeEditing] = useState<any>(null)
  const [typeForm] = Form.useForm()

  // 码值 Modal
  const [dataModalOpen, setDataModalOpen] = useState(false)
  const [dataEditing, setDataEditing] = useState<any>(null)
  const [dataForm] = Form.useForm()

  // ============== 加载 ==============
  const loadTypes = async () => {
    const res: any = await dictApi.getTypes()
    setTypes(res.data || [])
    if (!activeTypeId && res.data?.length > 0) {
      setActiveTypeId(res.data[0].id)
    }
  }

  const loadData = async (typeId: number) => {
    setLoading(true)
    try {
      const res: any = await dictApi.getData({ dict_type_id: typeId })
      setData(res.data || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadTypes() }, [])

  useEffect(() => {
    if (activeTypeId) loadData(activeTypeId)
  }, [activeTypeId])

  // ============== 统计 ==============
  const stats = useMemo(() => {
    const totalTypes = types.length
    const totalItems = types.reduce((acc, t) => acc + (t.data_count || 0), 0)
    const activeTypes = types.filter(t => t.status === 1).length
    const sortedTypes = [...types].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    return { totalTypes, totalItems, activeTypes, sortedTypes }
  }, [types])

  // ============== 筛选 ==============
  const filteredTypes = useMemo(() => {
    if (!typeKeyword.trim()) return stats.sortedTypes
    const kw = typeKeyword.toLowerCase()
    return stats.sortedTypes.filter(t =>
      (t.dict_code || '').toLowerCase().includes(kw) ||
      (t.dict_name || '').toLowerCase().includes(kw) ||
      (t.description || '').toLowerCase().includes(kw)
    )
  }, [stats.sortedTypes, typeKeyword])

  const filteredData = useMemo(() => {
    if (!dataKeyword.trim()) return data
    const kw = dataKeyword.toLowerCase()
    return data.filter(d =>
      (d.dict_key || '').toLowerCase().includes(kw) ||
      (d.dict_label || '').toLowerCase().includes(kw) ||
      (d.dict_value || '').toLowerCase().includes(kw) ||
      (d.description || '').toLowerCase().includes(kw)
    )
  }, [data, dataKeyword])

  // ============== 类型操作 ==============
  const openTypeModal = (record?: any) => {
    setTypeEditing(record || null)
    typeForm.resetFields()
    if (record) {
      typeForm.setFieldsValue(record)
    } else {
      typeForm.setFieldsValue({ sort_order: stats.totalTypes + 1, status: 1 })
    }
    setTypeModalOpen(true)
  }

  const submitType = async () => {
    const values = await typeForm.validateFields()
    if (typeEditing) {
      await dictApi.updateType(typeEditing.id, values)
      message.success('更新成功')
    } else {
      await dictApi.createType(values)
      message.success('创建成功')
    }
    setTypeModalOpen(false)
    loadTypes()
  }

  const deleteType = async (id: number) => {
    await dictApi.deleteType(id)
    message.success('删除成功')
    if (activeTypeId === id) setActiveTypeId(null)
    loadTypes()
  }

  // ============== 码值操作 ==============
  const openDataModal = (record?: any) => {
    setDataEditing(record || null)
    dataForm.resetFields()
    if (record) {
      dataForm.setFieldsValue({ ...record, is_default: record.is_default || 0 })
    } else {
      dataForm.setFieldsValue({ sort_order: data.length + 1, status: 1, is_default: 0 })
    }
    setDataModalOpen(true)
  }

  const submitData = async () => {
    const values = await dataForm.validateFields()
    const activeType = types.find(t => t.id === activeTypeId)
    const payload = { dict_code: activeType?.dict_code, ...values }
    if (dataEditing) {
      await dictApi.updateData(dataEditing.id, values)
      message.success('更新成功')
    } else {
      await dictApi.createData(payload)
      message.success('创建成功')
    }
    setDataModalOpen(false)
    loadData(activeTypeId!)
  }

  const deleteData = async (id: number) => {
    await dictApi.deleteData(id)
    message.success('删除成功')
    loadData(activeTypeId!)
  }

  const activeType = types.find(t => t.id === activeTypeId)

  // ============== 字典类别颜色映射 ==============
  const typeColor = (code: string) => {
    if (code.includes('curve') || code.includes('tenor')) return 'blue'
    if (code.includes('rate') || code.includes('compounding')) return 'green'
    if (code.includes('day_count')) return 'cyan'
    if (code.includes('source') || code.includes('data')) return 'gold'
    if (code.includes('validation') || code.includes('severity')) return 'red'
    if (code.includes('scenario')) return 'purple'
    if (code.includes('model') || code.includes('plugin')) return 'magenta'
    if (code.includes('unit')) return 'volcano'
    return 'default'
  }

  return (
    <div style={{ padding: 16 }}>
      {/* 顶部统计卡片 */}
      <Row gutter={12} style={{ marginBottom: 12 }}>
        <Col span={6}>
          <Card size="small" bodyStyle={{ padding: 12 }}>
            <Statistic
              title={<Space><BookOutlined />字典类型数</Space>}
              value={stats.totalTypes}
              suffix="类"
              valueStyle={{ fontSize: 22, color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" bodyStyle={{ padding: 12 }}>
            <Statistic
              title={<Space><TagsOutlined />码值总数</Space>}
              value={stats.totalItems}
              suffix="条"
              valueStyle={{ fontSize: 22, color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" bodyStyle={{ padding: 12 }}>
            <Statistic
              title={<Space><CheckCircleOutlined />启用类型</Space>}
              value={stats.activeTypes}
              suffix="类"
              valueStyle={{ fontSize: 22, color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" bodyStyle={{ padding: 12 }}>
            <Statistic
              title={<Space><StopOutlined />禁用类型</Space>}
              value={stats.totalTypes - stats.activeTypes}
              suffix="类"
              valueStyle={{ fontSize: 22, color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 12 }}
        message="字典 / 用说明"
        description={
          <span>
            字典用于维护系统中所有下拉选项（如曲线类型、计息基础、复利方式、利率单位、点类型等）。
            所有 <b>enum</b> 字段都应从字典读取，避免硬编码。<b>修改字典后已使用该字典的下拉会实时更新</b>。
          </span>
        }
      />

      <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: 16 }}>
        {/* 左侧：字典类型 */}
        <Card
          title={<Space><BookOutlined />字典类型</Space>}
          size="small"
          bodyStyle={{ padding: 0 }}
          extra={
            <Space size={4}>
              <Tooltip title="刷新">
                <Button size="small" icon={<ReloadOutlined />} onClick={loadTypes} />
              </Tooltip>
              <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => openTypeModal()}>
                新建
              </Button>
            </Space>
          }
        >
          <div style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0' }}>
            <Input
              prefix={<SearchOutlined />}
              placeholder="搜索编码/名称/描述"
              allowClear
              value={typeKeyword}
              onChange={(e) => setTypeKeyword(e.target.value)}
              size="small"
            />
          </div>
          <div style={{ maxHeight: 'calc(100vh - 320px)', overflowY: 'auto' }}>
            <Table
              size="small"
              rowKey="id"
              dataSource={filteredTypes}
              pagination={false}
              showHeader={false}
              onRow={(r) => ({
                onClick: () => setActiveTypeId(r.id),
                style: {
                  cursor: 'pointer',
                  background: r.id === activeTypeId ? '#e6f4ff' : undefined,
                  borderLeft: r.id === activeTypeId ? '3px solid #1677ff' : '3px solid transparent',
                },
              })}
              columns={[
                {
                  title: '编码', dataIndex: 'dict_code', width: 150,
                  render: (v: string) => <code style={{ fontSize: 12, color: '#666' }}>{v}</code>,
                },
                {
                  title: '名称', dataIndex: 'dict_name', ellipsis: false,
                  render: (v: string, r: any) => (
                    <div>
                      <div style={{ fontWeight: 500 }}>{v}</div>
                      {r.description && (
                        <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>{r.description}</div>
                      )}
                    </div>
                  ),
                },
                {
                  title: '码值', dataIndex: 'data_count', width: 70,
                  render: (v: number) => <Tag color="purple">{v}</Tag>,
                },
                {
                  title: '操作', width: 70, fixed: 'right',
                  render: (_, r: any) => (
                    <Space size={2}>
                      <Tooltip title="编辑">
                        <Button size="small" type="text" icon={<EditOutlined />}
                          onClick={(e) => { e.stopPropagation(); openTypeModal(r) }} />
                      </Tooltip>
                      <Popconfirm title="确认删除该类型及其码值？" onConfirm={(e) => { e?.stopPropagation?.(); deleteType(r.id) }} onCancel={(e) => e?.stopPropagation?.()}>
                        <Button size="small" type="text" danger icon={<DeleteOutlined />}
                          onClick={(e) => e.stopPropagation()} />
                      </Popconfirm>
                    </Space>
                  ),
                },
              ]}
            />
          </div>
          <div style={{ padding: '8px 12px', borderTop: '1px solid #f0f0f0', color: '#999', fontSize: 12 }}>
            共 {filteredTypes.length} 类
          </div>
        </Card>

        {/* 右侧：码值 */}
        <Card
          title={
            activeType ? (
              <Space wrap>
                <Tag color={typeColor(activeType.dict_code)} style={{ fontSize: 13, padding: '2px 8px' }}>
                  {activeType.dict_code}
                </Tag>
                <span style={{ fontWeight: 600 }}>{activeType.dict_name}</span>
                <span style={{ color: '#999', fontSize: 13 }}>· 共 {data.length} 个码值</span>
              </Space>
            ) : <Space><TagsOutlined />码值管理</Space>
          }
          size="small"
          bodyStyle={{ padding: 0 }}
          extra={
            <Space size={4}>
              <Tooltip title="刷新">
                <Button size="small" icon={<ReloadOutlined />} onClick={() => activeTypeId && loadData(activeTypeId)} />
              </Tooltip>
              <Button type="primary" size="small" icon={<PlusOutlined />}
                disabled={!activeTypeId} onClick={() => openDataModal()}>
                新建码值
              </Button>
            </Space>
          }
        >
          {activeType && (
            <div style={{ padding: '8px 16px', borderBottom: '1px solid #f0f0f0', background: '#fafafa' }}>
              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ color: '#999', fontSize: 12 }}>描述</div>
                  <div style={{ fontSize: 13 }}>{activeType.description || <span style={{ color: '#ccc' }}>暂无描述</span>}</div>
                </Col>
                <Col span={6}>
                  <div style={{ color: '#999', fontSize: 12 }}>排序号</div>
                  <div style={{ fontSize: 13 }}>{activeType.sort_order ?? '-'}</div>
                </Col>
                <Col span={6}>
                  <div style={{ color: '#999', fontSize: 12 }}>状态</div>
                  <div style={{ fontSize: 13 }}>
                    <Tag color={activeType.status === 1 ? 'green' : 'default'}>
                      {activeType.status === 1 ? '启用' : '禁用'}
                    </Tag>
                  </div>
                </Col>
              </Row>
            </div>
          )}
          <div style={{ padding: '8px 12px' }}>
            <Input
              prefix={<SearchOutlined />}
              placeholder="搜索键名/标签/说明"
              allowClear
              value={dataKeyword}
              onChange={(e) => setDataKeyword(e.target.value)}
              size="small"
              style={{ maxWidth: 320 }}
            />
          </div>
          {data.length === 0 && !loading ? (
            <Empty description={activeType ? '暂无码值' : '请先在左侧选择字典类型'} style={{ padding: 40 }} />
          ) : (
            <Table
              size="small"
              rowKey="id"
              loading={loading}
              dataSource={filteredData}
              pagination={{ pageSize: 15, size: 'small', showSizeChanger: false }}
              scroll={{ x: 800 }}
              columns={[
                {
                  title: '键名 (key)', dataIndex: 'dict_key', width: 160,
                  render: (v: string) => <code style={{ fontSize: 12 }}>{v}</code>,
                },
                {
                  title: '显示标签', dataIndex: 'dict_label', width: 180,
                  render: (v: string) => <Tag color="blue">{v}</Tag>,
                },
                {
                  title: '存储值', dataIndex: 'dict_value', width: 130,
                  render: (v: string) => v ? <code style={{ fontSize: 12 }}>{v}</code> : <span style={{ color: '#ccc' }}>-</span>,
                },
                {
                  title: '说明', dataIndex: 'description', ellipsis: true,
                  render: (v: string) => v
                    ? <Tooltip title={v}><span style={{ color: '#666' }}>{v.length > 30 ? v.slice(0, 30) + '...' : v}</span></Tooltip>
                    : <span style={{ color: '#ccc' }}>-</span>,
                },
                {
                  title: '默认', dataIndex: 'is_default', width: 80,
                  render: (v: number) => v ? <Tag color="blue">默认</Tag> : <span style={{ color: '#ccc' }}>-</span>,
                },
                {
                  title: '样式', dataIndex: 'list_class', width: 110,
                  render: (v: string) => v ? <Tag color={v}>{v}</Tag> : <span style={{ color: '#ccc' }}>-</span>,
                },
                {
                  title: '排序', dataIndex: 'sort_order', width: 70,
                  align: 'center' as const,
                },
                {
                  title: '状态', dataIndex: 'status', width: 80,
                  render: (v: number) => v === 1 ? <Tag color="green">启用</Tag> : <Tag>禁用</Tag>,
                },
                {
                  title: '操作', width: 130, fixed: 'right' as const,
                  render: (_, r: any) => (
                    <Space size={4}>
                      <Button size="small" type="link" icon={<EditOutlined />} onClick={() => openDataModal(r)}>编辑</Button>
                      <Popconfirm title="确认删除？" onConfirm={() => deleteData(r.id)}>
                        <Button size="small" type="link" danger icon={<DeleteOutlined />}>删除</Button>
                      </Popconfirm>
                    </Space>
                  ),
                },
              ]}
            />
          )}
        </Card>
      </div>

      {/* 类型 Modal */}
      <Modal
        title={typeEditing ? '编辑字典类型' : '新建字典类型'}
        open={typeModalOpen}
        onCancel={() => setTypeModalOpen(false)}
        onOk={submitType}
        destroyOnClose
      >
        <Form form={typeForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="dict_code" label="字典编码" rules={[{ required: true, pattern: /^[a-z][a-z0-9_]*$/, message: '小写字母开头，字母数字下划线' }]}>
            <Input placeholder="如 curve_type" disabled={!!typeEditing} />
          </Form.Item>
          <Form.Item name="dict_name" label="字典名称" rules={[{ required: true }]}>
            <Input placeholder="如 曲线类型" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="字典用途说明" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="sort_order" label="排序号">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="状态">
                <Select options={[{ value: 1, label: '启用' }, { value: 0, label: '禁用' }]} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 码值 Modal */}
      <Modal
        title={dataEditing ? '编辑字典码值' : '新建字典码值'}
        open={dataModalOpen}
        onCancel={() => setDataModalOpen(false)}
        onOk={submitData}
        width={640}
        destroyOnClose
      >
        <Form form={dataForm} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="dict_key" label="键名 (key)" rules={[{ required: true }]}>
                <Input placeholder="如 base" disabled={!!dataEditing} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="dict_label" label="显示标签" rules={[{ required: true }]}>
                <Input placeholder="如 基础曲线" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="dict_value" label="存储值（不填默认同键名）">
                <Input placeholder="可不填" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="list_class" label="列表样式类">
                <Select allowClear placeholder="选择 tag颜色">
                  <Select.Option value="primary">primary（蓝）</Select.Option>
                  <Select.Option value="success">success（绿）</Select.Option>
                  <Select.Option value="warning">warning（黄）</Select.Option>
                  <Select.Option value="danger">danger（红）</Select.Option>
                  <Select.Option value="default">default（灰）</Select.Option>
                  <Select.Option value="cyan">cyan（青）</Select.Option>
                  <Select.Option value="purple">purple（紫）</Select.Option>
                  <Select.Option value="magenta">magenta（玫红）</Select.Option>
                  <Select.Option value="volcano">volcano（橙红）</Select.Option>
                  <Select.Option value="gold">gold（金）</Select.Option>
                  <Select.Option value="lime">lime（绿黄）</Select.Option>
                  <Select.Option value="geekblue">geekblue（科技蓝）</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="description" label="说明">
                <Input.TextArea rows={2} placeholder="该码值的含义/用途说明" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="is_default" label="是否默认">
                <Select options={[{ value: 0, label: '否' }, { value: 1, label: '是' }]} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="sort_order" label="排序号">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="status" label="状态">
                <Select options={[{ value: 1, label: '启用' }, { value: 0, label: '禁用' }]} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}