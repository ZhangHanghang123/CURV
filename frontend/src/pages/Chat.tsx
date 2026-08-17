import { useState } from 'react'
import { Input, Button, Card, Avatar, Tag, message } from 'antd'
import { RobotOutlined, UserOutlined } from '@ant-design/icons'
import { agentApi } from '../api'

interface Message {
  role: 'user' | 'bot'
  text: string
  intent?: string
  charts?: any[]
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', text: '🤖 您好！我是 CURV 智能助手。可以问我：\n\n• 「10年国债近一年走势」\n• 「信用利差最近如何」\n• 「今天曲线数据有什么异常」\n• 「利率上行100bp，EVE变多少」\n• 「拟合10年国债曲线」' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const send = async () => {
    if (!input.trim()) return
    const userMsg = { role: 'user' as const, text: input }
    setMessages(m => [...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const res: any = await agentApi.chat({ query: input })
      setMessages(m => [...m, {
        role: 'bot',
        text: res.data.text,
        intent: res.data.intent,
        charts: res.data.charts,
      }])
    } catch (e: any) {
      message.error(e.response?.data?.detail || '对话失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>🤖 智能问数（CURVE_CHAT）</div>
      <Card style={{ minHeight: 500, background: '#fafafa' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {messages.map((m, i) => (
            <div key={i} style={{
              display: 'flex', gap: 12, marginBottom: 16,
              flexDirection: m.role === 'user' ? 'row-reverse' : 'row',
            }}>
              <Avatar icon={m.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                      style={{ background: m.role === 'user' ? '#722ed1' : '#1677ff', flexShrink: 0 }} />
              <div style={{
                background: m.role === 'user' ? '#722ed1' : '#fff',
                color: m.role === 'user' ? '#fff' : '#262626',
                padding: '12px 16px', borderRadius: 8, maxWidth: '80%',
                border: m.role === 'bot' ? '1px solid #f0f0f0' : 'none',
                whiteSpace: 'pre-wrap', lineHeight: 1.6,
              }}>
                <div>{m.text}</div>
                {m.intent && <Tag style={{ marginTop: 8 }}>意图: {m.intent}</Tag>}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', gap: 12 }}>
              <Avatar icon={<RobotOutlined />} style={{ background: '#1677ff' }} />
              <div style={{ background: '#fff', padding: '12px 16px', borderRadius: 8, border: '1px solid #f0f0f0' }}>
                🤔 思考中...
              </div>
            </div>
          )}
        </div>
      </Card>
      <Card style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <Input.TextArea
            value={input}
            onChange={e => setInput(e.target.value)}
            onPressEnter={e => { if (!e.shiftKey) { e.preventDefault(); send() } }}
            placeholder="向曲线平台提问）..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={loading}
          />
          <Button type="primary" onClick={send} loading={loading}
                  style={{ background: '#722ed1', borderColor: '#722ed1', height: 'auto' }}>发送</Button>
        </div>
      </Card>
    </div>
  )
}