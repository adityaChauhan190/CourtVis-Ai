'use client'

import { useState } from 'react'
import { researchApi } from '@/lib/api'
import type { ResearchResponse, Precedent } from '@/lib/types'
import styles from './page.module.css'

const QUICK_PROMPTS = [
  { label: 'Medical Negligence (Jacob Mathew)', query: 'Medical negligence standard under Section 304A IPC / Section 106 BNS and independent doctor opinion requirement' },
  { label: 'Bail is the rule (Satender Antil)', query: 'Bail is the rule jail is exception guidelines under Satender Kumar Antil and Section 437/439 CrPC' },
  { label: 'Arrest safeguards (Arnesh Kumar)', query: 'Mandatory Section 41A CrPC notice and arrest guidelines in offences under 7 years under Arnesh Kumar' },
  { label: 'Circumstantial evidence (Sharad Birdhichand)', query: 'Five golden principles of circumstantial evidence and unbroken chain of custody under Sharad Birdhichand Sarda' },
  { label: 'Quashing FIR (Bhajan Lal)', query: 'Parameters for quashing criminal proceedings under Section 482 CrPC / Section 528 BNSS under State of Haryana v. Bhajan Lal' },
  { label: 'Dying Declaration admissibility', query: 'Evidentiary value of dying declaration under Section 32 Indian Evidence Act without doctor fitness certificate' },
]

