// Widths the user can drag. They live in CSS variables so a drag moves the page without re-rendering it.
export type Panel = { key: string; cssVar: string; fallback: number; min: number; max: number; normalize: (n: number) => number; onApply?: (n: number) => void }

const clamp = (n: number, min: number, max: number) => Math.min(max, Math.max(min, Math.round(n)))
const stored = (p: Panel) => {
  try {
    const n = Number(localStorage.getItem(p.key))
    return n > 0 ? p.normalize(n) : p.fallback
  } catch {
    return p.fallback
  }
}

// The sidebar follows the drag all the way down to just its icons. Text shortens with an ellipsis and fades out on the way.
const SIDEBAR_MIN = 64
const SIDEBAR_MAX = 360
const LABELS_GONE = 84
const LABELS_FULL = 132
export const SIDEBAR: Panel = {
  key: 'sidebar-width', cssVar: '--sidebar-w', fallback: 236, min: SIDEBAR_MIN, max: SIDEBAR_MAX,
  normalize: (n) => clamp(n, SIDEBAR_MIN, SIDEBAR_MAX),
  onApply: (n) => document.documentElement.style.setProperty('--sidebar-label', String(Math.min(1, Math.max(0, (n - LABELS_GONE) / (LABELS_FULL - LABELS_GONE))))),
}

const AGENT_MIN = 320
const AGENT_MAX = 720
const PAGE_MIN = 420 // The page keeps at least this much room beside the two panels.
export const AGENT: Panel = {
  key: 'agent-width', cssVar: '--agent-w', fallback: 400, min: AGENT_MIN, max: AGENT_MAX,
  normalize: (n) => clamp(n, AGENT_MIN, Math.max(AGENT_MIN, Math.min(AGENT_MAX, window.innerWidth - readPanel(SIDEBAR) - PAGE_MIN))),
}

const live = new Map<Panel, number>()
export function readPanel(p: Panel) {
  return live.get(p) ?? stored(p)
}
export function applyPanel(p: Panel, n: number) {
  live.set(p, n)
  document.documentElement.style.setProperty(p.cssVar, `${n}px`)
  p.onApply?.(n)
}
export function savePanel(p: Panel) {
  try {
    localStorage.setItem(p.key, String(readPanel(p)))
  } catch {
    // The width just won't be remembered next time.
  }
}

// Set before the first paint, so the page doesn't start at the default width and jump.
applyPanel(SIDEBAR, stored(SIDEBAR))
applyPanel(AGENT, stored(AGENT))
