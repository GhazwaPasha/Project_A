import { redirect } from 'next/navigation'
import { createServerClient } from '@/lib/supabase-server'
import { AppLayout } from '@/components/layout/app-layout'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createServerClient()
  
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    redirect('/')
  }
  
  return <AppLayout>{children}</AppLayout>
}
