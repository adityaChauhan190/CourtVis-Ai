'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/auth/AuthProvider'
import styles from './auth.module.css'

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      if (isLogin) {
        const formData = new URLSearchParams()
        formData.append('username', email)
        formData.append('password', password)

        const res = await fetch(process.env.NEXT_PUBLIC_API_URL + '/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString(),
        })

        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.detail || 'Login failed')
        }

        const data = await res.json()

        const userRes = await fetch(process.env.NEXT_PUBLIC_API_URL + '/api/auth/me', {
          headers: { Authorization: `Bearer ${data.access_token}` },
        })

        if (!userRes.ok) throw new Error('Failed to fetch user details')
        const userData = await userRes.json()

        login(data.access_token, userData)
      } else {
        const res = await fetch(process.env.NEXT_PUBLIC_API_URL + '/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, name }),
        })

        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.detail || 'Registration failed')
        }

        setIsLogin(true)
        setError('Account created. Please sign in to continue.')
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const switchMode = (toLogin: boolean) => {
    setIsLogin(toLogin)
    setError(null)
    setEmail('')
    setPassword('')
    setName('')
  }

  const isSuccessMsg = error?.includes('created') || error?.includes('successful')

  return (
    <div className={styles.page}>
      {/* ── Left Brand Panel ──────────────────────────────────── */}
      <aside className={styles.brandPanel}>
        <div className={styles.brandTop}>
          <div className={styles.brandLogo}>
            <span className={styles.brandLogoIcon}>⚖</span>
            <span className={styles.brandLogoText}>Court Vision AI</span>
          </div>

          <h1 className={styles.brandHeading}>
            Your Cases,<br />
            <em>Intelligently</em><br />
            Analysed.
          </h1>

          <p className={styles.brandSubtext}>
            Upload case documents and let our AI surface the facts, entities,
            and arguments that matter — grounded, cited, and trial-ready.
          </p>
        </div>

        <div className={styles.brandBottom}>
          <div className={styles.brandStats}>
            <div className={styles.brandStat}>
              <span className={styles.brandStatNumber}>50MB</span>
              <span className={styles.brandStatLabel}>Max doc size</span>
            </div>
            <div className={styles.brandStat}>
              <span className={styles.brandStatNumber}>70B</span>
              <span className={styles.brandStatLabel}>Parameter model</span>
            </div>
            <div className={styles.brandStat}>
              <span className={styles.brandStatNumber}>∞</span>
              <span className={styles.brandStatLabel}>Cases supported</span>
            </div>
          </div>
        </div>

        {/* decorative large ⚖ ornament */}
        <svg
          className={styles.brandOrnament}
          viewBox="0 0 200 200"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <circle cx="100" cy="100" r="96" stroke="currentColor" strokeWidth="1" />
          <line x1="100" y1="10" x2="100" y2="190" stroke="currentColor" strokeWidth="1" />
          <line x1="40" y1="60" x2="160" y2="60" stroke="currentColor" strokeWidth="1" />
          <line x1="40" y1="60" x2="10" y2="120" stroke="currentColor" strokeWidth="1" />
          <line x1="160" y1="60" x2="190" y2="120" stroke="currentColor" strokeWidth="1" />
          <line x1="10" y1="120" x2="70" y2="120" stroke="currentColor" strokeWidth="1" />
          <line x1="130" y1="120" x2="190" y2="120" stroke="currentColor" strokeWidth="1" />
        </svg>
      </aside>

      {/* ── Right Form Panel ─────────────────────────────────── */}
      <main className={styles.formPanel}>
        <div className={styles.formInner}>
          <div className={styles.formHeader}>
            <p className={styles.formEyebrow}>
              {isLogin ? 'Welcome Back' : 'Get Started'}
            </p>
            <h2 className={styles.formTitle}>
              {isLogin ? 'Sign in to your chamber' : 'Create your chamber'}
            </h2>
            <p className={styles.formSubtitle}>
              {isLogin
                ? 'Access your cases, documents, and AI insights.'
                : 'Start analysing cases in minutes — free to use.'}
            </p>
          </div>

          <div className={styles.divider} />

          {/* Tab Switcher */}
          <div className={styles.tabSwitcher} role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={isLogin}
              id="tab-login"
              className={`${styles.tab} ${isLogin ? styles.tabActive : ''}`}
              onClick={() => switchMode(true)}
            >
              Sign In
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={!isLogin}
              id="tab-register"
              className={`${styles.tab} ${!isLogin ? styles.tabActive : ''}`}
              onClick={() => switchMode(false)}
            >
              Create Account
            </button>
          </div>

          <form className={styles.form} onSubmit={handleSubmit} noValidate>
            {error && (
              <div className={isSuccessMsg ? styles.success : styles.error} role="alert">
                {isSuccessMsg ? '✓' : '⚠'}&ensp;{error}
              </div>
            )}

            {!isLogin && (
              <div className={styles.formGroup}>
                <label htmlFor="auth-name" className={styles.formLabel}>
                  Full Name
                </label>
                <input
                  id="auth-name"
                  type="text"
                  required
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Doe"
                  className={styles.formInput}
                />
              </div>
            )}

            <div className={styles.formGroup}>
              <label htmlFor="auth-email" className={styles.formLabel}>
                Email Address
              </label>
              <input
                id="auth-email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="counsel@firm.com"
                className={styles.formInput}
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="auth-password" className={styles.formLabel}>
                Password
              </label>
              <input
                id="auth-password"
                type="password"
                required
                autoComplete={isLogin ? 'current-password' : 'new-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className={styles.formInput}
              />
            </div>

            <button
              type="submit"
              id="auth-submit"
              className={styles.submitBtn}
              disabled={isLoading}
            >
              {isLoading ? (
                <span className={styles.loadingDots} aria-label="Processing">
                  <span />
                  <span />
                  <span />
                </span>
              ) : isLogin ? (
                'Sign In to Your Chamber'
              ) : (
                'Create My Chamber'
              )}
            </button>
          </form>

          <div className={styles.formFooter}>
            <p className={styles.formFooterText}>
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault()
                  switchMode(!isLogin)
                }}
              >
                {isLogin ? 'Create one' : 'Sign in'}
              </a>
            </p>
          </div>

          <p className={styles.disclaimer}>
            For educational &amp; research use only. Not a substitute for qualified legal counsel.
          </p>
        </div>
      </main>
    </div>
  )
}
