import { redirect } from 'next/navigation'
import { auth } from '@/auth'
import { AppLayout } from '@/components/layout/app-layout'

export default async function DashboardLayout({
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
