import { MessageSquare, FileText, BarChart2, FlaskConical } from 'lucide-react'

const nav = [
  { id: 'query',     label: 'Query',     Icon: MessageSquare, dot: 'var(--green)' },
  { id: 'documents', label: 'Documents', Icon: FileText,       dot: 'var(--blue)' },
  { id: 'eval',      label: 'Evaluation',Icon: FlaskConical,   dot: 'var(--purple)' },
  { id: 'traces',    label: 'Traces',    Icon: BarChart2,      dot: 'var(--amber)' },
]

export default function Sidebar({ page, setPage, health }) {
  const online = health.status === 'ok'

  return (
    <aside style={{
      width: 220, flexShrink: 0,
      borderRight: '0.5px solid var(--border)',
      background: 'var(--bg-subtle)',
      display: 'flex', flexDirection: 'column',
      padding: '20px 12px',
    }}>
      {/* Logo */}
      <div style={{ padding: '0 8px 20px', borderBottom: '0.5px solid var(--border)', marginBottom: 12 }}>
        <div style={{ fontWeight: 600, fontSize: 15, letterSpacing: '-0.01em', marginBottom: 2 }}>
          RAG System
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-3)' }}>Production pipeline</div>
      </div>

      {/* Nav */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flex: 1 }}>
        {nav.map(({ id, label, Icon, dot }) => {
          const active = page === id
          return (
            <button
              key={id}
              onClick={() => setPage(id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 10px', borderRadius: 'var(--r)',
                background: active ? 'var(--bg)' : 'transparent',
                border: active ? '0.5px solid var(--border-2)' : '0.5px solid transparent',
                color: active ? 'var(--text)' : 'var(--text-2)',
                fontWeight: active ? 500 : 400,
                textAlign: 'left', width: '100%',
                transition: 'all 0.12s',
              }}
            >
              <span style={{
                width: 7, height: 7, borderRadius: '50%',
                background: active ? dot : 'var(--text-3)',
                flexShrink: 0, transition: 'background 0.12s',
              }}/>
              <Icon size={14} style={{ flexShrink: 0, opacity: active ? 1 : 0.6 }}/>
              <span style={{ fontSize: 13 }}>{label}</span>
            </button>
          )
        })}
      </div>

      {/* Status */}
      <div style={{
        padding: '12px 8px 0',
        borderTop: '0.5px solid var(--border)',
        display: 'flex', alignItems: 'center', gap: 7,
      }}>
        <span style={{
          width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
          background: online ? 'var(--green)' : '#E24B4A',
          animation: online ? 'pulse-dot 2s ease-in-out infinite' : 'none',
        }}/>
        <span style={{ fontSize: 11, color: 'var(--text-3)' }}>
          {online
            ? `${health.indexed_docs} doc${health.indexed_docs !== 1 ? 's' : ''} indexed`
            : 'Backend offline'}
        </span>
      </div>
    </aside>
  )
}
