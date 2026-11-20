'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { casesApi } from '@/lib/api'
import type { CaseType, UserCaseRole } from '@/lib/types'
import styles from './page.module.css'

const CASE_TYPES: { value: CaseType; label: string }[] = [
  { value: 'criminal', label: 'Criminal' },
  { value: 'civil', label: 'Civil' },
  { value: 'constitutional', label: 'Constitutional' },
  { value: 'corporate', label: 'Corporate' },
  { value: 'family', label: 'Family' },
  { value: 'intellectual_property', label: 'Intellectual Property' },
  { value: 'labour', label: 'Labour' },
  { value: 'tax', label: 'Tax' },
  { value: 'other', label: 'Other' },
]

const ROLES: { value: UserCaseRole; label: string; desc: string }[] = [
  { value: 'defence', label: 'Defence', desc: 'Preparing for the accused or respondent' },
  { value: 'prosecution', label: 'Prosecution', desc: 'Preparing for the state or plaintiff' },
  { value: 'researcher', label: 'Researcher', desc: 'Academic or neutral analysis' },
  { value: 'student', label: 'Student / Moot Court', desc: 'Educational preparation' },
]

export default function NewCasePage() {
  const router = useRouter()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState({
    name: '',
    case_type: 'criminal' as CaseType,
    description: '',
    case_number: '',
    user_role: 'student' as UserCaseRole,
  })

  function set(k: keyof typeof form, v: string) {
    setForm(prev => ({ ...prev, [k]: v }))
    setError(null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name.trim()) { setError('Case name is required.'); return }

    setSubmitting(true)
    setError(null)
    try {
      const created = await casesApi.create({
        name: form.name.trim(),
        case_type: form.case_type,
        description: form.description.trim() || undefined,
        case_number: form.case_number.trim() || undefined,
        user_role: form.user_role,
      })
      router.push(`/workspace/cases/${created.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create case. Is the backend running?')
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <p className="text-eyebrow">Case Management</p>
          <h1 className={`text-display-md ${styles.title}`}>Open a New Matter</h1>
          <p className={styles.subtitle}>
            Define the case parameters to create your secure case workspace.
          </p>
        </div>
        <Link href="/workspace" className="btn btn-ghost btn-sm">← Back</Link>
      </div>

      <div className={styles.divider} />

      <div className={styles.formContainer}>
        <form onSubmit={handleSubmit} className={styles.form} noValidate>

          {/* Case Name */}
          <div className="form-group">
            <label htmlFor="case-name" className="form-label">Case Name *</label>
            <input
              id="case-name"
              type="text"
              className="form-input"
              placeholder="e.g. State v. Sharma — Murder at Colaba"
              value={form.name}
              onChange={e => set('name', e.target.value)}
              maxLength={500}
              required
            />
          </div>

          <div className={styles.row}>
            {/* Case Type */}
            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="case-type" className="form-label">Case Type *</label>
              <select
                id="case-type"
                className="form-select"
                value={form.case_type}
                onChange={e => set('case_type', e.target.value as CaseType)}
              >
                {CASE_TYPES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            {/* Case Number */}
            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="case-number" className="form-label">Case Number (Optional)</label>
              <input
                id="case-number"
                type="text"
                className="form-input"
                placeholder="e.g. CRL.APPEAL 112/2024"
                value={form.case_number}
                onChange={e => set('case_number', e.target.value)}
                maxLength={100}
              />
            </div>
          </div>

          {/* Description */}
          <div className="form-group">
            <label htmlFor="case-desc" className="form-label">Description (Optional)</label>
            <textarea
              id="case-desc"
              className="form-textarea"
              placeholder="Brief summary of the case background, key facts, and what you want to prepare…"
              value={form.description}
              onChange={e => set('description', e.target.value)}
              rows={4}
              maxLength={5000}
            />
          </div>

          {/* Role */}
          <div className="form-group">
            <label className="form-label">Your Role *</label>
            <div className={styles.roleGrid}>
              {ROLES.map(r => (
                <button
                  key={r.value}
                  type="button"
                  id={`role-${r.value}`}
                  className={`${styles.roleBtn} ${form.user_role === r.value ? styles.roleBtnActive : ''}`}
                  onClick={() => set('user_role', r.value)}
                >
                  <span className={styles.roleBtnLabel}>{r.label}</span>
                  <span className={styles.roleBtnDesc}>{r.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className={styles.errorBox}>
              <span>⚠</span>
              <span>{error}</span>
            </div>
          )}

          <div className={styles.actions}>
            <Link href="/workspace" className="btn btn-secondary">Cancel</Link>
            <button
              type="submit"
              id="create-case-submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <span className="spinner" />
                  Creating…
                </>
              ) : (
                'Create Case →'
              )}
            </button>
          </div>
        </form>

        <aside className={styles.sidebar}>
          <div className={styles.sideNote}>
            <p className="text-label" style={{ marginBottom: '12px' }}>About this case</p>
            <p className={styles.sideNoteText}>
              Each case is a secure, isolated workspace. All documents you upload
              remain associated with this matter and are accessible only to you.
            </p>
          </div>
          <div className={styles.divider} />
          <div className={styles.sideNote}>
            <p className="text-label" style={{ marginBottom: '12px' }}>Disclaimer</p>
            <p className={styles.sideNoteText}>
              Court Vision AI is an educational preparation tool. It does not
              provide legal advice and should not replace qualified legal counsel.
            </p>
          </div>
        </aside>
      </div>
    </div>
  )
}
