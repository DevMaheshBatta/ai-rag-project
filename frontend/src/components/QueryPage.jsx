import { useState, useRef, useCallback } from 'react'
import { Send } from 'lucide-react'
import { askQuestion } from '../api'
import PipelineBar from './PipelineBar'
import SourceCard from './SourceCard'
import MetricsRow from './MetricsRow'

// Render answer text, turning [1] [2] into inline superscript badges
function AnswerText({ text }) {
  if (!text) return null
  const parts = text.split(/(\[\d+\])/g)
  return (
    <p style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text)' }}>
      {parts.map((p, i) => {
        const m = p.match(/^\[(\d+)\]$/)
        if (m) return (
          <sup key={i} style={{
            display: 'inline-block', fontSize: 10, padding: '1px 5px',
            background: 'var(--blue-bg)', color: 'var(--blue-text)',
            borderRadius: 4, margin: '0 1px', lineHeight: 1.6, verticalAlign: 'super',
            fontWeight: 500,
          }}>{m[1]}</sup>
        )
        return <span key={i}>{p}</span>
      })}
    </p>
  )
}

function LoadingSteps() {
  const steps = ['Vector search', 'BM25 keyword search', 'RRF fusion', 'Cohere reranking', 'LLM generation']
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 4 }}>Running pipeline…</div>
      {steps.map((s, i) => (
        <div key={s} style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '8px 12px',
          border: '0.5px solid var(--border)',
          borderRadius: 'var(--r)',
          background: 'var(--bg)',
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
            background: 'var(--green)',
            animation: `pulse-dot 0.9s ease-in-out ${i * 0.12}s infinite`,
          }}/>
          <span style={{ fontSize: 12, color: 'var(--text-2)' }}>{s}</span>
        </div>
      ))}
    </div>
  )
}

// Store trace history in module-level so TracesPage can read it
export const traceHistory = []

export default function QueryPage({ health }) {
  const [question, setQuestion] = useState('')
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState(null)
  const inputRef = useRef()

  const ask = useCallback(async () => {
    const q = question.trim()
    if (!q || loading) return
    if (!health || health.indexed_docs === 0) {
      setError('No documents indexed. Upload a PDF on the Documents page first.')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await askQuestion(q)
      setResult(data)
      // Push to shared trace history for TracesPage
      traceHistory.unshift({ query: q, ...data })
      if (traceHistory.length > 50) traceHistory.pop()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [question, loading, health])

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask() }
  }

  return (
    <div style={{ padding: '28px 28px', maxWidth: 820, display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Header */}
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>Ask a question</h1>
        <p style={{ fontSize: 13, color: 'var(--text-3)' }}>
          Queries run through: Vector → BM25 → RRF → Rerank → LLM
        </p>
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          ref={inputRef}
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={onKey}
          disabled={loading}
          placeholder="What are the key findings in this document?"
          style={{
            flex: 1, padding: '11px 14px',
            border: '0.5px solid var(--border-2)',
            borderRadius: 'var(--r)',
            background: 'var(--bg)', color: 'var(--text)',
            fontSize: 14,
            transition: 'border-color 0.15s',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--green)'}
          onBlur={e  => e.target.style.borderColor = 'var(--border-2)'}
        />
        <button
          onClick={ask}
          disabled={loading || !question.trim()}
          style={{
            padding: '11px 18px',
            borderRadius: 'var(--r)',
            background: loading || !question.trim() ? 'var(--bg-muted)' : 'var(--text)',
            color: loading || !question.trim() ? 'var(--text-3)' : 'var(--bg)',
            fontWeight: 500, display: 'flex', alignItems: 'center', gap: 6,
            transition: 'all 0.15s',
          }}
        >
          <Send size={14}/> {loading ? 'Thinking…' : 'Ask'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="fade-in" style={{
          padding: '10px 14px', borderRadius: 'var(--r)',
          background: 'var(--red-bg)', color: 'var(--red)',
          border: '0.5px solid var(--red-border)', fontSize: 13,
        }}>
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && <div className="fade-in"><LoadingSteps/></div>}

      {/* Results */}
      {result && !loading && (
        <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Pipeline latencies */}
          <PipelineBar latencies={result.trace?.latencies_ms}/>

          {/* Answer */}
          <div style={{
            border: '0.5px solid var(--border)',
            borderRadius: 'var(--rl)',
            padding: '18px 20px',
            background: 'var(--bg)',
          }}>
            <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '.05em' }}>
              Answer
            </div>
            <AnswerText text={result.answer}/>
          </div>

          {/* Sources */}
          {result.sources?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.05em' }}>
                Sources · reranked top {result.sources.length}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))', gap: 8 }}>
                {result.sources.map(s => <SourceCard key={s.index} source={s}/>)}
              </div>
            </div>
          )}

          {/* Observability */}
          {result.trace && (
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.05em' }}>
                Observability · run {result.trace.run_id?.slice(0, 8)}
              </div>
              <MetricsRow trace={result.trace}/>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
