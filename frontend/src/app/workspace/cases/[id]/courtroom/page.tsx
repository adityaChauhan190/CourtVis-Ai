'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { casesApi, documentsApi } from '@/lib/api'
import type { Document } from '@/lib/types'
import { VirtualCourtroom } from '@/components/courtroom/VirtualCourtroom'
import styles from './courtroom.module.css'

export default function CourtroomPage() {
  const { id } = useParams<{ id: string }>()

  const [caseName, setCaseName] = useState<string | undefined>(undefined)
  const [documentCount, setDocumentCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [c, docs] = await Promise.all([
          casesApi.get(id),
          documentsApi.list(id),
        ])
        setCaseName(c.name)
        const ready = (docs.documents as Document[]).filter(d => d.status === 'ready').length
        setDocumentCount(ready)
      } catch {
        // Non-fatal: courtroom can still start with 0 docs (will show warning)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  return (
    <div className={styles.page}>
      {/* ── Courtroom Nav Bar ─────────────────────────────────── */}
      <nav className={styles.nav}>
        <Link href={`/workspace/cases/${id}`} className={styles.backLink} id="back-to-case-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 5l-7 7 7 7" />
          </svg>
          Back to Case
        </Link>
        <div className={styles.navCenter}>
          <span className={styles.navIcon}>⚖</span>
          <span className={styles.navTitle}>Virtual Courtroom</span>
          {caseName && <span className={styles.navCaseName}>— {caseName}</span>}
        </div>
        <div className={styles.navRight}>
          {!loading && (
            <span className={styles.docBadge}>
              <span className={styles.docBadgeDot} />
              {documentCount} doc{documentCount !== 1 ? 's' : ''} ready
            </span>
          )}
        </div>
      </nav>

      {/* ── Full-screen Courtroom ─────────────────────────────── */}
      <div className={styles.courtroomWrapper}>
        {loading ? (
          <div className={styles.loadingState}>
            <span className="spinner" style={{ width: 24, height: 24 }} />
            <span>Loading courtroom…</span>
          </div>
        ) : (
          <VirtualCourtroom
            caseId={id}
            documentCount={documentCount}
            caseName={caseName}
          />
        )}
      </div>
    </div>
  )
}
