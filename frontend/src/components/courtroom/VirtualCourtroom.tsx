'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { courtroomApi } from '@/lib/api'
import type { SessionTurn, CourtroomResponse, VerdictResponse, TrialPhase, JudgeTemperament } from '@/lib/types'
import styles from './VirtualCourtroom.module.css'

// ── Types ─────────────────────────────────────────────────────────────────────

interface DisplayTurn {
  id: string
  speaker: 'lawyer' | 'judge' | 'opposing' | 'system'
  content: string
  timestamp: Date
}

const PHASE_LABELS: Record<TrialPhase, string> = {
  opening: 'Opening Statements',
  examination: 'Examination of Evidence',
  arguments: 'Legal Arguments',
  closing: 'Closing Arguments',
}

const PHASE_ORDER: TrialPhase[] = ['opening', 'examination', 'arguments', 'closing']

// ── Props ────────────────────────────────────────────────────────────────────

interface Props {
  caseId: string
  documentCount: number
  caseName?: string
}

// ── Helper ────────────────────────────────────────────────────────────────────

let turnCounter = 0
function newTurnId() { return `turn-${++turnCounter}-${Date.now()}` }

function formatTime(d: Date) {
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// ── Component ─────────────────────────────────────────────────────────────────

export function VirtualCourtroom({ caseId, documentCount, caseName }: Props) {
  const [sessionStarted, setSessionStarted] = useState(false)
  const [displayTurns, setDisplayTurns] = useState<DisplayTurn[]>([])
  const [sessionHistory, setSessionHistory] = useState<SessionTurn[]>([])
  const [input, setInput] = useState('')
  const [judgeTemperament, setJudgeTemperament] = useState<JudgeTemperament>('balanced')
  const [isLoading, setIsLoading] = useState(false)
  const [phase, setPhase] = useState<TrialPhase>('opening')
  const [verdict, setVerdict] = useState<VerdictResponse | null>(null)
  const [verdictLoading, setVerdictLoading] = useState(false)
  const [sessionEnded, setSessionEnded] = useState(false)
  const [objections, setObjections] = useState<string[]>([])

  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const hasDocuments = documentCount > 0

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [displayTurns, verdict])

  function addDisplay(speaker: DisplayTurn['speaker'], content: string) {
    setDisplayTurns(prev => [...prev, {
      id: newTurnId(),
      speaker,
      content,
      timestamp: new Date(),
    }])
  }

  function extractObjections(text: string): string[] {
    const matches = text.match(/\b(objection|I object|overruled|sustained)[^.!?]*[.!?]/gi)
    return matches ? matches.slice(0, 3) : []
  }

  function startSession() {
    setSessionStarted(true)
    setDisplayTurns([])
    setSessionHistory([])
    setVerdict(null)
    setSessionEnded(false)
    setObjections([])
    setPhase('opening')

    setTimeout(() => {
      addDisplay('system', '⚖ All rise. The Virtual Courtroom is now in session.')
      setTimeout(() => {
        const temperamentPrefix = judgeTemperament === 'strict'
          ? ' The Court will strictly enforce procedure and rules of evidence.'
          : judgeTemperament === 'inquisitive'
          ? ' The Court expects counsel to be thoroughly prepared on the factual record.'
          : ''
        addDisplay('judge', `THE COURT: This session is called to order. We are here to examine the matter of ${caseName ? `"${caseName}"` : 'this case'}.${temperamentPrefix} Counsel, you may deliver your opening statement.`)
      }, 800)
    }, 300)
  }

  const submitTurn = useCallback(async () => {
    const text = input.trim()
    if (!text || isLoading || sessionEnded) return

    addDisplay('lawyer', text)

    const newSessionTurn: SessionTurn = { speaker: 'lawyer', content: text }
    const updatedHistory = [...sessionHistory, newSessionTurn]
    setSessionHistory(updatedHistory)
    setInput('')
    setIsLoading(true)

    try {
      const response: CourtroomResponse = await courtroomApi.submitTurn(
        caseId,
        text,
        updatedHistory,
        phase,
        judgeTemperament,
      )

      // Extract and track objections
      const judgeObjections = extractObjections(response.judge_response)
      const opposingObjections = extractObjections(response.opposing_response)
      const allObjections = [...judgeObjections, ...opposingObjections]
      if (allObjections.length > 0) {
        setObjections(prev => [...prev, ...allObjections].slice(-6))
      }

      // Add judge response with delay for dramatic effect
      if (response.judge_response !== '[SILENCE]') {
        setTimeout(() => {
          addDisplay('judge', response.judge_response)
          setSessionHistory(prev => [...prev,
            { speaker: 'judge', content: response.judge_response }
          ])
        }, 300)
      }

      // Add opposing counsel response
      setTimeout(() => {
        addDisplay('opposing', response.opposing_response)
        setSessionHistory(prev => [...prev,
          { speaker: 'opposing', content: response.opposing_response }
        ])
      }, 700)

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An error occurred.'
      addDisplay('system', `⚠ Error: ${msg}`)
    } finally {
      setIsLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [input, isLoading, sessionEnded, sessionHistory, caseId, phase, judgeTemperament])

  const requestVerdict = useCallback(async () => {
    if (verdictLoading || sessionEnded) return
    setVerdictLoading(true)
    addDisplay('system', '⚖ Counsel, please be seated. The Court will now deliberate and deliver its verdict.')

    try {
      const v = await courtroomApi.getVerdict(caseId, sessionHistory)
      setVerdict(v)
      setSessionEnded(true)

      // Add final judge statement
      setTimeout(() => {
        addDisplay('judge', `THE COURT: Having considered all evidence and arguments presented, the Court is ready to deliver its verdict. ${v.outcome}.`)
      }, 500)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Verdict generation failed.'
      addDisplay('system', `⚠ ${msg}`)
    } finally {
      setVerdictLoading(false)
    }
  }, [caseId, sessionHistory, verdictLoading, sessionEnded])

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submitTurn()
    }
  }

  const currentPhaseIndex = PHASE_ORDER.indexOf(phase)

  // ── Pre-session: Landing ──────────────────────────────────────────────────
  if (!sessionStarted) {
    return (
      <div className={styles.container}>
        <div className={styles.landing}>
          <div className={styles.landingGavel}>⚖</div>
          <h2 className={`${styles.landingTitle} font-display`}>Virtual Courtroom</h2>
          <p className={styles.landingDesc}>
            Step into the courtroom. You play the lawyer — the AI simultaneously acts as
            <strong> The Judge</strong> and <strong>Opposing Counsel</strong>, both grounded
            in your case documents.
          </p>
          <div className={styles.landingRoles}>
            <div className={styles.role}>
              <span className={styles.roleIcon} style={{ color: '#c4923a' }}>👨‍⚖️</span>
              <span className={styles.roleName}>You</span>
              <span className={styles.roleLabel}>Lead Counsel</span>
            </div>
            <div className={styles.roleVs}>vs</div>
            <div className={styles.role}>
              <span className={styles.roleIcon} style={{ color: '#6b1e2a' }}>⚖</span>
              <span className={styles.roleName}>AI Judge</span>
              <span className={styles.roleLabel}>Presiding</span>
            </div>
            <div className={styles.roleVs}>+</div>
            <div className={styles.role}>
              <span className={styles.roleIcon} style={{ color: '#2a5a7a' }}>🎯</span>
              <span className={styles.roleName}>AI Opposing</span>
              <span className={styles.roleLabel}>Adversary</span>
            </div>
          </div>

          {/* Judge Temperament Selector */}
          <div className={styles.landingTemperament}>
            <p className={styles.temperamentHeading}>Presiding Judge Demeanour</p>
            <div className={styles.temperamentGrid}>
              {(['balanced', 'strict', 'inquisitive'] as JudgeTemperament[]).map(t => (
                <button
                  key={t}
                  type="button"
                  className={`${styles.temperamentCard} ${judgeTemperament === t ? styles.temperamentCardActive : ''}`}
                  onClick={() => setJudgeTemperament(t)}
                >
                  <div className={styles.temperamentCardTop}>
                    <span className={styles.temperamentIcon}>
                      {t === 'balanced' && '⚖'}
                      {t === 'strict' && '⚡'}
                      {t === 'inquisitive' && '🔍'}
                    </span>
                    <span className={styles.temperamentTitle}>
                      {t === 'balanced' && 'Balanced Judge'}
                      {t === 'strict' && 'Strict Proceduralist'}
                      {t === 'inquisitive' && 'Inquisitive Socratic'}
                    </span>
                  </div>
                  <p className={styles.temperamentDesc}>
                    {t === 'balanced' && 'Weighs submissions neutrally with dignified composure.'}
                    {t === 'strict' && 'Demands statutory citations and sustains objections swiftly.'}
                    {t === 'inquisitive' && 'Probes counsel logic and dissects factual contradictions.'}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {!hasDocuments && (
            <p className={styles.landingWarning}>
              ⚠ Upload and process case documents before starting a courtroom session.
            </p>
          )}

          <button
            className={styles.startBtn}
            onClick={startSession}
            disabled={!hasDocuments}
            id="start-courtroom-btn"
          >
            ⚖ Call to Order — Begin Session
          </button>

          <div className={styles.landingTips}>
            <p className={styles.tipTitle}>Courtroom tips</p>
            <ul>
              <li>Make statements, present arguments, or move for admission of evidence</li>
              <li>Raise objections with "Objection, Your Honour — …"</li>
              <li>Cross-examine with targeted questions</li>
              <li>Advance phases: Opening → Examination → Arguments → Closing</li>
              <li>Request a verdict anytime with the "Request Verdict" button</li>
            </ul>
          </div>
        </div>
      </div>
    )
  }

  // ── Active Session ────────────────────────────────────────────────────────
  return (
    <div className={styles.container}>
      {/* ── Header / Phase Bar ──────────────────────────────────────────── */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerIcon}>⚖</span>
          <div>
            <p className={styles.headerTitle}>Virtual Courtroom</p>
            <p className={styles.headerSub}>{caseName ?? 'Case Session'}</p>
          </div>
        </div>

        <div className={styles.phaseBar}>
          {PHASE_ORDER.map((p, i) => (
            <button
              key={p}
              className={`${styles.phaseBtn} ${phase === p ? styles.phaseBtnActive : ''} ${i < currentPhaseIndex ? styles.phaseBtnDone : ''}`}
              onClick={() => !sessionEnded && setPhase(p)}
              disabled={sessionEnded}
              title={PHASE_LABELS[p]}
            >
              {PHASE_LABELS[p]}
            </button>
          ))}
        </div>

        <div className={styles.headerRight}>
          {!sessionEnded && (
            <button
              className={styles.verdictBtn}
              onClick={requestVerdict}
              disabled={verdictLoading || displayTurns.length < 3}
              id="request-verdict-btn"
            >
              {verdictLoading ? <span className="spinner" style={{ width: 12, height: 12 }} /> : '⚖'}
              {verdictLoading ? ' Deliberating…' : ' Request Verdict'}
            </button>
          )}
          <button
            className={styles.newSessionBtn}
            onClick={() => setSessionStarted(false)}
          >
            ↩ New Session
          </button>
        </div>
      </div>

      {/* ── Transcript ──────────────────────────────────────────────────── */}
      <div className={styles.transcript}>
        {displayTurns.map(turn => (
          <CourtTurn key={turn.id} turn={turn} />
        ))}

        {isLoading && (
          <div className={styles.deliberating}>
            <span className="spinner" style={{ width: 14, height: 14 }} />
            <span>Court deliberating…</span>
          </div>
        )}

        {/* ── Verdict panel ─────────────────────────────────────────── */}
        {verdict && (
          <div className={styles.verdictPanel}>
            <div className={styles.verdictGavel}>⚖</div>
            <p className={styles.verdictLabel}>VERDICT</p>
            <h3 className={`${styles.verdictText} font-display`}>{verdict.verdict}</h3>
            <p className={styles.verdictOutcome}>{verdict.outcome}</p>
            <div className={styles.verdictReasoning}>
              <p className={styles.verdictReasoningTitle}>Judicial Reasoning</p>
              <p className={styles.verdictReasoningText}>{verdict.reasoning}</p>
            </div>
            {verdict.key_findings.length > 0 && (
              <div className={styles.verdictFindings}>
                <p className={styles.verdictFindingsTitle}>Key Findings</p>
                <ul>
                  {verdict.key_findings.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Junior Lawyer Advocacy Scorecard */}
            {verdict.scorecard && (
              <div className={styles.scorecardContainer}>
                <div className={styles.scorecardHeader}>
                  <div>
                    <span className={styles.scorecardBadge}>PERFORMANCE EVALUATION</span>
                    <h4 className={styles.scorecardTitle}>Junior Advocate Advocacy Scorecard</h4>
                    <p className={styles.scorecardSubtitle}>
                      Objective trial evaluation based on evidentiary citations and courtroom rules
                    </p>
                  </div>
                  <div className={styles.overallScoreCircle}>
                    <span className={styles.overallScoreVal}>{verdict.scorecard.overall_score}</span>
                    <span className={styles.overallScoreTotal}>/100</span>
                  </div>
                </div>

                <div className={styles.metricsGrid}>
                  <div className={styles.metricItem}>
                    <div className={styles.metricLabelRow}>
                      <span className={styles.metricName}>Legal Reasoning</span>
                      <span className={styles.metricValue}>{verdict.scorecard.legal_reasoning_score}/100</span>
                    </div>
                    <div className={styles.progressBar}>
                      <div
                        className={styles.progressFill}
                        style={{ width: `${verdict.scorecard.legal_reasoning_score}%` }}
                      />
                    </div>
                  </div>

                  <div className={styles.metricItem}>
                    <div className={styles.metricLabelRow}>
                      <span className={styles.metricName}>Evidence Grounding</span>
                      <span className={styles.metricValue}>{verdict.scorecard.evidence_grounding_score}/100</span>
                    </div>
                    <div className={styles.progressBar}>
                      <div
                        className={styles.progressFill}
                        style={{ width: `${verdict.scorecard.evidence_grounding_score}%` }}
                      />
                    </div>
                  </div>

                  <div className={styles.metricItem}>
                    <div className={styles.metricLabelRow}>
                      <span className={styles.metricName}>Courtroom Decorum</span>
                      <span className={styles.metricValue}>{verdict.scorecard.courtroom_decorum_score}/100</span>
                    </div>
                    <div className={styles.progressBar}>
                      <div
                        className={styles.progressFill}
                        style={{ width: `${verdict.scorecard.courtroom_decorum_score}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className={styles.feedbackColumns}>
                  {verdict.scorecard.strengths?.length > 0 && (
                    <div className={styles.feedbackCol}>
                      <p className={styles.feedbackHeading}>🌟 Key Strengths</p>
                      <ul className={styles.feedbackList}>
                        {verdict.scorecard.strengths.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {verdict.scorecard.areas_for_improvement?.length > 0 && (
                    <div className={styles.feedbackCol}>
                      <p className={styles.feedbackHeading}>🎯 Areas for Improvement</p>
                      <ul className={styles.feedbackList}>
                        {verdict.scorecard.areas_for_improvement.map((a, i) => (
                          <li key={i}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {verdict.scorecard.mentor_notes && (
                  <div className={styles.mentorBox}>
                    <span className={styles.mentorIcon}>👨‍⚖️ Senior Advocate Mentorship</span>
                    <p className={styles.mentorQuote}>"{verdict.scorecard.mentor_notes}"</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Objection Log sidebar ────────────────────────────────────── */}
      {objections.length > 0 && (
        <div className={styles.objectionLog}>
          <p className={styles.objectionLogTitle}>⚠ Objection Log</p>
          {objections.map((o, i) => (
            <p key={i} className={styles.objectionItem}>{o}</p>
          ))}
        </div>
      )}

      {/* ── Input Area ──────────────────────────────────────────────── */}
      {!sessionEnded && (
        <div className={styles.inputArea}>
          <div className={styles.inputRole}>
            <span className={styles.inputRoleLabel}>👨‍⚖️ Lead Counsel</span>
            <span className={styles.inputPhaseLabel}>{PHASE_LABELS[phase]}</span>
          </div>
          <div className={styles.inputRow}>
            <textarea
              ref={inputRef}
              id="courtroom-input"
              className={styles.input}
              placeholder="State your argument, make a motion, raise an objection, or ask a witness a question… (Enter to submit)"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={2}
              disabled={isLoading}
            />
            <button
              id="courtroom-submit-btn"
              className={styles.submitBtn}
              onClick={submitTurn}
              disabled={isLoading || !input.trim()}
              aria-label="Submit statement"
            >
              {isLoading ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '→'}
            </button>
          </div>
          <p className={styles.inputHint}>
            Enter to submit · Shift+Enter for new line · Be specific and cite evidence
          </p>
        </div>
      )}

      {sessionEnded && (
        <div className={styles.sessionEndedBar}>
          Session concluded. <button className={styles.restartLink} onClick={() => setSessionStarted(false)}>Start a new session →</button>
        </div>
      )}
    </div>
  )
}

// ── Court Turn ────────────────────────────────────────────────────────────────

function CourtTurn({ turn }: { turn: DisplayTurn }) {
  const configs = {
    system: { label: '', icon: '', cls: styles.turnSystem },
    judge:    { label: 'THE COURT',        icon: '⚖', cls: styles.turnJudge },
    opposing: { label: 'OPPOSING COUNSEL', icon: '🎯', cls: styles.turnOpposing },
    lawyer:   { label: 'LEAD COUNSEL',     icon: '👨‍⚖️', cls: styles.turnLawyer },
  }
  const cfg = configs[turn.speaker]

  if (turn.speaker === 'system') {
    return (
      <div className={styles.turnSystem}>
        <span>{turn.content}</span>
        <span className={styles.turnTime}>{formatTime(turn.timestamp)}</span>
      </div>
    )
  }

  return (
    <div className={`${styles.turn} ${cfg.cls}`}>
      <div className={styles.turnHeader}>
        <span className={styles.turnIcon}>{cfg.icon}</span>
        <span className={styles.turnLabel}>{cfg.label}</span>
        <span className={styles.turnTime}>{formatTime(turn.timestamp)}</span>
      </div>
      <div className={styles.turnContent}>
        {/* Strip the "THE COURT:" / "OPPOSING COUNSEL:" prefix if present */}
        {turn.content.replace(/^(THE COURT:|OPPOSING COUNSEL:)\s*/i, '')}
      </div>
    </div>
  )
}
