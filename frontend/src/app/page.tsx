'use client'
import Link from 'next/link'
import styles from './landing.module.css'

export default function LandingPage() {
  return (
    <div className={styles.page}>
      {/* ── Navigation ─────────────────────────────────────────── */}
      <nav className={styles.nav}>
        <div className={styles.navInner}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>⚖</span>
            <span className={styles.logoText}>COURT VISION AI</span>
          </div>
          <div className={styles.navLinks}>
            <a href="#product" className={styles.navLink}>Product</a>
            <a href="#how-it-works" className={styles.navLink}>How It Works</a>
            <a href="#technology" className={styles.navLink}>Technology</a>
            <a href="#about" className={styles.navLink}>About</a>
          </div>
          <Link href="/workspace" className={`btn btn-secondary ${styles.navCta}`}>
            Enter Workspace
          </Link>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────── */}
      <section className={styles.hero} id="product">
        <div className={styles.heroGlow} aria-hidden="true" />
        <div className={styles.heroBg} aria-hidden="true">
          <LegalVisual />
        </div>

        <div className={`container ${styles.heroContent}`}>
          <div className={styles.heroText}>
            <p className="text-eyebrow">AI-Powered Legal Case Preparation</p>
            <h1 className={`text-display-2xl ${styles.heroHeading}`}>
              Prepare Before<br />
              <em>You Enter the</em><br />
              Courtroom.
            </h1>
            <p className={styles.heroSubcopy}>
              Transform complex case files into structured case intelligence,
              evidence trails and trial-ready insights.
            </p>
            <div className={styles.heroCtas}>
              <Link href="/workspace" className="btn btn-primary btn-lg">
                Analyze a Case
              </Link>
              <a href="#how-it-works" className="btn btn-secondary btn-lg">
                Explore the Platform
              </a>
            </div>
            <p className={styles.heroDisclaimer}>
              Educational &amp; research use only. Not a substitute for qualified legal counsel.
            </p>
          </div>
        </div>
      </section>

      {/* ── Product Story ───────────────────────────────────────── */}
      <section className={styles.storySection} id="how-it-works">
        <div className="container">
          <div className={styles.sectionHeader}>
            <p className="text-eyebrow">The Intelligence Pipeline</p>
            <h2 className={`text-display-md ${styles.sectionTitle}`}>
              From Case File to Courtroom
            </h2>
            <div className="divider-gold" style={{ margin: '20px 0 0' }} />
          </div>

          <div className={styles.storySteps}>
            {STORY_STEPS.map((step, i) => (
              <div key={i} className={`${styles.storyStep} ${step.active ? styles.storyStepActive : ''}`}>
                <div className={styles.stepNumber}>{String(i + 1).padStart(2, '0')}</div>
                <div className={styles.stepConnector} aria-hidden="true" />
                <div className={styles.stepContent}>
                  <h3 className={styles.stepTitle}>{step.title}</h3>
                  <p className={styles.stepDesc}>{step.description}</p>
                  {!step.active && (
                    <span className="badge badge-coming-soon">Coming Soon</span>
                  )}
                  {step.active && (
                    <span className="badge badge-ready">Phase 1 — Live</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Technology ─────────────────────────────────────────── */}
      <section className={styles.techSection} id="technology">
        <div className="container">
          <div className={styles.sectionHeader}>
            <p className="text-eyebrow">Intelligence Architecture</p>
            <h2 className={`text-display-md ${styles.sectionTitle}`}>
              Built for the Complexity<br />of Legal Reasoning
            </h2>
            <div className="divider-gold" style={{ margin: '20px 0 0' }} />
          </div>

          <div className={styles.techGrid}>
            {TECH_CARDS.map((card, i) => (
              <div key={i} className={`${styles.techCard} ${card.upcoming ? styles.techCardUpcoming : ''}`}>
                <div className={styles.techCardIcon}>{card.icon}</div>
                <div>
                  <p className="text-eyebrow" style={{ marginBottom: '8px' }}>{card.label}</p>
                  <h3 className={styles.techCardTitle}>{card.title}</h3>
                  <p className={styles.techCardDesc}>{card.description}</p>
                  {card.upcoming && (
                    <span className="badge badge-coming-soon" style={{ marginTop: '12px' }}>Upcoming</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Banner ─────────────────────────────────────────── */}
      <section className={styles.ctaBanner} id="about">
        <div className="container-narrow">
          <p className="text-eyebrow">Begin Your Preparation</p>
          <h2 className={`text-display-lg ${styles.ctaTitle}`}>
            Your chambers await, Counsel.
          </h2>
          <p className={styles.ctaSubcopy}>
            Upload your case documents. Let the intelligence begin.
          </p>
          <Link href="/workspace" className="btn btn-primary btn-lg">
            Enter Workspace →
          </Link>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className={styles.footer}>
        <div className="container">
          <div className={styles.footerTop}>
            <div className={styles.footerBrand}>
              <div className={styles.logo} style={{ marginBottom: '12px' }}>
                <span className={styles.logoIcon}>⚖</span>
                <span className={styles.logoText}>COURT VISION AI</span>
              </div>
              <p className={styles.footerTagline}>
                AI-powered preparation for the next generation of legal professionals.
              </p>
            </div>
            <div className={styles.footerLinks}>
              <a href="#product" className={styles.footerLink}>Product</a>
              <a href="#technology" className={styles.footerLink}>Technology</a>
              <a href="#" className={styles.footerLink}>Privacy</a>
              <a href="#" className={styles.footerLink}>Terms</a>
              <a href="#" className={styles.footerLink}>Contact</a>
            </div>
          </div>
          <div className="divider" style={{ margin: '32px 0' }} />
          <div className={styles.footerBottom}>
            <p className={styles.footerDisclaimer}>
              <strong>Educational and research assistance only.</strong> Court Vision AI does not provide legal advice
              or replace qualified legal professionals. All AI-generated insights should be independently verified.
            </p>
            <p className={styles.footerCopy}>
              © {new Date().getFullYear()} Court Vision AI — Phase 1
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

// ── Legal Visual ─────────────────────────────────────────────────────────────

function LegalVisual() {
  return (
    <svg
      className={styles.legalVisual}
      viewBox="0 0 800 600"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Document stacks */}
      <rect x="80" y="150" width="220" height="280" rx="4" fill="#1c1a17" stroke="#2e2922" strokeWidth="1" />
      <rect x="88" y="158" width="220" height="280" rx="4" fill="#1a1916" stroke="#2e2922" strokeWidth="1" />
      <rect x="96" y="166" width="220" height="280" rx="4" fill="#201e1b" stroke="#3d3520" strokeWidth="1" />
      {/* Document lines */}
      {[200, 218, 236, 254, 272, 310, 328, 346].map((y, i) => (
        <rect key={i} x="116" y={y} width={i % 3 === 2 ? 100 : 160} height="2" rx="1" fill="#2e2922" />
      ))}
      {/* Gold highlight bar */}
      <rect x="116" y="190" width="4" height="30" rx="2" fill="#c4923a" opacity="0.8" />
      <rect x="124" y="194" width="120" height="2" rx="1" fill="#c4923a" opacity="0.4" />
      <rect x="124" y="200" width="80" height="2" rx="1" fill="#c4923a" opacity="0.25" />

      {/* Main document */}
      <rect x="320" y="60" width="280" height="380" rx="6" fill="#1c1a17" stroke="#3d3520" strokeWidth="1.5" />
      <rect x="320" y="60" width="280" height="48" rx="6" fill="#2a271f" />
      <rect x="320" y="96" width="280" height="12" fill="#2a271f" />
      <text x="340" y="88" fill="#c4923a" fontSize="10" fontFamily="Inter" fontWeight="600" letterSpacing="2">CASE FILE — CRIMINAL</text>
      {/* Body text lines */}
      {[130, 148, 166, 184, 220, 238, 256, 274, 310, 328, 346, 364].map((y, i) => (
        <rect key={i} x="340" y={y} width={i % 4 === 3 ? 120 : 220} height="2.5" rx="1.25" fill="#2e2922" />
      ))}
      {/* Annotation highlight */}
      <rect x="336" y="218" width="228" height="68" rx="2" fill="rgba(196,146,58,0.04)" stroke="rgba(196,146,58,0.15)" strokeWidth="1" />
      <rect x="340" y="220" width="3" height="64" rx="1.5" fill="#c4923a" opacity="0.6" />

      {/* Evidence nodes */}
      <circle cx="680" cy="140" r="20" fill="#1c1a17" stroke="#c4923a" strokeWidth="1" strokeOpacity="0.5" />
      <circle cx="680" cy="140" r="6" fill="#c4923a" fillOpacity="0.4" />

      <circle cx="720" cy="260" r="14" fill="#1c1a17" stroke="#6b1e2a" strokeWidth="1" strokeOpacity="0.6" />
      <circle cx="720" cy="260" r="5" fill="#6b1e2a" fillOpacity="0.5" />

      <circle cx="660" cy="360" r="18" fill="#1c1a17" stroke="#c4923a" strokeWidth="1" strokeOpacity="0.4" />
      <circle cx="660" cy="360" r="6" fill="#c4923a" fillOpacity="0.3" />

      {/* Connection lines */}
      <line x1="600" y1="150" x2="660" y2="140" stroke="#c4923a" strokeWidth="1" strokeOpacity="0.2" strokeDasharray="4 4" />
      <line x1="600" y1="250" x2="706" y2="260" stroke="#6b1e2a" strokeWidth="1" strokeOpacity="0.25" strokeDasharray="4 4" />
      <line x1="600" y1="340" x2="642" y2="352" stroke="#c4923a" strokeWidth="1" strokeOpacity="0.18" strokeDasharray="4 4" />
      <line x1="680" y1="160" x2="720" y2="246" stroke="#c4923a" strokeWidth="0.5" strokeOpacity="0.15" />

      {/* Status dots */}
      <circle cx="340" cy="395" r="4" fill="#3d7a4f" />
      <text x="350" y="399" fill="#5da878" fontSize="9" fontFamily="Inter" fontWeight="500">READY</text>
      <rect x="340" y="405" width="120" height="1.5" rx="0.75" fill="#2e2922" />

      {/* Subtle grid */}
      {[0, 1, 2, 3, 4].map(i => (
        <line key={i} x1="0" y1={i * 120 + 20} x2="800" y2={i * 120 + 20}
          stroke="#1c1a17" strokeWidth="1" />
      ))}
    </svg>
  )
}

// ── Data ─────────────────────────────────────────────────────────────────────

const STORY_STEPS = [
  {
    title: 'Upload',
    description: 'Ingest case documents, witness statements, evidence lists and legal briefs into your secure case file.',
    active: true,
  },
  {
    title: 'Understand',
    description: 'Legal NLP extracts entities, facts, statutes, and legal language from your documents.',
    active: false,
  },
  {
    title: 'Connect',
    description: 'Evidence Graph links people, events, documents and evidence into a navigable knowledge structure.',
    active: false,
  },
  {
    title: 'Prepare',
    description: 'Multi-agent reasoning assembles trial strategies, argument outlines and research summaries.',
    active: false,
  },
  {
    title: 'Simulate',
    description: 'Practice your arguments in the Virtual Courtroom against an adversarial AI.',
    active: false,
  },
]

const TECH_CARDS = [
  {
    icon: '§',
    label: 'Phase 2',
    title: 'Legal NLP',
    description: 'Understand entities, facts, statutes and legal language within your case documents using Legal-BERT and domain-specific NER.',
    upcoming: false,
  },
  {
    icon: '◈',
    label: 'Phase 5',
    title: 'Evidence Graph',
    description: 'Connect people, events, documents and evidence within a Neo4j knowledge graph. Visualise case relationships at a glance.',
    upcoming: true,
  },
  {
    icon: '⟳',
    label: 'Phase 4',
    title: 'Multi-Agent Reasoning',
    description: 'Specialised LangGraph agents analyse different dimensions of your case — facts, law, evidence, strategy — concurrently.',
    upcoming: true,
  },
  {
    icon: '⚖',
    label: 'Phase 7',
    title: 'Virtual Courtroom',
    description: 'Practice oral arguments against an adversarial AI judge and opposition counsel. Receive structured feedback.',
    upcoming: true,
  },
  {
    icon: '◎',
    label: 'Phase 3',
    title: 'Hybrid RAG',
    description: 'Dense + sparse retrieval over your case documents with cross-encoder reranking. Grounded, cited answers only.',
    upcoming: true,
  },
  {
    icon: '⊕',
    label: 'Phase 8',
    title: 'Accountable AI',
    description: 'Every AI insight is traceable back to its source. Confidence scores, citation verification, and full audit trails.',
    upcoming: true,
  },
]
