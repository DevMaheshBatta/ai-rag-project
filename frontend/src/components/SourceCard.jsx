export default function SourceCard({ source }) {
  const score = typeof source.rerank_score === 'number' ? source.rerank_score : null
  const pct   = score ? Math.round(score * 100) : 0
  const scoreColor = score > 0.8 ? 'var(--green)' : score > 0.5 ? 'var(--amber)' : 'var(--text-3)'
  const filename = source.source?.split('/').pop() ?? source.source ?? 'unknown'

  return (
    <div style={{
      border: '0.5px solid var(--border)',
      borderRadius: 'var(--r)',
      padding: '12px 14px',
      background: 'var(--bg)',
      display: 'flex', flexDirection: 'column', gap: 6,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{
          fontSize: 10, fontWeight: 500, padding: '2px 7px',
          borderRadius: 20, background: 'var(--bg-muted)', color: 'var(--text-3)',
        }}>
          [{source.index}]
        </span>
        {score !== null && (
          <span style={{ fontSize: 11, fontWeight: 500, color: scoreColor }}>
            {score.toFixed(3)}
          </span>
        )}
      </div>

      <div style={{
        fontSize: 12, fontWeight: 500, color: 'var(--text)',
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
      }}>
        {filename}
      </div>

      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
        Page {source.page}
      </div>

      {/* Rerank score bar */}
      {score !== null && (
        <div style={{ height: 3, background: 'var(--bg-muted)', borderRadius: 2 }}>
          <div style={{
            height: 3, borderRadius: 2,
            width: `${pct}%`,
            background: scoreColor,
            transition: 'width 0.4s ease',
          }}/>
        </div>
      )}

      <div style={{
        fontSize: 11, color: 'var(--text-3)', lineHeight: 1.5,
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {source.snippet}
      </div>
    </div>
  )
}
