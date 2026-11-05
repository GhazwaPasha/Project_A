import { lazy, Suspense, useEffect, useState, type ComponentType } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, Outlet, useNavigate, useRouterState } from '@tanstack/react-router'
import { motion } from 'motion/react'
import { BookOpen, Boxes, Building2, CheckSquare, ChevronsUpDown, Contact, FileBarChart, FileText, House, Landmark, Layers, ListTree, Lock, Menu, Percent, Plug, Receipt, Target, TrendingUp, Scale, Search, Settings, Shield, Truck, Users, History } from 'lucide-react'
import { Toaster } from 'sonner'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { AgentPanel } from '@/components/agent-panel'
import { Count, type Tone } from '@/components/chips'
import { PageIcons } from '@/components/page-icons'
import { ResizeHandle } from '@/components/resize-handle'
import { useAgent } from '@/lib/agent'
import { signOut } from '@/lib/api'
import { useApp, type Access } from '@/lib/boot'
import { lowStock, num, proposals, q, voucherStats } from '@/lib/data'
import { SIDEBAR } from '@/lib/panels'
import { useTheme } from '@/lib/theme'
import { cn, PAGE_SCROLLER, PAGE_SIDE, scrollPageToTop } from '@/lib/utils'

const CommandMenu = lazy(() => import('@/components/command-menu').then((m) => ({ default: m.CommandMenu })))

type Icon = ComponentType<{ className?: string }>
export type Item = { label: string; icon: Icon; to: string; roles?: Access[]; superOnly?: boolean; notInSidebar?: boolean }
const BOOKS: Access[] = ['owner', 'books']
// Each section has its own colour: on its menu icons, and on the page while you're in it.
export const NAV: { group: string; hue: string; items: Item[] }[] = [
  { group: '', hue: 'indigo', items: [{ label: 'Home', icon: House, to: '/home', roles: BOOKS }] },
  { group: 'Books', hue: 'blue', items: [
    { label: 'Journal', icon: BookOpen, to: '/journal', roles: BOOKS },
    { label: 'Ledger', icon: Layers, to: '/ledger', roles: BOOKS },
    { label: 'Trial Balance', icon: Scale, to: '/trial-balance', roles: BOOKS },
    { label: 'Accounts', icon: ListTree, to: '/accounts', roles: BOOKS },
    { label: 'Reports', icon: FileBarChart, to: '/reports', roles: BOOKS },
  ] },
  { group: 'Sales and bills', hue: 'emerald', items: [
    { label: 'Invoices', icon: FileText, to: '/invoices', roles: BOOKS },
    { label: 'Bills', icon: Receipt, to: '/bills', roles: BOOKS },
    { label: 'Customers', icon: Contact, to: '/customers', roles: BOOKS },
    { label: 'Banking', icon: Landmark, to: '/banking', roles: BOOKS },
  ] },
  { group: 'Planning', hue: 'violet', items: [
    { label: 'Budgets', icon: Target, to: '/budgets', roles: BOOKS },
    { label: 'Forecast', icon: TrendingUp, to: '/forecast', roles: BOOKS },
    { label: 'Tax', icon: Percent, to: '/tax', roles: BOOKS },
    { label: 'Close books', icon: Lock, to: '/close', roles: BOOKS },
  ] },
  { group: 'Operations', hue: 'amber', items: [
    { label: 'Inventory', icon: Boxes, to: '/inventory' },
    { label: 'Suppliers', icon: Truck, to: '/suppliers', roles: ['owner', 'books', 'member'] },
    { label: 'Approvals', icon: CheckSquare, to: '/approvals' },
  ] },
  { group: 'Organization', hue: 'rose', items: [
    { label: 'Team Management', icon: Users, to: '/team', roles: ['owner', 'books', 'member'] },
    { label: 'Audit log', icon: History, to: '/audit', roles: BOOKS },
    { label: 'Organization Settings', icon: Building2, to: '/organization', roles: ['owner'] },
    { label: 'Connections', icon: Plug, to: '/settings/connections', roles: BOOKS, notInSidebar: true },
    { label: 'Settings', icon: Settings, to: '/settings' },
    { label: 'Super Admin', icon: Shield, to: '/super-admin', superOnly: true },
  ] },
]

export const canOpen = (i: Item, access: Access, isSuperAdmin: boolean) => (i.superOnly ? isSuperAdmin : !i.roles || i.roles.includes(access))

const SEARCH_KEY = /Mac|iPhone|iPad/.test(navigator.userAgent) ? '⌘ K' : 'Ctrl K'

