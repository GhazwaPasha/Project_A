import { useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Copy, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Empty, Loaded, Screen, SettingsTabs, btn } from '@/components/page'
import { Badge } from '@/components/chips'
import { createConnection, revokeConnection } from '@/lib/api'
import { shortDate, useApp } from '@/lib/boot'
import { connections, queryClient } from '@/lib/data'

const copy = (text: string) => {
  navigator.clipboard.writeText(text).then(() => toast.success('Copied'), () => toast.error('Could not copy. Select the text instead.'))
}

function CodeBlock({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-2 mb-1"><p className="text-[12.5px] text-muted-foreground">{label}</p><button type="button" onClick={() => copy(text)} className="inline-flex items-center gap-1 text-[12.5px] text-primary cursor-pointer"><Copy className="size-3" />Copy</button></div>
      <pre className="fig text-[12px] bg-muted rounded-[6px] p-3 overflow-x-auto whitespace-pre">{text}</pre>
    </div>
  )
}

/** Lets someone use their own AI app with the same tools as the built-in agent, over MCP. */
export function Connections() {
  const { org } = useApp()
  const list = useQuery(connections(org.id))
  const [name, setName] = useState('')
  const [canRecord, setCanRecord] = useState(false)
  const [created, setCreated] = useState<string | null>(null)
  const url = `${location.origin}/api/mcp`
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['connections'] })
  const create = useMutation({
    mutationFn: () => createConnection(org.id, name.trim(), canRecord),
    onSuccess: (r) => { setCreated(r.token); setName(''); setCanRecord(false); void refresh() },
    onError: (e: Error) => toast.error(e.message),
  })
  const revoke = useMutation({
    mutationFn: revokeConnection,
    onSuccess: () => { toast.success('Connection removed'); void refresh() },
    onError: (e: Error) => toast.error(e.message),
  })
  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (name.trim() && !create.isPending) create.mutate()
  }

  return (
    <Screen title="Settings" tabs={<SettingsTabs />} sub="Use your own AI app with your books. It gets the same tools as the built-in agent, through MCP.">
      <div className="grid gap-3.5 lg:grid-cols-2 items-start">
      <form onSubmit={submit} className="sheet px-3.5 py-3 flex flex-col gap-2.5">
        <h2 className="font-semibold">Connect an AI app</h2>
        <Input id="connection-name" aria-label="Connection name" placeholder="Name it, for example My laptop" value={name} onChange={(e) => setName(e.target.value)} className="max-w-sm" />
        <label className="flex items-start gap-3 cursor-pointer max-w-[60ch]">
          <Switch checked={canRecord} onCheckedChange={setCanRecord} className="mt-0.5" />
          <span><span className="font-medium block">Allow it to record entries directly</span><span className="text-[13px] text-muted-foreground">Off is safer: the app can only propose entries, and you approve them on Home.</span></span>
        </label>
        <div><button type="submit" disabled={!name.trim() || create.isPending} className={btn.primary}>{create.isPending ? 'Creating…' : 'Create connection'}</button></div>
      </form>

      {created ? (
        <section data-agent-private className="sheet border-primary/50 px-3.5 py-3 flex flex-col gap-2.5 lg:row-start-2 lg:col-span-2">
          <div><h2 className="font-semibold">Copy this now</h2><p className="text-[13.5px] text-muted-foreground">This is the only time the token is shown. Anyone who has it can use this connection, so treat it like a password.</p></div>
          <CodeBlock label="Claude Code" text={`claude mcp add --transport http accountuitive ${url} --header "Authorization: Bearer ${created}"`} />
          <CodeBlock label="Other apps that take an MCP server config" text={JSON.stringify({ mcpServers: { accountuitive: { type: 'http', url, headers: { Authorization: `Bearer ${created}` } } } }, null, 2)} />
          <div><button type="button" className={btn.plain} onClick={() => setCreated(null)}>Done</button></div>
        </section>
      ) : null}

      <section className="flex flex-col gap-2">
        <h2 className="font-semibold">Your connections</h2>
        <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No connections yet" body="Create one above to use your own AI app with your books." /> : null)}>
          {(rows) => (
            <div className="sheet divide-y divide-border overflow-hidden">
              {rows.map((c) => (
                <div key={c.id} className="flex flex-wrap items-center justify-between gap-3 px-3.5 py-2">
                  <div className="min-w-0">
                    <p className="flex items-center gap-2 font-medium min-w-0"><span className="truncate">{c.name}</span><Badge tone={c.can_record ? 'warn' : 'neutral'}>{c.can_record ? 'Can record' : 'Can propose'}</Badge></p>
                    <p className="text-[12.5px] text-muted-foreground">Ending <span className="fig">{c.token_hint}</span> · {c.last_used_at ? `last used ${shortDate(c.last_used_at)}` : 'never used'}</p>
                  </div>
                  <button aria-label={`Remove ${c.name}`} disabled={revoke.isPending} onClick={() => revoke.mutate(c.id)} className={btn.plain}><Trash2 className="size-3.5 mr-1.5" />Remove</button>
                </div>
              ))}
            </div>
          )}
        </Loaded>
      </section>
      </div>
    </Screen>
  )
}
