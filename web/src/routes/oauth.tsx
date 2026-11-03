import { useState } from 'react'
import { useQuery, queryOptions } from '@tanstack/react-query'
import { Choice, Toggle } from '@/components/form'
import { btn } from '@/components/page'
import { rest } from '@/lib/api'
import { useApp } from '@/lib/boot'

/** Where a person approves an AI app connecting to their books over MCP. */
export function OAuthConsent() {
  const { orgs, org, access } = useApp()
  const p = new URLSearchParams(location.search)
  const clientId = p.get('client_id') ?? ''
  const redirect = p.get('redirect_uri') ?? ''
  const challenge = p.get('code_challenge') ?? ''
  const method = p.get('code_challenge_method') ?? ''
  const state = p.get('state') ?? undefined
  const client = useQuery(queryOptions({ queryKey: ['oauth-client', clientId, redirect], queryFn: () => rest<{ name: string }>(`/api/oauth/client?client_id=${encodeURIComponent(clientId)}&redirect_uri=${encodeURIComponent(redirect)}`), retry: false }))
  const [target, setTarget] = useState(org.id)
  const [canRecord, setCanRecord] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const usable = orgs.filter((o) => o.role !== 'member' && o.role !== 'observer')
  const valid = p.get('response_type') === 'code' && method === 'S256' && challenge.length >= 43

  const go = (url: string) => { location.href = url }
  const approve = async () => {
    setBusy(true)
    setError(null)
    try {
      const r = await rest<{ redirect: string }>('/api/oauth/approve', { body: { client_id: clientId, redirect_uri: redirect, code_challenge: challenge, code_challenge_method: method, state, org: target, can_record: canRecord } })
      go(r.redirect)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not approve this app.')
      setBusy(false)
    }
  }
  const deny = () => {
    const u = new URL(redirect)
    u.searchParams.set('error', 'access_denied')
    if (state) u.searchParams.set('state', state)
    go(u.toString())
  }
  let host = redirect
  try { host = new URL(redirect).host || new URL(redirect).protocol } catch { /* shown as given */ }

  return (
    <main className="min-h-dvh grid place-items-center p-4">
      <div className="sheet w-full max-w-[440px] p-5 flex flex-col gap-3.5">
        <p className="font-semibold text-[15px]">Accountuitive</p>
        {client.isPending ? <p className="text-muted-foreground">One moment…</p> : !client.data || !valid ? (
          <div role="alert"><h1 className="text-[18px] font-semibold">This request can't be approved</h1><p className="text-muted-foreground">The app isn't recognized, or its request is incomplete. Nothing has been shared.</p></div>
        ) : usable.length === 0 ? (
          <div><h1 className="text-[18px] font-semibold">Your role doesn't include this</h1><p className="text-muted-foreground">Ask an organization owner for access to the books first.</p></div>
        ) : (
          <>
            <div>
              <h1 className="text-[18px] leading-tight font-semibold">Connect {client.data.name}?</h1>
              <p className="text-[13.5px] text-muted-foreground mt-1">It will be able to read this organization's books and propose entries for you to approve, as you. It returns to <span className="whitespace-nowrap font-medium text-foreground">{host}</span>. Only approve apps you trust. The name is what the app calls itself.</p>
            </div>
            <Choice label="Organization" value={target} onChange={setTarget} options={usable.map((o) => ({ value: o.id, label: o.name }))} />
            {access === 'owner' || access === 'books' ? <Toggle label="Allow it to record entries directly" hint="Off is safer: anything it prepares waits for your approval." checked={canRecord} onChange={setCanRecord} /> : null}
            {error ? <p role="alert" className="text-[13px] text-destructive">{error}</p> : null}
            <div className="flex justify-end gap-2">
              <button className={btn.plain} disabled={busy} onClick={deny}>Deny</button>
              <button className={btn.primary} disabled={busy} onClick={() => void approve()}>{busy ? 'Connecting…' : 'Approve'}</button>
            </div>
            <p className="text-[12px] text-muted-foreground">You can remove it at any time under Settings, Connections.</p>
          </>
        )}
      </div>
    </main>
  )
}
