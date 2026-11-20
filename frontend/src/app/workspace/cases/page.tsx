'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { casesApi } from '@/lib/api'
import type { Case } from '@/lib/types'
import { CASE_TYPE_LABELS, STATUS_LABELS } from '@/lib/types'
import styles from './page.module.css'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function CasesListPage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    casesApi.list()
      .then(r => setCases(r.cases))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <p className="text-eyebrow">Case Management</p>
          <h1 className={`text-display-md ${styles.title}`}>My Cases</h1>
          <p className={styles.subtitle}>All matters currently in preparation.</p>
        </div>
        <Link href="/workspace/cases/new" className="btn btn-primary">+ New Case</Link>
      </div>
      <div className={styles.divider} />

      {loading ? (
        <div className={styles.loadingGrid}>
          {[1,2,3,4].map(i => <div key={i} className={`${styles.skeletonRow} shimmer`} />)}
        </div>
      ) : error ? (
        <div className={styles.error}><p>{error}</p></div>
      ) : cases.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>⚖</div>
          <h2 className="font-display">Your chambers are quiet.</h2>
          <p>Create your first case file to begin.</p>
          <Link href="/workspace/cases/new" className="btn btn-primary">Create Case</Link>
        </div>
      ) : (
        <div className={styles.caseTable}>
          <div className={styles.tableHeader}>
            <span>Case Name</span>
            <span>Type</span>
            <span>Status</span>
            <span>Documents</span>
            <span>Updated</span>
            <span />
          </div>
          {cases.map(c => (
            <Link key={c.id} href={`/workspace/cases/${c.id}`} className={styles.tableRow}>
              <div>
                <div className={styles.caseName}>{c.name}</div>
                {c.case_number && <div className={styles.caseNumber}>{c.case_number}</div>}
              </div>
              <span className={styles.cellMeta}>{CASE_TYPE_LABELS[c.case_type]}</span>
              <span>
                <span className={`badge ${c.status === 'preparing' ? 'badge-processing' : 'badge-ready'}`}>
                  {STATUS_LABELS[c.status]}
                </span>
              </span>
              <span className={styles.cellMeta}>{c.document_count}</span>
              <span className={styles.cellMeta}>{formatDate(c.updated_at)}</span>
              <span className={styles.arrow}>→</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
