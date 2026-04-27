'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { authClient } from '@/lib/auth-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Mail, Lock, Building2, User, ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { AuthScaffold } from '@/components/auth/auth-scaffold'
import { authFormFont } from '@/lib/auth-form-font'
import { getNeonAuthErrorMessage } from '@/lib/auth-error'

export function SignupPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    organizationName: '',
    organizationType: 'business',
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const router = useRouter()

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      setIsLoading(false)
      return
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters')
      setIsLoading(false)
      return
    }

    try {
      const signUpRes = await authClient.signUp.email({
        email: formData.email,
        password: formData.password,
        name: formData.fullName,
      })
      if (signUpRes.error) {
        setError(getNeonAuthErrorMessage(signUpRes.error, 'Registration failed'))
        return
      }
      if (!signUpRes.data?.user) {
        setError(
          'Sign-up did not return a session. If email verification is required, check your inbox or Neon Auth settings.'
        )
        return
      }

      // Ensure session cookies are visible to the next same-origin request (avoids 401 on
      // complete-profile in some browsers / hosting right after sign-up).
      await authClient.getSession()

      const profileRes = await fetch('/api/auth/complete-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          fullName: formData.fullName,
          organizationName: formData.organizationName,
          organizationType: formData.organizationType,
        }),
      })
      const profileData = (await profileRes.json().catch(() => ({}))) as { error?: string }

      if (!profileRes.ok) {
        setError(typeof profileData.error === 'string' ? profileData.error : 'Could not finish setup')
        return
      }

      setSuccess(true)
      await new Promise<void>((resolve) => setTimeout(resolve, 1200))
      router.push('/home')
      router.refresh()
    } catch (err) {
      setError(getNeonAuthErrorMessage(err, 'An unexpected error occurred'))
      console.error('Signup error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  if (success) {
    return (
      <AuthScaffold>
        <div className="w-full max-w-md">
          <div
            className={`md-card-expressive featured p-8 md-elevation-4 text-center auth-form-card ${authFormFont.className}`}
          >
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full mb-6 animate-fade-in" style={{ background: 'linear-gradient(135deg, var(--md-sys-color-tertiary) 0%, var(--md-sys-color-primary) 100%)' }}>
              <svg className="h-8 w-8 text-white animate-scale-in" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-2xl font-semibold mb-3" style={{ color: 'var(--md-sys-color-on-surface)' }}>Account Created Successfully!</h3>
            <p className="text-base mb-6" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>
              You will be redirected to the app shortly.
            </p>
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-transparent border-t-primary mx-auto"></div>
            </div>
          </div>
        </div>
      </AuthScaffold>
    )
  }

  return (
    <AuthScaffold>
      <div className="w-full max-w-3xl">
        <div
          className={`md-card-expressive interactive p-6 sm:p-8 md-elevation-3 group auth-form-card ${authFormFont.className}`}
        >
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold mb-3" style={{ color: 'var(--md-sys-color-on-surface)' }}>Create Account</h2>
            <p className="text-base" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>Get started with your accounting platform</p>
          </div>
          
          <form method="post" onSubmit={handleSignup} className="space-y-5">
            {error && (
              <div className="md-card p-4 border-2" style={{ borderColor: 'var(--md-sys-color-error)', backgroundColor: 'var(--md-sys-color-error-container)' }}>
                <p className="text-sm" style={{ color: 'var(--md-sys-color-on-error-container)' }}>{error}</p>
              </div>
            )}
            
            <div className="space-y-3">
              <label htmlFor="fullName" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Full Name</label>
              <div className="relative group">
                <User className="pointer-events-none absolute left-4 top-1/2 z-10 h-5 w-5 -translate-y-1/2 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  placeholder="Enter your full name"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  className="md-input md-input--icon-left w-full pr-4 py-3 group-hover:border-primary transition-all duration-200"
                  required
                />
              </div>
            </div>

            <div className="space-y-3">
              <label htmlFor="email" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Email</label>
              <div className="relative group">
                <Mail className="pointer-events-none absolute left-4 top-1/2 z-10 h-5 w-5 -translate-y-1/2 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="md-input md-input--icon-left w-full pr-4 py-3 group-hover:border-primary transition-all duration-200"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 sm:items-end">
              <div className="space-y-3">
                <label htmlFor="password" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Password</label>
                <div className="relative group">
                  <Lock className="pointer-events-none absolute left-4 top-1/2 z-10 h-5 w-5 -translate-y-1/2 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                  <input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="Password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="md-input md-input--icon-left w-full pr-4 py-3 group-hover:border-primary transition-all duration-200"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-3">
                <label htmlFor="confirmPassword" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Confirm</label>
                <div className="relative group">
                  <Lock className="pointer-events-none absolute left-4 top-1/2 z-10 h-5 w-5 -translate-y-1/2 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    placeholder="Confirm"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className="md-input md-input--icon-left w-full pr-4 py-3 group-hover:border-primary transition-all duration-200"
                    required
                  />
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <p className="text-sm" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>
                Workspace (optional). Add one now, or after sign-in from the app if you are joining an existing team.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:items-end">
              <div className="space-y-3">
                <label htmlFor="organizationName" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Organization name</label>
                <div className="relative group">
                  <Building2 className="pointer-events-none absolute left-4 top-1/2 z-10 h-5 w-5 -translate-y-1/2 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                  <input
                    id="organizationName"
                    name="organizationName"
                    type="text"
                    placeholder="Leave blank to set up later"
                    value={formData.organizationName}
                    onChange={handleInputChange}
                    className="md-input md-input--icon-left w-full pr-4 py-3 group-hover:border-primary transition-all duration-200"
                  />
                </div>
              </div>
              <div className="space-y-3">
                <label htmlFor="organizationType" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Type (if you add a workspace)</label>
                <select
                  id="organizationType"
                  name="organizationType"
                  value={formData.organizationType}
                  onChange={handleInputChange}
                  className="md-input w-full px-4 py-3 min-h-[48px] group-hover:border-primary transition-all duration-200"
                  style={{
                    backgroundColor: 'var(--md-sys-color-surface-container-highest)',
                    color: 'var(--md-sys-color-on-surface)',
                    border: '1px solid var(--md-sys-color-outline)',
                  }}
                >
                  <option value="business" style={{ backgroundColor: 'var(--md-sys-color-surface-container-highest)', color: 'var(--md-sys-color-on-surface)' }}>Business</option>
                  <option value="nonprofit" style={{ backgroundColor: 'var(--md-sys-color-surface-container-highest)', color: 'var(--md-sys-color-on-surface)' }}>Non-Profit</option>
                  <option value="personal" style={{ backgroundColor: 'var(--md-sys-color-surface-container-highest)', color: 'var(--md-sys-color-on-surface)' }}>Personal</option>
                  <option value="freelancer" style={{ backgroundColor: 'var(--md-sys-color-surface-container-highest)', color: 'var(--md-sys-color-on-surface)' }}>Freelancer</option>
                </select>
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
                  Creating Account...
                </div>
              ) : (
                <span className="group-hover:tracking-wide transition-all duration-200">Create Account</span>
              )}
            </button>
          </form>
          
          <div className="mt-8 text-center">
            <p style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>
              Already have an account?{' '}
              <Link 
                href="/" 
                className="font-semibold hover:tracking-wide transition-all duration-200" 
                style={{ color: 'var(--auth-form-link)' }}
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </AuthScaffold>
  )
}
