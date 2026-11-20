'use client'
import { useState } from 'react'
import Link from 'next/link'
import type { Document } from '@/lib/types'
import { documentsApi } from '@/lib/api'
import styles from './DocumentLibrary.module.css'

interface Props {
  documents: Document[]
  caseId: string
  onDelete: (id: string) => Promise<void>
}

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  const diffHrs = Math.floor(diffMins / 60)
  if (diffHrs < 24) return `${diffHrs} hour${diffHrs > 1 ? 's' : ''} ago`
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

export function DocumentLibrary({ documents, caseId, onDelete }: Props) {
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [confirmId, setConfirmId] = useState<string | null>(null)

  async function handleDelete(id: string) {
    setDeletingId(id)
    try {
      await onDelete(id)
    } finally {
      setDeletingId(null)
      setConfirmId(null)
    }
  }

  if (documents.length === 0) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <rect x="8" y="4" width="24" height="32" rx="3" stroke="currentColor" strokeWidth="1.5" />
            <path d="M14 15h12M14 21h12M14 27h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
        <p className={`${styles.emptyTitle} font-display`}>No documents have entered this case file yet.</p>
        <p className={styles.emptySubtitle}>
          Upload a PDF above to begin building your case foundation.
        </p>
      </div>
    )
  }

  return (
    <div className={styles.library}>
      <div className={styles.libraryHeader}>
        <h3 className={`${styles.libraryTitle} font-display`}>Case Documents</h3>
        <span className={styles.libraryCount}>{documents.length} {documents.length === 1 ? 'document' : 'documents'}</span>
      </div>

      <div className={styles.docList}>
        {documents.map(doc => (
          <DocumentCard
            key={doc.id}
            doc={doc}
            caseId={caseId}
            confirming={confirmId === doc.id}
            deleting={deletingId === doc.id}
            onConfirmDelete={() => setConfirmId(doc.id)}
            onCancelDelete={() => setConfirmId(null)}
            onDelete={() => handleDelete(doc.id)}
          />
        ))}
      </div>
    </div>
  )
}

interface CardProps {
  doc: Document
  caseId: string
  confirming: boolean
  deleting: boolean
  onConfirmDelete: () => void
  onCancelDelete: () => void
  onDelete: () => void
}

function DocumentCard({ doc, caseId, confirming, deleting, onConfirmDelete, onCancelDelete, onDelete }: CardProps) {
  return (
    <div className={`${styles.docCard} ${styles[`doc_${doc.status}`]}`}>
      {/* Icon */}
      <div className={styles.docIcon}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <rect x="4" y="2" width="16" height="20" rx="2" stroke="currentColor" strokeWidth="1.25" />
          <path d="M8 2v6H4" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" />
          <path d="M8 2l8 6" stroke="currentColor" strokeWidth="1.25" strokeLinejoin="round" />
          <path d="M8 14h8M8 18h5" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" />
        </svg>
      </div>

      {/* Info */}
      <div className={styles.docInfo}>
        <div className={styles.docTop}>
          <span className={styles.docName}>{doc.original_name}</span>
          <span className={`badge ${
            doc.status === 'ready' ? 'badge-ready' :
            doc.status === 'processing' ? 'badge-processing' :
            doc.status === 'uploading' ? 'badge-uploading' :
            'badge-failed'
          }`}>
            {doc.status.toUpperCase()}
          </span>
        </div>
        <div className={styles.docMeta}>
          {doc.page_count && <span>{doc.page_count} pages</span>}
          {doc.page_count && <span className={styles.dot}>·</span>}
          <span>{formatSize(doc.file_size)}</span>
          <span className={styles.dot}>·</span>
          <span>Uploaded {formatDate(doc.uploaded_at)}</span>
          {doc.status === 'failed' && doc.error_message && (
            <>
              <span className={styles.dot}>·</span>
              <span className={styles.errorMsg}>{doc.error_message}</span>
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className={styles.docActions}>
        {doc.status === 'ready' && !confirming && !deleting && (
          <>
            <Link
              href={`/workspace/cases/${caseId}/documents/${doc.id}`}
              className="btn btn-ghost btn-sm"
              id={`open-doc-${doc.id}`}
            >
              Open
            </Link>
            <a
              href={documentsApi.getFileUrl(doc.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost btn-sm"
              id={`download-doc-${doc.id}`}
            >
              Download
            </a>
          </>
        )}

        {!confirming && !deleting && (
          <button
            className="btn btn-danger btn-sm"
            id={`delete-doc-${doc.id}`}
            onClick={onConfirmDelete}
          >
            Delete
          </button>
        )}

        {confirming && (
          <div className={styles.confirmRow}>
            <span className={styles.confirmText}>Delete this document?</span>
            <button className="btn btn-danger btn-sm" onClick={onDelete}>
              Yes, Delete
            </button>
            <button className="btn btn-ghost btn-sm" onClick={onCancelDelete}>
              Cancel
            </button>
          </div>
        )}

        {deleting && (
          <div className={styles.deletingRow}>
            <span className="spinner" />
            <span className={styles.confirmText}>Deleting…</span>
          </div>
        )}
      </div>
    </div>
  )
}
