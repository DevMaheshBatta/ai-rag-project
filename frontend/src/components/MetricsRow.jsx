function Metric({ val, label }) {
  return (
    <div style={{
      background: 'var(--bg-subtle)',
      borderRadius: 'var(--r)',
      padding: '10px 14px',
    }}>
      <div style={{ fontSize: 17, fontWeight: 500, color: 'var(--text)', fontVariantNumeric: 'tabular-nums' }}>
        {val}
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>{label}</div>
    </div>
  )
}

export default function MetricsRow({ trace }) {
  if (!trace) return null
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
      gap: 8,
    }}>
      <Metric val={`${trace.latencies_ms?.total ?? 0}ms`}           label="Total latency" />
      <Metric val={(trace.tokens?.total ?? 0).toLocaleString()}      label="Total tokens" />
      <Metric val={`$${(trace.cost_usd ?? 0).toFixed(6)}`}          label="Est. cost" />
      <Metric val={(trace.tokens?.prompt ?? 0).toLocaleString()}     label="Prompt tokens" />
      <Metric val={(trace.tokens?.completion ?? 0).toLocaleString()} label="Completion tokens" />
    </div>
  )
}
