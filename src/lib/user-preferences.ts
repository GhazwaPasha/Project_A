import type { UserProfile, UserPreferences } from '@/types'
import { parseOrgAccent } from '@/lib/org-accent-color'

/**
 * `jsonb` is usually an object from the `postgres` driver, but we guard against
 * a serialized string (or odd shapes) so `preferences.accentColor` is always addressable.
 */
export function parseUserPreferences(raw: unknown): UserPreferences {
  if (raw == null) return {}
  if (typeof raw === 'string') {
    try {
      const o = JSON.parse(raw) as unknown
      if (o && typeof o === 'object' && !Array.isArray(o)) return o as UserPreferences
    } catch {
      return {}
    }
    return {}
  }
  if (typeof raw === 'object' && !Array.isArray(raw)) return raw as UserPreferences
  return {}
}

export function getAccentColorFromProfile(profile: UserProfile | null | undefined): string | null {
  if (!profile) return null
  const prefs = parseUserPreferences(profile.preferences)
  const s = prefs.accentColor
  if (s == null) return null
  return parseOrgAccent(String(s))
}

/**
 * True when the server row includes `preferences.accentColor` (key present), but the
 * value does not resolve to a custom hex — e.g. `null` (Use default) or empty/invalid.
 * When the key is **absent** (e.g. `{}` from API), this is false so we can keep
 * localStorage / inline tokens instead of flashing `globals.css` defaults.
 */
export function profileExplicitlyHasNoCustomAccent(
  profile: UserProfile | null | undefined
): boolean {
  if (!profile) return false
  const prefs = parseUserPreferences(profile.preferences)
  if (!Object.prototype.hasOwnProperty.call(prefs, 'accentColor')) return false
  return getAccentColorFromProfile(profile) == null
}

/**
 * Stable string for `UserAccentRoot` effect deps: avoid re-running on object identity
 * (e.g. `loadUserData` refetch) when the accent value did not change.
 */
export function getProfileAccentSignature(profile: UserProfile | null | undefined): string {
  if (!profile) return 'no_profile'
  const prefs = parseUserPreferences(profile.preferences)
  if (!Object.prototype.hasOwnProperty.call(prefs, 'accentColor')) {
    return 'accent_key_absent'
  }
  if (prefs.accentColor == null || String(prefs.accentColor).trim() === '') {
    return 'accent_default'
  }
  const hex = parseOrgAccent(String(prefs.accentColor))
  if (!hex) return 'accent_default'
  return `hex:${hex.toLowerCase()}`
}
