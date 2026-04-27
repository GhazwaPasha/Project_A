'use client'

import { useEffect, useState } from 'react'
import { useTheme } from 'next-themes'
import { Sun, Moon, Monitor } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * Form body for Theme (use inside the settings detail card).
 */
export function UserThemeSettingsContent() {
  const { theme, setTheme } = useTheme()
  const [ready, setReady] = useState(false)
  useEffect(() => {
    setReady(true)
  }, [])

  const current = (theme as 'light' | 'dark' | 'system' | undefined) ?? 'system'

  return (
    <div className="space-y-4">
      <p className="md-body-medium text-on-surface-variant">
        Choose the color scheme for the app. System follows your device setting.
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
              onClick={() => setTheme(id)}
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
