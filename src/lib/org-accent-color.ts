/** `#RRGGBB` (case-insensitive). */
const HEX6 = /^#[0-9A-Fa-f]{6}$/

export function isValidHex6(s: string): boolean {
  return HEX6.test(s.trim())
}

export function parseOrgAccent(settingsField: string | null | undefined): string | null {
  if (settingsField == null || String(settingsField).trim() === '') return null
  const s = String(settingsField).trim()
  if (!isValidHex6(s)) return null
  return s
}

/**
 * shadcn / Tailwind: `hsl(var(--primary) / 1)` expects `--primary` like `222 47% 12%` (H and % on S and L).
 */
export function hexToHslVarTriplet(hex: string): { primary: string; onPrimary: string } | null {
  if (!isValidHex6(hex)) return null
  const n = parseInt(hex.slice(1), 16)
  const r = ((n >> 16) & 0xff) / 255
  const g = ((n >> 8) & 0xff) / 255
  const b = (n & 0xff) / 255
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const d = max - min
  let h = 0
  if (d > 0) {
    if (max === r) h = 60 * ((g - b) / d)
    else if (max === g) h = 60 * ((b - r) / d + 2)
    else h = 60 * ((r - g) / d + 4)
    h = h % 360
    if (h < 0) h += 360
  }
  const hDeg = Math.round(h)
  const l = (max + min) / 2
  const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1) || 1e-6)
  const sPct = (s * 100).toFixed(1)
  const lPct = (l * 100).toFixed(1)
  const primary = `${hDeg} ${sPct}% ${lPct}%`
  // WCAG simple: light backgrounds use dark "on" text, else light
  const onPrimary = l > 0.6 ? '0 0% 5%' : '0 0% 100%'
  return { primary, onPrimary }
}
