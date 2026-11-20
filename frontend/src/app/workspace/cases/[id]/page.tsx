'use client'
import { useEffect, useState, useCallback, useRef } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { casesApi, documentsApi, ApiError } from '@/lib/api'
import type { Case, Document, CaseSummaryResponse } from '@/lib/types'
import { CASE_TYPE_LABELS, ROLE_LABELS, STATUS_LABELS } from '@/lib/types'
import { CaseIntelligenceChat } from '@/components/chat/CaseIntelligenceChat'
import { EvidenceGraph } from '@/components/graph/EvidenceGraph'

import styles from './page.module.css'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const MAX_SIZE_MB = 50

export default function CaseWorkspacePage() {
  const { id } = useParams<{ id: string }>()

  const [case_, setCase] = useState<Case | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Summary for the Case Snapshot panel
  const [summary, setSummary] = useState<CaseSummaryResponse | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  // Upload state
  const [dragging, setDragging] = useState(false)
  const [uploads, setUploads] = useState<UploadItem[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Sidebar collapse on mobile
  const [sidebarOpen, setSidebarOpen] = useState(false)
  // Right panel collapse
  const [snapshotOpen, setSnapshotOpen] = useState(true)
  // Centre panel tab: 'chat' | 'graph'
  const [centreTab, setCentreTab] = useState<'chat' | 'graph'>('chat')

  const loadCase = useCallback(async () => {
    try {
      const [c, docs] = await Promise.all([
        casesApi.get(id),
        documentsApi.list(id),
      ])
      setCase(c)
      setDocuments(docs.documents)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load case.')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { loadCase() }, [loadCase])

  // Poll for document status updates if any are still uploading or processing
  useEffect(() => {
    const hasProcessing = documents.some(d => d.status === 'processing' || d.status === 'uploading')
    if (!hasProcessing) return
    
    const interval = setInterval(async () => {
      try {
        const docs = await documentsApi.list(id)
        setDocuments(docs.documents)
      } catch (e) {
        // ignore errors during polling
      }
    }, 3000)
    
    return () => clearInterval(interval)
  }, [documents, id])

  // Load summary once there are ready documents
  const readyDocs = documents.filter(d => d.status === 'ready')
  useEffect(() => {
    if (readyDocs.length > 0 && !summary && !summaryLoading) {
      setSummaryLoading(true)
      casesApi.getSummary(id)
        .then(setSummary)
        .catch(() => { /* fail silently — panel shows case metadata */ })
        .finally(() => setSummaryLoading(false))
    }
  }, [readyDocs.length, id, summary, summaryLoading])

  // ── Upload logic ────────────────────────────────────────────────

  function updateUpload(uid: string, patch: Partial<UploadItem>) {
    setUploads(prev => prev.map(u => u.id === uid ? { ...u, ...patch } : u))
  }

  async function processFile(file: File) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert(`"${file.name}" is not a PDF. Only PDF files are accepted.`)
      return
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      alert(`"${file.name}" exceeds the ${MAX_SIZE_MB}MB limit.`)
      return
    }

    const uid = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    const item: UploadItem = { id: uid, file, progress: 0, status: 'uploading' }
    setUploads(prev => [item, ...prev])

    try {
      const doc = await documentsApi.upload(id, file, (pct) => {
        updateUpload(uid, { progress: pct, status: pct < 100 ? 'uploading' : 'processing' })
      })
      updateUpload(uid, { status: 'done', progress: 100, document: doc })
      // Add to documents list
      setDocuments(prev => [doc, ...prev])
      if (case_) setCase({ ...case_, document_count: case_.document_count + 1 })
      // Refresh summary when new doc is ready
      setSummary(null)
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Upload failed. Please try again.'
      updateUpload(uid, { status: 'error', error: msg })
    }
  }

  function handleFiles(files: FileList | File[]) {
    Array.from(files).forEach(processFile)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files)
  }

  async function handleDeleteDocument(docId: string) {
    try {
      await documentsApi.delete(docId)
      setDocuments(prev => prev.filter(d => d.id !== docId))
      if (case_) setCase({ ...case_, document_count: Math.max(0, case_.document_count - 1) })
      setSummary(null)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to delete document. Please try again.'
      alert(msg)
    }
  }

  // ── Loading / Error states ──────────────────────────────────────

  if (loading) {
    return (
      <div className={styles.loadingState}>
        <div className="spinner" style={{ width: 24, height: 24 }} />
        <p>Loading case…</p>
      </div>
    )
  }

  if (error || !case_) {
    return (
      <div className={styles.errorState}>
        <h2 className="font-display">Case not found.</h2>
        <p>{error ?? 'This case does not exist or you do not have access.'}</p>
        <Link href="/workspace" className="btn btn-secondary">← Back to Workspace</Link>
      </div>
    )
  }

  // ── Render ──────────────────────────────────────────────────────

  return (
    <div className={styles.page}>
      {/* ── Compact Header ────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          {/* Mobile sidebar toggle */}
          <button
            className={styles.mobileToggle}
            onClick={() => setSidebarOpen(v => !v)}
            aria-label="Toggle documents"
          >
            ☰
          </button>
          <Link href="/workspace" className={styles.backLink}>← Cases</Link>
          <div className={styles.headerDivider} />
          <div className={styles.headerMeta}>
            {case_.case_number && (
              <span className={styles.caseNumber}>{case_.case_number}</span>
            )}
            <h1 className={`${styles.caseName} font-display`}>{case_.name}</h1>
            <div className={styles.metaRow}>
              <span className={styles.metaItem}>{CASE_TYPE_LABELS[case_.case_type]}</span>
              <span className={styles.metaDot}>·</span>
              <span className={styles.metaItem}>{ROLE_LABELS[case_.user_role]}</span>
              <span className={styles.metaDot}>·</span>
              <span className={styles.metaItem}>{readyDocs.length} of {documents.length} doc{documents.length !== 1 ? 's' : ''} ready</span>
            </div>
          </div>
        </div>
        <div className={styles.headerRight}>
          <span className={`badge ${case_.status === 'preparing' ? 'badge-processing' : 'badge-ready'}`}>
            {STATUS_LABELS[case_.status]}
          </span>
          <span className={`badge badge-ready`} style={{ gap: 6 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#3d7a4f', display: 'inline-block', boxShadow: '0 0 6px rgba(61,122,79,0.6)' }} />
            Case Intelligence
          </span>
          <Link
            href={`/workspace/cases/${id}/courtroom`}
            className={styles.courtroomBtn}
            id="enter-courtroom-btn"
          >
            ⚖ Enter Courtroom
          </Link>
          <button
            className={styles.snapshotToggle}
            onClick={() => setSnapshotOpen(v => !v)}
            title="Toggle case snapshot"
          >
            {snapshotOpen ? '◧' : '◨'}
          </button>
        </div>
      </header>

      {/* ── 3-Column Workspace ────────────────────────────── */}
      <div className={styles.workspace}>

        {/* LEFT — Document Sidebar */}
        <aside className={`${styles.sidebar} ${sidebarOpen ? styles.sidebarOpen : ''}`}>
          <div className={styles.sidebarHeader}>
            <span className={styles.sidebarTitle}>Case Documents</span>
            <span className={styles.sidebarCount}>{documents.length}</span>
          </div>

          {/* Compact upload zone */}
          <div
            className={`${styles.uploadZone} ${dragging ? styles.uploadZoneDragging : ''}`}
            onDrop={handleDrop}
            onDragOver={e => { e.preventDefault(); setDragging(true) }}
            onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setDragging(false) }}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && fileInputRef.current?.click()}
            aria-label="Upload PDF documents"
            id="document-upload-zone"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,.pdf"
              multiple
              onChange={e => { if (e.target.files?.length) { handleFiles(e.target.files); e.target.value = '' } }}
              style={{ display: 'none' }}
              id="file-input"
            />
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>{dragging ? 'Drop here' : 'Upload PDF'}</span>
          </div>

          {/* Active upload items */}
          {uploads.length > 0 && (
            <div className={styles.uploadList}>
              {uploads.filter(u => u.status !== 'done' || uploads.indexOf(u) < 3).map(u => (
                <MiniUploadItem
                  key={u.id}
                  item={u}
                  onDismiss={() => setUploads(prev => prev.filter(x => x.id !== u.id))}
                />
              ))}
            </div>
          )}

          {/* Document list */}
          <div className={styles.docList}>
            {documents.length === 0 && uploads.length === 0 && (
              <div className={styles.docListEmpty}>
                <p>No documents yet.</p>
                <p>Upload a PDF to begin.</p>
              </div>
            )}
            {documents.map(doc => (
              <SidebarDocCard
                key={doc.id}
                doc={doc}
                caseId={id}
                onDelete={handleDeleteDocument}
              />
            ))}
          </div>
        </aside>

        {/* CENTER — Tabbed Panel: Chat + Evidence Graph */}
        <main className={styles.centrePanel}>
          {/* Tab bar */}
          <div className={styles.centreTabBar} role="tablist">
            <button
              role="tab"
              aria-selected={centreTab === 'chat'}
              id="tab-chat"
              className={`${styles.centreTab} ${centreTab === 'chat' ? styles.centreTabActive : ''}`}
              onClick={() => setCentreTab('chat')}
            >
              {centreTab === 'chat' && <span className={styles.centreTabDot} />}
              Case Intelligence
            </button>
            <button
              role="tab"
              aria-selected={centreTab === 'graph'}
              id="tab-graph"
              className={`${styles.centreTab} ${centreTab === 'graph' ? styles.centreTabActive : ''}`}
              onClick={() => setCentreTab('graph')}
            >
              {centreTab === 'graph' && <span className={styles.centreTabDot} />}
              Evidence Graph
              {readyDocs.length > 0 && (
                <span style={{
                  marginLeft: 4,
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-accent)',
                  borderRadius: 99,
                  fontSize: '0.6rem',
                  padding: '1px 6px',
                  color: 'var(--text-muted)',
                }}>
                  {readyDocs.length}
                </span>
              )}
            </button>
          </div>

          {/* Chat panel */}
          <div className={styles.chatArea} style={{ display: centreTab === 'chat' ? 'flex' : 'none' }}>
            <CaseIntelligenceChat
              caseId={id}
              documentCount={readyDocs.length}
              caseName={case_.name}
            />
          </div>

          {/* Evidence Graph panel — only mounted when tab is active to prevent wasteful background fetches */}
          {centreTab === 'graph' && (
            <div className={styles.graphArea}>
              <EvidenceGraph
                caseId={id}
                documentCount={readyDocs.length}
              />
            </div>
          )}

        </main>

        {/* RIGHT — Case Snapshot */}
        {snapshotOpen && (
          <aside className={styles.snapshot}>
            <div className={styles.snapshotHeader}>
              <span className={styles.snapshotTitle}>Case Snapshot</span>
            </div>
            <div className={styles.snapshotBody}>
              {/* Static case metadata always visible */}
              <SnapshotSection title="Case">
                <SnapshotRow label="Name" value={case_.name} />
                <SnapshotRow label="Type" value={CASE_TYPE_LABELS[case_.case_type]} />
                <SnapshotRow label="Role" value={ROLE_LABELS[case_.user_role]} />
                {case_.case_number && <SnapshotRow label="Ref" value={case_.case_number} />}
                <SnapshotRow label="Opened" value={formatDate(case_.created_at)} />
                <SnapshotRow label="Status" value={STATUS_LABELS[case_.status]} />
              </SnapshotSection>

              <SnapshotSection title="Documents">
                <SnapshotRow label="Total" value={String(documents.length)} />
                <SnapshotRow label="Ready" value={String(readyDocs.length)} />
                {documents.filter(d => d.status === 'processing').length > 0 && (
                  <SnapshotRow
                    label="Processing"
                    value={String(documents.filter(d => d.status === 'processing').length)}
                  />
                )}
              </SnapshotSection>

              {/* AI-generated intelligence */}
              {summaryLoading && (
                <div className={styles.snapshotLoading}>
                  <span className="spinner" style={{ width: 14, height: 14 }} />
                  <span>Generating intelligence…</span>
                </div>
              )}

              {summary && summary.has_documents && (
                <>
                  {summary.overview && (
                    <SnapshotSection title="Overview">
                      <p className={styles.snapshotOverview}>{summary.overview}</p>
                    </SnapshotSection>
                  )}
                  {summary.key_issues.length > 0 && (
                    <SnapshotSection title="Key Issues">
                      <SnapshotList items={summary.key_issues} />
                    </SnapshotSection>
                  )}
                  {summary.important_dates.length > 0 && (
                    <SnapshotSection title="Key Dates">
                      <SnapshotList items={summary.important_dates} />
                    </SnapshotSection>
                  )}
                  {summary.potential_weaknesses.length > 0 && (
                    <SnapshotSection title="Potential Risks">
                      <SnapshotList items={summary.potential_weaknesses} variant="risk" />
                    </SnapshotSection>
                  )}
                  {summary.recommended_next_steps.length > 0 && (
                    <SnapshotSection title="Next Steps">
                      <SnapshotList items={summary.recommended_next_steps} variant="action" />
                    </SnapshotSection>
                  )}
                </>
              )}

              {!summaryLoading && readyDocs.length === 0 && (
                <div className={styles.snapshotHint}>
                  Upload and process documents to generate case intelligence.
                </div>
              )}
            </div>
          </aside>
        )}
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className={styles.sidebarOverlay}
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}

