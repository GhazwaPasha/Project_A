import { lazy, Suspense, useEffect, useState, type ComponentType } from 'react'
import { Link, Outlet, useRouterState } from '@tanstack/react-router'
import { BookOpen, Boxes, Building2, CheckSquare, ChevronsUpDown, FileBarChart, House, Layers, ListTree, Menu, Moon, Plug, Scale, Search, Settings, Shield, Sun, Truck, UserCog, Users } from 'lucide-react'
import { Toaster } from 'sonner'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { AgentPanel, Composer } from '@/components/agent-panel'
import { useAgent } from '@/lib/agent'
import { signOut } from '@/lib/api'
import { useApp } from '@/lib/boot'
import { useTheme } from '@/lib/theme'
import { cn } from '@/lib/utils'

const CommandMenu = lazy(() => import('@/components/command-menu').then((m) => ({ default: m.CommandMenu })))

type Icon = ComponentType<{ className?: string }>
export type Item = { label: string; icon: Icon; to?: string; href?: string; superOnly?: boolean; ownerOnly?: boolean }
/** Items with `href` still open in the current app until they are rebuilt here. */
export const NAV: { group: string; items: Item[] }[] = [
  { group: '', items: [{ label: 'Home', icon: House, to: '/home' }] },
  { group: 'Books', items: [
    { label: 'Journal', icon: BookOpen, to: '/journal' },
    { label: 'Ledger', icon: Layers, to: '/ledger' },
    { label: 'Trial Balance', icon: Scale, to: '/trial-balance' },
    { label: 'Accounts', icon: ListTree, href: '/accounts' },
    { label: 'Reports', icon: FileBarChart, to: '/reports' },
  ] },
  { group: 'Operations', items: [
    { label: 'Inventory', icon: Boxes, href: '/inventory' },
    { label: 'Suppliers', icon: Truck, href: '/suppliers' },
    { label: 'Approvals', icon: CheckSquare, href: '/approvals' },
  ] },
  { group: 'Organization', items: [
    { label: 'Connections', icon: Plug, to: '/connections' },
    { label: 'Team Management', icon: Users, href: '/team' },
    { label: 'Organization Settings', icon: Building2, href: '/organization', ownerOnly: true },
    { label: 'User Management', icon: UserCog, href: '/users', ownerOnly: true },
    { label: 'Settings', icon: Settings, href: '/settings' },
    { label: 'Super Admin', icon: Shield, href: '/super-admin', superOnly: true },
  ] },
]

