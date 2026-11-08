/**
 * Money arithmetic in whole cents, so sums are exact however many lines they add up. Postgres stores money as
 * numeric; values arrive as text or numbers, are turned into integer cents here, added, and turned back at the end.
 * Rounds half away from zero, the usual rule for money.
 */

const MAX_SAFE_CENTS = Number.MAX_SAFE_INTEGER

/** Integer cents for a money value. Text is read digit by digit, so "0.1" is exactly 10 cents. */
export function toCents(value: number | string | null | undefined): number {
  if (value === null || value === undefined || value === '') return 0
  if (typeof value === 'string') {
    const m = /^\s*([+-])?(\d*)(?:\.(\d*))?\s*$/.exec(value)
    if (!m || (!m[2] && !m[3])) {
      const n = Number(value)
      if (!Number.isFinite(n)) throw new Error(`"${value}" is not an amount.`)
      return toCents(n)
    }
    const sign = m[1] === '-' ? -1 : 1
    const whole = m[2] ? Number(m[2]) : 0
    const frac = (m[3] ?? '').padEnd(3, '0')
    let cents = whole * 100 + Number(frac.slice(0, 2))
    if (Number(frac[2]) >= 5) cents += 1
    if (cents > MAX_SAFE_CENTS) throw new Error('That amount is too large.')
    return sign * cents
  }
  if (!Number.isFinite(value)) throw new Error('An amount must be a number.')
  const sign = value < 0 ? -1 : 1
  // The small nudge undoes binary error, so 1.005 (stored as 1.00499999...) rounds to 1.01 as written.
  const cents = Math.round(Math.abs(value) * 100 + 1e-7)
  if (cents > MAX_SAFE_CENTS) throw new Error('That amount is too large.')
  return sign * cents
}

export const fromCents = (cents: number) => cents / 100

/** A money value rounded to the cent. */
export const roundMoney = (value: number | string) => fromCents(toCents(value))

/** The exact sum of money values. */
export const sumMoney = (values: readonly (number | string)[]) => {
  let cents = 0
  for (const v of values) cents += toCents(v)
  return fromCents(cents)
}

/** a minus b, exactly. */
export const subtractMoney = (a: number | string, b: number | string) => fromCents(toCents(a) - toCents(b))
