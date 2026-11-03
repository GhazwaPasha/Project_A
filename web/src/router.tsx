import { Outlet, createRootRoute, createRoute, createRouter, lazyRouteComponent, redirect, useRouterState } from '@tanstack/react-router'
import { Empty } from '@/components/page'
import { Shell } from '@/components/shell'
import { Skeleton } from '@/components/ui/skeleton'
import { AgentProvider } from '@/lib/agent'
import type { Period } from '@/lib/data'
import type { LedgerSearch } from '@/routes/ledger'

function Root() {
  const isDocument = useRouterState({ select: (s) => s.location.pathname.startsWith('/print/') })
  return <AgentProvider>{isDocument ? <Outlet /> : <Shell />}</AgentProvider>
}
const root = createRootRoute({ component: Root })
const route = (path: string, component: ReturnType<typeof lazyRouteComponent>) =>
  createRoute({ getParentRoute: () => root, path, component })

const Home = lazyRouteComponent(() => import('@/routes/home'), 'Home')
const Journal = lazyRouteComponent(() => import('@/routes/books'), 'Journal')
const Ledger = lazyRouteComponent(() => import('@/routes/ledger'), 'Ledger')
const LedgerAccount = lazyRouteComponent(() => import('@/routes/ledger'), 'LedgerAccount')
const TrialBalance = lazyRouteComponent(() => import('@/routes/books'), 'TrialBalance')
const ReportsIndex = lazyRouteComponent(() => import('@/routes/reports'), 'ReportsIndex')
const IncomeStatementPage = lazyRouteComponent(() => import('@/routes/reports'), 'IncomeStatementPage')
const BalanceSheetPage = lazyRouteComponent(() => import('@/routes/reports'), 'BalanceSheetPage')
const Connections = lazyRouteComponent(() => import('@/routes/connections'), 'Connections')
const Accounts = lazyRouteComponent(() => import('@/routes/accounts'), 'Accounts')
const Inventory = lazyRouteComponent(() => import('@/routes/inventory'), 'Inventory')
const Categories = lazyRouteComponent(() => import('@/routes/inventory'), 'Categories')
const Movements = lazyRouteComponent(() => import('@/routes/inventory'), 'Movements')
const Vouchers = lazyRouteComponent(() => import('@/routes/vouchers'), 'Vouchers')
const Approvals = lazyRouteComponent(() => import('@/routes/vouchers'), 'Approvals')
const Suppliers = lazyRouteComponent(() => import('@/routes/suppliers'), 'Suppliers')
const Team = lazyRouteComponent(() => import('@/routes/admin'), 'Team')
const OrganizationSettings = lazyRouteComponent(() => import('@/routes/admin'), 'OrganizationSettings')
const Settings = lazyRouteComponent(() => import('@/routes/admin'), 'Settings')
const SuperAdmin = lazyRouteComponent(() => import('@/routes/admin'), 'SuperAdmin')

const income = createRoute({
  getParentRoute: () => root,
  path: '/reports/income-statement',
  component: IncomeStatementPage,
  validateSearch: (s: Record<string, unknown>): { period: Period } => ({
    period: s.period === 'quarter' || s.period === 'year' ? s.period : 'month',
  }),
})

const ledgerSearch = (s: Record<string, unknown>): LedgerSearch => {
  const date = (v: unknown) => (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : undefined)
  const range = s.range === 'month' || s.range === 'quarter' || s.range === 'year' || s.range === 'custom' ? s.range : 'all'
  return range === 'custom' ? { range, from: date(s.from), to: date(s.to) } : { range }
}
const periodSearch = (s: Record<string, unknown>): { period: Period } => ({
  period: s.period === 'quarter' || s.period === 'year' ? s.period : 'month',
})
const ledgerAccount = createRoute({ getParentRoute: () => root, path: '/ledger/$accountId', component: LedgerAccount, validateSearch: ledgerSearch })
const ledgerDoc = createRoute({ getParentRoute: () => root, path: '/print/ledger/$accountId', component: lazyRouteComponent(() => import('@/routes/print'), 'LedgerDoc'), validateSearch: ledgerSearch })
const incomeDoc = createRoute({ getParentRoute: () => root, path: '/print/income-statement', component: lazyRouteComponent(() => import('@/routes/print'), 'IncomeDoc'), validateSearch: periodSearch })

const tree = root.addChildren([
  createRoute({ getParentRoute: () => root, path: '/', beforeLoad: () => { throw redirect({ to: '/home' }) } }),
  route('/home', Home),
  route('/journal', Journal),
  route('/ledger', Ledger),
  ledgerAccount,
  ledgerDoc,
  incomeDoc,
  route('/print/balance-sheet', lazyRouteComponent(() => import('@/routes/print'), 'BalanceDoc')),
  route('/print/trial-balance', lazyRouteComponent(() => import('@/routes/print'), 'TrialDoc')),
  route('/trial-balance', TrialBalance),
  route('/reports', ReportsIndex),
  route('/reports/balance-sheet', BalanceSheetPage),
  route('/settings/connections', Connections),
  createRoute({ getParentRoute: () => root, path: '/connections', beforeLoad: () => { throw redirect({ to: '/settings/connections' }) } }),
  route('/accounts', Accounts),
  route('/inventory', Inventory),
  route('/inventory/categories', Categories),
  route('/inventory/transactions', Movements),
  route('/inventory/vouchers', Vouchers),
  route('/approvals', Approvals),
  route('/suppliers', Suppliers),
  route('/team', Team),
  route('/organization', OrganizationSettings),
  route('/settings', Settings),
  route('/super-admin', SuperAdmin),
  createRoute({ getParentRoute: () => root, path: '/signup', beforeLoad: () => { throw redirect({ to: '/home' }) } }),
  income,
])

export const router = createRouter({
  routeTree: tree,
  defaultPreload: 'intent',
  defaultPendingMs: 80,
  defaultPendingComponent: () => <Skeleton className="h-40 w-full" />,
  defaultNotFoundComponent: () => <Empty title="Page not found" body="That page doesn't exist. Use the menu to find what you need." />,
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