// ── Types ─────────────────────────────────────────────────────────

interface UploadItem {
  id: string
  file: File
  progress: number
  status: 'uploading' | 'processing' | 'done' | 'error'
  error?: string
  document?: Document
}

// ── Sidebar Document Card ─────────────────────────────────────────

function SidebarDocCard({
  doc,
  caseId,
  onDelete,
}: {
  doc: Document
  caseId: string
  onDelete: (id: string) => Promise<void>
}) {
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function handleDelete() {
    setDeleting(true)
    try {
      await onDelete(doc.id)
    } finally {
      setDeleting(false)
      setConfirming(false)
    }
  }

  const statusClass = {
    ready: styles.docStatusReady,
    processing: styles.docStatusProcessing,
    uploading: styles.docStatusUploading,
    failed: styles.docStatusFailed,
  }[doc.status]

  return (
    <div className={`${styles.docCard} ${doc.status === 'failed' ? styles.docCardFailed : ''}`}>
      <div className={styles.docCardTop}>
        <div className={styles.docCardIcon}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="4" y="2" width="16" height="20" rx="2" />
            <path d="M8 2v6H4M8 2l8 6" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M8 14h8M8 18h5" strokeLinecap="round" />
          </svg>
        </div>
        <span className={styles.docCardName} title={doc.original_name}>
          {doc.original_name}
        </span>
        <span className={`${styles.docStatus} ${statusClass}`}>
          {doc.status === 'ready' ? '●' : doc.status === 'failed' ? '✕' : '◌'}
        </span>
      </div>

      <div className={styles.docCardMeta}>
        <span>{formatSize(doc.file_size)}</span>
        {doc.page_count && <><span>·</span><span>{doc.page_count}p</span></>}
        {doc.status === 'failed' && doc.error_message && (
          <span className={styles.docCardError} title={doc.error_message}>Failed</span>
        )}
      </div>

      {!confirming && !deleting && doc.status === 'ready' && (
        <div className={styles.docCardActions}>
          <a
            href={documentsApi.getFileUrl(doc.id)}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.docActionBtn}
            id={`download-doc-${doc.id}`}
          >
            ↓ Download
          </a>
          <button
            className={`${styles.docActionBtn} ${styles.docActionDanger}`}
            onClick={() => setConfirming(true)}
            id={`delete-doc-${doc.id}`}
          >
            Delete
          </button>
        </div>
      )}

      {confirming && !deleting && (
        <div className={styles.docCardActions}>
          <span className={styles.confirmText}>Delete?</span>
          <button className={`${styles.docActionBtn} ${styles.docActionDanger}`} onClick={handleDelete}>Yes</button>
          <button className={styles.docActionBtn} onClick={() => setConfirming(false)}>No</button>
        </div>
      )}

      {deleting && (
        <div className={styles.docCardActions}>
          <span className="spinner" style={{ width: 12, height: 12 }} />
          <span className={styles.confirmText}>Deleting…</span>
        </div>
      )}
    </div>
  )
}

