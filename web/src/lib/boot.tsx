import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ApiError, acceptInvite, completeProfile, getBootstrap, type Org } from './api'
import { Skeleton } from '@/components/ui/skeleton'
import { AuthScreen, CreateOrganization, ResetPassword } from '@/components/auth'

export type Access = 'owner' | 'books' | 'member' | 'observer'

type Ctx = {
  userId: string
  email: string
  profile: { full_name: string | null; phone: string | null } | null
  orgs: Org[]
  org: Org
  setOrg: (id: string) => void
  access: Access
  canSeeBooks: boolean
  isSuperAdmin: boolean
  pro: boolean
  setPro: (v: boolean) => void
  money: (n: number) => string
}
const BootContext = createContext<Ctx | null>(null)

export const useApp = () => {
  const ctx = useContext(BootContext)
  if (!ctx) throw new Error('useApp must be used inside BootProvider')
  return ctx
}

const read = (k: string) => {
  try { return localStorage.getItem(k) } catch { return null }
}
const write = (k: string, v: string) => {
  try { localStorage.setItem(k, v) } catch { /* private mode: keep the choice for this session only */ }
}

function accessFor(role: string | null, superAdmin: boolean): Access {
  if (superAdmin || role === 'organization_owner' || role === 'super_admin') return 'owner'
  if (role === 'accountant') return 'books'
  if (role === 'member') return 'member'
  return 'observer'
}

/** A link like /invite/abc is kept through signing up or signing in, then used once. */
function pendingInvite() {
  const fromPath = location.pathname.match(/^\/invite\/([\w-]{20,200})$/)?.[1]
  if (fromPath) write('pendingInvite', fromPath)
  return read('pendingInvite') || null
}

export function BootProvider({ children }: { children: ReactNode }) {
  const boot = useQuery({ queryKey: ['bootstrap'], queryFn: getBootstrap, staleTime: 5 * 60_000 })
  const [orgId, setOrgId] = useState(() => read('selectedOrganizationId'))
  const [pro, setProState] = useState(() => read('detailLevel') === 'accountant')

  const setOrg = useCallback((id: string) => {
    write('selectedOrganizationId', id)
    setOrgId(id)
  }, [])
  const setPro = useCallback((v: boolean) => {
    write('detailLevel', v ? 'accountant' : 'simple')
    setProState(v)
  }, [])

  const unauthorized = boot.error instanceof ApiError && boot.error.status === 401
  // A signed-in person with no profile row (for example, sign-up was interrupted) is repaired here.
  const noProfile = boot.data && !boot.data.hasProfile
  const refetch = boot.refetch
  const user = boot.data?.user
  useEffect(() => {
    if (noProfile && user) void completeProfile(user.name?.trim() || user.email.split('@')[0] || 'User', '').then(() => refetch())
  }, [noProfile, user, refetch])

  const [invite, setInvite] = useState(pendingInvite)
  const [inviteError, setInviteError] = useState<string | null>(null)
  const ready = Boolean(boot.data?.hasProfile)
  useEffect(() => {
    if (!invite || !ready) return
    acceptInvite(invite)
      .then((r) => {
        const joined = r as { organization_id: string }
        write('pendingInvite', '')
        write('selectedOrganizationId', joined.organization_id)
        location.replace('/home')
      })
      .catch((e: Error) => {
        write('pendingInvite', '')
        setInvite(null)
        setInviteError(e.message)
      })
  }, [invite, ready])

  const orgs = boot.data?.organizations
  const org = orgs?.find((o) => o.id === orgId) ?? orgs?.[0]
  const value = useMemo<Ctx | null>(() => {
    if (!boot.data || !org) return null
    const access = accessFor(org.role, boot.data.isSuperAdmin)
    return {
      userId: boot.data.user.id,
      email: boot.data.user.email,
      profile: boot.data.profile ?? null,
      orgs: boot.data.organizations,
      org,
      setOrg,
      access,
      canSeeBooks: access === 'owner' || access === 'books',
      isSuperAdmin: boot.data.isSuperAdmin,
      pro,
      setPro,
      money: makeMoney(org.currency, org.decimals),
    }
  }, [boot.data, org, setOrg, pro, setPro])

  if (location.pathname === '/reset-password') return <ResetPassword />
  if (unauthorized) return <AuthScreen invited={Boolean(invite)} />
  if (inviteError) return <Centered title="Couldn't accept this invite" body={inviteError} action={<button className="text-primary font-medium underline underline-offset-[3px] cursor-pointer" onClick={() => location.replace('/home')}>Continue</button>} />
  if (invite && boot.data) return <Centered title="Joining your team" body="One moment." action={null} />
  if (boot.isError) {
    return <Centered title="Couldn't load your account" body="Check your connection and try again." action={<button className="text-primary font-medium underline underline-offset-[3px] cursor-pointer" onClick={() => boot.refetch()}>Try again</button>} />
  }
  if (boot.data && boot.data.hasProfile && !org) return <CreateOrganization first />
  if (!value) return <div className="p-6 max-w-5xl mx-auto"><Skeleton className="h-9 w-40 mt-12" /><Skeleton className="h-28 w-full mt-6" /></div>
  return <BootContext.Provider value={value}>{children}</BootContext.Provider>
}

function Centered({ title, body, action }: { title: string; body: string; action: ReactNode }) {
  return (
    <div className="min-h-dvh grid place-items-center p-6 text-center">
      <div className="flex flex-col gap-2 items-center">
        <h1 className="text-xl font-semibold">{title}</h1>
        <p className="text-muted-foreground">{body}</p>
        {action}
      </div>
    </div>
  )
}

function makeMoney(currency: string, decimals: number) {
  let f: Intl.NumberFormat
  try {
    f = new Intl.NumberFormat('en', { style: 'currency', currency, currencyDisplay: 'code', minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  } catch {
    f = new Intl.NumberFormat('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
  return (n: number) => f.format(n).replace(/\s/g, ' ').replace(/\.0+$/, '')
}

/** Plain figures for table columns, with brackets for negatives as on a statement. */
export function figure(n: number, decimals = 2) {
  const s = Math.abs(n).toLocaleString('en', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  return n < 0 ? `(${s})` : s
}

export const shortDate = (d: string) => {
  const parsed = new Date(d.length === 10 ? `${d}T00:00:00` : d)
  return Number.isNaN(parsed.getTime()) ? d : parsed.toLocaleDateString('en', { day: 'numeric', month: 'short', year: 'numeric' })
}
