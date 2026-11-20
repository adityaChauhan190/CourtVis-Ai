'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { casesApi } from '@/lib/api'
import type { Case } from '@/lib/types'
import { CASE_TYPE_LABELS, STATUS_LABELS } from '@/lib/types'
import styles from './page.module.css'

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function WorkspacePage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    casesApi.list()
      .then(r => setCases(r.cases))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const totalDocs = cases.reduce((acc, c) => acc + c.document_count, 0)
  const activeCases = cases.filter(c => c.status === 'active' || c.status === 'preparing')

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <p className="text-eyebrow">Workspace</p>
          <h1 className={`text-display-md ${styles.greeting}`}>{getGreeting()}, Counsel.</h1>
          <p className={styles.subheading}>
            Review your active matters and continue your case preparation.
          </p>
        </div>
        <Link href="/workspace/cases/new" className="btn btn-primary">
          + New Case
        </Link>
      </div>

      <div className={styles.divider} />

      {/* Stats */}
      <div className={styles.statsGrid}>
        <StatCard label="Active Cases" value={activeCases.length} icon="◧" />
        <StatCard label="Total Documents" value={totalDocs} icon="◪" />
        <StatCard
          label="Analysis Status"
          value={loading ? '—' : cases.length > 0 ? 'Preparing' : 'Idle'}
          icon="◎"
          isText
        />
        <StatCard label="Total Matters" value={cases.length} icon="⊞" />
      </div>

      {/* Cases */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={`${styles.sectionTitle} font-display`}>Recent Cases</h2>
          <Link href="/workspace/cases" className="btn btn-ghost btn-sm">View All →</Link>
        </div>

        {loading ? (
          <div className={styles.loadingGrid}>
            {[1, 2, 3].map(i => <div key={i} className={`${styles.skeletonCard} shimmer`} />)}
          </div>
        ) : error ? (
          <div className={styles.errorState}>
            <p className={styles.errorText}>Could not connect to the API server.</p>
            <p className={styles.errorSub}>Make sure the backend is running on port 8000.</p>
          </div>
        ) : cases.length === 0 ? (
          <EmptyState />
        ) : (
          <div className={styles.caseGrid}>
            {cases.slice(0, 6).map(c => (
              <CaseCard key={c.id} case_={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({
  label, value, icon, isText,
}: { label: string; value: string | number; icon: string; isText?: boolean }) {
  return (
    <div className={styles.statCard}>
      <div className={styles.statIcon}>{icon}</div>
      <div className={styles.statValue} style={{ fontFamily: isText ? 'var(--font-body)' : 'var(--font-display)' }}>
        {value}
      </div>
      <div className={styles.statLabel}>{label}</div>
    </div>
  )
}

function CaseCard({ case_: c }: { case_: Case }) {
  return (
    <Link href={`/workspace/cases/${c.id}`} className={`card card-interactive ${styles.caseCard}`}>
      <div className={styles.caseCardHeader}>
        <span className={`badge ${c.status === 'preparing' ? 'badge-processing' : 'badge-ready'}`}>
          {STATUS_LABELS[c.status]}
        </span>
        {c.case_number && <span className={styles.caseNumber}>{c.case_number}</span>}
      </div>
      <h3 className={`${styles.caseName} font-display`}>{c.name}</h3>
      <div className={styles.caseMeta}>
        <span>{CASE_TYPE_LABELS[c.case_type]}</span>
        <span className={styles.metaDot}>·</span>
        <span>{c.document_count} {c.document_count === 1 ? 'document' : 'documents'}</span>
      </div>
      {c.description && (
        <p className={styles.caseDesc}>{c.description.slice(0, 100)}{c.description.length > 100 ? '…' : ''}</p>
      )}
      <div className={styles.caseFooter}>
        <span className={styles.caseDate}>Updated {formatDate(c.updated_at)}</span>
        <span className={styles.caseArrow}>→</span>
      </div>
    </Link>
  )
}

function EmptyState() {
  return (
    <div className={styles.emptyState}>
      <div className={styles.emptyIcon}>⚖</div>
      <h3 className={`${styles.emptyTitle} font-display`}>Your chambers are quiet.</h3>
      <p className={styles.emptyDesc}>Create your first case file to begin your preparation.</p>
      <Link href="/workspace/cases/new" className="btn btn-primary">
        Create Case
      </Link>
    </div>
  )
}
