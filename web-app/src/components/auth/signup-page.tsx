'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Mail, Lock, Building2, User, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export function SignupPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    organizationName: '',
    organizationType: 'business'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const router = useRouter()
  const supabase = createClient()

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
      // Step 1: Sign up user with Supabase Auth
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
        options: {
          data: {
            full_name: formData.fullName,
          }
        }
      })

      if (authError) {
        setError(authError.message)
        setIsLoading(false)
        return
      }

      if (authData.user) {
        // Step 2: Create user profile
        const { error: profileError } = await supabase
          .from('user_profiles')
          .insert({
            id: authData.user.id,
            email: formData.email,
            full_name: formData.fullName,
            is_super_admin: false,
            preferences: {}
          })

        if (profileError) {
          console.error('Error creating user profile:', profileError)
        }

        // Step 3: Create organization
        const { data: orgData, error: orgError } = await supabase
          .from('organizations')
          .insert({
            name: formData.organizationName,
            description: `${formData.organizationType} organization`,
            settings: {
              organization_type: formData.organizationType,
              created_by: authData.user.id
            }
          })
          .select()
          .single()

        if (orgError) {
          console.error('Error creating organization:', orgError)
        }

        // Step 4: Add user as organization owner
        if (orgData) {
          const { error: memberError } = await supabase
            .from('organization_members')
            .insert({
              organization_id: orgData.id,
              user_id: authData.user.id,
              role: 'organization_owner',
              is_active: true,
              joined_at: new Date().toISOString()
            })

          if (memberError) {
            console.error('Error adding user to organization:', memberError)
          }
        }

        setSuccess(true)
        
        // Redirect to dashboard after successful signup
        setTimeout(() => {
          router.push('/dashboard')
        }, 2000)
      }
    } catch (err) {
      setError('An unexpected error occurred')
      console.error('Signup error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'linear-gradient(135deg, var(--md-sys-color-primary-container) 0%, var(--md-sys-color-surface-container-low) 50%, var(--md-sys-color-tertiary-container) 100%)' }}>
        <div className="w-full max-w-md">
          <div className="md-card-expressive featured p-8 md-elevation-4 text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full mb-6 animate-fade-in" style={{ background: 'linear-gradient(135deg, var(--md-sys-color-tertiary) 0%, var(--md-sys-color-primary) 100%)' }}>
              <svg className="h-8 w-8 text-white animate-scale-in" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-2xl font-semibold mb-3" style={{ color: 'var(--md-sys-color-on-surface)' }}>Account Created Successfully!</h3>
            <p className="text-base mb-6" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>
              Please check your email to verify your account. You'll be redirected to the dashboard shortly.
            </p>
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-transparent border-t-primary mx-auto"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden" style={{ background: 'linear-gradient(135deg, var(--md-sys-color-primary-container) 0%, var(--md-sys-color-surface-container-low) 50%, var(--md-sys-color-tertiary-container) 100%)' }}>
      {/* Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/5 to-transparent"></div>
      
      {/* Material Design 3 Expressive Floating Elements */}
      <div className="absolute top-20 left-20 w-32 h-32 rounded-full blur-xl animate-pulse opacity-60" style={{ background: 'radial-gradient(circle, var(--md-sys-color-primary) 0%, transparent 70%)' }}></div>
      <div className="absolute bottom-20 right-20 w-40 h-40 rounded-full blur-2xl animate-pulse delay-1000 opacity-40" style={{ background: 'radial-gradient(circle, var(--md-sys-color-tertiary) 0%, transparent 70%)' }}></div>
      <div className="absolute top-1/2 left-1/4 w-24 h-24 rounded-full blur-lg animate-pulse delay-500 opacity-50" style={{ background: 'radial-gradient(circle, var(--md-sys-color-secondary) 0%, transparent 70%)' }}></div>
      
      <div className="w-full max-w-md relative z-10">
        {/* Logo Section */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl mb-6 md-elevation-3 group hover:md-elevation-4 transition-all duration-300" style={{ background: 'linear-gradient(135deg, var(--md-sys-color-primary) 0%, var(--md-sys-color-tertiary) 100%)' }}>
            <Building2 className="h-10 w-10 text-white group-hover:scale-110 transition-transform duration-300" />
          </div>
          <h1 className="text-5xl font-bold mb-2" style={{ color: 'var(--md-sys-color-on-surface)' }}>Accountuitive</h1>
          <p className="text-lg" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>Multi-Tenant SaaS Platform</p>
        </div>

        {/* Signup Card - Material Design 3 Expressive */}
        <div className="md-card-expressive interactive p-8 md-elevation-3 group">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold mb-3" style={{ color: 'var(--md-sys-color-on-surface)' }}>Create Account</h2>
            <p className="text-base" style={{ color: 'var(--md-sys-color-on-surface-variant)' }}>Get started with your accounting platform</p>
          </div>
          
          <form onSubmit={handleSignup} className="space-y-5">
            {error && (
              <div className="md-card p-4 border-2" style={{ borderColor: 'var(--md-sys-color-error)', backgroundColor: 'var(--md-sys-color-error-container)' }}>
                <p className="text-sm" style={{ color: 'var(--md-sys-color-on-error-container)' }}>{error}</p>
              </div>
            )}
            
            <div className="space-y-3">
              <label htmlFor="fullName" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Full Name</label>
              <div className="relative group">
                <User className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  placeholder="Enter your full name"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  className="md-input w-full pl-12 pr-4 py-3 group-hover:border-primary transition-all duration-200"
                  required
                />
              </div>
            </div>
            
            <div className="space-y-3">
              <label htmlFor="email" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Email</label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="md-input w-full pl-12 pr-4 py-3 group-hover:border-primary transition-all duration-200"
                  required
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <label htmlFor="password" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Password</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                  <input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="Password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="md-input w-full pl-12 pr-4 py-3 group-hover:border-primary transition-all duration-200"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-3">
                <label htmlFor="confirmPassword" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Confirm</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    placeholder="Confirm"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className="md-input w-full pl-12 pr-4 py-3 group-hover:border-primary transition-all duration-200"
                    required
                  />
                </div>
              </div>
            </div>
            
            <div className="space-y-3">
              <label htmlFor="organizationName" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Organization Name</label>
              <div className="relative group">
                <Building2 className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 transition-colors duration-200" style={{ color: 'var(--md-sys-color-on-surface-variant)' }} />
                <input
                  id="organizationName"
                  name="organizationName"
                  type="text"
                  placeholder="Enter organization name"
                  value={formData.organizationName}
                  onChange={handleInputChange}
                  className="md-input w-full pl-12 pr-4 py-3 group-hover:border-primary transition-all duration-200"
                  required
                />
              </div>
            </div>
            
            <div className="space-y-3">
              <label htmlFor="organizationType" className="text-sm font-medium block" style={{ color: 'var(--md-sys-color-on-surface)' }}>Organization Type</label>
              <select
                id="organizationType"
                name="organizationType"
                value={formData.organizationType}
                onChange={handleInputChange}
                className="md-input w-full px-4 py-3 group-hover:border-primary transition-all duration-200"
                required
                style={{ 
                  backgroundColor: 'var(--md-sys-color-surface-container-highest)',
                  color: 'var(--md-sys-color-on-surface)',
                  border: '1px solid var(--md-sys-color-outline)'
                }}
              >
                <option value="business" style={{ backgroundColor: 'var(--md-sys-color-surface-container-highest)', color: 'var(--md-sys-color-on-surface)' }}>Business</option>
                <option value="nonprofit" style={{ backgroundColor: 'var(--md-sys-color-surface-container-highest)', color: 'var(--md-sys-color-on-surface)' }}>Non-Profit</option>
                <option value="personal" style={{ backgroundColor: 'var(--md-sys-color-surface-container-highest)', color: 'var(--md-sys-color-on-surface)' }}>Personal</option>
                <option value="freelancer" style={{ backgroundColor: 'var(--md-sys-color-surface-container-highest)', color: 'var(--md-sys-color-on-surface)' }}>Freelancer</option>
              </select>
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
                style={{ color: 'var(--md-sys-color-primary)' }}
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
