import type { UserProfile } from '@/types'
import { hexToHslVarTriplet } from '@/lib/org-accent-color'
import { getAccentColorFromProfile, profileExplicitlyHasNoCustomAccent } from '@/lib/user-preferences'

const ACCENT = '--org-accent-hex'
const PRIMARY = '--primary'
const RING = '--ring'
const PRIMARY_FG = '--primary-foreground'

/** Persisted for `beforeInteractive` boot; must match the inline script reader. */
export const USER_ACCENT_TOKENS_KEY = 'accui.userAccentTokensV1'

type TokensV1 = { a: string; p: string; o: string }

const HEX6 = /^#[0-9A-Fa-f]{6}$/

function normalizeHexKey(hex: string): string {
  return String(hex).trim().toLowerCase()
}

function readInlineTokensOnRoot(root: HTMLElement): TokensV1 | null {
  const a = root.style.getPropertyValue(ACCENT).trim()
  if (!a || !HEX6.test(a)) return null
  const p = root.style.getPropertyValue(PRIMARY).trim()
  const o = root.style.getPropertyValue(PRIMARY_FG).trim()
  if (!p || o === '') return null
  return { a: normalizeHexKey(a), p, o: o.trim() }
}

function tokensV1Equal(a: TokensV1, b: TokensV1): boolean {
  return (
    normalizeHexKey(a.a) === normalizeHexKey(b.a) && a.p === b.p && a.o === b.o
  )
}

function setTokensOnRoot(root: HTMLElement, t: TokensV1): void {
  const norm: TokensV1 = { a: normalizeHexKey(t.a), p: t.p, o: t.o }
  root.style.setProperty(ACCENT, norm.a)
  root.style.setProperty(PRIMARY, norm.p)
  root.style.setProperty(RING, norm.p)
  root.style.setProperty(PRIMARY_FG, norm.o)
}

/** No-op if inline tokens already match (avoids double paint on Strict / rehydration). */
function setTokensOnRootIfChanged(root: HTMLElement, t: TokensV1): void {
  const norm: TokensV1 = { a: normalizeHexKey(t.a), p: t.p, o: t.o }
  const cur = readInlineTokensOnRoot(root)
  if (cur && tokensV1Equal(cur, norm)) {
    return
  }
  setTokensOnRoot(root, norm)
}

export function clearUserAccentOnRoot(root: HTMLElement): void {
  root.style.removeProperty(ACCENT)
  root.style.removeProperty(PRIMARY)
  root.style.removeProperty(RING)
  root.style.removeProperty(PRIMARY_FG)
}

/** Same validation as the boot IIFE. */
export function readUserAccentFromLocalStorage(): TokensV1 | null {
  if (typeof localStorage === 'undefined') return null
  try {
    const j = localStorage.getItem(USER_ACCENT_TOKENS_KEY)
    if (!j) return null
    const t = JSON.parse(j) as unknown
    if (!t || typeof t !== 'object' || Array.isArray(t)) return null
    const o = t as Record<string, unknown>
    if (
      typeof o.a === 'string' &&
      typeof o.p === 'string' &&
      typeof o.o === 'string' &&
      HEX6.test(o.a)
    ) {
      return { a: normalizeHexKey(o.a), p: o.p, o: o.o }
    }
    return null
  } catch {
    return null
  }
}

type ApplyUserAccentContext = {
  /**
   * While `loadUserData` is in flight, a persisted `profile` can still show
   * `accentColor: null` before the server response — do not clear theme tokens
   * in that case if we have valid localStorage (avoids a flash to `globals.css` defaults).
   */
  profileLoadInProgress?: boolean
}

/**
 * Applies the user's accent color to CSS custom properties on `root`.
 *
 * When `userId` is null we do **nothing** — the boot-script inline-script already
 * set the right tokens before first paint.  Clearing here caused a visible flash:
 * `user` is not persisted by zustand so it's null for a tick after rehydration
 * while `profile` (which IS persisted) is already available.
 * Explicit sign-out clears both localStorage and root inline styles via `logout()`.
 */
export function applyUserAccentToRoot(
  root: HTMLElement,
  profile: UserProfile | null | undefined,
  userId: string | null | undefined,
  ctx?: ApplyUserAccentContext
): void {
  if (!userId) {
    // Not yet authenticated (or session resolving) — leave boot-script values intact.
    return
  }
  const fromProfile = getAccentColorFromProfile(profile)
  if (fromProfile) {
    const hsl = hexToHslVarTriplet(fromProfile)
    if (hsl) {
      setTokensOnRootIfChanged(root, { a: fromProfile, p: hsl.primary, o: hsl.onPrimary })
    } else {
      clearUserAccentOnRoot(root)
    }
    return
  }
  if (profileExplicitlyHasNoCustomAccent(profile)) {
    if (ctx?.profileLoadInProgress) {
      const cached = readUserAccentFromLocalStorage()
      if (cached) {
        setTokensOnRootIfChanged(root, { a: cached.a, p: cached.p, o: cached.o })
        return
      }
    }
    clearUserAccentOnRoot(root)
    return
  }
  const cached = readUserAccentFromLocalStorage()
  if (cached) {
    setTokensOnRootIfChanged(root, {
      a: cached.a,
      p: cached.p,
      o: cached.o,
    })
  }
  // Else: do not call removeProperty — keep stylesheet or boot IIFE.
}

export function syncUserAccentLocalStorageFromProfile(profile: UserProfile | null | undefined): void {
  if (typeof localStorage === 'undefined') return
  if (profileExplicitlyHasNoCustomAccent(profile)) {
    try {
      localStorage.removeItem(USER_ACCENT_TOKENS_KEY)
    } catch {
      /* private mode / quota */
    }
    return
  }
  const hex = getAccentColorFromProfile(profile)
  if (!hex) {
    return
  }
  const hsl = hexToHslVarTriplet(hex)
  if (!hsl) {
    return
  }
  const payload: TokensV1 = { a: normalizeHexKey(hex), p: hsl.primary, o: hsl.onPrimary }
  try {
    localStorage.setItem(USER_ACCENT_TOKENS_KEY, JSON.stringify(payload))
  } catch {
    /* */
  }
}

export function clearUserAccentLocalStorage(): void {
  if (typeof localStorage === 'undefined') return
  try {
    localStorage.removeItem(USER_ACCENT_TOKENS_KEY)
  } catch {
    /* */
  }
}

/**
 * Runs before first paint (see root layout `beforeInteractive` script) so the
 * document is not stuck on stylesheet defaults until React hydrates.
 */
export const USER_ACCENT_BOOT_INLINE = `!function(){try{var j=localStorage.getItem('${USER_ACCENT_TOKENS_KEY}');if(!j)return;var t=JSON.parse(j);if(!t||typeof t.a!=='string'||!/^#[0-9A-Fa-f]{6}$/.test(t.a)||typeof t.p!=='string'||typeof t.o!=='string')return;var r=document.documentElement;r.style.setProperty('--org-accent-hex',t.a);r.style.setProperty('--primary',t.p);r.style.setProperty('--ring',t.p);r.style.setProperty('--primary-foreground',t.o);}catch(e){}}();`
