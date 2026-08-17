import { useState, useEffect, useMemo } from 'react'
import {
  Card, Button, Table, Modal, Form, Input, Select, InputNumber,
  Space, Tag, Row, Col, message, Popconfirm, Empty, Divider, Radio, Tooltip, Alert,
  Drawer, DatePicker, Statistic, Tabs,
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  ImportOutlined, ReloadOutlined, QuestionCircleOutlined,
  HistoryOutlined, CalendarOutlined, LineChartOutlined,
  CloudDownloadOutlined, ThunderboltOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { curvesApi, dictApi, ratesApi, collectionApi } from '../api'

interface CurveDefinition {
  id: number
  code: string
  name: string
  curve_type: string
  curve_category?: string
  currency: string
  rate_type_code: string
  day_count_method?: string
  compounding_method?: string
  interpolation_method?: string
  extrapolation_method?: string
  display_unit?: string
  point_unit?: string
  precision_digits?: number
  is_real_time?: number
  tenor_set?: string[]
  description?: string
}

interface CurvePoint {
  id: number
  curve_code: string
  tenor: string
  rate_value: number | null
  point_unit: string
  point_type: string
  sort_order: number
  description?: string
}

interface DictItem {
  dict_key: string
  dict_label: string
  description?: string
  list_class?: string
}

export default function Curves() {
  const [curves, setCurves] = useState<CurveDefinition[]>([])
  const [loadingCurves, setLoadingCurves] = useState(false)
  const [selectedCurve, setSelectedCurve] = useState<string | null>(null)

  const [points, setPoints] = useState<CurvePoint[]>([])
  const [loadingPoints, setLoadingPoints] = useState(false)

  // 字典
  const [dictAll, setDictAll] = useState<Record<string, DictItem[]>>({})

  // 弹窗
  const [curveModalOpen, setCurveModalOpen] = useState(false)
  const [editingCurve, setEditingCurve] = useState<CurveDefinition | null>(null)
  const [curveForm] = Form.useForm()

  const [pointModalOpen, setPointModalOpen] = useState(false)
  const [editingPoint, setEditingPoint] = useState<CurvePoint | null>(null)
  const [pointForm] = Form.useForm()

  const [batchModalOpen, setBatchModalOpen] = useState(false)
  const [batchText, setBatchText] = useState('')
  const [batchUnit, setBatchUnit] = useState('percent')

  // ========== 利率历史 Drawer（按曲线点 -> 日期维护） ==========
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyPoint, setHistoryPoint] = useState<CurvePoint | null>(null)
  const [historyData, setHistoryData] = useState<any[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyEditOpen, setHistoryEditOpen] = useState(false)
  const [historyEditing, setHistoryEditing] = useState<any | null>(null)
  const [historyForm] = Form.useForm()
  const [historyBatchOpen, setHistoryBatchOpen] = useState(false)
  const [historyBatchText, setHistoryBatchText] = useState('')

  // ========== 业务规则采集 ==========
  const [collectModalOpen, setCollectModalOpen] = useState(false)
  const [collecting, setCollecting] = useState(false)
  const [collectResult, setCollectResult] = useState<any>(null)
  const [collectForm] = Form.useForm()
  const [collectRules, setCollectRules] = useState<any[]>([])
  const [collectLogs, setCollectLogs] = useState<any[]>([])

  // ========== 加载 ==========
  const loadCurves = async () => {
    setLoadingCurves(true)
    try {
      const r: any = await curvesApi.listDefinitions()
      setCurves(r.data || [])
      if (!selectedCurve && r.data?.length) {
        setSelectedCurve(r.data[0].code)
      }
    } finally {
      setLoadingCurves(false)
    }
  }

  const loadDicts = async () => {
    const r: any = await dictApi.getAll()
    setDictAll(r.data || {})
  }

  const loadPoints = async (curveCode: string) => {
    setLoadingPoints(true)
    try {
      const r: any = await curvesApi.listPoints({ curve_code: curveCode })
      const sorted = (r.data || []).sort((a: CurvePoint, b: CurvePoint) => a.sort_order - b.sort_order)
      setPoints(sorted)
    } finally {
      setLoadingPoints(false)
    }
  }

  useEffect(() => { loadDicts() }, [])
  useEffect(() => { loadCurves() }, [])
  useEffect(() => {
    if (selectedCurve) loadPoints(selectedCurve)
    else setPoints([])
  }, [selectedCurve])

  // ========== 辅助 ==========
  const dictItem = (dictCode: string, key?: string): DictItem | undefined => {
    if (!key) return undefined
    return (dictAll[dictCode] || []).find(d => d.dict_key === key)
  }

  const dictLabel = (dictCode: string, key?: string) => {
    const item = dictItem(dictCode, key)
    return item?.dict_label || key || '-'
  }

  const dictDesc = (dictCode: string, key?: string) => dictItem(dictCode, key)?.description || ''

  // 期限点的标准说明（优先用户填的说明，否则用字典说明）
  const pointDescription = (p: CurvePoint) => {
    if (p.description) return p.description
    return dictDesc('tenor_description', p.tenor) || `${dictLabel('curve_point_type', p.point_type)} · ${dictLabel('point_unit', p.point_unit)}`
  }

  const selectedCurveData = useMemo(
    () => curves.find(c => c.code === selectedCurve),
    [curves, selectedCurve]
  )

  // ========== 业务规则采集 ==========
  const loadCollectRules = async () => {
    const r: any = await collectionApi.listRules()
    setCollectRules(r.data || [])
  }
  const loadCollectLogs = async () => {
    const r: any = await collectionApi.listLogs({ limit: 10 })
    setCollectLogs(r.data || [])
  }
  const openCollect = async () => {
    setCollectResult(null)
    collectForm.resetFields()
    // 默认 1 年
    collectForm.setFieldsValue({
      start_date: dayjs().subtract(1, 'year').add(1, 'day'),
      end_date: dayjs(),
      source_code: 'auto_collector',
    })
    await Promise.all([loadCollectRules(), loadCollectLogs()])
    setCollectModalOpen(true)
  }
  const submitCollect = async () => {
    const v = await collectForm.validateFields()
    setCollecting(true)
    setCollectResult(null)
    try {
      const r: any = await collectionApi.run({
        start_date: (v.start_date as any).format('YYYY-MM-DD'),
        end_date: (v.end_date as any).format('YYYY-MM-DD'),
        curve_codes: v.curve_codes?.length ? v.curve_codes : undefined,
        source_code: v.source_code || 'auto_collector',
      })
      setCollectResult(r.data)
      message.success(`采集完成：${r.data.total_records} 条记录`)
      loadCollectLogs()
    } catch (e: any) {
      message.error('采集失败：' + (e?.response?.data?.detail || e?.message || ''))
    } finally {
      setCollecting(false)
    }
  }

  // ========== 曲线定义 CRUD ==========
  const openCreateCurve = () => {
    setEditingCurve(null)
    curveForm.resetFields()
    curveForm.setFieldsValue({
      curve_type: 'base',
      curve_category: 'risk_free',
      currency: 'CNY',
      rate_type_code: 'yield_to_maturity',
      day_count_method: 'ACT/365',
      compounding_method: 'compound',
      interpolation_method: 'pchip',
      extrapolation_method: 'flat',
      display_unit: 'percent',
      point_unit: 'percent',
      precision_digits: 4,
      is_real_time: 0,
    })
    setCurveModalOpen(true)
  }

  const openEditCurve = (c: CurveDefinition) => {
    setEditingCurve(c)
    curveForm.setFieldsValue({
      ...c,
      tenor_set: (c.tenor_set || []).join(','),
    })
    setCurveModalOpen(true)
  }

  const submitCurve = async () => {
    const v = await curveForm.validateFields()
    const tenorSet = (v.tenor_set || '').split(/[,，;\s]+/).filter(Boolean)
    const payload = { ...v, tenor_set: tenorSet }
    if (editingCurve) {
      await curvesApi.updateDefinition(editingCurve.code, payload)
      message.success('更新成功')
    } else {
      await curvesApi.createDefinition(payload)
      message.success('新建成功')
    }
    setCurveModalOpen(false)
    loadCurves()
  }

  const deleteCurve = async (code: string) => {
    await curvesApi.deleteDefinition(code)
    message.success('已删除')
    if (selectedCurve === code) setSelectedCurve(null)
    loadCurves()
  }

  // ========== 曲线点 CRUD ==========
  const openCreatePoint = () => {
    if (!selectedCurve) return message.warning('请先选择曲线')
    setEditingPoint(null)
    pointForm.resetFields()
    pointForm.setFieldsValue({
      curve_code: selectedCurve,
      point_unit: selectedCurveData?.point_unit || 'percent',
      point_type: 'standard',
      sort_order: points.length + 1,
    })
    setPointModalOpen(true)
  }

  const openEditPoint = (p: CurvePoint) => {
    setEditingPoint(p)
    pointForm.setFieldsValue(p)
    setPointModalOpen(true)
  }

  const submitPoint = async () => {
    const v = await pointForm.validateFields()
    if (editingPoint) {
      await curvesApi.updatePoint(editingPoint.id, v)
      message.success('更新成功')
    } else {
      await curvesApi.createPoint(v)
      message.success('新增成功')
    }
    setPointModalOpen(false)
    if (selectedCurve) loadPoints(selectedCurve)
  }

  const deletePoint = async (id: number) => {
    await curvesApi.deletePoint(id)
    message.success('已删除')
    if (selectedCurve) loadPoints(selectedCurve)
  }

  // ========== 批量导入 ==========
  const openBatchImport = () => {
    if (!selectedCurve) return message.warning('请先选择曲线')
    setBatchUnit(selectedCurveData?.point_unit || 'percent')
    setBatchText('')
    setBatchModalOpen(true)
  }

  const submitBatchImport = async () => {
    const lines = batchText.split('\n').map(l => l.trim()).filter(Boolean)
    if (!lines.length) return message.warning('请输入数据')

    const points: any[] = []
    const errors: string[] = []
    lines.forEach((line, idx) => {
      // 支持 期限,值,类型 / 期限,值 / 期限 \t 值 三种格式
      const parts = line.split(/[,，\t\s]+/).filter(Boolean)
      if (parts.length < 2) {
        errors.push(`第 ${idx + 1} 行：格式错误`)
        return
      }
      points.push({
        tenor: parts[0].toUpperCase(),
        rate_value: parseFloat(parts[1]),
        point_type: parts[2] || 'standard',
        sort_order: idx + 1,
      })
    })
    if (errors.length) {
      Modal.error({ title: '部分行解析失败', content: errors.join('\n') })
      return
    }

    const r: any = await curvesApi.batchPoints({
      curve_code: selectedCurve,
      point_unit: batchUnit,
      points,
    })
    message.success(`成功导入 ${r.data?.inserted || 0} 个点`)
    setBatchModalOpen(false)
    loadPoints(selectedCurve!)
  }

  // ========== 利率历史 Drawer（按曲线点 -> 日期维护） ==========
  const loadHistory = async (curveCode: string, tenor: string) => {
    setHistoryLoading(true)
    try {
      const r: any = await ratesApi.pointHistory(curveCode, tenor)
      setHistoryData(r.data || [])
    } finally {
      setHistoryLoading(false)
    }
  }

  const openHistory = (p: CurvePoint) => {
    setHistoryPoint(p)
    setHistoryOpen(true)
    loadHistory(p.curve_code, p.tenor)
  }

  const openHistoryCreate = () => {
    if (!historyPoint) return
    setHistoryEditing(null)
    historyForm.resetFields()
    historyForm.setFieldsValue({
      trade_date: dayjs(),
      rate_value: historyPoint.rate_value ?? null,
      source_version: 'official',
      remark: '',
    })
    setHistoryEditOpen(true)
  }

  const openHistoryEdit = (row: any) => {
    setHistoryEditing(row)
    historyForm.setFieldsValue({
      trade_date: dayjs(row.trade_date),
      rate_value: row.rate_value,
      source_version: row.source_version || 'official',
      remark: row.remark || '',
    })
    setHistoryEditOpen(true)
  }

  const submitHistory = async () => {
    if (!historyPoint) return
    const v = await historyForm.validateFields()
    const trade_date = (v.trade_date as any).format('YYYY-MM-DD')
    if (historyEditing) {
      await ratesApi.updateRate(historyEditing.id, {
        rate_value: v.rate_value,
        source_version: v.source_version,
        remark: v.remark,
      })
      message.success('已更新')
    } else {
      // 新增：调 point-batch 走批量入口（也支持新建）
      await ratesApi.pointBatch({
        curve_code: historyPoint.curve_code,
        tenor: historyPoint.tenor,
        source_version: v.source_version || 'official',
        records: [{ trade_date, rate_value: v.rate_value }],
      })
      message.success('已新增')
    }
    setHistoryEditOpen(false)
    loadHistory(historyPoint.curve_code, historyPoint.tenor)
  }

  const deleteHistoryRow = async (id: number) => {
    await ratesApi.deleteRate(id)
    message.success('已删除')
    if (historyPoint) loadHistory(historyPoint.curve_code, historyPoint.tenor)
  }

  const openHistoryBatch = () => {
    if (!historyPoint) return
    setHistoryBatchText('')
    setHistoryBatchOpen(true)
  }

  const submitHistoryBatch = async () => {
    if (!historyPoint) return
    const lines = historyBatchText.split('\n').map(l => l.trim()).filter(Boolean)
    if (!lines.length) return message.warning('请输入数据')

    const records: any[] = []
    const errors: string[] = []
    lines.forEach((line, idx) => {
      const parts = line.split(/[,，\t\s]+/).filter(Boolean)
      if (parts.length < 2) {
        errors.push(`第 ${idx + 1} 行格式错误`)
        return
      }
      const dateRaw = parts[0]
      // 兼容 YYYY-MM-DD / YYYYMMDD / YYYY/MM/DD
      let d = dayjs(dateRaw)
      if (!d.isValid()) {
        d = dayjs(dateRaw.replace(/^(\d{4})(\d{2})(\d{2})$/, '$1-$2-$3'))
      }
      if (!d.isValid()) {
        errors.push(`第 ${idx + 1} 行日期格式错误：${dateRaw}`)
        return
      }
      records.push({
        trade_date: d.format('YYYY-MM-DD'),
        rate_value: parseFloat(parts[1]),
      })
    })

    if (errors.length) {
      Modal.error({ title: '部分行解析失败', content: errors.join('\n') })
      return
    }

    const r: any = await ratesApi.pointBatch({
      curve_code: historyPoint.curve_code,
      tenor: historyPoint.tenor,
      source_version: 'official',
      records,
    })
    message.success(`成功 ${r.data?.total || 0} 条（新增 ${r.data?.inserted || 0} / 更新 ${r.data?.updated || 0}）`)
    setHistoryBatchOpen(false)
    loadHistory(historyPoint.curve_code, historyPoint.tenor)
  }

  // 历史统计
  const historyStats = useMemo(() => {
    if (!historyData.length) return { count: 0, latest: '-', min: 0, max: 0, avg: 0, change: 0 }
    const values = historyData.map(d => d.rate_value)
    const sorted = [...historyData].sort((a, b) => a.trade_date.localeCompare(b.trade_date))
    const latest = sorted[sorted.length - 1]?.rate_value ?? 0
    const earliest = sorted[0]?.rate_value ?? 0
    return {
      count: historyData.length,
      latest: historyData[0]?.trade_date || '-',
      min: Math.min(...values),
      max: Math.max(...values),
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      change: latest - earliest,
    }
  }, [historyData])

  // ========== 表格列 ==========
  const curveColumns = [
    { title: '编码', dataIndex: 'code', width: 180 },
    { title: '名称', dataIndex: 'name', width: 160 },
    {
      title: '类型', dataIndex: 'curve_type', width: 80,
      render: (v: string) => <Tag color="blue">{dictLabel('curve_type', v)}</Tag>,
    },
    {
      title: '大类', dataIndex: 'curve_category', width: 90,
      render: (v: string) => <Tag color="cyan">{dictLabel('curve_category', v)}</Tag>,
    },
    {
      title: '计息基础', dataIndex: 'day_count_method', width: 100,
      render: (v: string) => <Tag>{dictLabel('day_count', v)}</Tag>,
    },
    {
      title: '复利方式', dataIndex: 'compounding_method', width: 100,
      render: (v: string) => <Tag>{dictLabel('compounding', v)}</Tag>,
    },
    {
      title: '插值', dataIndex: 'interpolation_method', width: 90,
      render: (v: string) => <Tag color="purple">{dictLabel('interpolation_method', v)}</Tag>,
    },
    { title: '币种', dataIndex: 'currency', width: 60 },
    {
      title: '操作', width: 160, fixed: 'right' as const,
      render: (_: any, r: CurveDefinition) => (
        <Space size="small">
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditCurve(r)}>编辑</Button>
          <Popconfirm title={`删除曲线 ${r.code}？`} onConfirm={() => deleteCurve(r.code)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const pointColumns = [
    { title: '序号', dataIndex: 'sort_order', width: 60, align: 'center' as const },
    {
      title: '期限点', dataIndex: 'tenor', width: 90,
      render: (v: string) => {
        const desc = dictDesc('tenor_description', v)
        return (
          <Tooltip title={desc || '标准期限点'}>
            <span style={{ fontWeight: 500 }}>{v}</span>
          </Tooltip>
        )
      },
    },
    {
      title: '利率值', dataIndex: 'rate_value', width: 110,
      render: (v: number | null) =>
        v == null
          ? <Tag color="default" style={{ opacity: 0.6 }}>待填</Tag>
          : <span style={{ fontWeight: 500, color: '#1677ff' }}>{v.toFixed(4)}</span>,
    },
    {
      title: '单位', dataIndex: 'point_unit', width: 80,
      render: (v: string) => {
        const item = dictItem('point_unit', v)
        return (
          <Tooltip title={item?.description}>
            <Tag color="cyan">{item?.dict_label || v}</Tag>
          </Tooltip>
        )
      },
    },
    {
      title: '类型', dataIndex: 'point_type', width: 110,
      render: (v: string) => {
        const item = dictItem('curve_point_type', v)
        const color = item?.list_class || 'geekblue'
        return (
          <Tooltip title={item?.description}>
            <Tag color={color}>{item?.dict_label || v}</Tag>
          </Tooltip>
        )
      },
    },
    {
      title: '说明', ellipsis: true,
      render: (_: any, r: CurvePoint) => {
        const txt = pointDescription(r)
        return txt ? (
          <span style={{ color: r.description ? '#000' : '#888', fontSize: 12 }}>
            {r.description ? <Tag color="processing" style={{ marginRight: 4 }}>自定义</Tag> : null}
            {txt}
          </span>
        ) : <span style={{ color: '#ccc' }}>-</span>
      },
    },
    {
      title: '操作', width: 220, fixed: 'right' as const,
      render: (_: any, r: CurvePoint) => (
        <Space size="small">
          <Tooltip title="按日期维护利率历史">
            <Button
              size="small"
              type="link"
              icon={<HistoryOutlined />}
              onClick={(e) => { e.stopPropagation(); openHistory(r) }}
              style={{ padding: '0 4px' }}
            >
              历史
            </Button>
          </Tooltip>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditPoint(r)} />
          <Popconfirm title="删除该点？" onConfirm={() => deletePoint(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 历史表格列
  const historyColumns = [
    { title: '交易日', dataIndex: 'trade_date', width: 120, fixed: 'left' as const },
    {
      title: '利率值', dataIndex: 'rate_value', width: 110,
      render: (v: number) => <span style={{ fontWeight: 500, color: '#1677ff' }}>{v.toFixed(4)}</span>,
    },
    {
      title: '版本', dataIndex: 'source_version', width: 90,
      render: (v: string) => <Tag color="purple">{v || 'official'}</Tag>,
    },
    {
      title: '状态', dataIndex: 'data_status', width: 80,
      render: (v: string) => <Tag color={v === 'active' ? 'green' : 'default'}>{v}</Tag>,
    },
    {
      title: '调整', dataIndex: 'is_adjusted', width: 70,
      render: (v: boolean) => v ? <Tag color="orange">已调整</Tag> : <span style={{ color: '#ccc' }}>-</span>,
    },
    { title: '备注', dataIndex: 'remark', ellipsis: true },
    {
      title: '操作', width: 120, fixed: 'right' as const,
      render: (_: any, row: any) => (
        <Space size="small">
          <Button size="small" icon={<EditOutlined />} onClick={() => openHistoryEdit(row)} />
          <Popconfirm title={`删除 ${row.trade_date} 的利率？`} onConfirm={() => deleteHistoryRow(row.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 16 }}>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 12 }}
        message="联动机制"
        description={
          <span>
            新建/更新曲线时，<b>系统会自动根据曲线定义中的期限集生成对应的曲线点</b>（利率值留空待人工填写）。
            期限点说明 / 类型 / 单位 均来自字典（<b>期限点说明</b>、<b>曲线点类型</b>、<b>利率单位</b>）。
            修改期限集后，已存在的点（带值的）会保留，新增的自动添加，移除的会自动删除。
          </span>
        }
        action={
          <Button
            type="primary"
            icon={<CloudDownloadOutlined />}
            onClick={openCollect}
          >
            采集历史数据
          </Button>
        }
      />
      <Row gutter={16}>
        {/* ========== 左侧：曲线定义 ========== */}
        <Col span={11}>
          <Card
            title="📈 曲线定义"
            extra={
              <Space>
                <Button icon={<ReloadOutlined />} onClick={loadCurves}>刷新</Button>
                <Button type="primary" icon={<PlusOutlined />} onClick={openCreateCurve}>
                  新建曲线
                </Button>
              </Space>
            }
            bodyStyle={{ padding: 0 }}
          >
            <Table
              rowKey="code"
              size="small"
              loading={loadingCurves}
              dataSource={curves}
              columns={curveColumns}
              pagination={{ pageSize: 8, size: 'small' }}
              scroll={{ x: 800 }}
              rowClassName={(r: CurveDefinition) =>
                r.code === selectedCurve ? 'ant-table-row-selected' : ''
              }
              onRow={(r: CurveDefinition) => ({
                onClick: () => setSelectedCurve(r.code),
                style: { cursor: 'pointer' },
              })}
            />
          </Card>
        </Col>

        {/* ========== 右侧：曲线点定义 ========== */}
        <Col span={13}>
          <Card
            title={
              selectedCurveData ? (
                <span>
                  📊 曲线点定义 — <span style={{ color: '#1677ff' }}>{selectedCurveData.name}</span>
                  <Tag style={{ marginLeft: 8 }}>{selectedCurveData.code}</Tag>
                  <Tag color="blue">{points.length} 个点</Tag>
                </span>
              ) : '📊 曲线点定义'
            }
            extra={
              <Space>
                <Button icon={<ReloadOutlined />} onClick={() => selectedCurve && loadPoints(selectedCurve)}>
                  刷新
                </Button>
                <Button type="primary" icon={<PlusOutlined />} onClick={openCreatePoint} disabled={!selectedCurve}>
                  新增点
                </Button>
                <Button icon={<ImportOutlined />} onClick={openBatchImport} disabled={!selectedCurve}>
                  批量导入
                </Button>
              </Space>
            }
            bodyStyle={{ padding: 0 }}
          >
            {!selectedCurve ? (
              <Empty description="请在左侧选择一条曲线" style={{ padding: 60 }} />
            ) : (
              <Table
                rowKey="id"
                size="small"
                loading={loadingPoints}
                dataSource={points}
                columns={pointColumns}
                pagination={{ pageSize: 12, size: 'small' }}
                scroll={{ x: 700 }}
              />
            )}
          </Card>

          {selectedCurveData && (
            <Card size="small" style={{ marginTop: 12 }} title="📌 曲线属性">
              <Row gutter={16}>
                <Col span={8}>
                  <div><b>利率类型：</b>{dictLabel('rate_type', selectedCurveData.rate_type_code)}</div>
                  <div><b>计息基础：</b>{dictLabel('day_count', selectedCurveData.day_count_method)}</div>
                  <div><b>复利方式：</b>{dictLabel('compounding', selectedCurveData.compounding_method)}</div>
                </Col>
                <Col span={8}>
                  <div><b>插值方法：</b>{dictLabel('interpolation_method', selectedCurveData.interpolation_method)}</div>
                  <div><b>外推方法：</b>{dictLabel('extrapolation_method', selectedCurveData.extrapolation_method)}</div>
                  <div><b>展示单位：</b>{dictLabel('point_unit', selectedCurveData.display_unit)}</div>
                </Col>
                <Col span={8}>
                  <div><b>精度：</b>{selectedCurveData.precision_digits} 位小数</div>
                  <div><b>实时：</b>{selectedCurveData.is_real_time ? '是' : '否'}</div>
                  <div><b>期限集：</b>{(selectedCurveData.tenor_set || []).join(', ')}</div>
                </Col>
              </Row>
            </Card>
          )}
        </Col>
      </Row>

      {/* ===== 曲线定义弹窗 ===== */}
      <Modal
        title={editingCurve ? `编辑曲线：${editingCurve.code}` : '新建曲线定义'}
        open={curveModalOpen}
        onCancel={() => setCurveModalOpen(false)}
        onOk={submitCurve}
        width={780}
        destroyOnClose
      >
        <Form form={curveForm} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="曲线编码" name="code" rules={[{ required: true, pattern: /^[a-z0-9_]+$/, message: '小写字母+数字+下划线' }]}>
                <Input disabled={!!editingCurve} placeholder="例如 cnb_treasury_yield" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="曲线名称" name="name" rules={[{ required: true }]}>
                <Input placeholder="中债国债收益率" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="曲线类型" name="curve_type">
                <Select options={(dictAll.curve_type || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="业务大类" name="curve_category">
                <Select options={(dictAll.curve_category || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="币种" name="currency">
                <Select options={[{ value: 'CNY', label: 'CNY 人民币' }, { value: 'USD', label: 'USD 美元' }]} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="利率类型" name="rate_type_code">
                <Select options={(dictAll.rate_type || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="计息基础" name="day_count_method">
                <Select options={(dictAll.day_count || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="复利方式" name="compounding_method">
                <Select options={(dictAll.compounding || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="插值方法" name="interpolation_method">
                <Select options={(dictAll.interpolation_method || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="外推方法" name="extrapolation_method">
                <Select options={(dictAll.extrapolation_method || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="展示单位" name="display_unit">
                <Select options={(dictAll.point_unit || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="利率单位" name="point_unit">
                <Select options={(dictAll.point_unit || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="小数位数" name="precision_digits">
                <InputNumber min={0} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="是否实时" name="is_real_time">
                <Radio.Group options={[{ label: '是', value: 1 }, { label: '否', value: 0 }]} optionType="button" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="期限集" name="tenor_set" tooltip="逗号分隔，如 1M,3M,6M,1Y,5Y,10Y">
                <Input placeholder="1M, 3M, 6M, 1Y, 2Y, 5Y, 10Y, 30Y" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="说明" name="description">
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* ===== 曲线点弹窗 ===== */}
      <Modal
        title={editingPoint ? '编辑曲线点' : '新增曲线点'}
        open={pointModalOpen}
        onCancel={() => setPointModalOpen(false)}
        onOk={submitPoint}
        destroyOnClose
      >
        <Form form={pointForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item label="曲线编码" name="curve_code">
            <Input disabled />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="期限点" name="tenor" rules={[{ required: true, message: '请输入期限' }]}>
                <Input placeholder="如 1M / 3M / 5Y" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="利率值" name="rate_value">
                <InputNumber step={0.0001} style={{ width: '100%' }} placeholder="留空表示未定义" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="单位" name="point_unit">
                <Select options={(dictAll.point_unit || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="类型" name="point_type">
                <Select options={(dictAll.curve_point_type || []).map(d => ({ label: d.dict_label, value: d.dict_key }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="排序" name="sort_order">
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="说明" name="description">
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* ===== 批量导入弹窗 ===== */}
      <Modal
        title={`批量导入曲线点 - ${selectedCurveData?.name || ''}`}
        open={batchModalOpen}
        onCancel={() => setBatchModalOpen(false)}
        onOk={submitBatchImport}
        width={680}
        destroyOnClose
      >
        <Divider plain>格式说明</Divider>
        <div style={{ color: '#666', marginBottom: 12, fontSize: 13 }}>
          • 每行一个点，支持 3 种格式：<br />
          &nbsp;&nbsp;<code>期限,利率</code>（如 <code>1M,1.45</code>）<br />
          &nbsp;&nbsp;<code>期限,利率,类型</code>（如 <code>10Y,2.45,key</code>）<br />
          &nbsp;&nbsp;逗号 / 空格 / Tab 均可作为分隔符<br />
          • 期限会自动转大写；类型留空默认为 standard
        </div>
        <Row gutter={16}>
          <Col span={6}>
            <div style={{ marginBottom: 4 }}>单位</div>
            <Select
              value={batchUnit}
              onChange={setBatchUnit}
              style={{ width: '100%' }}
              options={(dictAll.point_unit || []).map(d => ({ label: d.dict_label, value: d.dict_key }))}
            />
          </Col>
          <Col span={18}>
            <div style={{ marginBottom: 4 }}>数据（每行一个点）</div>
            <Input.TextArea
              rows={10}
              value={batchText}
              onChange={e => setBatchText(e.target.value)}
              placeholder={`1M,1.45\n3M,1.58\n6M,1.65\n1Y,1.77\n2Y,1.85\n3Y,1.95\n5Y,2.15,key\n10Y,2.45,key\n15Y,2.62\n30Y,2.78`}
              style={{ fontFamily: 'monospace' }}
            />
          </Col>
        </Row>
      </Modal>

      {/* ===== 利率历史 Drawer（按曲线点 + 日期维护） ===== */}
      <Drawer
        title={
          historyPoint ? (
            <Space>
              <HistoryOutlined />
              <span>利率历史 — <b style={{ color: '#1677ff' }}>{historyPoint.curve_code}</b></span>
              <Tag color="blue">{historyPoint.tenor}</Tag>
              <Tag color="cyan">{dictLabel('point_unit', historyPoint.point_unit)}</Tag>
              <Tag>{dictLabel('curve_point_type', historyPoint.point_type)}</Tag>
              <Tag color="default">{historyData.length} 条</Tag>
            </Space>
          ) : '利率历史'
        }
        placement="right"
        width={880}
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        destroyOnClose
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => historyPoint && loadHistory(historyPoint.curve_code, historyPoint.tenor)}>
              刷新
            </Button>
            <Button icon={<ImportOutlined />} onClick={openHistoryBatch}>批量导入</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openHistoryCreate}>新增日期</Button>
          </Space>
        }
      >
        {/* 统计卡片 */}
        <Row gutter={12} style={{ marginBottom: 12 }}>
          <Col span={5}>
            <Card size="small" bodyStyle={{ padding: 12 }}>
              <Statistic title="记录数" value={historyStats.count} suffix="条" valueStyle={{ fontSize: 20 }} />
            </Card>
          </Col>
          <Col span={5}>
            <Card size="small" bodyStyle={{ padding: 12 }}>
              <Statistic title="最新日期" value={historyStats.latest} valueStyle={{ fontSize: 14 }} />
            </Card>
          </Col>
          <Col span={5}>
            <Card size="small" bodyStyle={{ padding: 12 }}>
              <Statistic title="最新利率" value={historyStats.latest === '-' ? '-' : historyData[0]?.rate_value?.toFixed(4)} valueStyle={{ fontSize: 14, color: '#1677ff' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small" bodyStyle={{ padding: 12 }}>
              <Statistic title="均值" value={historyStats.avg ? historyStats.avg.toFixed(4) : 0} valueStyle={{ fontSize: 14 }} />
            </Card>
          </Col>
          <Col span={5}>
            <Card size="small" bodyStyle={{ padding: 12 }}>
              <Statistic
                title="区间变动"
                value={historyStats.change ? (historyStats.change > 0 ? `+${historyStats.change.toFixed(2)}` : historyStats.change.toFixed(2)) : 0}
                precision={2}
                valueStyle={{
                  fontSize: 14,
                  color: historyStats.change > 0 ? '#cf1322' : historyStats.change < 0 ? '#3f8600' : '#666',
                }}
              />
            </Card>
          </Col>
        </Row>

        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="利率按日期维护"
          description={
            <span>
              每个曲线点对应一条利率历史（按交易日 <b>trade_date</b> 维护）。
              <b>批量导入</b>支持 <code>YYYY-MM-DD,利率</code> 格式多行文本，已存在日期会更新。
              系统会自动记录调整时间与操作人，便于审计追溯。
            </span>
          }
        />

        <Table
          rowKey="id"
          size="small"
          loading={historyLoading}
          dataSource={historyData}
          columns={historyColumns}
          pagination={{ pageSize: 10, size: 'small' }}
          scroll={{ x: 700 }}
          summary={(rows: any[]) => {
            if (!rows.length) return null
            const values = rows.map(r => r.rate_value)
            return (
              <Table.Summary fixed>
                <Table.Summary.Row>
                  <Table.Summary.Cell index={0}><b>统计</b></Table.Summary.Cell>
                  <Table.Summary.Cell index={1}>
                    <span style={{ color: '#1677ff' }}>
                      min {Math.min(...values).toFixed(4)} / max {Math.max(...values).toFixed(4)}
                    </span>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={2} colSpan={5}>
                    均值 {(values.reduce((a, b) => a + b, 0) / values.length).toFixed(4)} · 中位数 {values.sort((a, b) => a - b)[Math.floor(values.length / 2)].toFixed(4)}
                  </Table.Summary.Cell>
                </Table.Summary.Row>
              </Table.Summary>
            )
          }}
        />
      </Drawer>

      {/* ===== 单条新增/编辑历史利率 ===== */}
      <Modal
        title={historyEditing ? `编辑利率：${historyPoint?.curve_code} ${historyPoint?.tenor} ${historyEditing.trade_date}` : `新增日期利率：${historyPoint?.curve_code} ${historyPoint?.tenor}`}
        open={historyEditOpen}
        onCancel={() => setHistoryEditOpen(false)}
        onOk={submitHistory}
        destroyOnClose
      >
        <Form form={historyForm} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="交易日" name="trade_date" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} disabled={!!historyEditing} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="利率值" name="rate_value" rules={[{ required: true }]}>
                <InputNumber step={0.0001} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="数据版本" name="source_version">
                <Select
                  options={[
                    { value: 'official', label: 'official（正式）' },
                    { value: 'raw', label: 'raw（原始）' },
                    { value: 'adjusted', label: 'adjusted（调整后）' },
                    { value: 'build_ns', label: 'build_ns（NS拟合）' },
                    { value: 'build_nss', label: 'build_nss（NSS拟合）' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="备注" name="remark">
                <Input.TextArea rows={2} placeholder="数据来源 / 调整原因等" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* ===== 批量导入历史利率 ===== */}
      <Modal
        title={`批量导入历史利率：${historyPoint?.curve_code} ${historyPoint?.tenor}`}
        open={historyBatchOpen}
        onCancel={() => setHistoryBatchOpen(false)}
        onOk={submitHistoryBatch}
        width={680}
        destroyOnClose
      >
        <Divider plain>格式说明</Divider>
        <div style={{ color: '#666', marginBottom: 12, fontSize: 13 }}>
          • 每行一个日期的利率值：<code>YYYY-MM-DD,利率</code><br />
          • 日期支持多种格式：YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD<br />
          • 已存在的日期会<b>自动更新</b>，不存在的日期会<b>新增</b>
        </div>
        <Input.TextArea
          rows={12}
          value={historyBatchText}
          onChange={e => setHistoryBatchText(e.target.value)}
          placeholder={`2026-08-10,2.40\n2026-08-11,2.42\n2026-08-12,2.43\n2026-08-13,2.44\n2026/08/14,2.44\n20260815,2.45\n2026-08-16,2.45\n2026-08-17,2.45`}
          style={{ fontFamily: 'monospace' }}
        />
      </Modal>

      {/* ===== 业务规则采集 Modal ===== */}
      <Modal
        title={<Space><ThunderboltOutlined style={{ color: '#fa8c16' }} /><span>按业务规则采集历史数据</span></Space>}
        open={collectModalOpen}
        onCancel={() => !collecting && setCollectModalOpen(false)}
        onOk={submitCollect}
        confirmLoading={collecting}
        okText={collecting ? '采集中...' : '开始采集'}
        cancelText="取消"
        width={780}
        destroyOnClose
      >
        <Tabs
          defaultActiveKey="form"
          items={[
            {
              key: 'form',
              label: '📋 采集配置',
              children: (
                <Form form={collectForm} layout="vertical" style={{ marginTop: 16 }}>
                  <Alert
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message="业务规则采集"
                    description={
                      <span>
                        系统会根据每条曲线的<b>采集频率</b>（daily / monthly）、<b>波动率</b>、<b>趋势</b>、<b>利差关系</b>等业务规则，
                        生成符合实际市场特征的历史数据。基础曲线（国债/国开/信用/Shibor/Repo/NCD）每日采集，LPR 每月 20 日采集，派生曲线（信用利差/流动性利差）由基础曲线实时计算。
                      </span>
                    }
                  />
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item label="开始日期" name="start_date" rules={[{ required: true }]}>
                        <DatePicker style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="结束日期" name="end_date" rules={[{ required: true }]}>
                        <DatePicker style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="数据源标识" name="source_code" tooltip="用于追溯采集来源">
                        <Input prefix="📡" />
                      </Form.Item>
                    </Col>
                    <Col span={24}>
                      <Form.Item label="采集曲线（不选则全部）" name="curve_codes">
                        <Select
                          mode="multiple"
                          allowClear
                          placeholder="默认采集全部 11 条曲线"
                          options={collectRules.map((r: any) => ({
                            value: r.curve_code,
                            label: `${r.curve_code} (${r.frequency}, ${r.current_value || '派生'})`,
                          }))}
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  {collectResult && (
                    <Alert
                      type="success"
                      showIcon
                      style={{ marginTop: 12 }}
                      message={`采集完成：${collectResult.total_records} 条记录，耗时 ${collectResult.duration_ms}ms`}
                      description={
                        <div>
                          {collectResult.curves?.map((c: any) => (
                            <Tag key={c.code} color="cyan" style={{ margin: '2px' }}>
                              {c.code}: {c.count} 条
                            </Tag>
                          ))}
                        </div>
                      }
                    />
                  )}
                </Form>
              ),
            },
            {
              key: 'rules',
              label: `📚 业务规则（${collectRules.length}）`,
              children: (
                <div style={{ marginTop: 16 }}>
                  <Table
                    rowKey="curve_code"
                    size="small"
                    dataSource={collectRules}
                    pagination={false}
                    columns={[
                      { title: '曲线编码', dataIndex: 'curve_code', width: 200 },
                      {
                        title: '类别', dataIndex: 'category', width: 100,
                        render: (v: string) => <Tag color={v === 'base' ? 'blue' : v === 'derived' ? 'purple' : 'cyan'}>{v}</Tag>,
                      },
                      {
                        title: '频率', dataIndex: 'frequency', width: 80,
                        render: (v: string) => <Tag color={v === 'daily' ? 'green' : 'orange'}>{v}</Tag>,
                      },
                      {
                        title: '当前值', dataIndex: 'current_value', width: 100,
                        render: (v: number, r: any) =>
                          v != null ? `${v.toFixed(2)}%` : <span style={{ color: '#999' }}>{r.derived_from || '-'}</span>,
                      },
                      { title: '波动率 (bp)', dataIndex: 'volatility_bp', width: 100,
                        render: (v: number) => v != null ? v.toFixed(1) : '-' },
                      { title: '年趋势 (bp)', dataIndex: 'year_trend_bp', width: 100,
                        render: (v: number) => v != null ? (
                          <span style={{ color: v < 0 ? '#3f8600' : v > 0 ? '#cf1322' : '#666' }}>
                            {v > 0 ? '+' : ''}{v}
                          </span>
                        ) : '-' },
                    ]}
                  />
                </div>
              ),
            },
            {
              key: 'logs',
              label: `📜 采集日志（${collectLogs.length}）`,
              children: (
                <div style={{ marginTop: 16 }}>
                  <Table
                    rowKey="id"
                    size="small"
                    dataSource={collectLogs}
                    pagination={false}
                    columns={[
                      { title: 'ID', dataIndex: 'id', width: 60 },
                      { title: '开始时间', dataIndex: 'start_time', width: 180,
                        render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
                      {
                        title: '状态', dataIndex: 'status', width: 100,
                        render: (v: string) => (
                          <Tag color={v === 'success' ? 'green' : v === 'failed' ? 'red' : 'blue'}>
                            {v}
                          </Tag>
                        ),
                      },
                      { title: '记录数', dataIndex: 'record_count', width: 100 },
                      { title: '耗时 (ms)', dataIndex: 'duration_ms', width: 100 },
                      {
                        title: '错误', dataIndex: 'error_msg', ellipsis: true,
                        render: (v: string) => v ? <span style={{ color: '#cf1322' }}>{v}</span> : '-',
                      },
                    ]}
                  />
                </div>
              ),
            },
          ]}
        />
      </Modal>
    </div>
  )
}