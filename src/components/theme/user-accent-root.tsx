'use client'

import { useEffect } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import { applyUserAccentToRoot } from '@/lib/user-accent-early'
import { getProfileAccentSignature } from '@/lib/user-preferences'

/**
 * Pushes the signed-in user’s `preferences.accentColor` to theme tokens.
 * Deps use `getProfileAccentSignature` (not `profile.preferences` ref) so
 * `loadUserData` refetches don’t re-apply the same color and double-paint.
 *
 * Uses `useEffect` (not `useLayoutEffect`) so this runs *after* `AuthProvider`’s
 * effect, which calls `loadUserData` and sets `profileLoadInProgress` before the
 * first `await` — that ordering avoids clearing accent tokens on a stale
 * rehydrated `profile`. Initial paint is still covered by the inline boot script
 * in the root layout.
 */
export function UserAccentRoot() {
  const user = useAuthStore((s) => s.user)
  const profile = useAuthStore((s) => s.profile)
  const profileLoadInProgress = useAuthStore((s) => s.profileLoadInProgress)
  const accentDep = getProfileAccentSignature(profile)

  // profile omitted from deps on purpose: accentDep already tracks accent value changes; including profile
  // re-ran when loadUserData returns the same payload with a new object reference.
  // eslint-disable-next-line react-hooks/exhaustive-deps -- see above
  useEffect(() => {
    applyUserAccentToRoot(document.documentElement, profile, user?.id ?? null, {
      profileLoadInProgress,
    })
  }, [user?.id, accentDep, profileLoadInProgress])

  return null
}
