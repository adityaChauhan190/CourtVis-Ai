'use client'
import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { documentsApi } from '@/lib/api'
import type { Document } from '@/lib/types'
import styles from './page.module.css'

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function DocumentViewerPage() {
  const { id: caseId, docId } = useParams<{ id: string; docId: string }>()
  const [doc, setDoc] = useState<Document | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Blob URL — created by fetching the PDF with the auth token,
  // then turning the binary response into an object URL the iframe can load.
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [pdfLoading, setPdfLoading] = useState(false)
  const [pdfError, setPdfError] = useState<string | null>(null)

  useEffect(() => {
    documentsApi.get(docId)
      .then(setDoc)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [docId])

  // Fetch the PDF as a blob once the document metadata is ready
  const loadPdfBlob = useCallback(async () => {
    if (!doc || doc.status !== 'ready') return
    setPdfLoading(true)
    setPdfError(null)
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
      const url = `${apiBase}/api/documents/${docId}/file`
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error(`Failed to load PDF (${res.status})`)
      const blob = await res.blob()
      const objectUrl = URL.createObjectURL(blob)
      setBlobUrl(objectUrl)
    } catch (e: unknown) {
      setPdfError(e instanceof Error ? e.message : 'Failed to load PDF')
    } finally {
      setPdfLoading(false)
    }
  }, [doc, docId])

  useEffect(() => {
    if (doc?.status === 'ready') loadPdfBlob()
    // Cleanup blob URL on unmount
    return () => { if (blobUrl) URL.revokeObjectURL(blobUrl) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc])

  if (loading) {
    return (
      <div className={styles.loadingState}>
        <div className="spinner" style={{ width: 24, height: 24 }} />
        <p>Loading document…</p>
      </div>
    )
  }

  if (error || !doc) {
    return (
      <div className={styles.errorState}>
        <h2 className="font-display">Document not found.</h2>
        <p>{error}</p>
        <Link href={`/workspace/cases/${caseId}`} className="btn btn-secondary">← Back to Case</Link>
      </div>
    )
  }

  const directFileUrl = documentsApi.getFileUrl(docId)

  return (
    <div className={styles.viewerPage}>
      {/* ── Top Bar ───────────────────────────────────────────── */}
      <div className={styles.topBar}>
        <div className={styles.topBarLeft}>
          <Link href={`/workspace/cases/${caseId}`} className={styles.backLink}>
            ← Cases
          </Link>
          <span className={styles.breadcrumbSep}>›</span>
          <span className={styles.breadcrumbCase}>Case</span>
          <span className={styles.breadcrumbSep}>›</span>
          <span className={styles.breadcrumbDoc} title={doc.original_name}>
            {doc.original_name.length > 40
              ? doc.original_name.slice(0, 37) + '…'
              : doc.original_name}
          </span>
        </div>
        <div className={styles.topBarActions}>
          {doc.page_count && (
            <span className={styles.pageCount}>{doc.page_count} pages</span>
          )}
          <span className={`badge ${
            doc.status === 'ready' ? 'badge-ready' :
            doc.status === 'processing' ? 'badge-processing' : 'badge-failed'
          }`}>
            {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
          </span>
          <a
            href={directFileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary btn-sm"
            id="download-pdf-btn"
          >
            ↓ Download PDF
          </a>
        </div>
      </div>

      {/* ── Main Viewer Layout ────────────────────────────────── */}
      <div className={styles.viewerLayout}>
        {/* ── CENTER: PDF Viewer ─────────────────────────────── */}
        <div className={styles.pdfPane}>
          {doc.status === 'ready' ? (
            pdfLoading ? (
              <div className={styles.pdfLoading}>
                <div className="spinner" style={{ width: 28, height: 28 }} />
                <p>Loading PDF…</p>
              </div>
            ) : pdfError ? (
              <div className={styles.pdfPlaceholder}>
                <span style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>⚠</span>
                <p className={styles.pdfPlaceholderText}>{pdfError}</p>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={loadPdfBlob}
                  style={{ marginTop: '0.75rem' }}
                >
                  Retry
                </button>
                <p style={{ marginTop: '0.5rem', fontSize: '0.75rem', opacity: 0.5 }}>
                  Or <a href={directFileUrl} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-gold)' }}>open in new tab</a>
                </p>
              </div>
            ) : blobUrl ? (
              <iframe
                src={blobUrl}
                className={styles.pdfFrame}
                title={doc.original_name}
                id="pdf-viewer-frame"
              />
            ) : null
          ) : (
            <div className={styles.pdfPlaceholder}>
              <span className={`badge ${
                doc.status === 'processing' ? 'badge-processing' : 'badge-failed'
              }`} style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}>
                {doc.status === 'processing' ? '◌ Processing' : '✕ Failed'}
              </span>
              <p className={styles.pdfPlaceholderText}>
                {doc.status === 'processing'
                  ? 'Document is being processed. Come back in a moment.'
                  : 'Document processing failed. Please delete and re-upload.'}
              </p>
              {doc.error_message && (
                <p className={styles.pdfErrorDetail}>{doc.error_message}</p>
              )}
            </div>
          )}
        </div>

        {/* ── RIGHT: Info Panel ──────────────────────────────── */}
        <aside className={styles.infoPanel}>
          <div className={styles.infoPanelHeader}>
            <div className={styles.infoPanelIcon}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="4" y="2" width="16" height="20" rx="2" />
                <path d="M8 2v6H4M8 2l8 6" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M8 14h8M8 18h5" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <p className={styles.infoPanelTitle}>Document Info</p>
              <p className={styles.infoPanelSub}>PDF Case File</p>
            </div>
          </div>

          <div className={styles.infoSection}>
            <InfoRow label="Filename" value={doc.original_name} mono />
            <InfoRow label="Type" value="PDF Document" />
            <InfoRow label="Size" value={formatSize(doc.file_size)} />
            {doc.page_count && <InfoRow label="Pages" value={String(doc.page_count)} />}
            <InfoRow label="Uploaded" value={formatDate(doc.uploaded_at)} />
            {doc.processed_at && <InfoRow label="Processed" value={formatDate(doc.processed_at)} />}
          </div>

          <div className={styles.infoStatus}>
            <span className={styles.infoStatusLabel}>Status</span>
            <span className={`badge ${
              doc.status === 'ready' ? 'badge-ready' :
              doc.status === 'processing' ? 'badge-processing' : 'badge-failed'
            }`}>
              {doc.status === 'ready' ? '● Ready for AI analysis' :
               doc.status === 'processing' ? '◌ Processing…' : '✕ Failed'}
            </span>
          </div>

          <div className={styles.infoDivider} />

          {/* Quick actions */}
          <div className={styles.quickActions}>
            <p className={styles.quickActionsTitle}>Quick Actions</p>
            <Link
              href={`/workspace/cases/${caseId}?tab=chat`}
              className={styles.quickAction}
              id="ask-ai-about-doc"
            >
              <span className={styles.quickActionIcon}>◈</span>
              <div>
                <p className={styles.quickActionLabel}>Ask AI about this doc</p>
                <p className={styles.quickActionSub}>Open Case Intelligence chat</p>
              </div>
            </Link>
            <a
              href={directFileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.quickAction}
              id="open-in-new-tab"
            >
              <span className={styles.quickActionIcon}>↗</span>
              <div>
                <p className={styles.quickActionLabel}>Open in new tab</p>
                <p className={styles.quickActionSub}>Full-screen browser PDF viewer</p>
              </div>
            </a>
          </div>

          <div className={styles.infoDivider} />

          {/* AI Analysis teaser */}
          <div className={styles.aiNote}>
            <p className={styles.aiNoteTitle}>◈ AI Analysis</p>
            <p className={styles.aiNoteDesc}>
              Use the <strong>Case Intelligence</strong> tab to ask questions about
              this document, extract evidence, build timelines, and more.
            </p>
            <Link
              href={`/workspace/cases/${caseId}`}
              className="btn btn-secondary btn-sm"
              style={{ marginTop: '0.75rem', display: 'inline-block' }}
            >
              Open Case Workspace →
            </Link>
          </div>
        </aside>
      </div>
    </div>
  )
}

// ── Info Row ──────────────────────────────────────────────────────────────────

function InfoRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className={styles.infoRow}>
      <span className={styles.infoLabel}>{label}</span>
      <span className={`${styles.infoValue} ${mono ? styles.infoValueMono : ''}`} title={value}>
        {value.length > 36 ? value.slice(0, 33) + '…' : value}
      </span>
    </div>
  )
}
