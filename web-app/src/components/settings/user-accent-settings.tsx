'use client'

import { useCallback, useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth-store'
import { DataService } from '@/lib/data-service'
import { isValidHex6 } from '@/lib/org-accent-color'
import { getAccentColorFromProfile } from '@/lib/user-preferences'
import { Save, RotateCcw } from 'lucide-react'

/**
 * Form body for the Accent color section (use inside the settings detail card).
 */
export function UserAccentSettingsContent() {
  const user = useAuthStore((s) => s.user)
  const profile = useAuthStore((s) => s.profile)
  const setProfile = useAuthStore((s) => s.setProfile)

  const initial = getAccentColorFromProfile(profile) ?? ''
  const [hex, setHex] = useState(initial)
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    setHex(getAccentColorFromProfile(profile) ?? '')
  }, [profile?.id, profile?.updated_at, profile?.preferences])

  const applyProfile = useCallback(
    (next: NonNullable<typeof profile>) => {
      setProfile(next)
    },
    [setProfile]
  )

  const save = async (clear: boolean) => {
    if (!user) return
    const patch: { accentColor: string | null } = clear ? { accentColor: null } : { accentColor: hex.trim() }
    if (!clear && patch.accentColor && !isValidHex6(patch.accentColor)) {
      setErr('Use a valid color in the form #RRGGBB.')
      return
    }
    setErr(null)
    setSaving(true)
    try {
      const updated = await DataService.updateUserPreferences(user.id, patch)
      if (updated) {
        applyProfile(updated)
      } else {
        setErr('Could not save. Ensure your user profile exists (complete sign-up) or try again.')
      }
      if (clear) setHex('')
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not save')
    } finally {
      setSaving(false)
    }
  }

  if (!user) {
    return <p className="text-sm text-on-surface-variant">Sign in to set your accent color.</p>
  }

  return (
    <div className="space-y-4">
      <p className="md-body-medium text-on-surface-variant">
        Pick a color for buttons, focus rings, and other primary highlights. Stored in your account
        preferences, not the organization.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="text-sm font-medium text-on-surface-variant block mb-1">Accent</label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              className="h-10 w-14 cursor-pointer rounded border border-outline bg-transparent p-0"
              value={isValidHex6(hex) ? hex : '#4a5568'}
              onChange={(e) => setHex(e.target.value.toLowerCase())}
              aria-label="Pick accent color"
            />
            <input
              type="text"
              className="h-10 w-32 rounded-lg border border-outline bg-surface-container px-3 text-sm text-on-surface"
              placeholder="#4a5568"
              value={hex}
              onChange={(e) => setHex(e.target.value)}
              spellCheck={false}
            />
          </div>
        </div>
        <Button type="button" className="md-button" disabled={saving} onClick={() => void save(false)}>
          <Save className="w-4 h-4 mr-2" />
          Save
        </Button>
        <Button type="button" variant="outline" disabled={saving} onClick={() => void save(true)}>
          <RotateCcw className="w-4 h-4 mr-2" />
          Use default
        </Button>
      </div>
      {err && <p className="text-sm text-error">{err}</p>}
    </div>
  )
}
