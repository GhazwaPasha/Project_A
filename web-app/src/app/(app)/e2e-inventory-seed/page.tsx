'use client'

import { useState } from 'react'
import { useCurrentOrganization } from '@/contexts/organization-context'
import { runE2EInventoryAccountingSeed, type E2EInventorySeedResult } from '@/lib/e2e/inventory-accounting-seed'
import { Button } from '@/components/ui/button'

const HINT_ORG = '2dd4de28-8d87-40c2-88a7-9fb87d4e2bfc'

/**
 * Local dev: sign in as E2E Owner, select **E2E Org Sidebar Fix**, then run the seed
 * to create 20+ inventory records + journal activity on the same GL lines as the UI.
 * Same API calls as the rest of the app (DataService → /api/app-data).
 */
export default function E2EInventorySeedPage() {
  const org = useCurrentOrganization()
  const [result, setResult] = useState<E2EInventorySeedResult | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (process.env.NODE_ENV === 'production') {
    return (
      <div className="p-6">
        <p className="text-on-surface">This E2E helper is not available in production.</p>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-3xl space-y-4 text-on-surface">
      <h1 className="text-2xl font-semibold">E2E inventory + GL seed (dev only)</h1>
      <p className="text-on-surface-variant text-sm">
        Use test user <strong>Owner</strong> from <code>TEST_CREDENTIALS.md</code> and the org
        <strong> E2E Org Sidebar Fix</strong> (id <code className="text-xs">{HINT_ORG}</code>).
        This creates 3 categories, 6 items, 20 stock transactions, and 5 posted journal lines using the same
        <code> DataService</code> paths as the Inventory, Chart of accounts, and Journal UIs.
      </p>
      {org ? (
        <p className="text-sm">Current org: {org.name} — {org.id}</p>
      ) : (
        <p className="text-sm text-error">No organization in context. Select the E2E org in the app header.</p>
      )}
      <Button
        type="button"
        disabled={!org || busy}
        onClick={async () => {
          if (!org) return
          setErr(null)
          setResult(null)
          setBusy(true)
          try {
            const r = await runE2EInventoryAccountingSeed(org.id)
            setResult(r)
          } catch (e) {
            setErr(e instanceof Error ? e.message : String(e))
          } finally {
            setBusy(false)
          }
        }}
      >
        {busy ? 'Seeding…' : 'Run inventory + journal seed'}
      </Button>
      {err && (
        <div className="rounded border border-error p-3 text-sm text-error whitespace-pre-wrap">{err}</div>
      )}
      {result && (
        <div className="space-y-2 text-sm">
          <p>
            <strong>Run</strong> <code>{result.runId}</code> — transactions: {result.transactionIds.length}, journals:{' '}
            {result.journalEntryIds.length}
          </p>
          <pre className="p-3 rounded border border-outline bg-surface-container-low text-xs overflow-auto max-h-[32rem]">
            {result.log.join('\n')}
          </pre>
        </div>
      )}
    </div>
  )
}
