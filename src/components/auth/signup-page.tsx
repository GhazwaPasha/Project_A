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
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Card className="win11-card">
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-success/20 mb-4">
                  <svg className="h-6 w-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-foreground mb-2">Account Created Successfully!</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Please check your email to verify your account. You'll be redirected to the dashboard shortly.
                </p>
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-background"></div>
      <div className="absolute inset-0 bg-black/20"></div>
      
      {/* Glassmorphism Floating Elements */}
      <div className="absolute top-20 left-20 w-32 h-32 bg-indigo-500/20 rounded-full blur-xl animate-pulse"></div>
      <div className="absolute bottom-20 right-20 w-40 h-40 bg-purple-500/20 rounded-full blur-2xl animate-pulse delay-1000"></div>
      <div className="absolute top-1/2 left-1/4 w-24 h-24 bg-blue-500/20 rounded-full blur-lg animate-pulse delay-500"></div>
      
      <div className="w-full max-w-md relative z-10">
        {/* Logo Section */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white/20 backdrop-blur-xl rounded-2xl mb-6 shadow-2xl">
            <Building2 className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold win11-text-primary mb-2">Accountuitive</h1>
          <p className="win11-text-secondary text-lg">Multi-Tenant SaaS Platform</p>
        </div>

        {/* Signup Card */}
        <div className="win11-card rounded-3xl p-8 win11-slide-up">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold win11-text-primary mb-2">Create Account</h2>
            <p className="win11-text-secondary">Get started with your accounting platform</p>
          </div>
          
          <form onSubmit={handleSignup} className="space-y-5">
            {error && (
              <div className="win11-card rounded-2xl p-4 border border-destructive/30">
                <p className="text-destructive text-sm">{error}</p>
              </div>
            )}
            
            <div className="space-y-2">
              <label htmlFor="fullName" className="win11-text-primary text-sm font-medium">Full Name</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-white/60" />
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  placeholder="Enter your full name"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  className="win11-input w-full pl-12 pr-4 py-3"
                  required
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label htmlFor="email" className="win11-text-primary text-sm font-medium">Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-white/60" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="win11-input w-full pl-12 pr-4 py-3"
                  required
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label htmlFor="password" className="win11-text-primary text-sm font-medium">Password</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-white/60" />
                  <input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="Password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="win11-input w-full pl-12 pr-4 py-3"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="win11-text-primary text-sm font-medium">Confirm</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-white/60" />
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    placeholder="Confirm"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className="win11-input w-full pl-12 pr-4 py-3"
                    required
                  />
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <label htmlFor="organizationName" className="win11-text-primary text-sm font-medium">Organization Name</label>
              <div className="relative">
                <Building2 className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-white/60" />
                <input
                  id="organizationName"
                  name="organizationName"
                  type="text"
                  placeholder="Enter organization name"
                  value={formData.organizationName}
                  onChange={handleInputChange}
                  className="win11-input w-full pl-12 pr-4 py-3"
                  required
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label htmlFor="organizationType" className="win11-text-primary text-sm font-medium">Organization Type</label>
              <select
                id="organizationType"
                name="organizationType"
                value={formData.organizationType}
                onChange={handleInputChange}
                className="win11-input w-full px-4 py-3"
                required
              >
                <option value="business" className="bg-slate-800 text-white">Business</option>
                <option value="nonprofit" className="bg-slate-800 text-white">Non-Profit</option>
                <option value="personal" className="bg-slate-800 text-white">Personal</option>
                <option value="freelancer" className="bg-slate-800 text-white">Freelancer</option>
              </select>
            </div>
            
            <button 
              type="submit" 
              className="win11-button-primary w-full py-4 font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  Creating Account...
                </div>
              ) : (
                'Create Account'
              )}
            </button>
          </form>
          
          <div className="mt-8 text-center">
            <p className="win11-text-secondary">
              Already have an account?{' '}
              <Link href="/" className="text-white font-semibold hover:text-white/80 transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
