import { useState, type FormEvent } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { completeProfile, createOrganization, requestPasswordReset, resetPassword, signIn, signOut, signUp } from '@/lib/api'
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

/** Where a password reset email lands. */
export function ResetPassword() {
  const token = new URLSearchParams(location.search).get('token')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (password !== confirm) return setError("The passwords don't match.")
    setBusy(true)
    try {
      await resetPassword(password, token ?? '')
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Try again.')
    } finally {
      setBusy(false)
    }
  }
  const signInLink = <a href="/" className="text-primary font-medium underline underline-offset-[3px]">Back to sign in</a>
  if (!token) return <Frame title="This link isn't complete" sub="Open the link from your email again, or ask for a new one.">{signInLink}</Frame>
  if (done) return <Frame title="Password changed" sub="You can sign in with your new password now.">{signInLink}</Frame>
  return (
    <Frame title="Choose a new password" sub="At least 8 characters.">
      <form onSubmit={submit} className="flex flex-col gap-3.5">
        <Labelled label="New password"><Input id="new-password" required type="password" minLength={8} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} /></Labelled>
        <Labelled label="Confirm password"><Input id="confirm-password" required type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} /></Labelled>
        {error ? <p role="alert" className="text-[13px] text-destructive">{error}</p> : null}
        <button type="submit" disabled={busy} className={`${btn.primary} h-9`}>{busy ? 'One moment…' : 'Change password'}</button>
      </form>
    </Frame>
  )
}

function ForgotPassword({ email: start, onBack }: { email: string; onBack: () => void }) {
  const [email, setEmail] = useState(start)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState(false)
  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await requestPasswordReset(email.trim())
      setSent(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Try again.')
    } finally {
      setBusy(false)
    }
  }
  const back = <button type="button" onClick={onBack} className="text-primary font-medium underline underline-offset-[3px] cursor-pointer">Back to sign in</button>
  if (sent) return <Frame title="Check your email" sub={`If ${email.trim()} has an account, a reset link is on its way. It lasts 15 minutes.`}>{back}</Frame>
  return (
    <Frame title="Reset your password" sub="We'll email you a link to choose a new one.">
      <form onSubmit={submit} className="flex flex-col gap-3.5">
        <Labelled label="Email"><Input id="reset-email" required type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} /></Labelled>
        {error ? <p role="alert" className="text-[13px] text-destructive">{error}</p> : null}
        <button type="submit" disabled={busy} className={`${btn.primary} h-9`}>{busy ? 'One moment…' : 'Send reset link'}</button>
      </form>
      <p className="mt-4 text-[13.5px]">{back}</p>
    </Frame>
  )
}

export function AuthScreen({ invited }: { invited?: boolean }) {
  const [mode, setMode] = useState<'in' | 'up' | 'forgot'>(invited || location.pathname === '/signup' ? 'up' : 'in')
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
  if (mode === 'forgot') return <ForgotPassword email={form.email} onBack={() => setMode('in')} />
  return (
    <Frame title={up ? 'Create your account' : 'Sign in'} sub={invited ? "You've been invited to join a team. Use the email the invite was sent to." : up ? 'Your agent will keep the books. You stay in control.' : 'Welcome back.'}>
      <form onSubmit={submit} className="flex flex-col gap-3.5">
        {up ? <Labelled label="Your name"><Input id="name" required autoComplete="name" value={form.name} onChange={set('name')} /></Labelled> : null}
        <Labelled label="Email"><Input id="email" required type="email" autoComplete="email" value={form.email} onChange={set('email')} /></Labelled>
        <Labelled label="Password"><Input id="password" required type="password" minLength={up ? 8 : undefined} autoComplete={up ? 'new-password' : 'current-password'} value={form.password} onChange={set('password')} /></Labelled>
        {up ? <>
          <Labelled label="Confirm password"><Input id="confirm" required type="password" autoComplete="new-password" value={form.confirm} onChange={set('confirm')} /></Labelled>
          {invited ? null : <Labelled label="Business name (optional)"><Input id="organization" value={form.organization} onChange={set('organization')} /></Labelled>}
        </> : null}
        {error ? <p role="alert" className="text-[13px] text-destructive">{error}</p> : null}
        <button type="submit" disabled={busy} className={`${btn.primary} h-9`}>{busy ? 'One moment…' : up ? 'Create account' : 'Sign in'}</button>
        {up ? null : <button type="button" onClick={() => { setMode('forgot'); setError(null) }} className="self-start text-[13.5px] text-muted-foreground underline underline-offset-[3px] cursor-pointer">Forgot your password?</button>}
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
