'use client'
import { useCallback, useRef, useState } from 'react'
import { documentsApi, ApiError } from '@/lib/api'
import type { Document } from '@/lib/types'
import styles from './DocumentUploadZone.module.css'

const MAX_SIZE_MB = 50

interface Props {
  caseId: string
  onUploadComplete: (doc: Document) => void
}

interface UploadItem {
  id: string
  file: File
  progress: number
  status: 'uploading' | 'processing' | 'done' | 'error'
  error?: string
  document?: Document
}

export function DocumentUploadZone({ caseId, onUploadComplete }: Props) {
  const [dragging, setDragging] = useState(false)
  const [uploads, setUploads] = useState<UploadItem[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  function updateUpload(id: string, patch: Partial<UploadItem>) {
    setUploads(prev => prev.map(u => u.id === id ? { ...u, ...patch } : u))
  }

  async function processFile(file: File) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert(`"${file.name}" is not a PDF file. Only PDF files are accepted.`)
      return
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      alert(`"${file.name}" exceeds the ${MAX_SIZE_MB}MB file size limit.`)
      return
    }

    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    const item: UploadItem = { id, file, progress: 0, status: 'uploading' }
    setUploads(prev => [item, ...prev])

    try {
      const doc = await documentsApi.upload(caseId, file, (pct) => {
        updateUpload(id, { progress: pct, status: pct < 100 ? 'uploading' : 'processing' })
      })
      updateUpload(id, { status: 'done', progress: 100, document: doc })
      onUploadComplete(doc)
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Upload failed. Please try again.'
      updateUpload(id, { status: 'error', error: msg })
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

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    setDragging(true)
  }

  function handleDragLeave(e: React.DragEvent) {
    if (!e.currentTarget.contains(e.relatedTarget as Node)) setDragging(false)
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files?.length) {
      handleFiles(e.target.files)
      e.target.value = ''
    }
  }

  function dismissUpload(id: string) {
    setUploads(prev => prev.filter(u => u.id !== id))
  }

  return (
    <div className={styles.wrapper}>
      {/* Drop Zone */}
      <div
        id="document-upload-zone"
        className={`${styles.dropZone} ${dragging ? styles.dropZoneDragging : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={e => e.key === 'Enter' && inputRef.current?.click()}
        aria-label="Upload PDF documents"
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          onChange={handleInputChange}
          className={styles.hiddenInput}
          id="file-input"
        />
        <div className={styles.dropZoneIcon}>
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <rect x="8" y="4" width="24" height="32" rx="3" stroke="currentColor" strokeWidth="1.5" />
            <path d="M16 4v8h-8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M16 4l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M20 22v7M17 26l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <p className={styles.dropZoneTitle}>
          {dragging ? 'Drop your documents here' : 'Drag & Drop PDF here'}
        </p>
        <p className={styles.dropZoneOr}>or</p>
        <span className="btn btn-secondary btn-sm" onClick={e => e.stopPropagation()}>
          Browse Files
        </span>
        <p className={styles.dropZoneHint}>PDF only · Maximum {MAX_SIZE_MB}MB per file · Multiple files allowed</p>
      </div>

      {/* Upload Progress Items */}
      {uploads.length > 0 && (
        <div className={styles.uploadList}>
          {uploads.map(u => (
            <UploadProgressItem key={u.id} item={u} onDismiss={() => dismissUpload(u.id)} />
          ))}
        </div>
      )}
    </div>
  )
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function UploadProgressItem({ item, onDismiss }: { item: UploadItem; onDismiss: () => void }) {
  const statusLabel = {
    uploading: 'Uploading…',
    processing: 'Processing…',
    done: 'Ready',
    error: 'Failed',
  }[item.status]

  return (
    <div className={`${styles.uploadItem} ${styles[`uploadItem_${item.status}`]}`}>
      <div className={styles.uploadItemIcon}>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <rect x="3" y="1" width="14" height="18" rx="2" stroke="currentColor" strokeWidth="1.25" />
          <path d="M7 1v5H3" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" />
          <path d="M7 1l6 5" stroke="currentColor" strokeWidth="1.25" strokeLinejoin="round" />
        </svg>
      </div>
      <div className={styles.uploadItemBody}>
        <div className={styles.uploadItemTop}>
          <span className={styles.uploadItemName}>{item.file.name}</span>
          <div className={styles.uploadItemRight}>
            <span className={styles.uploadItemSize}>{formatSize(item.file.size)}</span>
            {(item.status === 'done' || item.status === 'error') && (
              <button className={styles.dismissBtn} onClick={onDismiss} aria-label="Dismiss">×</button>
            )}
          </div>
        </div>

        {item.status === 'error' ? (
          <div className={styles.uploadError}>
            <p className={styles.uploadErrorText}>{item.error}</p>
            <p className={styles.uploadErrorHints}>
              Possible reasons: Invalid PDF · File too large · Corrupted document · Upload interrupted
            </p>
          </div>
        ) : (
          <>
            <div className="progress-bar" style={{ marginTop: '8px' }}>
              <div
                className="progress-fill"
                style={{ width: item.status === 'done' ? '100%' : `${item.progress}%` }}
              />
            </div>
            <div className={styles.uploadItemStatus}>
              {(item.status === 'uploading' || item.status === 'processing') && (
                <span className="spinner" style={{ width: 12, height: 12 }} />
              )}
              <span className={`badge ${
                item.status === 'done' ? 'badge-ready' :
                item.status === 'processing' ? 'badge-processing' :
                'badge-uploading'
              }`}>
                {statusLabel}
              </span>
              {item.document?.page_count && (
                <span className={styles.pageCount}>{item.document.page_count} pages</span>
              )}
              {item.status === 'uploading' && (
                <span className={styles.progressPct}>{item.progress}%</span>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
