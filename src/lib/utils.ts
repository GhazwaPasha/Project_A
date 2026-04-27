import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format a monetary amount in the given ISO 4217 currency. Falls back to USD if the code is invalid.
 * `fractionDigits` maps to the organization’s accounting decimal-places when using org settings.
 */
export function formatMonetaryAmount(
  amount: number,
  currency: string = 'USD',
  fractionDigits: number = 2
): string {
  const code = (currency && currency.trim()) ? currency.trim().toUpperCase() : 'USD'
  const fd = Math.min(6, Math.max(0, Math.floor(fractionDigits)))
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: code,
      minimumFractionDigits: fd,
      maximumFractionDigits: fd,
    }).format(amount)
  } catch {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  }
}

/** For non–org UIs, pass `currency` explicitly. Org screens should use `useOrganizationFormatters`. */
export function formatCurrency(amount: number, currency: string = 'USD', fractionDigits: number = 2): string {
  return formatMonetaryAmount(amount, currency, fractionDigits)
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value)
}

export function formatPercentage(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100)
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(date))
}

/** Avoids 1970 epoch and invalid dates from null/undefined. */
export function formatReportLastGeneratedAt(date: string | Date | null | undefined): string {
  if (date == null) return 'Never'
  const t = new Date(date).getTime()
  if (!Number.isFinite(t) || t <= 0) return 'Never'
  return formatDate(date)
}

export function formatDateTime(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date))
}

/** Journal line: accounting date (`entry_date`) plus wall-clock time when the entry was recorded (`created_at`). */
export function formatEntryDateTime(
  entryDate: string,
  createdAt: string | null | undefined
): string {
  if (!createdAt) return formatDate(entryDate)
  const datePart = formatDate(entryDate)
  const timePart = new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(createdAt))
  return `${datePart}, ${timePart}`
}

/** General Ledger account row: prefer wall-clock `last_transaction_at`, else accounting date only. */
export function formatAccountLastActivity(
  lastTransactionDate: string | null | undefined,
  lastTransactionAt: string | null | undefined
): string | null {
  if (lastTransactionAt) {
    const t = new Date(lastTransactionAt).getTime()
    if (Number.isFinite(t)) return formatDateTime(lastTransactionAt)
  }
  if (lastTransactionDate) return formatDate(lastTransactionDate)
  return null
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}
