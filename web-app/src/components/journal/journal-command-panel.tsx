'use client'

import { useState, useEffect, useCallback } from 'react'
import { useCurrentOrganization } from '@/contexts/organization-context'
import { commandApiFetch, CommandApiError } from '@/lib/command-api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { useAccounts } from '@/hooks/use-organization-data'

type ProposalRow = {
  id: number
  status: string
  payload: {
    description?: string
    entry_date?: string
    lines?: Array<{ account_id: number; debit_amount: number; credit_amount: number }>
  }
  created_at: string
}

export function JournalCommandPanel({ readOnly = false }: { readOnly?: boolean }) {
  const org = useCurrentOrganization()
  const { toast } = useToast()
  const { data: accounts = [] } = useAccounts()
  const [proposals, setProposals] = useState<ProposalRow[]>([])
  const [loading, setLoading] = useState(false)
  const [description, setDescription] = useState('Accrual (event ledger)')
  const [entryDate, setEntryDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [debitAccountId, setDebitAccountId] = useState('')
  const [creditAccountId, setCreditAccountId] = useState('')
  const [amount, setAmount] = useState('100')

  const load = useCallback(async () => {
    if (!org?.id) return
    setLoading(true)
    try {
      const data = (await commandApiFetch(
        `journal/proposals?organization_id=${encodeURIComponent(org.id)}`
      )) as { proposals: ProposalRow[] }
      setProposals(data.proposals ?? [])
    } catch (e) {
      const msg = e instanceof CommandApiError ? e.message : 'Failed to load proposals'
      toast({ title: 'Command API', description: msg, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }, [org?.id, toast])

  useEffect(() => {
    void load()
  }, [load])

  const propose = async () => {
    if (readOnly || !org?.id) return
    const amt = Number(amount)
    const da = Number(debitAccountId)
    const ca = Number(creditAccountId)
    if (!Number.isFinite(amt) || amt <= 0 || !Number.isFinite(da) || !Number.isFinite(ca)) {
      toast({ title: 'Validation', description: 'Enter valid account ids and amount', variant: 'destructive' })
      return
    }
    try {
      await commandApiFetch('journal/propose', {
        method: 'POST',
        body: JSON.stringify({
          organization_id: org.id,
          description,
          entry_date: entryDate,
          reference: null,
          lines: [
            { account_id: da, debit_amount: amt, credit_amount: 0, description: 'Debit' },
            { account_id: ca, debit_amount: 0, credit_amount: amt, description: 'Credit' },
          ],
        }),
        headers: { 'Idempotency-Key': crypto.randomUUID() },
      })
      toast({ title: 'Proposed', description: 'Journal proposal created (event log).' })
      await load()
    } catch (e) {
      const msg = e instanceof CommandApiError ? e.message : 'Propose failed'
      toast({ title: 'Error', description: msg, variant: 'destructive' })
    }
  }

  const approve = async (id: number) => {
    if (readOnly || !org?.id) return
    try {
      await commandApiFetch('journal/approve', {
        method: 'POST',
        body: JSON.stringify({ organization_id: org.id, proposal_id: id }),
      })
      toast({ title: 'Approved', description: `Proposal #${id}` })
      await load()
    } catch (e) {
      const msg = e instanceof CommandApiError ? e.message : 'Approve failed'
      toast({ title: 'Error', description: msg, variant: 'destructive' })
    }
  }

  const post = async (id: number) => {
    if (readOnly || !org?.id) return
    try {
      await commandApiFetch('journal/post', {
        method: 'POST',
        body: JSON.stringify({ organization_id: org.id, proposal_id: id }),
      })
      toast({ title: 'Posted', description: `Proposal #${id} posted to projection.` })
      await load()
    } catch (e) {
      const msg = e instanceof CommandApiError ? e.message : 'Post failed'
      toast({ title: 'Error', description: msg, variant: 'destructive' })
    }
  }

  return (
    <Card className="mb-6 border border-outline-variant">
      <CardHeader>
        <CardTitle className="text-on-surface">Event ledger (commands)</CardTitle>
        <CardDescription>
          Propose → approve → post via append-only events. Requires running{' '}
          <code className="text-xs">services/command-api</code> and v2 SQL migrations.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Description</Label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              readOnly={readOnly}
              disabled={readOnly}
            />
          </div>
          <div className="space-y-2">
            <Label>Entry date</Label>
            <Input
              type="date"
              value={entryDate}
              onChange={(e) => setEntryDate(e.target.value)}
              readOnly={readOnly}
              disabled={readOnly}
            />
          </div>
          <div className="space-y-2">
            <Label>Debit account id</Label>
            <Input
              value={debitAccountId}
              onChange={(e) => setDebitAccountId(e.target.value)}
              placeholder="e.g. 6000"
              readOnly={readOnly}
              disabled={readOnly}
            />
          </div>
          <div className="space-y-2">
            <Label>Credit account id</Label>
            <Input
              value={creditAccountId}
              onChange={(e) => setCreditAccountId(e.target.value)}
              placeholder="e.g. 1000"
              readOnly={readOnly}
              disabled={readOnly}
            />
          </div>
          <div className="space-y-2">
            <Label>Amount</Label>
            <Input value={amount} onChange={(e) => setAmount(e.target.value)} readOnly={readOnly} disabled={readOnly} />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            onClick={() => void propose()}
            disabled={readOnly}
            title={readOnly ? 'Your role cannot propose journal entries' : undefined}
          >
            Propose balanced entry
          </Button>
          <Button type="button" variant="outline" onClick={() => void load()} disabled={loading}>
            Refresh list
          </Button>
        </div>
        {accounts.length > 0 && (
          <p className="text-xs text-on-surface-variant">
            Tip: use account ids from your chart (e.g. {accounts[0]?.id} — {accounts[0]?.code}).
          </p>
        )}
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-on-surface">Recent proposals</h3>
          <ul className="space-y-2 text-sm">
            {proposals.map((p) => (
              <li
                key={p.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-outline-variant p-3"
              >
                <div>
                  <span className="font-mono text-on-surface-variant">#{p.id}</span>{' '}
                  <span className="text-on-surface">{p.status}</span>
                  {p.payload?.description ? (
                    <span className="text-on-surface-variant"> — {p.payload.description}</span>
                  ) : null}
                </div>
                <div className="flex gap-2">
                  {p.status === 'pending' ? (
                    <Button
                      size="sm"
                      variant="secondary"
                      type="button"
                      disabled={readOnly}
                      onClick={() => void approve(p.id)}
                    >
                      Approve
                    </Button>
                  ) : null}
                  {p.status === 'approved' ? (
                    <Button
                      size="sm"
                      type="button"
                      disabled={readOnly}
                      onClick={() => void post(p.id)}
                    >
                      Post
                    </Button>
                  ) : null}
                </div>
              </li>
            ))}
            {proposals.length === 0 && !loading ? (
              <li className="text-on-surface-variant">No proposals yet.</li>
            ) : null}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
