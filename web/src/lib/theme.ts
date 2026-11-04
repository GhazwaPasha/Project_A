import { useCallback, useSyncExternalStore } from 'react'

const media = () => matchMedia('(prefers-color-scheme: dark)')
const saved = () => {
  try { return localStorage.getItem('theme') } catch { return null }
}
const isDark = () => (saved() ? saved() === 'dark' : media().matches)
const listeners = new Set<() => void>()

function apply() {
  document.documentElement.classList.toggle('dark', isDark())
  listeners.forEach((l) => l())
}

function subscribe(l: () => void) {
  listeners.add(l)
  media().addEventListener('change', apply)
  return () => {
    listeners.delete(l)
    media().removeEventListener('change', apply)
  }
}

/** Follows the system until the person picks a side. index.html applies it before first paint. */
export function useTheme() {
  const dark = useSyncExternalStore(subscribe, isDark)
  const toggle = useCallback(() => {
    try { localStorage.setItem('theme', isDark() ? 'light' : 'dark') } catch { /* keep the system setting */ }
    // A cross-fade, so the whole screen doesn't flash. Browsers without it just switch.
    if ('startViewTransition' in document && !matchMedia('(prefers-reduced-motion: reduce)').matches) document.startViewTransition(apply)
    else apply()
  }, [])
  return { dark, toggle }
}
