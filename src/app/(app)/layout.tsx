import { redirect } from 'next/navigation'
import { auth } from '@/auth'
import { AppLayout } from '@/components/layout/app-layout'

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

  return <AppLayout>{children}</AppLayout>
}
