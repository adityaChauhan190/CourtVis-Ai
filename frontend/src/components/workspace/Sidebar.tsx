'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/components/auth/AuthProvider'
import { useState, useEffect } from 'react'
import styles from './Sidebar.module.css'

const NAV_SECTIONS = [
  {
    label: 'Command Center',
    items: [
      { href: '/workspace', icon: '⊞', label: 'Overview', exact: true },
      { href: '/workspace/cases', icon: '◧', label: 'Case Vault', exact: false },
      { href: '/workspace/evidence-graph', icon: '◉', label: 'Evidence Graphs', exact: false },
      { href: '/workspace/courtroom', icon: '⚖', label: 'Virtual Courtroom', exact: false },
      { href: '/workspace/research', icon: '§', label: 'Legal Precedents', exact: false },
      { href: '/workspace/reports', icon: '📄', label: 'Trial Prep & Reports', exact: false },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const [isCollapsed, setIsCollapsed] = useState(false)

  useEffect(() => {
    if (isCollapsed) {
      document.body.classList.add('sidebar-collapsed')
    } else {
      document.body.classList.remove('sidebar-collapsed')
    }
  }, [isCollapsed])

  type NavItem = { href: string; icon: string; label: string; exact: boolean }
  function isActive(item: NavItem) {
    if (item.exact) return pathname === item.href
    return pathname.startsWith(item.href)
  }

  return (
    <aside className={styles.sidebar}>
      {/* Brand */}
      <div className={styles.brand}>
        <Link href="/" className={styles.brandLink}>
          <span className={styles.brandIcon}>⚖</span>
          <div>
            <div className={styles.brandName}>COURT VISION AI</div>
            <div className={styles.brandSub}>Case Intelligence</div>
          </div>
        </Link>
      </div>
      
      <button 
        className={styles.collapseBtn} 
        onClick={() => setIsCollapsed(!isCollapsed)}
        title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
      >
        {isCollapsed ? "→" : "←"}
      </button>

      <div className={styles.divider} />

      {/* Navigation */}
      <nav className={styles.nav}>
        {NAV_SECTIONS.map((section) => (
          <div key={section.label} className={styles.navSection}>
            <p className={styles.navLabel}>{section.label}</p>
            <ul className={styles.navList}>
              {section.items.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`${styles.navItem} ${isActive(item) ? styles.navItemActive : ''}`}
                    title={item.label}
                  >
                    <span className={styles.navIcon}>{item.icon}</span>
                    <span className={styles.navItemLabel}>{item.label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className={styles.spacer} />
      <div className={styles.divider} />

      {/* User */}
      <div className={styles.userSection}>
        <div className={styles.userAvatar}>
          {user?.name?.substring(0, 2).toUpperCase() || 'U'}
        </div>
        <div className={styles.userInfo}>
          <div className={styles.userName}>{user?.name || 'Loading...'}</div>
          <div className={styles.userRole}>{user?.email || ''}</div>
          <button 
            onClick={logout}
            style={{ marginTop: '0.5rem', background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.75rem', padding: 0, textAlign: 'left' }}
          >
            Sign Out
          </button>
        </div>
      </div>
    </aside>
  )
}
