'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import { authClient } from '@/lib/auth-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Building2, Loader2 } from 'lucide-react'
import { authFormFont } from '@/lib/auth-form-font'
import type { Organization } from '@/types'

export function CreateOrganizationForm() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      const res = await fetch('/api/organizations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: name.trim() }),
      })
      const data = (await res.json().catch(() => ({}))) as { error?: string; organization?: Organization }
      if (!res.ok) {
        setError(typeof data.error === 'string' ? data.error : 'Could not create organization')
        return
      }
      if (data.organization?.id) {
        localStorage.setItem('selectedOrganizationId', data.organization.id)
        const { data: session } = await authClient.getSession()
        if (session?.user?.id) {
          await queryClient.invalidateQueries({ queryKey: ['user-organizations', session.user.id] })
        }
        await queryClient.invalidateQueries({ queryKey: ['current-organization', data.organization.id] })
        router.push('/organization')
        router.refresh()
      }
    } catch {
      setError('An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={`md-card-expressive interactive p-8 max-w-md mx-auto ${authFormFont.className}`}>
      <div className="mb-6 flex items-center gap-2">
        <Building2 className="h-6 w-6" style={{ color: 'var(--md-sys-color-primary)' }} />
        <h1 className="md-headline-small text-on-surface">New organization</h1>
      </div>
      <p className="md-body-medium text-on-surface-variant mb-6">
        Create another workspace. You can switch between organizations anytime from the header.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div
            className="md-body-small p-3 rounded-lg border-2"
            style={{
              borderColor: 'var(--md-sys-color-error)',
              color: 'var(--md-sys-color-on-error-container)',
            }}
          >
            {error}
          </div>
        )}
        <div className="space-y-2">
          <Label htmlFor="org-name">Organization name</Label>
          <Input
            id="org-name"
            name="organizationName"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="md-text-field-input h-12"
            autoComplete="organization"
            maxLength={200}
          />
        </div>
        <div className="flex gap-2 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push('/organization')}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading || !name.trim()} className="flex-1">
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create'}
          </Button>
        </div>
      </form>
    </div>
  )
}
