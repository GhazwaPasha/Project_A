export type AppDataServiceName = 'DataService' | 'AccountService' | 'VoucherService' | 'SupplierService'

export async function appDataRequest<T>(
  service: AppDataServiceName,
  method: string,
  args: unknown[]
): Promise<T> {
  const res = await fetch('/api/app-data', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ service, method, args }),
  })
  if (!res.ok) {
    const text = await res.text()
    const err = new Error(text || res.statusText) as Error & {
      status?: number
      code?: string
      body?: { error?: string; code?: string; hint?: string }
    }
    err.status = res.status
    try {
      const j = JSON.parse(text) as { error?: string; code?: string; hint?: string }
      err.body = j
      if (j?.code) err.code = j.code
      if (j?.error && typeof j.error === 'string') err.message = j.error
    } catch {
      // leave message as full text
    }
    throw err
  }
  if (res.status === 204) {
    return undefined as T
  }
  const text = await res.text()
  if (!text) {
    return undefined as T
  }
  return JSON.parse(text) as T
}
