'use client'

import { Win11Sidebar } from './win11-sidebar'
import { Win11Header } from './win11-header'
import { OrgPathAccessGuard } from '@/components/access/org-path-access-guard'
import { useBackgroundSync } from '@/hooks/use-background-sync'
import { AppShellBootstrapSeed } from '@/components/app-shell/app-shell-bootstrap-seed'
import type { AppShellServerBootstrap } from '@/types/app-shell'

interface AppLayoutProps {
  children: React.ReactNode
  /** RSC-fetched profile + org list; seeds the client store when useful. */
  appShell?: AppShellServerBootstrap | null
}

export function AppLayout({ children, appShell }: AppLayoutProps) {
  useBackgroundSync()

  return (
    <div className="app-shell">
      <AppShellBootstrapSeed bootstrap={appShell} />
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
