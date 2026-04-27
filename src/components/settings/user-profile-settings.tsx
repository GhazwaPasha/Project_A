'use client'

import { useCallback, useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/stores/auth-store'
import { DataService } from '@/lib/data-service'
import { Save } from 'lucide-react'

/**
 * Editable fields stored on `public.user_profiles`. Email is managed by Neon Auth.
 */
export function UserProfileSettingsContent() {
  const user = useAuthStore((s) => s.user)
  const profile = useAuthStore((s) => s.profile)
  const setProfile = useAuthStore((s) => s.setProfile)

  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setFullName(profile?.full_name?.trim() ?? '')
    setPhone(profile?.phone?.trim() ?? '')
    setAvatarUrl(profile?.avatar_url?.trim() ?? '')
  }, [profile?.id, profile?.full_name, profile?.phone, profile?.avatar_url])

  const save = useCallback(async () => {
    if (!user) return
    setErr(null)
    setSaved(false)
    setSaving(true)
    try {
      const updated = await DataService.updateUserProfile(user.id, {
        full_name: fullName.trim() || null,
        phone: phone.trim() || null,
        avatar_url: avatarUrl.trim() || null,
      })
      if (updated) {
        setProfile(updated)
        setSaved(true)
      } else {
        setErr('Could not save. Ensure your profile exists or try again.')
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not save')
    } finally {
      setSaving(false)
    }
  }, [user, fullName, phone, avatarUrl, setProfile])

  if (!user) {
    return <p className="text-sm text-on-surface-variant">Sign in to edit your profile.</p>
  }

  return (
    <div className="space-y-6">
      <p className="md-body-medium text-on-surface-variant">
        Your name and contact details are stored in your Accountuitive profile. Email is tied to your
        sign-in account and cannot be changed here.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
        <div className="md:col-span-2 space-y-2">
          <label htmlFor="settings-full-name" className="text-sm font-medium text-on-surface-variant">
            Full name
          </label>
          <Input
            id="settings-full-name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="md-text-field-input rounded-xl"
            autoComplete="name"
          />
        </div>
        <div className="space-y-2">
          <span className="text-sm font-medium text-on-surface-variant">Email</span>
          <p className="text-base text-on-surface py-2 px-3 rounded-xl bg-surface-container border border-outline">
            {profile?.email ?? user.email}
          </p>
        </div>
        <div className="space-y-2">
          <label htmlFor="settings-phone" className="text-sm font-medium text-on-surface-variant">
            Phone
          </label>
          <Input
            id="settings-phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="md-text-field-input rounded-xl"
            autoComplete="tel"
          />
        </div>
        <div className="md:col-span-2 space-y-2">
          <label htmlFor="settings-avatar" className="text-sm font-medium text-on-surface-variant">
            Avatar image URL
          </label>
          <Input
            id="settings-avatar"
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
            placeholder="https://…"
            className="md-text-field-input rounded-xl"
            autoComplete="off"
          />
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button type="button" className="md-button" disabled={saving} onClick={() => void save()}>
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving…' : 'Save profile'}
        </Button>
        {saved && <span className="text-sm text-on-surface-variant">Saved.</span>}
      </div>
      {err && <p className="text-sm text-error">{err}</p>}
    </div>
  )
}
