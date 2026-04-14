import { useState } from 'react'
import { traceHistory } from './QueryPage'
import { Clock, Coins, Layers } from 'lucide-react'

const STEP_COLORS = {
  vector: 'var(--blue)',
  bm25:   'var(--green)',
  rrf:    'var(--purple)',
  rerank: 'var(--amber)',
  llm:    'var(--text-3)',
}

function TraceRow({ item, expanded, onToggle }) {
  const t = item.trace
  return (
    <div style={{
      border: '0.5px solid var(--border)',
      borderRadius: 'var(--rl)',
      background: 'var(--bg)',
      overflow: 'hidden',
      transition: 'border-color 0.12s',
    }}>
      {/* Summary row */}
      <button
        onClick={onToggle}
        style={{
          width: '100%', display: 'flex', alignItems: 'center',
          gap: 12, padding: '13px 16px', background: 'transparent',
          textAlign: 'left',
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: 13, fontWeight: 500, color: 'var(--text)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {item.query}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 3, fontFamily: 'monospace' }}>
            {t?.run_id?.slice(0, 8)}
          </div>
        </div>

        <div style={{ display: 'flex', gap: 14, flexShrink: 0 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-2)' }}>
            <Clock size={11}/> {t?.latencies_ms?.total ?? '?'}ms
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-2)' }}>
            <Layers size={11}/> {t?.tokens?.total?.toLocaleString() ?? '?'}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-2)' }}>
            <Coins size={11}/> ${(t?.cost_usd ?? 0).toFixed(6)}
          </span>
        </div>

        <span style={{ color: 'var(--text-3)', fontSize: 14, transform: expanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' }}>›</span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div style={{ borderTop: '0.5px solid var(--border)', padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Step latencies */}
          {t?.latencies_ms && (
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '.05em' }}>Latency breakdown</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                {Object.entries(t.latencies_ms).filter(([k]) => k !== 'total').map(([step, ms]) => {
                  const pct = t.latencies_ms.total > 0 ? (ms / t.latencies_ms.total) * 100 : 0
                  return (
                    <div key={step} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: 11, color: 'var(--text-2)', width: 54, flexShrink: 0 }}>{step}</span>
                      <div style={{ flex: 1, height: 4, background: 'var(--bg-muted)', borderRadius: 2 }}>
                        <div style={{ height: 4, borderRadius: 2, width: `${pct}%`, background: STEP_COLORS[step] ?? 'var(--text-3)' }}/>
                      </div>
                      <span style={{ fontSize: 11, color: 'var(--text-3)', width: 42, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{ms}ms</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Answer preview */}
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '.05em' }}>Answer preview</div>
            <div style={{
              fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6,
              display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden',
            }}>
              {item.answer}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function TracesPage() {
  const [expanded, setExpanded] = useState(null)
  const traces = traceHistory

  const toggle = (i) => setExpanded(expanded === i ? null : i)

  return (
    <div style={{ padding: '28px', maxWidth: 820, display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>Traces</h1>
        <p style={{ fontSize: 13, color: 'var(--text-3)' }}>
          Per-request latency, token usage, and cost for every query this session.
        </p>
      </div>

      {traces.length === 0 ? (
        <div style={{
          padding: '40px', textAlign: 'center',
          border: '0.5px solid var(--border)', borderRadius: 'var(--rl)',
          background: 'var(--bg)', color: 'var(--text-3)', fontSize: 13,
        }}>
          No traces yet. Ask a question to see observability data here.
        </div>
      ) : (
        <>
          {/* Session summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: 8 }}>
            {[
              { val: traces.length,                                                               label: 'Queries' },
              { val: `${Math.round(traces.reduce((a, t) => a + (t.trace?.latencies_ms?.total ?? 0), 0) / traces.length)}ms`, label: 'Avg latency' },
              { val: traces.reduce((a, t) => a + (t.trace?.tokens?.total ?? 0), 0).toLocaleString(), label: 'Total tokens' },
              { val: `$${traces.reduce((a, t) => a + (t.trace?.cost_usd ?? 0), 0).toFixed(5)}`,  label: 'Total cost' },
            ].map(m => (
              <div key={m.label} style={{ background: 'var(--bg-subtle)', borderRadius: 'var(--r)', padding: '10px 14px' }}>
                <div style={{ fontSize: 17, fontWeight: 500, color: 'var(--text)', fontVariantNumeric: 'tabular-nums' }}>{m.val}</div>
                <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>{m.label}</div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {traces.map((t, i) => (
              <TraceRow key={i} item={t} expanded={expanded === i} onToggle={() => toggle(i)}/>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
