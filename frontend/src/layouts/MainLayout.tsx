import { Layout, Menu, theme, Avatar, Dropdown } from 'antd'
import {
  DashboardOutlined, DatabaseOutlined, LineChartOutlined,
  ToolOutlined, AreaChartOutlined, CalculatorOutlined,
  DollarOutlined, FileTextOutlined, RobotOutlined,
  BookOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '总览看板' },
  { key: 'data', icon: <DatabaseOutlined />, label: '数据中心', children: [
    { key: '/data-sources', label: '数据源' },
    { key: '/curves', label: '曲线定义' },
  ]},
  { key: 'build', icon: <ToolOutlined />, label: '曲线构建', children: [
    { key: '/build/fit', label: '曲线拟合' },
    { key: '/build/interpolate', label: '插值' },
  ]},
  { key: 'analysis', icon: <AreaChartOutlined />, label: '走势分析', children: [
    { key: '/analysis/trend', label: '时序分析' },
    { key: '/analysis/spread', label: '利差形态' },
  ]},
  { key: 'risk', icon: <CalculatorOutlined />, label: '风险计量', children: [
    { key: '/risk/krd', label: '关键利率久期' },
    { key: '/risk/scenario', label: '情景模拟' },
  ]},
  { key: 'app', icon: <DollarOutlined />, label: '业务应用', children: [
    { key: '/app/ftp', label: 'FTP 定价' },
    { key: '/app/valuation', label: '估值核算' },
    { key: '/app/regulatory', label: '监管报送' },
  ]},
  { key: '/chat', icon: <RobotOutlined />, label: '智能问数' },
  { key: '/dict', icon: <BookOutlined />, label: '字典管理' },
]

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const { token: { colorBgContainer } } = theme.useToken()

  const userStr = localStorage.getItem('user')
  const user = userStr ? JSON.parse(userStr) : { real_name: '管理员', username: 'admin' }

  const handleMenu = (e: any) => {
    if (e.key.startsWith('/')) navigate(e.key)
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="dark" width={220}>
        <div style={{ height: 56, display: 'flex', alignItems: 'center', justifyContent: 'center',
                     color: '#fff', fontSize: 16, fontWeight: 700, borderBottom: '1px solid #1f1f1f' }}>
          {collapsed ? '📈' : '📈 CURV 平台'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenu}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex',
                         alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f0f0f0' }}>
          <div style={{ fontSize: 16, fontWeight: 600 }}>
            📈 收益率曲线管理与建模分析平台
          </div>
          <Dropdown menu={{
            items: [
              { key: 'logout', label: '退出登录', onClick: () => {
                localStorage.removeItem('token')
                localStorage.removeItem('user')
                window.location.href = '/curv/login'
              }}
            ]
          }}>
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar style={{ background: '#722ed1' }}>{user.real_name?.[0] || 'A'}</Avatar>
              <span>{user.real_name || user.username}</span>
            </div>
          </Dropdown>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: colorBgContainer, borderRadius: 8, minHeight: 'calc(100vh - 100px)' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}