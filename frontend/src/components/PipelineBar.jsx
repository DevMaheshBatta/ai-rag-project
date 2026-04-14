const STEPS = [
  { key: 'vector',  label: 'Vector',  bg: 'var(--blue-bg)',   color: 'var(--blue-text)' },
  { key: 'bm25',    label: 'BM25',    bg: 'var(--green-bg)',  color: 'var(--green-text)' },
  { key: 'rrf',     label: 'RRF',     bg: 'var(--purple-bg)', color: 'var(--purple-text)' },
  { key: 'rerank',  label: 'Rerank',  bg: 'var(--amber-bg)',  color: 'var(--amber-text)' },
  { key: 'llm',     label: 'LLM',     bg: 'var(--bg-muted)',  color: 'var(--text-2)' },
]

export default function PipelineBar({ latencies }) {
  if (!latencies) return null
  const total = latencies.total ?? 0

  return (
    <div style={{
      border: '0.5px solid var(--border)',
      borderRadius: 'var(--r)',
      background: 'var(--bg-subtle)',
      padding: '14px 16px',
    }}>
      {/* Step pills */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
        {STEPS.map((s, i) => {
          const ms = latencies[s.key] ?? 0
          return (
            <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
                <span style={{
                  fontSize: 11, fontWeight: 500, padding: '3px 10px',
                  borderRadius: 20, background: s.bg, color: s.color,
                }}>
                  {s.label}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{ms}ms</span>
              </div>
              {i < STEPS.length - 1 && (
                <span style={{ color: 'var(--text-3)', fontSize: 14, marginBottom: 14 }}>›</span>
              )}
            </div>
          )
        })}
        <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
          <div style={{ fontSize: 12, color: 'var(--text-3)' }}>Total</div>
          <div style={{ fontSize: 15, fontWeight: 500 }}>{total}ms</div>
        </div>
      </div>

      {/* Proportional bar */}
      <div style={{ display: 'flex', height: 4, borderRadius: 4, overflow: 'hidden', gap: 1 }}>
        {STEPS.map(s => {
          const ms = latencies[s.key] ?? 0
          const pct = total > 0 ? (ms / total) * 100 : 0
          return (
            <div key={s.key} title={`${s.label}: ${ms}ms`}
              style={{ width: `${pct}%`, background: s.color, opacity: 0.7, minWidth: pct > 0 ? 2 : 0 }}/>
          )
        })}
      </div>
    </div>
  )
}
