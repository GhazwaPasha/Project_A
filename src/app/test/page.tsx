'use client'

import { useEffect, useState } from 'react'
import { authClient } from '@/lib/auth-client'

export default function TestPage() {
  const { data, isPending } = authClient.useSession()
  const [msg, setMsg] = useState('Checking session…')

  useEffect(() => {
    if (isPending) return
    if (data?.user) {
      setMsg(`Signed in as ${data.user.email ?? data.user.id}`)
    } else {
      setMsg('Not signed in (Neon Auth)')
    }
  }, [data, isPending])

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Auth test</h1>
      <p className="text-on-surface">{msg}</p>
    </div>
  )
}
