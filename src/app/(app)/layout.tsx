import { dehydrate } from '@tanstack/react-query'
import { redirect } from 'next/navigation'
import { auth } from '@/auth'
import { AppLayout } from '@/components/layout/app-layout'
import { AppShellHydration } from '@/components/app-shell/app-shell-hydration'
import { createAppQueryClient } from '@/lib/query-client'
import { queryKeys } from '@/lib/query-keys'
import { fetchAppShellServerBootstrap } from '@/server/app-shell-data'

export const dynamic = 'force-dynamic'

export default async function AppShellLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth()

  if (!session?.user) {
    redirect('/')
  }

  const userId = session.user.id
  let appShell: Awaited<ReturnType<typeof fetchAppShellServerBootstrap>> | null = null
  try {
    appShell = await fetchAppShellServerBootstrap(userId)
  } catch {
    appShell = null
  }

  const q = createAppQueryClient()
  if (appShell) {
    q.setQueryData(queryKeys.userOrganizations(userId), appShell.organizations)
  }

  return (
    <AppShellHydration state={dehydrate(q)}>
      <AppLayout appShell={appShell}>{children}</AppLayout>
    </AppShellHydration>
  )
}
