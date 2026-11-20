'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { casesApi } from '@/lib/api'
import type { Case } from '@/lib/types'
import { CASE_TYPE_LABELS } from '@/lib/types'
import styles from './page.module.css'

export default function CourtroomHubPage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadCases() {
      try {
        setLoading(true)
        const res = await casesApi.list()
        setCases(res.cases || [])
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load cases.')
      } finally {
        setLoading(false)
      }
    }
    loadCases()
  }, [])

  const casesWithDocs = cases.filter(c => c.document_count > 0)
  const casesWithoutDocs = cases.filter(c => c.document_count === 0)

  return (
    <div className={styles.page}>
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerIcon}>⚖</span>
          <div>
            <h1 className={styles.headerTitle}>Virtual Courtroom Arena</h1>
            <p className={styles.headerSub}>
              Practice oral arguments, tackle sudden objections, and refine court decorum before real High Court &amp; District Court appearances.
            </p>
          </div>
        </div>
        <div className={styles.headerBadges}>
          <span className="badge badge-gold">AI Judge &amp; Opposing Counsel</span>
          <span className="badge badge-ready">Real Document Grounding</span>
        </div>
      </header>

      {/* ── Quick Stats & Tips Bar ─────────────────────────────── */}
      <div className={styles.quickBar}>
        <div className={styles.statCard}>
          <span className={styles.statVal}>{cases.length}</span>
          <span className={styles.statLabel}>Total Cases</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>{casesWithDocs.length}</span>
          <span className={styles.statLabel}>Ready for Trial</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>3</span>
          <span className={styles.statLabel}>Judge Demeanours</span>
        </div>
        <div className={styles.tipCard}>
          <span className={styles.tipIcon}>💡</span>
          <div className={styles.tipContent}>
            <strong>Junior Counsel Tip:</strong> The AI Judge grades oral arguments on evidentiary grounding. Always cite FIR dates, exhibit numbers, or witness contradictions!
          </div>
        </div>
      </div>

      {/* ── Case Grid ─────────────────────────────────────────── */}
      <div className={styles.content}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Select a Case to Enter Mock Trial</h2>
          <p className={styles.sectionSub}>Choose any case with uploaded documents to launch the interactive trial simulation.</p>
        </div>

        {loading && (
          <div className={styles.loadingBox}>
            <span className="spinner" style={{ width: 24, height: 24 }} />
            <p>Loading case courtroom roster…</p>
          </div>
        )}

        {error && (
          <div className={styles.errorBox}>
            <p>⚠ {error}</p>
          </div>
        )}

        {!loading && !error && cases.length === 0 && (
          <div className={styles.emptyBox}>
            <span className={styles.emptyIcon}>📂</span>
            <h3>No cases found</h3>
            <p>Create a case and upload pleadings or charge sheets to enter mock trial.</p>
            <Link href="/workspace/cases/new" className={styles.createCaseBtn}>
              + Create New Case
            </Link>
          </div>
        )}

        {!loading && !error && cases.length > 0 && (
          <div className={styles.caseGrid}>
            {cases.map((c) => {
              const isReady = c.document_count > 0
              return (
                <div key={c.id} className={`${styles.caseCard} ${isReady ? styles.caseCardReady : ''}`}>
                  <div className={styles.caseCardTop}>
                    <div className={styles.caseTypeBadge}>
                      {CASE_TYPE_LABELS[c.case_type] ?? c.case_type}
                    </div>
                    <span className={isReady ? styles.readyStatus : styles.unreadyStatus}>
                      {isReady ? `● ${c.document_count} Doc${c.document_count > 1 ? 's' : ''} Ready` : '○ No Docs'}
                    </span>
                  </div>

                  <h3 className={styles.caseName}>{c.name}</h3>
                  <p className={styles.caseDesc}>
                    {c.description || 'No description provided for this matter.'}
                  </p>

                  <div className={styles.caseCardFeatures}>
                    <div className={styles.featureItem}>
                      <span>🏛 Phase:</span> Opening to Closing
                    </div>
                    <div className={styles.featureItem}>
                      <span>⚡ Features:</span> Live Objections &amp; Scorecard
                    </div>
                  </div>

                  <div className={styles.caseCardActions}>
                    {isReady ? (
                      <Link
                        href={`/workspace/cases/${c.id}/courtroom`}
                        className={styles.enterTrialBtn}
                      >
                        ⚖ Enter Mock Trial →
                      </Link>
                    ) : (
                      <Link
                        href={`/workspace/cases/${c.id}`}
                        className={styles.uploadDocsBtn}
                      >
                        📄 Upload Documents First
                      </Link>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
