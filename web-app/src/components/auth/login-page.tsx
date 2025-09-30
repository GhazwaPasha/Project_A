'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Mail, Lock, Building2 } from 'lucide-react'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()
  const supabase = createClient()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        setError(error.message)
      } else if (data.user) {
        router.push('/dashboard')
      }
    } catch (err) {
      setError('An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden" style={{ background: 'linear-gradient(135deg, var(--md-sys-color-primary-container) 0%, var(--md-sys-color-surface-container-low) 50%, var(--md-sys-color-tertiary-container) 100%)' }}>
      {/* Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/5 to-transparent"></div>
      
      {/* Material Design 3 Expressive Floating Elements */}
      <div className="absolute top-20 left-20 w-32 h-32 rounded-full blur-xl animate-pulse opacity-60" style={{ background: 'radial-gradient(circle, var(--md-sys-color-primary) 0%, transparent 70%)' }}></div>
      <div className="absolute bottom-20 right-20 w-40 h-40 rounded-full blur-2xl animate-pulse delay-1000 opacity-40" style={{ background: 'radial-gradient(circle, var(--md-sys-color-tertiary) 0%, transparent 70%)' }}></div>
      <div className="absolute top-1/2 left-1/4 w-24 h-24 rounded-full blur-lg animate-pulse delay-500 opacity-50" style={{ background: 'radial-gradient(circle, var(--md-sys-color-secondary) 0%, transparent 70%)' }}></div>
      
      <div className="w-full max-w-sm relative z-10">
        {/* Logo Section */}
        <div className="text-center mb-12 animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl mb-6 md-elevation-3 group hover:md-elevation-4 transition-all duration-300" style={{ background: 'linear-gradient(135deg, var(--md-sys-color-primary) 0%, var(--md-sys-color-tertiary) 100%)' }}>
            <Building2 className="h-10 w-10 text-white group-hover:scale-110 transition-transform duration-300" />
          </div>
          <h1 className="text-5xl font-bold mb-2" style={{ color: 'var(--md-sys-color-on-surface)' }}>Accountuitive</h1>
          <p className="text-lg" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>Multi-Tenant SaaS Platform</p>
        </div>

        {/* Login Card - Material Design 3 Expressive */}
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
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                <input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="md-input w-full pl-12 pr-4 py-4 group-hover:border-primary transition-all duration-200"
                  required
                />
              </div>
            </div>
            
            <div className="space-y-3">
              <label htmlFor="password" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Password</label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                <input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="md-input w-full pl-12 pr-4 py-4 group-hover:border-primary transition-all duration-200"
                  required
                />
              </div>
            </div>
            
            <button 
              type="submit" 
              className="md-button w-full py-4 font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed group hover:scale-[1.02] transition-all duration-200"
              disabled={isLoading}
              style={{ 
                background: 'linear-gradient(135deg, var(--md-sys-color-primary) 0%, var(--md-sys-color-tertiary) 100%)',
                color: 'var(--md-sys-color-on-primary)'
              }}
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  Signing In...
                </div>
              ) : (
                <span className="group-hover:tracking-wide transition-all duration-200">Sign In</span>
              )}
            </button>
          </form>
          
          <div className="mt-8 text-center">
            <p style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>
              Don't have an account?{' '}
              <Link 
                href="/signup" 
                className="font-semibold hover:tracking-wide transition-all duration-200" 
                style={{ color: 'var(--md-sys-color-primary)' }}
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
