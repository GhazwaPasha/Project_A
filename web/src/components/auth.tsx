import { useState, type FormEvent } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { completeProfile, createOrganization, signIn, signOut, signUp } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { btn } from '@/components/page'
import { useTheme } from '@/lib/theme'

function Frame({ title, sub, children }: { title: string; sub: string; children: React.ReactNode }) {
  useTheme()
  return (
    <div className="min-h-dvh grid place-items-center p-4 bg-background">
      <main className="w-full max-w-[400px]">
        <p className="font-semibold text-[15px] mb-6">Accountuitive</p>
        <h1 className="text-[22px] leading-tight font-semibold tracking-[-0.018em]">{title}</h1>
        <p className="text-muted-foreground mt-1 mb-5">{sub}</p>
        {children}
      </main>
    </div>
  )
}

function Labelled({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="flex flex-col gap-1.5 text-[13px] font-medium">{label}{children}</label>
}

export function AuthScreen() {
  const [mode, setMode] = useState<'in' | 'up'>(location.pathname === '/signup' ? 'up' : 'in')
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '', organization: '' })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const client = useQueryClient()
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (mode === 'up' && form.password !== form.confirm) return setError("The passwords don't match.")
    setBusy(true)
    try {
      if (mode === 'in') {
        await signIn(form.email.trim(), form.password)
      } else {
        await signUp(form.name.trim(), form.email.trim(), form.password)
        await completeProfile(form.name.trim(), form.organization.trim())
      }
      await client.invalidateQueries({ queryKey: ['bootstrap'] })
      if (location.pathname === '/signup') history.replaceState(null, '', '/home')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Try again.')
    } finally {
      setBusy(false)
    }
  }

  const up = mode === 'up'
  return (
    <Frame title={up ? 'Create your account' : 'Sign in'} sub={up ? 'Your agent will keep the books. You stay in control.' : 'Welcome back.'}>
      <form onSubmit={submit} className="flex flex-col gap-3.5">
        {up ? <Labelled label="Your name"><Input id="name" required autoComplete="name" value={form.name} onChange={set('name')} /></Labelled> : null}
        <Labelled label="Email"><Input id="email" required type="email" autoComplete="email" value={form.email} onChange={set('email')} /></Labelled>
        <Labelled label="Password"><Input id="password" required type="password" minLength={up ? 8 : undefined} autoComplete={up ? 'new-password' : 'current-password'} value={form.password} onChange={set('password')} /></Labelled>
        {up ? <>
          <Labelled label="Confirm password"><Input id="confirm" required type="password" autoComplete="new-password" value={form.confirm} onChange={set('confirm')} /></Labelled>
          <Labelled label="Business name (optional)"><Input id="organization" value={form.organization} onChange={set('organization')} /></Labelled>
        </> : null}
        {error ? <p role="alert" className="text-[13px] text-destructive">{error}</p> : null}
        <button type="submit" disabled={busy} className={`${btn.primary} h-9`}>{busy ? 'One moment…' : up ? 'Create account' : 'Sign in'}</button>
      </form>
      <p className="mt-4 text-[13.5px] text-muted-foreground">
        {up ? 'Already have an account?' : 'New to Accountuitive?'}{' '}
        <button type="button" onClick={() => { setMode(up ? 'in' : 'up'); setError(null) }} className="text-primary font-medium underline underline-offset-[3px] cursor-pointer">{up ? 'Sign in' : 'Create an account'}</button>
      </p>
    </Frame>
  )
}

export function CreateOrganization({ first }: { first?: boolean }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const client = useQueryClient()
  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await createOrganization(name.trim(), description.trim() || null)
      await client.invalidateQueries({ queryKey: ['bootstrap'] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create the organization.')
    } finally {
      setBusy(false)
    }
  }
  const form = (
    <form onSubmit={submit} className="flex flex-col gap-3.5">
      <Labelled label="Business name"><Input id="org-name" required value={name} onChange={(e) => setName(e.target.value)} /></Labelled>
      <Labelled label="What does it do? (optional)"><Input id="org-description" value={description} onChange={(e) => setDescription(e.target.value)} /></Labelled>
      {error ? <p role="alert" className="text-[13px] text-destructive">{error}</p> : null}
      <button type="submit" disabled={busy || !name.trim()} className={`${btn.primary} h-9`}>{busy ? 'Creating…' : 'Create organization'}</button>
    </form>
  )
  if (!first) return form
  return (
    <Frame title="Set up your business" sub="Your books live in an organization. You can add more later.">
      {form}
      <button type="button" onClick={() => void signOut()} className="mt-4 text-[13.5px] text-muted-foreground underline underline-offset-[3px] cursor-pointer">Sign out</button>
    </Frame>
  )
}
