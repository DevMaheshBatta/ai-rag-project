import { useState } from 'react'
import Sidebar     from './components/Sidebar'
import QueryPage   from './components/QueryPage'
import DocumentsPage from './components/DocumentsPage'
import EvalPage    from './components/EvalPage'
import TracesPage  from './components/TracesPage'
import { useHealth } from './hooks/useHealth'

const PAGES = {
  query:     QueryPage,
  documents: DocumentsPage,
  eval:      EvalPage,
  traces:    TracesPage,
}

export default function App() {
  const [page, setPage] = useState('query')
  const { health, refresh } = useHealth()

  const Page = PAGES[page] ?? QueryPage

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar page={page} setPage={setPage} health={health}/>
      <main style={{
        flex: 1, overflow: 'auto',
        background: 'var(--bg)',
        borderLeft: '0.5px solid var(--border)',
      }}>
        <Page health={health} onUpload={refresh}/>
      </main>
    </div>
  )
}
