'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { authClient } from '@/lib/auth-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Loader2, Mail, Lock } from 'lucide-react'
import { AuthScaffold } from '@/components/auth/auth-scaffold'
import { authFormFont } from '@/lib/auth-form-font'
import { getNeonAuthErrorMessage } from '@/lib/auth-error'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const res = await authClient.signIn.email({
        email,
        password,
      })
      if (res.error) {
        setError(getNeonAuthErrorMessage(res.error, 'Invalid email or password'))
        return
      }
      router.push('/home')
      router.refresh()
    } catch (err) {
      setError(getNeonAuthErrorMessage(err, 'An unexpected error occurred'))
      console.error('Login error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthScaffold>
      <div className="w-full max-w-sm">
        <div
          className={`md-card-expressive interactive p-8 md-elevation-3 group auth-form-card ${authFormFont.className}`}
        >
          <div className="text-center mb-8">
            <h2
              className="text-center text-2xl font-semibold sm:text-3xl"
              style={{ color: 'var(--md-sys-color-on-surface)' }}
            >
              Sign in
            </h2>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            {error && (
              <div className="md-card p-4 border-2" style={{ borderColor: 'var(--md-sys-color-error)', backgroundColor: 'var(--md-sys-color-error-container)' }}>
                <p className="text-sm" style={{ color: 'var(--md-sys-color-on-error-container)' }}>{error}</p>
              </div>
            )}

            <div className="space-y-3">
              <label htmlFor="email" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Email</label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 h-4 w-4" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="md-text-field-input--icon-left h-12 rounded-xl"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="space-y-3">
              <label htmlFor="password" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Password</label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 h-4 w-4" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="md-text-field-input--icon-left h-12 rounded-xl"
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            <Button type="submit" className="w-full h-12 rounded-xl" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in…
                </>
              ) : (
                'Sign in'
              )}
            </Button>
          </form>

          <p className="text-center text-sm mt-6" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>
            No account?{' '}
            <Link href="/signup" className="font-medium underline" style={{ color: 'var(--auth-form-link)' }}>
              Create one
            </Link>
          </p>
        </div>
      </div>
    </AuthScaffold>
  )
}
