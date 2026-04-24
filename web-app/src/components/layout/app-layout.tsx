'use client'

import { Win11Sidebar } from './win11-sidebar'
import { Win11Header } from './win11-header'
import { OrgPathAccessGuard } from '@/components/access/org-path-access-guard'

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  // Disable background sync for now to prevent state persistence issues
  // TODO: Re-enable with proper configuration once tested
  // useBackgroundSync()

  return (
    <div className="app-shell">
      <Win11Sidebar />
      <div className="app-shell-main">
        <Win11Header />
        <main className="flex-1 overflow-y-auto md-scrollbar relative">
          <OrgPathAccessGuard>{children}</OrgPathAccessGuard>
        </main>
      </div>
    </div>
  )
}