export default function ResearchPage() {
  const [query, setQuery] = useState('')
  const [jurisdiction, setJurisdiction] = useState('Supreme Court of India')
  const [statute, setStatute] = useState('All Indian Statutes')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<ResearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  async function handleSearch(searchQuery?: string) {
    const q = (searchQuery ?? query).trim()
    if (!q) return

    setLoading(true)
    setError(null)
    try {
      const data = await researchApi.queryPrecedents(
        q,
        jurisdiction,
        statute === 'All Indian Statutes' ? undefined : statute,
      )
      setResults(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Research query failed.')
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  function handleQuickPrompt(q: string) {
    setQuery(q)
    handleSearch(q)
  }

  function copyCitation(p: Precedent, index: number) {
    const text = `${p.case_title}, ${p.citation} (${p.court})`
    navigator.clipboard.writeText(text)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  return (
    <div className={styles.page}>
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerIconWrap}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
          </div>
          <div>
            <h1 className={styles.headerTitle}>Indian Legal Precedents &amp; Research Hub</h1>
            <p className={styles.headerSub}>
              Query authoritative Supreme Court &amp; High Court rulings, extract core ratios, and explore dual statutory mappings (IPC/BNS, CrPC/BNSS, IEA/BSA) tailored for junior advocates.
            </p>
          </div>
        </div>
        <div className={styles.headerBadges}>
          <span className={styles.badgeGold}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18"/><path d="M9 8h1"/><path d="M14 8h1"/><rect x="2" y="3" width="20" height="18" rx="2"/></svg>
            Supreme Court &amp; High Courts
          </span>
          <span className={styles.badgeReady}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            IPC / BNS Dual Citations
          </span>
        </div>
      </header>

      {/* ── Search & Filter Controls ───────────────────────────── */}
      <div className={styles.searchSection}>
        <div className={styles.searchRow}>
          <div className={styles.searchInputWrapper}>
            <span className={styles.searchIcon}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </span>
            <input
              id="precedents-search-input"
              type="text"
              className={styles.searchInput}
              placeholder="Search legal doctrine, section, or proposition (e.g., Medical negligence 304A IPC, Bail in PMLA, Section 41A safeguards)…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            {query && (
              <button className={styles.clearBtn} onClick={() => setQuery('')}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            )}
          </div>
          <button
            id="precedents-search-btn"
            className={styles.searchBtn}
            onClick={() => handleSearch()}
            disabled={loading || !query.trim()}
          >
            {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Search Rulings'}
          </button>
        </div>

        {/* Filters */}
        <div className={styles.filterRow}>
          <div className={styles.filterGroup}>
            <span className={styles.filterLabel}>Jurisdiction:</span>
            <select
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
              className={styles.filterSelect}
            >
              <option value="Supreme Court of India">Supreme Court of India</option>
              <option value="Delhi High Court">Delhi High Court</option>
              <option value="Bombay High Court">Bombay High Court</option>
              <option value="Allahabad High Court">Allahabad High Court</option>
              <option value="All Indian Courts">All Indian Courts</option>
            </select>
          </div>

          <div className={styles.filterGroup}>
            <span className={styles.filterLabel}>Statute:</span>
            <select
              value={statute}
              onChange={(e) => setStatute(e.target.value)}
              className={styles.filterSelect}
            >
              <option value="All Indian Statutes">All Indian Statutes</option>
              <option value="BNS / IPC (Substantive Criminal)">BNS / IPC (Substantive Criminal)</option>
              <option value="BNSS / CrPC (Procedural / Bail)">BNSS / CrPC (Procedural / Bail)</option>
              <option value="BSA / Evidence Act (Admissibility)">BSA / Evidence Act (Admissibility)</option>
              <option value="Special Acts (PMLA, NDPS, POCSO)">Special Acts (PMLA, NDPS, POCSO)</option>
            </select>
          </div>
        </div>

        {/* Quick Suggestion Chips */}
        <div className={styles.chipsRow}>
          <span className={styles.chipsLabel}>Quick Precedents:</span>
          <div className={styles.chipsList}>
            {QUICK_PROMPTS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                className={styles.chip}
                onClick={() => handleQuickPrompt(p.query)}
              >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Search Results Area ─────────────────────────────────── */}
      <div className={styles.resultsArea}>
        {loading && (
          <div className={styles.loadingCard}>
            <div className={styles.loadingPulse}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </div>
            <p className={styles.loadingTitle}>Querying Indian Law Database &amp; Landmark Authorities…</p>
            <p className={styles.loadingSub}>Analyzing ratios, citations, and statutory sections under BNS/IPC and BNSS/CrPC.</p>
          </div>
        )}

        {error && (
          <div className={styles.errorCard}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            <p>{error}</p>
          </div>
        )}

        {!loading && !results && !error && (
          <div className={styles.placeholderCard}>
            <div className={styles.placeholderGavel}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="M12 8v4l3 3"/></svg>
            </div>
            <h3 className={styles.placeholderTitle}>Indian Law Precedent Finder</h3>
            <p className={styles.placeholderDesc}>
              Select any of the quick topics above or enter a legal proposition to extract reported landmark citations, legal ratios, and courtroom argument strategies.
            </p>
          </div>
        )}

        {!loading && results && (
          <div className={styles.resultsContent}>
            {/* Top Overview Grid */}
            <div className={styles.overviewGrid}>
              {/* Key Principles */}
              <div className={styles.principlesCard}>
                <h3 className={styles.cardHeading}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21h18"/><path d="M9 8h1"/><path d="M14 8h1"/><rect x="2" y="3" width="20" height="18" rx="2"/></svg>
                  Core Legal Principles
                </h3>
                <ul className={styles.principlesList}>
                  {results.key_principles.map((principle, idx) => (
                    <li key={idx}>{principle}</li>
                  ))}
                </ul>
              </div>

              {/* Statutory Provisions */}
              <div className={styles.statutesCard}>
                <h3 className={styles.cardHeading}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                  Statutory Provisions (Dual Mapped)
                </h3>
                <ul className={styles.statutesList}>
                  {results.statutory_provisions.map((provision, idx) => (
                    <li key={idx}>
                      <span className={styles.statuteTag}>{provision}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Precedents List */}
            <div className={styles.precedentsSection}>
              <div className={styles.precedentsSectionHeader}>
                <h3 className={styles.sectionTitle}>
                  Precedents ({results.precedents.length})
                </h3>
                <span className={styles.citationBadge}>
                  {results.library_count ?? 0} from your library{typeof results.library_size === 'number' ? ` of ${results.library_size}` : ''} · {results.ai_count ?? 0} AI-suggested
                </span>
              </div>

              {results.warnings && results.warnings.length > 0 && (
                <div className={styles.warningBox}>
                  {results.warnings.map((w, i) => <p key={i}>{w}</p>)}
                </div>
              )}

              <div className={styles.precedentsList}>
                {results.precedents.map((p, pIdx) => (
                  <div key={pIdx} className={styles.precedentCard}>
                    <div className={styles.precedentTop}>
                      <div>
                        <h4 className={styles.caseTitle}>{p.case_title}</h4>
                        <div className={styles.citationMeta}>
                          <span className={styles.citationText}>{p.citation}</span>
                          <span className={styles.courtBadge}>{p.court}</span>
                          {p.bench_size && (
                            <span className={styles.benchBadge}>{p.bench_size}</span>
                          )}
                          {p.source === 'library' || p.verify === false ? (
                            <span className={styles.sourceLibrary} title={p.source_document ?? undefined}>
                              ✓ In your library{p.page ? ` · p. ${p.page}` : ''}
                            </span>
                          ) : (
                            <span className={styles.sourceVerify} title="Suggested by AI and not found in your library — check the citation on SCC Online / Indian Kanoon before relying on it">
                              AI suggestion · verify citation
                            </span>
                          )}
                        </div>
                        {p.source_document && (
                          <div className={styles.sourceDoc}>{p.source_document}</div>
                        )}
                      </div>

                      <button
                        onClick={() => copyCitation(p, pIdx)}
                        className={styles.copyCitationBtn}
                        title="Copy official citation"
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                        {copiedIndex === pIdx ? 'Copied' : 'Copy Citation'}
                      </button>
                    </div>

                    {/* Ratio Decidendi */}
                    <div className={styles.ratioSection}>
                      <span className={styles.fieldLabel}>Ratio Decidendi:</span>
                      <p className={styles.ratioText}>{p.ratio_decidendi}</p>
                    </div>

                    {p.passage && (
                      <div className={styles.passageSection}>
                        <span className={styles.fieldLabel}>From the judgment{p.page ? ` (p. ${p.page})` : ''}:</span>
                        <p className={styles.passageText}>…{p.passage}…</p>
                      </div>
                    )}

                    {/* Key Quote */}
                    {p.key_quote && (
                      <div className={styles.quoteSection}>
                        <span className={styles.quoteIcon}>&ldquo;</span>
                        <p className={styles.quoteText}>{p.key_quote}</p>
                      </div>
                    )}

                    {/* Practical Application */}
                    {p.application_guidance && <div className={styles.guidanceSection}>
                      <span className={styles.guidanceLabel}>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18"/><path d="M9 8h1"/><path d="M14 8h1"/><rect x="2" y="3" width="20" height="18" rx="2"/></svg>
                        Application in Court Arguments:
                      </span>
                      <p className={styles.guidanceText}>{p.application_guidance}</p>
                    </div>}

                    {/* Statutory tags */}
                    {p.statutory_provisions && p.statutory_provisions.length > 0 && (
                      <div className={styles.statutoryPills}>
                        {p.statutory_provisions.map((sp, spIdx) => (
                          <span key={spIdx} className={styles.statutoryPill}>{sp}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {results.unverified_leads && results.unverified_leads.length > 0 && (
              <details className={styles.leadsBox}>
                <summary>
                  Unverified AI leads ({results.unverified_leads.length}) — not found in your library; check each on SCC Online / Indian Kanoon before relying on it
                </summary>
                <ul>
                  {results.unverified_leads.map((p, i) => (
                    <li key={i}>
                      <strong>{p.case_title}</strong> — {p.citation} ({p.court})
                      {p.ratio_decidendi && <div className={styles.leadRatio}>{p.ratio_decidendi}</div>}
                    </li>
                  ))}
                </ul>
              </details>
            )}

            {/* Senior Counsel Argument Strategy */}
            {results.argument_strategy && (
              <div className={styles.strategyCard}>
                <div className={styles.strategyHeader}>
                  <div className={styles.strategyIconWrap}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  </div>
                  <h3 className={styles.strategyTitle}>Courtroom Argument Strategy for Junior Advocates</h3>
                </div>
                <div className={styles.strategyBody}>
                  {results.argument_strategy.split('\n\n').map((para, idx) => (
                    <p key={idx}>{para}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
