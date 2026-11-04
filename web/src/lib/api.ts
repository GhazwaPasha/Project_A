import type { PageContext } from './page-context'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export type Service = 'DataService' | 'VoucherService' | 'AccountService' | 'SupplierService' | 'BooksService' | 'InventoryService'

/** Dev only: `?demo=1` swaps the network for sample data, so screens can be built without signing in. */
const useDemo = () => {
  if (new URLSearchParams(location.search).has('demo')) sessionStorage.setItem('demo', '1')
  return sessionStorage.getItem('demo') === '1'
}

export async function getBootstrap(): Promise<Bootstrap> {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).bootstrap
  const res = await fetch('/api/v2/bootstrap', { credentials: 'include' })
  if (!res.ok) throw new ApiError('Could not load your account', res.status)
  return res.json()
}

export async function call<T>(service: Service, method: string, args: unknown[]): Promise<T> {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).respond(method, args) as T
  const res = await fetch(`/api/app-data?m=${service}.${method}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ service, method, args }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(body?.error ?? 'Something went wrong', res.status)
  }
  return res.status === 204 ? (undefined as T) : res.json()
}

export async function getMonthly<T>(org: string): Promise<T> {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).respond('monthly', [org]) as T
  const res = await fetch(`/api/v2/monthly?org=${encodeURIComponent(org)}`, { credentials: 'include' })
  if (!res.ok) throw new ApiError('Could not load monthly figures', res.status)
  return res.json()
}

export type Proposal = {
  id: string
  source: 'app' | 'mcp'
  source_name: string | null
  status: 'pending' | 'recorded' | 'discarded'
  date: string
  description: string
  explanation: string
  confidence: 'high' | 'medium' | 'low'
  lines: { account_id: number; code: string; name: string; debit: number; credit: number }[]
}
export type AgentEvent =
  | { type: 'text'; text: string }
  | { type: 'status'; text: string }
  | { type: 'proposal'; proposal: Proposal }
  | { type: 'error'; message: string }
  | { type: 'done' }
export type AgentRequest = { org: string; screen: string; mode: 'simple' | 'accountant'; currency: string; today: string; page?: PageContext; messages: { role: 'user' | 'assistant'; text: string }[] }

/** Streams the agent's reply as newline-delimited JSON events. */
export async function streamAgent(body: AgentRequest, onEvent: (e: AgentEvent) => void) {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).streamDemo(body, onEvent)
  const res = await fetch('/api/v2/agent', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!res.ok || !res.body) {
    const err = await res.json().catch(() => null)
    throw new ApiError(err?.error ?? 'The agent is not available right now.', res.status)
  }
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += value
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) if (line.trim()) onEvent(JSON.parse(line))
  }
}

async function jsonOr<T>(res: Response, fallback: string): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(body?.error ?? fallback, res.status)
  }
  return res.json()
}

export async function getProposals(org: string): Promise<Proposal[]> {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).listDemoProposals()
  return jsonOr(await fetch(`/api/v2/proposals?org=${encodeURIComponent(org)}`, { credentials: 'include' }), 'Could not load proposals')
}

export async function decideProposal(org: string, id: string, action: 'approve' | 'discard') {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).decideDemoProposal(id)
  return jsonOr(await fetch('/api/v2/proposals', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ org, id, action }) }), 'Could not save your decision')
}

export type Connection = { id: string; name: string; token_hint: string; can_record: boolean; created_at: string; last_used_at: string | null }

export async function getConnections(org: string): Promise<Connection[]> {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).demoConnections
  return jsonOr(await fetch(`/api/v2/connections?org=${encodeURIComponent(org)}`, { credentials: 'include' }), 'Could not load connections')
}

export async function createConnection(org: string, name: string, canRecord: boolean): Promise<{ token: string; row: Connection }> {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).addDemoConnection(name, canRecord)
  return jsonOr(await fetch('/api/v2/connections', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ org, name, canRecord }) }), 'Could not create the connection')
}

export async function revokeConnection(id: string) {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).removeDemoConnection(id)
  return jsonOr(await fetch(`/api/v2/connections?id=${encodeURIComponent(id)}`, { method: 'DELETE', credentials: 'include' }), 'Could not remove the connection')
}

const json = (body: unknown): RequestInit => ({ credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

/** Neon Auth errors arrive as { message } or { error: { message } }. */
async function authCall(path: string, body: unknown, fallback: string) {
  const res = await fetch(`/api/auth/${path}`, { method: 'POST', ...json(body) })
  const data = await res.json().catch(() => null)
  if (!res.ok || data?.error) throw new ApiError(data?.message ?? data?.error?.message ?? fallback, res.status)
  return data
}

export const signIn = (email: string, password: string) => authCall('sign-in/email', { email, password }, 'That email and password do not match.')
export const signUp = (name: string, email: string, password: string) => authCall('sign-up/email', { name, email, password }, 'Could not create your account.')

export const requestPasswordReset = (email: string) => authCall('request-password-reset', { email, redirectTo: `${location.origin}/reset-password` }, "Couldn't send the reset email. Try again.")
export const resetPassword = (newPassword: string, token: string) => authCall('reset-password', { newPassword, token }, 'That reset link has expired. Ask for a new one.')

export async function acceptInvite(token: string) {
  return jsonOr(await fetch('/api/invites/accept', { method: 'POST', ...json({ token }) }), 'Could not accept this invite.')
}

export async function completeProfile(fullName: string, organizationName: string) {
  return jsonOr(await fetch('/api/auth/complete-profile', { method: 'POST', ...json({ fullName, organizationName, organizationType: 'business' }) }), 'Could not finish setting up your account')
}

/** Calls an app route, or the sample data when building screens locally. */
export async function rest<T>(path: string, init?: { method?: string; body?: unknown }): Promise<T> {
  if (import.meta.env.DEV && useDemo()) return (await import('./demo')).demoRest(path, init?.method ?? (init?.body !== undefined ? 'POST' : 'GET'), init?.body) as T
  const res = await fetch(path, init?.body !== undefined ? { method: init.method ?? 'POST', ...json(init.body) } : { method: init?.method ?? 'GET', credentials: 'include' })
  return jsonOr(res, 'Something went wrong')
}

export const createOrganization = (name: string, description: string | null) => rest<{ id: string }>('/api/organizations', { body: { name, description } })

export async function uploadAttachment(voucherId: string | number, file: File) {
  if (import.meta.env.DEV && useDemo()) return { ok: true }
  const form = new FormData()
  form.set('voucherId', String(voucherId))
  form.set('file', file)
  return jsonOr(await fetch('/api/vouchers/attachments', { method: 'POST', credentials: 'include', body: form }), 'Could not upload the file')
}

export async function signOut() {
  await fetch('/api/auth/sign-out', { method: 'POST', credentials: 'include' })
  location.href = '/'
}

export type OrgSettings = {
  companyInfo: { legalName: string; taxId: string; registrationNumber: string; industry: string; website: string; email: string; phone: string; address: { street: string; city: string; state: string; zipCode: string; country: string } }
  accountingSettings: { fiscalYearStart: string; reportingCurrency: string; decimalPlaces: number; [k: string]: unknown }
  notificationSettings: { lowBalanceAlert: number; [k: string]: unknown }
  securitySettings: { sessionTimeout: number; [k: string]: unknown }
}
export type Org = { id: string; name: string; description?: string | null; role: string | null; currency: string; decimals: number; settings?: OrgSettings }
export type Bootstrap = {
  user: { id: string; email: string; name?: string | null }
  isSuperAdmin: boolean
  hasProfile: boolean
  profile?: { full_name: string | null; phone: string | null } | null
  organizations: Org[]
}
