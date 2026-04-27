'use client'

import { useEffect, useRef, useState } from 'react'
import { useTheme } from 'next-themes'
import { Sun, Moon, Monitor } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import { DataService } from '@/lib/data-service'
import { getThemePreferenceFromProfile } from '@/lib/user-preferences'

/**
 * Theme control backed by next-themes and persisted in `user_profiles.preferences.theme`.
 */
export function UserThemeSettingsContent() {
  const { theme, setTheme } = useTheme()
  const [ready, setReady] = useState(false)
  const user = useAuthStore((s) => s.user)
  const profile = useAuthStore((s) => s.profile)
  const setProfile = useAuthStore((s) => s.setProfile)
  const hydratedFromProfile = useRef(false)

  useEffect(() => {
    setReady(true)
  }, [])

  const prefTheme = profile ? getThemePreferenceFromProfile(profile) : undefined

  useEffect(() => {
    if (!ready || !prefTheme) return
    if (hydratedFromProfile.current) return
    const current = (theme as 'light' | 'dark' | 'system' | undefined) ?? 'system'
    if (current !== prefTheme) {
      setTheme(prefTheme)
    }
    hydratedFromProfile.current = true
  }, [ready, prefTheme, theme, setTheme])

  useEffect(() => {
    hydratedFromProfile.current = false
  }, [profile?.id])

  const current = (theme as 'light' | 'dark' | 'system' | undefined) ?? 'system'

  const pick = async (id: 'light' | 'dark' | 'system') => {
    setTheme(id)
    if (!user) return
    try {
      const updated = await DataService.updateUserPreferences(user.id, { theme: id })
      if (updated) setProfile(updated)
    } catch {
      // Theme already applied locally; profile sync can retry on next navigation
    }
  }

  return (
    <div className="space-y-4">
      <p className="md-body-medium text-on-surface-variant">
        Choose the color scheme for the app. System follows your device setting. Your choice is saved
        to your account.
      </p>
      <div className="grid grid-cols-3 gap-2 max-w-md" role="group" aria-label="Color mode">
        {(
          [
            { id: 'light' as const, label: 'Light', Icon: Sun },
            { id: 'dark' as const, label: 'Dark', Icon: Moon },
            { id: 'system' as const, label: 'System', Icon: Monitor },
          ] as const
        ).map(({ id, label, Icon }) => {
          const active = ready && current === id
          return (
            <button
              key={id}
              type="button"
              disabled={!ready}
              onClick={() => void pick(id)}
              className={cn(
                'flex flex-col items-center justify-center gap-1 rounded-2xl border py-3 px-2 text-sm font-medium transition-colors',
                active
                  ? 'border-primary bg-primary-container text-on-primary-container'
                  : 'border-outline bg-surface-container text-on-surface hover:bg-surface-container-highest'
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
              {label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
