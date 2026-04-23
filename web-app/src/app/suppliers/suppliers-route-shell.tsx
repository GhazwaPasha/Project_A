'use client'

import { OrgPathAccessGuard } from '@/components/access/org-path-access-guard'

export function SuppliersRouteShell({ children }: { children: React.ReactNode }) {
  return <OrgPathAccessGuard>{children}</OrgPathAccessGuard>
}
