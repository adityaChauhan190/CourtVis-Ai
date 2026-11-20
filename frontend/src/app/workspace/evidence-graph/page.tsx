'use client'
import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { casesApi } from '@/lib/api'
import type { Case } from '@/lib/types'
import { CASE_TYPE_LABELS } from '@/lib/types'
import { EvidenceGraph } from '@/components/graph/EvidenceGraph'
import styles from './page.module.css'

export default function EvidenceGraphPage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)

  const selectedCase = cases.find(c => c.id === selectedCaseId) ?? null
  const readyCount = selectedCase?.document_count ?? 0

  const loadCases = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await casesApi.list()
      setCases(res.cases)
      // Auto-select first case that has documents
      const first = res.cases.find(c => c.document_count > 0)
      if (first) setSelectedCaseId(first.id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load cases.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadCases() }, [loadCases])

  return (
    <div className={styles.page}>
      {/* ── Header ───────────────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerIcon}>◉</span>
          <div>
            <h1 className={styles.headerTitle}>Evidence Graph</h1>
            <p className={styles.headerSub}>
              AI-extracted entity &amp; relationship graph from your case documents
            </p>
          </div>
        </div>
        <span className="badge badge-coming-soon" style={{ fontSize: '0.6875rem' }}>
          Groq · Knowledge Graph
        </span>
      </header>

      {/* ── Body: two panels ─────────────────────────────────── */}
      <div className={styles.body}>

        {/* LEFT — Case selector */}
        <aside className={styles.casePanel}>
          <div className={styles.casePanelHeader}>
            <span className={styles.casePanelTitle}>Select Case</span>
            {!loading && (
              <span className={styles.caseCount}>{cases.length}</span>
            )}
          </div>

          {loading && (
            <div className={styles.casePanelState}>
              <span className="spinner" style={{ width: 18, height: 18 }} />
              <p className={styles.casePanelStateText}>Loading cases…</p>
            </div>
          )}

          {!loading && error && (
            <div className={styles.casePanelState}>
              <span className={styles.casePanelStateIcon}>⚠</span>
              <p className={styles.casePanelStateText}>{error}</p>
              <button className="btn btn-secondary" style={{ fontSize: '0.75rem' }} onClick={loadCases}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && cases.length === 0 && (
            <div className={styles.casePanelState}>
              <span className={styles.casePanelStateIcon}>◌</span>
              <p className={styles.casePanelStateText}>
                No cases found.<br />
                <Link href="/workspace/cases" style={{ color: 'var(--gold-dim)' }}>
                  Create a case
                </Link>{' '}and upload documents to get started.
              </p>
            </div>
          )}

          {!loading && !error && cases.length > 0 && (
            <ul className={styles.caseList} role="listbox" aria-label="Select a case">
              {cases.map(c => {
                const isActive = c.id === selectedCaseId
                const hasReadyDocs = c.document_count > 0
                return (
                  <li key={c.id}>
                    <button
                      id={`case-selector-${c.id}`}
                      role="option"
                      aria-selected={isActive}
                      className={`${styles.caseCard} ${isActive ? styles.caseCardActive : ''}`}
                      onClick={() => setSelectedCaseId(c.id)}
                    >
                      <span className={styles.caseName} title={c.name}>{c.name}</span>
                      <div className={styles.caseMeta}>
                        <span className={styles.caseTypeBadge}>
                          {CASE_TYPE_LABELS[c.case_type]}
                        </span>
                        <span className={styles.caseDocCount}>
                          <span
                            className={`${styles.docDot} ${hasReadyDocs ? styles.docDotReady : ''}`}
                          />
                          {c.document_count} doc{c.document_count !== 1 ? 's' : ''}
                        </span>
                      </div>
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </aside>

        {/* RIGHT — Graph panel */}
        <div className={styles.graphPanel}>
          {selectedCaseId ? (
            <EvidenceGraph
              key={selectedCaseId}
              caseId={selectedCaseId}
              documentCount={readyCount}
            />
          ) : (
            <div className={styles.graphEmpty}>
              <div className={styles.graphEmptyIcon}>◉</div>
              <span className={styles.arrowHint}>←</span>
              <h2 className={styles.graphEmptyTitle}>Select a case to begin</h2>
              <p className={styles.graphEmptyDesc}>
                Choose a case from the panel on the left. The AI will extract
                entities and relationships from your uploaded documents and
                render them as an interactive knowledge graph.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
