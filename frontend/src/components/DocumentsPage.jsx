import { useState, useEffect, useRef, useCallback } from 'react'
import { Upload, Trash2, FileText, AlertCircle } from 'lucide-react'
import { uploadPDF, getDocuments, deleteDocument } from '../api'

function DropZone({ onFile, uploading }) {
  const [drag, setDrag] = useState(false)
  const ref = useRef()

  const onDrop = (e) => {
    e.preventDefault(); setDrag(false)
    const f = e.dataTransfer.files[0]
    if (f) onFile(f)
  }

  return (
    <div
      onDragOver={e => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      onClick={() => ref.current?.click()}
      style={{
        border: `1.5px dashed ${drag ? 'var(--green)' : 'var(--border-2)'}`,
        borderRadius: 'var(--rl)',
        padding: '40px 24px',
        textAlign: 'center',
        cursor: uploading ? 'wait' : 'pointer',
        background: drag ? 'var(--green-bg)' : 'var(--bg)',
        transition: 'all 0.15s',
      }}
    >
      <input ref={ref} type="file" accept=".pdf" style={{ display: 'none' }}
        onChange={e => { if (e.target.files[0]) onFile(e.target.files[0]) }}/>
      <Upload size={22} style={{ color: drag ? 'var(--green)' : 'var(--text-3)', marginBottom: 10 }}/>
      <div style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 4 }}>
        {uploading ? 'Indexing…' : 'Drop a PDF here or click to browse'}
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
        Chunks into ChromaDB + Elasticsearch · BM25 + vector indexed
      </div>
    </div>
  )
}

function DocRow({ doc, onDelete }) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async () => {
    if (!confirm(`Remove "${doc.filename}"?`)) return
    setDeleting(true)
    try { await onDelete(doc.id) } finally { setDeleting(false) }
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '12px 14px',
      border: '0.5px solid var(--border)',
      borderRadius: 'var(--r)',
      background: 'var(--bg)',
    }}>
      <FileText size={16} style={{ color: 'var(--blue)', flexShrink: 0 }}/>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {doc.filename}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>
          {doc.pages ?? '?'} pages · {doc.chunks ?? '?'} chunks
          {doc.uploaded_at && ` · ${new Date(doc.uploaded_at).toLocaleDateString()}`}
        </div>
      </div>
      <button
        onClick={handleDelete}
        disabled={deleting}
        style={{
          padding: '5px 8px', borderRadius: 'var(--r)',
          color: deleting ? 'var(--text-3)' : 'var(--red)',
          background: 'transparent',
          border: '0.5px solid transparent',
          transition: 'all 0.12s',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--red-bg)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
      >
        <Trash2 size={14}/>
      </button>
    </div>
  )
}

export default function DocumentsPage({ onUpload }) {
  const [docs,      setDocs]      = useState([])
  const [uploading, setUploading] = useState(false)
  const [msg,       setMsg]       = useState(null)
  const [loading,   setLoading]   = useState(true)

  const loadDocs = useCallback(async () => {
    try {
      const data = await getDocuments()
      // API returns array or { documents: [] } depending on your router
      setDocs(Array.isArray(data) ? data : data.documents ?? [])
    } catch (e) {
      setMsg({ ok: false, text: `Could not load documents: ${e.message}` })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadDocs() }, [loadDocs])

  const handleFile = async (file) => {
    if (!file.name.endsWith('.pdf')) {
      setMsg({ ok: false, text: 'Only PDF files are supported.' }); return
    }
    setUploading(true); setMsg(null)
    try {
      const res = await uploadPDF(file)
      setMsg({ ok: true, text: `"${res.filename ?? file.name}" indexed — ${res.pages ?? '?'} pages, ${res.chunks ?? '?'} chunks` })
      await loadDocs()
      onUpload?.()
    } catch (e) {
      setMsg({ ok: false, text: e.message })
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id) => {
    await deleteDocument(id)
    await loadDocs()
    onUpload?.()
  }

  return (
    <div style={{ padding: '28px', maxWidth: 680, display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>Documents</h1>
        <p style={{ fontSize: 13, color: 'var(--text-3)' }}>
          Upload PDFs — each is chunked, embedded, and indexed into both ChromaDB and Elasticsearch.
        </p>
      </div>

      <DropZone onFile={handleFile} uploading={uploading}/>

      {msg && (
        <div className="fade-in" style={{
          padding: '10px 14px', borderRadius: 'var(--r)', fontSize: 13,
          background: msg.ok ? 'var(--green-bg)' : 'var(--red-bg)',
          color:      msg.ok ? 'var(--green-text)' : 'var(--red)',
          border:     `0.5px solid ${msg.ok ? 'var(--green)' : 'var(--red-border)'}`,
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          {!msg.ok && <AlertCircle size={14}/>}
          {msg.text}
        </div>
      )}

      <div>
        <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.05em' }}>
          Indexed documents · {docs.length}
        </div>
        {loading ? (
          <div style={{ fontSize: 13, color: 'var(--text-3)' }}>Loading…</div>
        ) : docs.length === 0 ? (
          <div style={{
            padding: '20px', textAlign: 'center', border: '0.5px solid var(--border)',
            borderRadius: 'var(--r)', color: 'var(--text-3)', fontSize: 13,
          }}>
            No documents indexed yet. Upload a PDF above.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {docs.map(d => <DocRow key={d.id ?? d.filename} doc={d} onDelete={handleDelete}/>)}
          </div>
        )}
      </div>
    </div>
  )
}