function Sidebar({ onNavigate, onSearch }: { onNavigate?: () => void; onSearch: () => void }) {
  const { org, orgs, setOrg, email, isSuperAdmin, canSeeBooks } = useApp()
  const isOwner = isSuperAdmin || org.role === 'organization_owner' || org.role === 'super_admin'
  const row = 'flex items-center gap-2.5 h-8 px-2.5 rounded-[6px] text-[13.5px] text-muted-foreground hover:bg-accent hover:text-foreground'
  return (
    <div className="flex flex-col h-full">
      <div className="px-3 pt-3 pb-2">
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

      <nav className="flex-1 min-h-0 overflow-y-auto px-3 pb-3 flex flex-col gap-4" aria-label="Main">
        {NAV.map((g) => {
          const items = g.items.filter((i) => (!i.superOnly || isSuperAdmin) && (!i.ownerOnly || isOwner) && (canSeeBooks || i.href))
          if (!items.length) return null
          return (
            <div key={g.group || 'top'} className="flex flex-col gap-px">
              {g.group ? <h2 className="px-2.5 mb-1 text-[11.5px] font-medium text-muted-foreground">{g.group}</h2> : null}
              {items.map((i) => i.to
                ? <Link key={i.label} to={i.to} onClick={onNavigate} className={row} activeProps={{ className: 'bg-accent text-foreground! font-medium' }}><i.icon className="size-4 shrink-0" /><span className="truncate">{i.label}</span></Link>
                : <a key={i.label} href={i.href} className={row}><i.icon className="size-4 shrink-0" /><span className="truncate">{i.label}</span></a>)}
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
            <DropdownMenuItem onClick={() => { location.href = '/home' }}>Open the current app</DropdownMenuItem>
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
  const { canSeeBooks, pro, setPro, org } = useApp()
  const { open: agentOpen, setOpen: setAgentOpen, turns } = useAgent()
  const { dark, toggle } = useTheme()
  const path = useRouterState({ select: (s) => s.location.pathname })
  const onHome = path === '/app/home' || path === '/home'

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
  // Roles without access to the books work in Inventory, which still lives in the current app.
  useEffect(() => { if (!canSeeBooks) location.replace('/inventory') }, [canSeeBooks])
  useEffect(() => { window.scrollTo(0, 0) }, [path])

  return (
    <>
      <aside className="hidden lg:block fixed inset-y-0 left-0 w-[240px] border-r border-border z-10" style={{ background: 'var(--sidebar-bg)' }}>
        <Sidebar onSearch={() => setSearch(true)} />
      </aside>
      <Sheet open={menu} onOpenChange={setMenu}>
        <SheetContent side="left" showCloseButton={false} className="w-[264px] p-0 gap-0">
          <SheetTitle className="sr-only">Menu</SheetTitle>
          <Sidebar onNavigate={() => setMenu(false)} onSearch={() => { setMenu(false); setSearch(true) }} />
        </SheetContent>
      </Sheet>

      <div className={cn('lg:ml-[240px]', agentOpen && 'xl:pr-[400px]')}>
        <header className="sticky top-0 z-[5] flex items-center gap-2 h-12 px-4 md:px-6 border-b border-border bg-background">
          <button onClick={() => setMenu(true)} aria-label="Open menu" className="lg:hidden size-8 -ml-1 grid place-items-center rounded-[6px] hover:bg-accent cursor-pointer"><Menu className="size-[18px]" /></button>
          <span className="lg:hidden font-semibold text-[13.5px] truncate">{org.name}</span>
          <div className="ml-auto flex items-center gap-2">
            {turns.length && !agentOpen ? <button onClick={() => setAgentOpen(true)} className="press h-8 px-3 rounded-[6px] border border-input text-[12.5px] font-medium cursor-pointer hover:bg-accent">Conversation</button> : null}
            <div className="flex p-0.5 rounded-[7px] border border-border bg-muted text-[12px]" role="group" aria-label="Level of detail">
              <button aria-pressed={!pro} onClick={() => setPro(false)} className={cn('h-6 px-2.5 rounded-[5px] cursor-pointer', !pro ? 'bg-card font-medium shadow-[0_0_0_1px_var(--border)]' : 'text-muted-foreground')}>Simple</button>
              <button aria-pressed={pro} onClick={() => setPro(true)} className={cn('h-6 px-2.5 rounded-[5px] cursor-pointer', pro ? 'bg-card font-medium shadow-[0_0_0_1px_var(--border)]' : 'text-muted-foreground')}>Accountant</button>
            </div>
            <button onClick={toggle} aria-label={dark ? 'Use light theme' : 'Use dark theme'} className="size-8 grid place-items-center rounded-[6px] text-muted-foreground hover:bg-accent cursor-pointer">{dark ? <Sun className="size-4" /> : <Moon className="size-4" />}</button>
          </div>
        </header>
        <main className="px-4 md:px-6 pt-6 pb-28 max-w-[1180px] mx-auto"><Outlet /></main>
      </div>

      <div className={cn('fixed bottom-4 right-0 left-0 lg:left-[240px] z-[5] px-4 md:px-6 pointer-events-none', (agentOpen || onHome) && 'hidden')}>
        <div className="max-w-[1132px] mx-auto pointer-events-auto shadow-[0_8px_24px_rgb(15_23_42/0.12)] rounded-[10px]">
          <Composer id="agent-dock-input" placeholder="Ask the agent, or tell it what happened" />
        </div>
      </div>

      <AgentPanel />
      {searchLoaded ? <Suspense fallback={null}><CommandMenu open={search} onOpenChange={setSearch} /></Suspense> : null}
      <Toaster position="top-center" theme={dark ? 'dark' : 'light'} />
    </>
  )
}
