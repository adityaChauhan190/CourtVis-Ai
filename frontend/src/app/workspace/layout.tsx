import { Sidebar } from '@/components/workspace/Sidebar'
import styles from './workspace.module.css'

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={styles.layout}>
      <Sidebar />
      <main className={styles.main}>
        {children}
      </main>
    </div>
  )
}
