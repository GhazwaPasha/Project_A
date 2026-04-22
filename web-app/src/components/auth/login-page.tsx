'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { authClient } from '@/lib/auth-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Loader2, Mail, Lock, Building2 } from 'lucide-react'

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
        callbackURL: '/dashboard',
      })
      if (res.error) {
        setError(res.error.message || 'Invalid email or password')
        return
      }
      router.push('/dashboard')
      router.refresh()
    } catch {
      setError('An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden" style={{ background: 'linear-gradient(135deg, var(--md-sys-color-primary-container) 0%, var(--md-sys-color-surface-container-low) 50%, var(--md-sys-color-tertiary-container) 100%)' }}>
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/5 to-transparent"></div>

      <div className="absolute top-20 left-20 w-32 h-32 rounded-full blur-xl animate-pulse opacity-60" style={{ background: 'radial-gradient(circle, var(--md-sys-color-primary) 0%, transparent 70%)' }}></div>
      <div className="absolute bottom-20 right-20 w-40 h-40 rounded-full blur-2xl animate-pulse delay-1000 opacity-40" style={{ background: 'radial-gradient(circle, var(--md-sys-color-tertiary) 0%, transparent 70%)' }}></div>
      <div className="absolute top-1/2 left-1/4 w-24 h-24 rounded-full blur-lg animate-pulse delay-500 opacity-50" style={{ background: 'radial-gradient(circle, var(--md-sys-color-secondary) 0%, transparent 70%)' }}></div>

      <div className="w-full max-w-sm relative z-10">
        <div className="text-center mb-12 animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl mb-6 md-elevation-3 group hover:md-elevation-4 transition-all duration-300" style={{ background: 'linear-gradient(135deg, var(--md-sys-color-primary) 0%, var(--md-sys-color-tertiary) 100%)' }}>
            <Building2 className="h-10 w-10 text-white group-hover:scale-110 transition-transform duration-300" />
          </div>
          <h1 className="text-5xl font-bold mb-2" style={{ color: 'var(--md-sys-color-on-surface)' }}>Accountuitive</h1>
          <p className="text-lg" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>Multi-Tenant SaaS Platform</p>
        </div>

        <div className="md-card-expressive interactive p-8 md-elevation-3 group">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold mb-3" style={{ color: 'var(--md-sys-color-on-surface)' }}>Welcome Back</h2>
            <p className="text-base" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>Sign in to your account to continue</p>
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
            <Link href="/signup" className="font-medium underline" style={{ color: 'var(--md-sys-color-primary)' }}>
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
