import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, CheckCircle, XCircle, FlaskConical } from 'lucide-react'
import { getEvalResults } from '../api'

function ScoreGauge({ value, label, threshold = 0.7 }) {
  const pct    = Math.round(value * 100)
  const passed = value >= threshold
  const color  = passed ? 'var(--green)' : 'var(--red)'
  const bg     = passed ? 'var(--green-bg)' : 'var(--red-bg)'
  const textC  = passed ? 'var(--green-text)' : 'var(--red)'

  return (
    <div style={{
      border: '0.5px solid var(--border)',
      borderRadius: 'var(--rl)',
      padding: '20px 22px',
      background: 'var(--bg)',
      display: 'flex', flexDirection: 'column', gap: 14,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>{label}</span>
        <span style={{
          fontSize: 11, fontWeight: 500, padding: '3px 9px',
          borderRadius: 20, background: bg, color: textC,
          display: 'flex', alignItems: 'center', gap: 4,
        }}>
          {passed
            ? <CheckCircle size={11}/>
            : <XCircle size={11}/>}
          {passed ? 'Pass' : 'Fail'}
        </span>
      </div>

      {/* Score */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span style={{ fontSize: 36, fontWeight: 500, color: 'var(--text)', fontVariantNumeric: 'tabular-nums' }}>
          {value.toFixed(4)}
        </span>
        <span style={{ fontSize: 13, color: 'var(--text-3)' }}>/ 1.0</span>
      </div>

      {/* Progress bar */}
      <div style={{ height: 5, background: 'var(--bg-muted)', borderRadius: 3 }}>
        <div style={{
          height: 5, borderRadius: 3,
          width: `${pct}%`, background: color,
          transition: 'width 0.5s ease',
        }}/>
      </div>

      {/* Threshold marker (visual only) */}
      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
        Threshold: {threshold.toFixed(2)} · Score: {pct}%
      </div>
    </div>
  )
}

function CIStatus({ passed }) {
  return (
    <div style={{
      padding: '14px 18px', borderRadius: 'var(--r)',
      background: passed ? 'var(--green-bg)' : 'var(--red-bg)',
      border: `0.5px solid ${passed ? 'var(--green)' : 'var(--red-border)'}`,
      display: 'flex', alignItems: 'center', gap: 10,
    }}>
      {passed
        ? <CheckCircle size={16} style={{ color: 'var(--green)', flexShrink: 0 }}/>
        : <XCircle    size={16} style={{ color: 'var(--red)',   flexShrink: 0 }}/>}
      <div>
        <div style={{ fontSize: 13, fontWeight: 500, color: passed ? 'var(--green-text)' : 'var(--red)' }}>
          CI gate {passed ? 'would pass ✓' : 'would fail ✗'}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>
          GitHub Actions exits {passed ? '0' : '1'} — build {passed ? 'continues' : 'blocked'}
        </div>
      </div>
    </div>
  )
}

export default function EvalPage() {
  const [data,     setData]     = useState(null)
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const res = await getEvalResults()
      setData(res)
    } catch (e) {
      // 404 = no eval run yet — treat as "not run" rather than error
      if (e.message.includes('404') || e.message.includes('No eval')) {
        setData(null)
      } else {
        setError(e.message)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const threshold  = 0.70
  const allPassed  = data
    ? Object.values(data.scores).every(v => v >= threshold)
    : false

  return (
    <div style={{ padding: '28px', maxWidth: 700, display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>RAGAS Evaluation</h1>
          <p style={{ fontSize: 13, color: 'var(--text-3)' }}>
            Faithfulness + Answer Relevancy · Groq judge · threshold {threshold}
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '7px 12px', borderRadius: 'var(--r)',
            border: '0.5px solid var(--border-2)',
            background: 'var(--bg)', color: 'var(--text-2)', fontSize: 12,
          }}
        >
          <RefreshCw size={12} style={{ animation: loading ? 'spin 0.8s linear infinite' : 'none' }}/>
          Refresh
        </button>
      </div>

      {/* How to run */}
      <div style={{
        padding: '12px 16px', borderRadius: 'var(--r)',
        background: 'var(--bg-subtle)', border: '0.5px solid var(--border)',
        fontSize: 12, color: 'var(--text-2)', fontFamily: 'monospace',
        lineHeight: 1.6,
      }}>
        <span style={{ color: 'var(--text-3)', display: 'block', marginBottom: 4, fontFamily: 'inherit', fontWeight: 500 }}>
          Run evaluation locally:
        </span>
        python eval/run_ragas_eval.py --threshold {threshold}
      </div>

      {loading && (
        <div style={{ fontSize: 13, color: 'var(--text-3)' }}>Loading latest results…</div>
      )}

      {error && (
        <div style={{
          padding: '10px 14px', borderRadius: 'var(--r)', fontSize: 13,
          background: 'var(--red-bg)', color: 'var(--red)',
          border: '0.5px solid var(--red-border)',
        }}>
          {error}
        </div>
      )}

      {!loading && !data && !error && (
        <div style={{
          padding: '32px', textAlign: 'center',
          border: '0.5px solid var(--border)', borderRadius: 'var(--rl)',
          background: 'var(--bg)',
        }}>
          <FlaskConical size={28} style={{ color: 'var(--text-3)', marginBottom: 12 }}/>
          <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 6 }}>No evaluation results yet</div>
          <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
            Run <code style={{ background: 'var(--bg-muted)', padding: '1px 5px', borderRadius: 4 }}>
              python eval/run_ragas_eval.py
            </code> to generate results
          </div>
        </div>
      )}

      {data && !loading && (
        <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Meta */}
          <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
            Last run: {data.timestamp ? new Date(data.timestamp.replace(/(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6')).toLocaleString() : 'unknown'}
          </div>

          {/* CI Gate status */}
          <CIStatus passed={allPassed}/>

          {/* Score gauges */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
            {Object.entries(data.scores).map(([metric, score]) => (
              <ScoreGauge
                key={metric}
                value={score}
                label={metric.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                threshold={threshold}
              />
            ))}
          </div>

          {/* What this means */}
          <div style={{
            padding: '14px 16px', borderRadius: 'var(--r)',
            background: 'var(--bg-subtle)', border: '0.5px solid var(--border)',
            fontSize: 12, color: 'var(--text-2)', lineHeight: 1.7,
          }}>
            <span style={{ fontWeight: 500, color: 'var(--text)' }}>Faithfulness</span> — are claims in the answer grounded in the retrieved context?
            <br/>
            <span style={{ fontWeight: 500, color: 'var(--text)' }}>Answer Relevancy</span> — does the answer actually address the question asked?
          </div>
        </div>
      )}
    </div>
  )
}
