import { useState } from 'react'
import { Form, Input, Button, Card, message, Typography } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api'

const { Title, Text } = Typography

// CURV 专属吉祥物：紫色渐变背景 + 牛头 + 头顶收益率曲线波纹
function CurvMascot({ size = 64 }: { size?: number }) {
  return (
    <div
      style={{
        width: size, height: size, borderRadius: '50%',
        background: 'linear-gradient(135deg, #b37feb, #722ed1, #531dab)',
        boxShadow: '0 4px 16px rgba(114, 46, 209, 0.4)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        animation: 'curvPulse 2s ease-in-out infinite',
        transition: 'transform 0.15s',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.animation = 'none'; e.currentTarget.style.transform = 'scale(1.2)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.animation = 'curvPulse 2s ease-in-out infinite'; e.currentTarget.style.transform = 'scale(1)'; }}
    >
      <svg viewBox="0 0 64 64" width={size * 0.55} height={size * 0.55}>
        {/* 头顶收益率曲线波纹（CURV 主题特征） */}
        <path
          d="M6 18 Q14 8 22 14 T40 12 T58 18"
          fill="none" stroke="#FFF8E7" strokeWidth="2" strokeLinecap="round"
          style={{ animation: 'curvCurveWave 1.8s ease-in-out infinite' }}
        />
        {/* 牛头轮廓 */}
        <ellipse cx="32" cy="36" rx="20" ry="17" fill="#FFF8E7" stroke="#D4A574" strokeWidth="1.5" />
        {/* 左耳 */}
        <ellipse cx="13" cy="22" rx="5.5" ry="4.5" fill="#FFF8E7" stroke="#D4A574" strokeWidth="1.2" transform="rotate(-18, 13, 22)" />
        <ellipse cx="13" cy="22" rx="3" ry="2.5" fill="#FFE0C0" />
        {/* 右耳 */}
        <ellipse cx="51" cy="22" rx="5.5" ry="4.5" fill="#FFF8E7" stroke="#D4A574" strokeWidth="1.2" transform="rotate(18, 51, 22)" />
        <ellipse cx="51" cy="22" rx="3" ry="2.5" fill="#FFE0C0" />
        {/* 左牛角 */}
        <path d="M16 20 Q13 10 10 8" fill="none" stroke="#8B6914" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="10" cy="8" r="2.5" fill="#D4A017" />
        {/* 右牛角 */}
        <path d="M48 20 Q51 10 54 8" fill="none" stroke="#8B6914" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="54" cy="8" r="2.5" fill="#D4A017" />
        {/* 左眼 */}
        <ellipse cx="25" cy="31" rx="4.5" ry="5" fill="#fff" />
        <circle cx="26" cy="31" r="2.5" fill="#2c1810" />
        <circle cx="27" cy="30" r="1" fill="#fff" />
        {/* 右眼 */}
        <ellipse cx="39" cy="31" rx="4.5" ry="5" fill="#fff" />
        <circle cx="38" cy="31" r="2.5" fill="#2c1810" />
        <circle cx="39" cy="30" r="1" fill="#fff" />
        {/* 眼眶装饰（紫色高亮） */}
        <circle cx="25" cy="31" r="7" fill="none" stroke="#722ed1" strokeWidth="1.2" />
        <circle cx="39" cy="31" r="7" fill="none" stroke="#722ed1" strokeWidth="1.2" />
        {/* 鼻孔 */}
        <ellipse cx="29" cy="39" rx="2" ry="1.5" fill="#D4A574" />
        <ellipse cx="35" cy="39" rx="2" ry="1.5" fill="#D4A574" />
        {/* 嘴 */}
        <path d="M27 43 Q32 46 37 43" fill="none" stroke="#D4A574" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    </div>
  )
}

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const res: any = await authApi.login(values.username, values.password)
      const token = res.data?.access_token || res.data?.token || res.access_token
      if (token) {
        localStorage.setItem('token', token)
        localStorage.setItem('user', JSON.stringify(res.data?.user || {}))
        message.success('登录成功')
        navigate('/dashboard')
      } else {
        message.error('登录失败: ' + (res.message || '未获取到token'))
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || '用户名或密码错误'
      message.error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Card
        style={{
          width: 400,
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          borderRadius: 12,
        }}
        bordered={false}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ marginBottom: 16, display: 'inline-block' }}>
            <CurvMascot size={64} />
          </div>
          <Title level={3} style={{ margin: 0 }}>曲线经营智能分析平台</Title>
          <Text type="secondary">Curve Yield Intelligence Platform</Text>
        </div>

        <Form
          name="login"
          onFinish={handleLogin}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名: admin"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码: admin123"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ marginTop: 8 }}
            >
              登 录
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              默认账号: admin / admin123
            </Text>
          </div>
        </Form>
      </Card>
    </div>
  )
}
