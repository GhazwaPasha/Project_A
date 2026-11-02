import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ApiError, getBootstrap, type Org } from './api'
import { Skeleton } from '@/components/ui/skeleton'

type Ctx = {
  email: string
  orgs: Org[]
  org: Org
  setOrg: (id: string) => void
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
  const noProfile = boot.data && !boot.data.hasProfile
  useEffect(() => {
    if (unauthorized) location.replace('/')
    // The current app repairs a missing profile on load, so hand over to it.
    if (noProfile) location.replace('/home')
  }, [unauthorized, noProfile])

  const orgs = boot.data?.organizations
  const org = orgs?.find((o) => o.id === orgId) ?? orgs?.[0]
  const value = useMemo<Ctx | null>(() => {
    if (!boot.data || !org) return null
    const money = makeMoney(org.currency, org.decimals)
    const canSeeBooks = boot.data.isSuperAdmin || org.role === 'organization_owner' || org.role === 'accountant' || org.role === 'super_admin'
    return { email: boot.data.user.email, orgs: boot.data.organizations, org, setOrg, canSeeBooks, isSuperAdmin: boot.data.isSuperAdmin, pro, setPro, money }
  }, [boot.data, org, setOrg, pro, setPro])

  if (boot.isError && !unauthorized) {
    return <Centered title="Couldn't load your account" body="Check your connection and try again." action={<button className="text-primary font-medium" onClick={() => boot.refetch()}>Try again</button>} />
  }
  if (boot.data && !org) {
    return <Centered title="Create your first organization" body="You need an organization before you can start." action={<a className="text-primary font-medium" href="/organization/new">Create organization</a>} />
  }
  if (!value) return <div className="p-6 max-w-5xl mx-auto"><Skeleton className="h-9 w-40 mt-12" /><Skeleton className="h-28 w-full mt-6 rounded-2xl" /></div>
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