const DOT: Record<Tone, string> = { solid: 'bg-primary', warn: 'bg-[var(--note)]', neutral: 'bg-muted-foreground', bad: 'bg-destructive', good: 'bg-[var(--tick)]' }

// The sidebar has one layout at every width. Its side padding keeps each icon centred in the 64px folded width,
// so as it narrows the icons stay put while the text shortens and fades.
function Sidebar({ onNavigate, onSearch, pill = 'nav-pill' }: { onNavigate?: () => void; onSearch: () => void; pill?: string }) {
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
  const row = 'nav-row relative isolate flex items-center gap-2 h-[30px] px-[7px] rounded-[6px] text-[13.5px] whitespace-nowrap text-muted-foreground transition-colors duration-100 hover:bg-accent/70 hover:text-foreground'
  return (
    <div className="flex flex-col gap-2.5 h-full p-2.5">
      <div className="sheet h-[34px] p-0.5 shrink-0">
        <DropdownMenu>
          <DropdownMenuTrigger title={org.name} className="flex w-full items-center gap-1.5 h-full px-[10px] overflow-hidden rounded-[6px] text-left hover:bg-accent cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <span className="size-[18px] rounded-[5px] bg-primary text-primary-foreground grid place-items-center font-semibold text-[10px] shrink-0">{org.name.charAt(0).toUpperCase()}</span>
            <span className="fold flex-1 min-w-0 truncate font-semibold text-[12.5px] leading-4">{org.name}</span>
            <ChevronsUpDown className="fold size-3.5 text-muted-foreground shrink-0" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-[216px]">
            {orgs.map((o) => <DropdownMenuItem key={o.id} onClick={() => setOrg(o.id)}><span className="truncate">{o.name}</span></DropdownMenuItem>)}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="sheet flex-1 min-h-0 flex flex-col overflow-hidden">
        <div className="px-1 py-2">
          <button data-sidebar-search onClick={onSearch} title={`Search (${SEARCH_KEY})`} className="flex w-full items-center gap-2 h-8 px-[9px] overflow-hidden whitespace-nowrap rounded-[6px] border border-border bg-background text-[13px] text-muted-foreground cursor-pointer hover:border-input">
            <Search className="size-3.5 shrink-0" /><span className="fold flex-1 min-w-0 truncate text-left">Search</span><span className="fold shrink-0 max-lg:hidden"><kbd className="key-cap">{SEARCH_KEY}</kbd></span>
          </button>
        </div>

        <motion.nav layoutScroll className="flex-1 min-h-0 overflow-x-hidden overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden px-1 pb-3 flex flex-col gap-3" aria-label="Main">
          {NAV.map((g) => {
            const items = g.items.filter((i) => !i.notInSidebar && canOpen(i, access, isSuperAdmin))
            if (!items.length) return null
            return (
              <div key={g.group || 'top'} data-hue={g.hue} className="flex flex-col gap-px">
                {g.group ? <h2 className="relative px-[9px] mb-1 text-[11.5px] font-medium whitespace-nowrap text-muted-foreground"><span className="fold block truncate">{g.group}</span><span aria-hidden className="unfold absolute inset-x-1.5 top-1/2 border-t border-border" /></h2> : null}
                {items.map((i) => {
                  const c = counts[i.to]
                  const hint = c?.n ? `${i.label}: ${c.n} ${c.label}` : i.label
                  return (
                    <Link key={i.label} to={i.to} onClick={onNavigate} title={hint} className={row} activeProps={{ className: 'text-foreground! font-medium' }}>
                      {({ isActive }) => <>
                        {isActive ? <motion.span aria-hidden layoutId={pill} transition={{ type: 'spring', bounce: 0, duration: 0.35 }} className="nav-pill absolute inset-0 -z-10 rounded-[6px]" /> : null}
                        <span className="nav-ico relative" data-active={isActive || undefined}><i.icon className="size-[15px]" />{c?.n ? <span aria-hidden className={cn('unfold absolute top-0 right-0 size-1.5 rounded-full', DOT[c.tone])} /> : null}</span>
                        <span className="fold flex-1 min-w-0 truncate">{i.label}</span>
                        {c?.n ? <span className="fold shrink-0"><Count {...c} /></span> : null}
                      </>}
                    </Link>
                  )
                })}
              </div>
            )
          })}
        </motion.nav>

        <div className="px-1 py-2 border-t border-border">
          <DropdownMenu>
            <DropdownMenuTrigger title={email} className="flex w-full items-center gap-2.5 h-9 px-[5px] overflow-hidden rounded-[6px] hover:bg-accent cursor-pointer outline-none text-left">
              <span className="size-6 rounded-full bg-muted border border-border grid place-items-center text-[11px] font-semibold shrink-0">{email.charAt(0).toUpperCase()}</span>
              <span className="fold flex-1 min-w-0 truncate text-[12.5px] text-muted-foreground">{email}</span>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" side="top" className="w-[216px]">
              <DropdownMenuItem onClick={() => { onNavigate?.(); void navigate({ to: '/settings' }) }}>Settings</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => void signOut()}>Sign out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}

