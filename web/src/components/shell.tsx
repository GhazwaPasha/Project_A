import { lazy, Suspense, useEffect, useState, type ComponentType } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, Outlet, useNavigate, useRouterState } from '@tanstack/react-router'
import { BookOpen, Boxes, Building2, CheckSquare, ChevronsUpDown, Contact, FileBarChart, FileText, House, Landmark, Layers, ListTree, Lock, Menu, Percent, Plug, Receipt, Target, TrendingUp, Scale, Search, Settings, Shield, Truck, Users, History } from 'lucide-react'
import { Toaster } from 'sonner'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { AgentPanel } from '@/components/agent-panel'
import { Count, type Tone } from '@/components/chips'
import { PageIcons } from '@/components/page-icons'
import { useAgent } from '@/lib/agent'
import { signOut } from '@/lib/api'
import { useApp, type Access } from '@/lib/boot'
import { lowStock, num, proposals, q, voucherStats } from '@/lib/data'
import { useTheme } from '@/lib/theme'
import { cn } from '@/lib/utils'

const CommandMenu = lazy(() => import('@/components/command-menu').then((m) => ({ default: m.CommandMenu })))

type Icon = ComponentType<{ className?: string }>
export type Item = { label: string; icon: Icon; to: string; roles?: Access[]; superOnly?: boolean; notInSidebar?: boolean }
const BOOKS: Access[] = ['owner', 'books']
export const NAV: { group: string; items: Item[] }[] = [
  { group: '', items: [{ label: 'Home', icon: House, to: '/home', roles: BOOKS }] },
  { group: 'Books', items: [
    { label: 'Journal', icon: BookOpen, to: '/journal', roles: BOOKS },
    { label: 'Ledger', icon: Layers, to: '/ledger', roles: BOOKS },
    { label: 'Trial Balance', icon: Scale, to: '/trial-balance', roles: BOOKS },
    { label: 'Accounts', icon: ListTree, to: '/accounts', roles: BOOKS },
    { label: 'Reports', icon: FileBarChart, to: '/reports', roles: BOOKS },
  ] },
  { group: 'Sales and bills', items: [
    { label: 'Invoices', icon: FileText, to: '/invoices', roles: BOOKS },
    { label: 'Bills', icon: Receipt, to: '/bills', roles: BOOKS },
    { label: 'Customers', icon: Contact, to: '/customers', roles: BOOKS },
    { label: 'Banking', icon: Landmark, to: '/banking', roles: BOOKS },
  ] },
  { group: 'Planning', items: [
    { label: 'Budgets', icon: Target, to: '/budgets', roles: BOOKS },
    { label: 'Forecast', icon: TrendingUp, to: '/forecast', roles: BOOKS },
    { label: 'Tax', icon: Percent, to: '/tax', roles: BOOKS },
    { label: 'Close books', icon: Lock, to: '/close', roles: BOOKS },
  ] },
  { group: 'Operations', items: [
    { label: 'Inventory', icon: Boxes, to: '/inventory' },
    { label: 'Suppliers', icon: Truck, to: '/suppliers', roles: ['owner', 'books', 'member'] },
    { label: 'Approvals', icon: CheckSquare, to: '/approvals' },
  ] },
  { group: 'Organization', items: [
    { label: 'Team Management', icon: Users, to: '/team', roles: ['owner', 'books', 'member'] },
    { label: 'Audit log', icon: History, to: '/audit', roles: BOOKS },
    { label: 'Organization Settings', icon: Building2, to: '/organization', roles: ['owner'] },
    { label: 'Connections', icon: Plug, to: '/settings/connections', roles: BOOKS, notInSidebar: true },
    { label: 'Settings', icon: Settings, to: '/settings' },
    { label: 'Super Admin', icon: Shield, to: '/super-admin', superOnly: true },
  ] },
]

export const canOpen = (i: Item, access: Access, isSuperAdmin: boolean) => (i.superOnly ? isSuperAdmin : !i.roles || i.roles.includes(access))