// ── Mini Upload Item ──────────────────────────────────────────────

function MiniUploadItem({ item, onDismiss }: { item: UploadItem; onDismiss: () => void }) {
  return (
    <div className={`${styles.miniUpload} ${item.status === 'error' ? styles.miniUploadError : ''}`}>
      <div className={styles.miniUploadTop}>
        <span className={styles.miniUploadName}>{item.file.name}</span>
        {(item.status === 'done' || item.status === 'error') && (
          <button className={styles.miniDismiss} onClick={onDismiss}>×</button>
        )}
      </div>
      {item.status === 'error' ? (
        <p className={styles.miniUploadErrorText}>{item.error}</p>
      ) : (
        <div className="progress-bar" style={{ marginTop: 4 }}>
          <div
            className="progress-fill"
            style={{ width: item.status === 'done' ? '100%' : `${item.progress}%` }}
          />
        </div>
      )}
      <span className={styles.miniUploadStatus}>
        {item.status === 'uploading' && `${item.progress}% uploading…`}
        {item.status === 'processing' && 'Processing…'}
        {item.status === 'done' && '✓ Uploaded'}
        {item.status === 'error' && 'Failed'}
      </span>
    </div>
  )
}

// ── Snapshot Components ───────────────────────────────────────────

function SnapshotSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className={styles.snapshotSection}>
      <p className={styles.snapshotSectionTitle}>{title}</p>
      {children}
    </div>
  )
}

function SnapshotRow({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.snapshotRow}>
      <span className={styles.snapshotRowLabel}>{label}</span>
      <span className={styles.snapshotRowValue}>{value}</span>
    </div>
  )
}

function SnapshotList({ items, variant }: { items: string[]; variant?: 'risk' | 'action' }) {
  return (
    <ul className={styles.snapshotList}>
      {items.map((item, i) => (
        <li
          key={i}
          className={`${styles.snapshotListItem} ${
            variant === 'risk' ? styles.snapshotListRisk :
            variant === 'action' ? styles.snapshotListAction : ''
          }`}
        >
          {item}
        </li>
      ))}
    </ul>
  )
}