export function Shell() {
  const [search, setSearch] = useState(false)
  const [menu, setMenu] = useState(false)
  const { org, access, isSuperAdmin } = useApp()
  const navigate = useNavigate()
  const { open: agentOpen } = useAgent()
  const { dark } = useTheme()
  const path = useRouterState({ select: (s) => s.location.pathname })

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
  const hue = NAV.find((g) => g.items.includes(current as Item))?.hue ?? 'indigo'
  useEffect(() => { if (blocked) void navigate({ to: '/inventory', replace: true }) }, [blocked, navigate])
  useEffect(() => { scrollPageToTop() }, [path])

  return (
    <>
      <aside className="sidebar-fold hidden lg:block print:hidden fixed inset-y-0 left-0 w-[var(--sidebar-w)] z-10" style={{ background: 'var(--sidebar-bg)' }}>
        <Sidebar onSearch={() => setSearch(true)} />
        <ResizeHandle panel={SIDEBAR} label="Resize sidebar" grows="right" className="right-0 w-2.5" />
      </aside>
      <Sheet open={menu} onOpenChange={setMenu}>
        <SheetContent side="left" showCloseButton={false} className="w-[264px] p-0 gap-0 bg-[var(--sidebar-bg)]">
          <SheetTitle className="sr-only">Menu</SheetTitle>
          <Sidebar pill="nav-pill-menu" onNavigate={() => setMenu(false)} onSearch={() => { setMenu(false); setSearch(true) }} />
        </SheetContent>
      </Sheet>

      <div className={cn('lg:ml-[var(--sidebar-w)] lg:h-dvh lg:flex lg:flex-col lg:bg-[var(--sidebar-bg)] print:block print:ml-0 print:pr-0 print:h-auto print:bg-transparent', agentOpen && 'xl:pr-[var(--agent-w-live)]')}>
        {/* Phones have no sidebar, so they keep a slim bar for the menu. */}
        <div className="lg:hidden print:hidden sticky top-0 z-[5] flex items-center gap-2 h-11 px-4 border-b border-border bg-background">
          <button onClick={() => setMenu(true)} aria-label="Open menu" className="size-8 -ml-1 grid place-items-center rounded-[6px] hover:bg-accent cursor-pointer"><Menu className="size-[18px]" /></button>
          <span className="font-semibold text-[13.5px] truncate">{org.name}</span>
          <PageIcons className="ml-auto" />
        </div>
        {/* Sits level with the organization switcher, so the panel below starts level with the sidebar card. */}
        <div className="hidden lg:flex print:hidden shrink-0 justify-end my-2.5 pr-4 overflow-hidden [scrollbar-width:thin] [scrollbar-gutter:stable]"><PageIcons /></div>
        {/* From lg up the page is a panel that scrolls on its own, rounded at the top left and flush with the window's right and bottom edges. */}
        <div className="relative bg-background lg:@container lg:flex lg:flex-1 lg:min-h-0 lg:overflow-hidden lg:rounded-tl-[14px] lg:border-t lg:border-l lg:border-border print:block print:h-auto print:overflow-visible print:rounded-none print:border-0">
        <motion.div layoutScroll id={PAGE_SCROLLER} className="lg:flex-1 lg:min-w-0 lg:overflow-y-auto [scrollbar-width:thin] print:h-auto print:overflow-visible">
          <main data-hue={hue} className="relative isolate px-4 pt-4 pb-6 print:p-0">
            <Outlet />
          </main>
        </motion.div>
        {/* Sits beside the page when the main box has room, and fills the box when it doesn't. */}
        <div id={PAGE_SIDE} className="empty:hidden print:hidden max-lg:fixed max-lg:inset-x-0 max-lg:top-11 max-lg:bottom-0 max-lg:z-[4] lg:absolute lg:inset-0 lg:z-[4] lg:@4xl:relative lg:@4xl:inset-auto lg:@4xl:shrink-0 lg:@4xl:w-[clamp(420px,42cqw,560px)] lg:@4xl:border-l lg:@4xl:border-border" />
        </div>
      </div>

      <AgentPanel />
      <Suspense fallback={null}><CommandMenu open={search} onOpenChange={setSearch} /></Suspense>
      <Toaster position="top-center" theme={dark ? 'dark' : 'light'} />
    </>
  )
}
