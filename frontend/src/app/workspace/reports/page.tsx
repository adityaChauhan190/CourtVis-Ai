'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { casesApi, reportsApi } from '@/lib/api'
import type { Case, TrialBriefResponse } from '@/lib/types'
import { CASE_TYPE_LABELS } from '@/lib/types'
import styles from './page.module.css'

type ReportTab = 'chronology' | 'crossexam' | 'synopsis'

export default function ReportsPage() {
  const [cases, setCases] = useState<Case[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)
  const [brief, setBrief] = useState<TrialBriefResponse | null>(null)
  const [loadingCases, setLoadingCases] = useState(true)
  const [loadingBrief, setLoadingBrief] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<ReportTab>('chronology')
  const [copySuccess, setCopySuccess] = useState(false)

  // Load all cases on mount
  useEffect(() => {
    async function loadCases() {
      try {
        setLoadingCases(true)
        const res = await casesApi.list()
        setCases(res.cases || [])
        // Auto-select first case with documents or first case
        const withDocs = res.cases.find(c => c.document_count > 0)
        if (withDocs) {
          setSelectedCaseId(withDocs.id)
        } else if (res.cases.length > 0) {
          setSelectedCaseId(res.cases[0].id)
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load cases.')
      } finally {
        setLoadingCases(false)
      }
    }
    loadCases()
  }, [])

  // Load trial brief for selected case
  const fetchBrief = useCallback(async (caseId: string) => {
    try {
      setLoadingBrief(true)
      setError(null)
      const data = await reportsApi.getTrialBrief(caseId)
      setBrief(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate trial brief.')
    } finally {
      setLoadingBrief(false)
    }
  }, [])

  useEffect(() => {
    if (selectedCaseId) {
      fetchBrief(selectedCaseId)
    }
  }, [selectedCaseId, fetchBrief])

  const selectedCase = cases.find(c => c.id === selectedCaseId)

  // Copy full brief as Markdown
  function handleCopyMarkdown() {
    if (!brief) return
    let md = `# TRIAL PREPARATION BRIEF: ${brief.case_title}\n\n`

    md += `## 1. DATE-WISE CHRONOLOGY OF EVENTS\n\n`
    md += `| Date | Event Description | Evidentiary Significance | Source |\n`
    md += `| :--- | :--- | :--- | :--- |\n`
    brief.chronology.forEach(c => {
      md += `| ${c.date} | ${c.event} | ${c.significance} | ${c.source || 'N/A'} |\n`
    })

    md += `\n## 2. CROSS-EXAMINATION QUESTION BANK\n\n`
    brief.cross_examination.forEach(w => {
      md += `### Witness: ${w.witness} (${w.role || 'Deponent'})\n`
      w.questions.forEach((q, idx) => {
        md += `${idx + 1}. **Q:** ${q.question}\n   - *Objective:* ${q.objective}\n`
        if (q.contradiction) md += `   - *Contradiction Targeted:* ${q.contradiction}\n`
      })
      md += `\n`
    })

    md += `\n## 3. EXECUTIVE CASE SYNOPSIS\n\n${brief.synopsis}\n`

    if (brief.related_precedents?.length) {
      md += `\n## 4. RELATED PRECEDENTS (FROM YOUR LIBRARY)\n\n`
      brief.related_precedents.forEach(r => {
        md += `- **${r.case_title}**${r.citation ? `, ${r.citation}` : ''}${r.court ? ` (${r.court})` : ''}${r.ratio_decidendi ? ` — ${r.ratio_decidendi}` : ''}\n`
      })
    }

    navigator.clipboard.writeText(md)
    setCopySuccess(true)
    setTimeout(() => setCopySuccess(false), 2500)
  }

  function handlePrint() {
    window.print()
  }

  return (
    <div className={styles.page}>
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerIconWrap}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          </div>
          <div>
            <h1 className={styles.headerTitle}>Trial Prep &amp; Brief Generator</h1>
            <p className={styles.headerSub}>
              Instantly compile date-wise chronologies, targeted witness cross-examination banks, and executive trial briefs for Senior Counsel.
            </p>
          </div>
        </div>
        <div className={styles.headerActions}>
          <button
            onClick={handleCopyMarkdown}
            disabled={!brief || loadingBrief}
            className={styles.copyBtn}
            title="Copy formatted brief as Markdown"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            {copySuccess ? 'Copied!' : 'Copy as Markdown'}
          </button>
          <button
            onClick={handlePrint}
            disabled={!brief || loadingBrief}
            className={styles.printBtn}
            title="Print or export as PDF"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            Print / Export
          </button>
        </div>
      </header>

      {/* ── Case Selector Bar ──────────────────────────────────── */}
      <div className={styles.caseSelectorBar}>
        <div className={styles.selectorGroup}>
          <label htmlFor="case-select" className={styles.selectorLabel}>Select Case Matter:</label>
          <select
            id="case-select"
            value={selectedCaseId ?? ''}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className={styles.caseDropdown}
            disabled={loadingCases || cases.length === 0}
          >
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({CASE_TYPE_LABELS[c.case_type] ?? c.case_type}) — {c.document_count} doc{c.document_count === 1 ? '' : 's'}
              </option>
            ))}
          </select>
        </div>

        {selectedCase && (
          <div className={styles.caseSummaryMeta}>
            <span className={styles.metaBadge}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
              {selectedCase.document_count} Document{selectedCase.document_count === 1 ? '' : 's'}
            </span>
            <span className={styles.metaBadge}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              {selectedCase.user_role ? `Role: ${selectedCase.user_role}` : 'Litigation'}
            </span>
            <button
              onClick={() => selectedCaseId && fetchBrief(selectedCaseId)}
              className={styles.regenerateBtn}
              disabled={loadingBrief}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
              Refresh Brief
            </button>
          </div>
        )}
      </div>

      {/* ── Main Workspace ────────────────────────────────────── */}
      <div className={styles.workspace}>
        {/* Navigation Tabs */}
        <div className={styles.tabsNav}>
          <button
            className={`${styles.tabBtn} ${activeTab === 'chronology' ? styles.tabBtnActive : ''}`}
            onClick={() => setActiveTab('chronology')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            Chronology of Events
            {brief && <span className={styles.tabCount}>{brief.chronology.length}</span>}
          </button>
          <button
            className={`${styles.tabBtn} ${activeTab === 'crossexam' ? styles.tabBtnActive : ''}`}
            onClick={() => setActiveTab('crossexam')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
            Cross-Examination Bank
            {brief && <span className={styles.tabCount}>{brief.cross_examination.length}</span>}
          </button>
          <button
            className={`${styles.tabBtn} ${activeTab === 'synopsis' ? styles.tabBtnActive : ''}`}
            onClick={() => setActiveTab('synopsis')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
            Executive Synopsis
          </button>
        </div>

        {/* Loading State */}
        {loadingBrief && (
          <div className={styles.loadingState}>
            <div className={styles.loadingPulse}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            </div>
            <p className={styles.loadingTitle}>Analyzing case record and generating trial brief…</p>
            <p className={styles.loadingSub}>Extracting dates, witness depositions, and statutory sections under Indian law.</p>
          </div>
        )}

        {/* Error State */}
        {!loadingBrief && error && (
          <div className={styles.errorState}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            <p>{error}</p>
            <button onClick={() => selectedCaseId && fetchBrief(selectedCaseId)} className={styles.retryBtn}>
              Retry Generation
            </button>
          </div>
        )}

        {/* Sections the AI could not complete are reported, never filled with template text */}
        {!loadingBrief && !error && brief?.errors && brief.errors.length > 0 && (
          <div className={styles.errorState} style={{ marginBottom: '1rem' }}>
            {brief.errors.map((e, i) => <p key={i}>{e}</p>)}
            <button onClick={() => selectedCaseId && fetchBrief(selectedCaseId)} className={styles.retryBtn}>
              Regenerate
            </button>
          </div>
        )}

        {/* Tab 1: Chronology of Events */}
        {!loadingBrief && !error && brief && activeTab === 'chronology' && (
          <div className={styles.tabContent}>
            <div className={styles.tabHeader}>
              <div>
                <h3 className={styles.tabHeading}>Date-Wise Chronology of Events</h3>
                <p className={styles.tabDescription}>
                  Structured factual timeline in sequential order, demonstrating procedural compliance and evidentiary milestones.
                </p>
              </div>
              <span className={styles.docCountBadge}>Based on {brief.doc_count} source documents</span>
            </div>

            <div className={styles.tableCard}>
              <table className={styles.chronologyTable}>
                <thead>
                  <tr>
                    <th style={{ width: '16%' }}>Date / Time</th>
                    <th style={{ width: '44%' }}>Event Description</th>
                    <th style={{ width: '25%' }}>Evidentiary Significance</th>
                    <th style={{ width: '15%' }}>Source Exhibit</th>
                  </tr>
                </thead>
                <tbody>
                  {brief.chronology.map((item, i) => (
                    <tr key={i}>
                      <td className={styles.dateCell}>{item.date}</td>
                      <td className={styles.eventCell}>{item.event}</td>
                      <td className={styles.significanceCell}>{item.significance}</td>
                      <td className={styles.sourceCell}>
                        <span className={styles.sourceBadge}>{item.source || 'Case Record'}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Cross-Examination Bank */}
        {!loadingBrief && !error && brief && activeTab === 'crossexam' && (
          <div className={styles.tabContent}>
            <div className={styles.tabHeader}>
              <div>
                <h3 className={styles.tabHeading}>Witness Cross-Examination Bank</h3>
                <p className={styles.tabDescription}>
                  Targeted questions categorized by witness, formulated to impeach credibility and expose contradictions.
                </p>
              </div>
            </div>

            <div className={styles.witnessList}>
              {brief.cross_examination.map((witnessItem, wIdx) => (
                <div key={wIdx} className={styles.witnessCard}>
                  <div className={styles.witnessHeader}>
                    <div className={styles.witnessIdentity}>
                      <span className={styles.witnessAvatar}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                      </span>
                      <div>
                        <h4 className={styles.witnessName}>{witnessItem.witness}</h4>
                        <span className={styles.witnessRoleBadge}>{witnessItem.role || 'Deponent'}</span>
                      </div>
                    </div>
                    <span className={styles.questionCountBadge}>
                      {witnessItem.questions.length} Question{witnessItem.questions.length === 1 ? '' : 's'}
                    </span>
                  </div>

                  <div className={styles.questionList}>
                    {witnessItem.questions.map((q, qIdx) => (
                      <div key={qIdx} className={styles.questionItem}>
                        <div className={styles.questionNum}>Q{qIdx + 1}</div>
                        <div className={styles.questionBody}>
                          <p className={styles.questionText}>&quot;{q.question}&quot;</p>
                          <div className={styles.questionMeta}>
                            <div className={styles.objectiveTag}>
                              <strong>Tactical Objective:</strong> {q.objective}
                            </div>
                            {q.contradiction && (
                              <div className={styles.contradictionTag}>
                                <strong>Contradiction Target:</strong> {q.contradiction}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Executive Synopsis */}
        {!loadingBrief && !error && brief && activeTab === 'synopsis' && (
          <div className={styles.tabContent}>
            <div className={styles.tabHeader}>
              <div>
                <h3 className={styles.tabHeading}>Executive Legal Synopsis</h3>
                <p className={styles.tabDescription}>
                  Comprehensive strategic trial memorandum covering theories of the case, statutory sections, and recommended submissions.
                </p>
              </div>
            </div>

            <div className={styles.synopsisCard}>
              <div className={styles.synopsisProse}>
                {renderSynopsis(brief.synopsis)}
              </div>
            </div>

            {brief.related_precedents && brief.related_precedents.length > 0 && (
              <div className={styles.synopsisCard} style={{ marginTop: '1rem' }}>
                <div className={styles.synopsisProse}>
                  <h3 className={styles.synopsisH2}>Related precedents from your library</h3>
                  <ul className={styles.synopsisBulletList}>
                    {brief.related_precedents.map((r, i) => (
                      <li key={i}>
                        <strong>{r.case_title}</strong>{r.citation ? `, ${r.citation}` : ''}{r.court ? ` (${r.court})` : ''}
                        {r.ratio_decidendi ? ` — ${r.ratio_decidendi}` : ''}
                        <span style={{ opacity: 0.6 }}> · {r.source_document}{r.page ? `, p. ${r.page}` : ''}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty / Zero Docs State */}
        {!loadingBrief && !brief && (
          <div className={styles.emptyState}>
            <div className={styles.emptyIconWrap}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            </div>
            <h3>No Documents in this Case</h3>
            <p>Upload case PDFs, charge sheets, or petitions to generate an AI trial brief.</p>
            {selectedCase && (
              <Link href={`/workspace/cases/${selectedCase.id}`} className={styles.uploadBtn}>
                Upload Documents Now →
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/** Bold (**text**) inside a line. */
function inline(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : part,
  )
}

/** Line-aware Markdown: headings, bullet runs and paragraphs (the model may omit blank lines). */
function renderSynopsis(md: string) {
  const out: React.ReactNode[] = []
  let bullets: string[] = []
  const flush = () => {
    if (bullets.length) {
      out.push(
        <ul key={`ul-${out.length}`} className={styles.synopsisBulletList}>
          {bullets.map((b, i) => <li key={i}>{inline(b)}</li>)}
        </ul>,
      )
      bullets = []
    }
  }
  md.split('\n').forEach(raw => {
    const line = raw.trim()
    if (!line) { flush(); return }
    if (/^[-*•]\s+/.test(line)) { bullets.push(line.replace(/^[-*•]\s+/, '')); return }
    flush()
    if (line.startsWith('### ')) out.push(<h4 key={out.length} className={styles.synopsisH3}>{inline(line.slice(4))}</h4>)
    else if (line.startsWith('## ')) out.push(<h3 key={out.length} className={styles.synopsisH2}>{inline(line.slice(3))}</h3>)
    else if (line.startsWith('# ')) out.push(<h2 key={out.length} className={styles.synopsisH1}>{inline(line.slice(2))}</h2>)
    else out.push(<p key={out.length} className={styles.synopsisP}>{inline(line)}</p>)
  })
  flush()
  return out
}
