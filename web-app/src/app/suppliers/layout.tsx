import { redirect } from 'next/navigation'
import { auth } from '@/auth'
import { SuppliersRouteShell } from './suppliers-route-shell'

export default async function SuppliersLayout({ children }: { children: React.ReactNode }) {
  const session = await auth()
  if (!session?.user) {
    redirect('/')
  }
  return <SuppliersRouteShell>{children}</SuppliersRouteShell>
}