function Sidebar({ onNavigate, onSearch }: { onNavigate?: () => void; onSearch: () => void }) {
  const { org, orgs, setOrg, email, isSuperAdmin, access, canSeeBooks } = useApp()
  const waiting = useQuery({ ...proposals(org.id), enabled: canSeeBooks }).data?.length ?? 0
  const low = useQuery(lowStock(org.id)).data?.length ?? 0
  const pending = num(useQuery(voucherStats(org.id)).data?.pending_approval)
  const work = useQuery({ ...q<{ overdue_invoices: number; overdue_bills: number; unmatched_bank_lines: number }>(['work-summary', org.id], 'BooksService', 'getWorkSummary', [org.id]), enabled: canSeeBooks, retry: false }).data
  const counts: Record<string, { n: number; tone: Tone; label: string }> = {
    '/home': { n: waiting, tone: 'solid', label: 'entries to approve' },
    '/inventory': { n: low, tone: 'warn', label: 'items running low' },
    '/approvals': { n: pending, tone: 'solid', label: 'vouchers need approval' },
    '/invoices': { n: work?.overdue_invoices ?? 0, tone: 'warn', label: 'overdue invoices' },
    '/bills': { n: work?.overdue_bills ?? 0, tone: 'warn', label: 'overdue bills' },
    '/banking': { n: work?.unmatched_bank_lines ?? 0, tone: 'neutral', label: 'bank lines to sort' },
  }
  const navigate = useNavigate()
  const row = 'flex items-center gap-2.5 h-[30px] px-2.5 rounded-[6px] text-[13.5px] text-muted-foreground hover:bg-accent hover:text-foreground'
  return (
    <div className="flex flex-col h-full">
      <div className="px-3 pt-2 pb-2">
        <DropdownMenu>
          <DropdownMenuTrigger className="flex w-full items-center gap-2.5 h-11 px-2 rounded-[8px] text-left hover:bg-accent cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <span className="size-7 rounded-[6px] bg-primary text-primary-foreground grid place-items-center font-semibold text-[13px] shrink-0">{org.name.charAt(0).toUpperCase()}</span>
            <span className="flex-1 min-w-0">
              <span className="block truncate font-semibold text-[13.5px] leading-tight">{org.name}</span>
              <span className="block text-[11.5px] text-muted-foreground leading-tight">{org.currency}</span>
            </span>
            <ChevronsUpDown className="size-3.5 text-muted-foreground shrink-0" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-[216px]">
            {orgs.map((o) => <DropdownMenuItem key={o.id} onClick={() => setOrg(o.id)}><span className="truncate">{o.name}</span></DropdownMenuItem>)}
          </DropdownMenuContent>
        </DropdownMenu>
        <button onClick={onSearch} className="mt-2 flex w-full items-center gap-2 h-8 px-2.5 rounded-[6px] border border-border bg-background text-[13px] text-muted-foreground cursor-pointer hover:border-input">
          <Search className="size-3.5" /><span>Search</span><kbd className="ml-auto text-[11px] font-medium">Ctrl K</kbd>
        </button>
      </div>

      <nav className="flex-1 min-h-0 overflow-y-auto [scrollbar-width:thin] px-3 pb-3 flex flex-col gap-3" aria-label="Main">
        {NAV.map((g) => {
          const items = g.items.filter((i) => !i.notInSidebar && canOpen(i, access, isSuperAdmin))
          if (!items.length) return null
          return (
            <div key={g.group || 'top'} className="flex flex-col gap-px">
              {g.group ? <h2 className="px-2.5 mb-1 text-[11.5px] font-medium text-muted-foreground">{g.group}</h2> : null}
              {items.map((i) => <Link key={i.label} to={i.to} onClick={onNavigate} className={row} activeProps={{ className: 'bg-accent text-foreground! font-medium' }}><i.icon className="size-4 shrink-0" /><span className="truncate">{i.label}</span>{counts[i.to] ? <span className="ml-auto"><Count {...counts[i.to]} /></span> : null}</Link>)}
            </div>
          )
        })}
      </nav>

      <div className="px-3 py-2.5 border-t border-border">
        <DropdownMenu>
          <DropdownMenuTrigger className="flex w-full items-center gap-2.5 h-9 px-2 rounded-[6px] hover:bg-accent cursor-pointer outline-none text-left">
            <span className="size-6 rounded-full bg-muted border border-border grid place-items-center text-[11px] font-semibold shrink-0">{email.charAt(0).toUpperCase()}</span>
            <span className="truncate text-[12.5px] text-muted-foreground">{email}</span>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" side="top" className="w-[216px]">
            <DropdownMenuItem onClick={() => { onNavigate?.(); void navigate({ to: '/settings' }) }}>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => void signOut()}>Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}

export function Shell() {
  const [search, setSearch] = useState(false)
  const [searchLoaded, setSearchLoaded] = useState(false)
  const [menu, setMenu] = useState(false)
  const { org, access, isSuperAdmin } = useApp()
  const navigate = useNavigate()
  const { open: agentOpen } = useAgent()
  const { dark } = useTheme()
  const path = useRouterState({ select: (s) => s.location.pathname })

  useEffect(() => { if (search) setSearchLoaded(true) }, [search])
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setSearch((s) => !s)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  // Each role lands on a screen it can use. Inventory is the one everyone has. The server enforces the same rules.
  const current = NAV.flatMap((g) => g.items).find((i) => path === i.to || path.startsWith(`${i.to}/`))
  const blocked = current && !canOpen(current, access, isSuperAdmin)
  useEffect(() => { if (blocked) void navigate({ to: '/inventory', replace: true }) }, [blocked, navigate])
  useEffect(() => { window.scrollTo(0, 0) }, [path])

  return (
    <>
      <aside className="hidden lg:block print:hidden fixed inset-y-0 left-0 w-[220px] border-r border-border z-10" style={{ background: 'var(--sidebar-bg)' }}>
        <Sidebar onSearch={() => setSearch(true)} />
      </aside>
      <Sheet open={menu} onOpenChange={setMenu}>
        <SheetContent side="left" showCloseButton={false} className="w-[264px] p-0 gap-0">
          <SheetTitle className="sr-only">Menu</SheetTitle>
          <Sidebar onNavigate={() => setMenu(false)} onSearch={() => { setMenu(false); setSearch(true) }} />
        </SheetContent>
      </Sheet>

      <div className={cn('lg:ml-[220px] print:ml-0 print:pr-0', agentOpen && 'xl:pr-[400px]')}>
        {/* Phones have no sidebar, so they keep a slim bar for the menu. */}
        <div className="lg:hidden print:hidden sticky top-0 z-[5] flex items-center gap-2 h-11 px-4 border-b border-border bg-background">
          <button onClick={() => setMenu(true)} aria-label="Open menu" className="size-8 -ml-1 grid place-items-center rounded-[6px] hover:bg-accent cursor-pointer"><Menu className="size-[18px]" /></button>
          <span className="font-semibold text-[13.5px] truncate">{org.name}</span>
          <PageIcons className="ml-auto" />
        </div>
        <main className="px-4 lg:px-5 pt-4 pb-6 print:p-0 max-w-[1640px] mx-auto">
          <Outlet />
        </main>
      </div>

      <AgentPanel />
      {searchLoaded ? <Suspense fallback={null}><CommandMenu open={search} onOpenChange={setSearch} /></Suspense> : null}
      <Toaster position="top-center" theme={dark ? 'dark' : 'light'} />
    </>
  )
}
