import { redirect } from 'next/navigation'
import { auth } from '@/auth'
import { LoginPage } from '@/components/auth/login-page'

export const dynamic = 'force-dynamic'

export default async function HomePage() {
  const session = await auth()

  if (session?.user) {
    redirect('/home')
  }

  return <LoginPage />
}
