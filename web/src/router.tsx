import { Outlet, createRootRoute, createRoute, createRouter, lazyRouteComponent, redirect, useRouterState } from '@tanstack/react-router'
import { Empty } from '@/components/page'
import { Shell } from '@/components/shell'
import { Skeleton } from '@/components/ui/skeleton'
import { AgentProvider } from '@/lib/agent'
import type { Period } from '@/lib/data'
import type { LedgerSearch } from '@/routes/ledger'

function Root() {
  const isDocument = useRouterState({ select: (s) => /^\/(print|oauth)\//.test(s.location.pathname) })
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
const cashFlow = createRoute({ getParentRoute: () => root, path: '/reports/cash-flow', component: lazyRouteComponent(() => import('@/routes/reports'), 'CashFlowPage'), validateSearch: periodSearch })
const cashFlowDoc = createRoute({ getParentRoute: () => root, path: '/print/cash-flow', component: lazyRouteComponent(() => import('@/routes/print'), 'CashFlowDoc'), validateSearch: periodSearch })
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
  cashFlow,
  cashFlowDoc,
  route('/audit', lazyRouteComponent(() => import('@/routes/audit'), 'AuditLog')),
  // Handled before the app loads: BootProvider acts on these addresses.
  route('/reset-password', () => null as never),
  route('/invite/$token', () => null as never),
  route('/invoices', lazyRouteComponent(() => import('@/routes/documents'), 'Invoices')),
  route('/bills', lazyRouteComponent(() => import('@/routes/documents'), 'Bills')),
  route('/customers', lazyRouteComponent(() => import('@/routes/documents'), 'Customers')),
  route('/banking', lazyRouteComponent(() => import('@/routes/banking'), 'Banking')),
  route('/budgets', lazyRouteComponent(() => import('@/routes/planning'), 'Budgets')),
  route('/forecast', lazyRouteComponent(() => import('@/routes/planning'), 'ForecastPage')),
  route('/tax', lazyRouteComponent(() => import('@/routes/planning'), 'Tax')),
  route('/close', lazyRouteComponent(() => import('@/routes/planning'), 'CloseBooks')),
  route('/reports/aged-receivables', lazyRouteComponent(() => import('@/routes/reports'), 'AgedReceivables')),
  route('/reports/aged-payables', lazyRouteComponent(() => import('@/routes/reports'), 'AgedPayables')),
  route('/oauth/authorize', lazyRouteComponent(() => import('@/routes/oauth'), 'OAuthConsent')),
  route('/print/document/$documentId', lazyRouteComponent(() => import('@/routes/print'), 'DocumentDoc')),
  route('/print/aged-receivables', lazyRouteComponent(() => import('@/routes/print'), 'AgedReceivablesDoc')),
  route('/print/aged-payables', lazyRouteComponent(() => import('@/routes/print'), 'AgedPayablesDoc')),
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
  route('/inventory/items/$itemId', lazyRouteComponent(() => import('@/routes/stock'), 'ItemPage')),
  route('/inventory/warehouses', lazyRouteComponent(() => import('@/routes/stock'), 'Warehouses')),
  route('/inventory/purchase-orders', lazyRouteComponent(() => import('@/routes/purchasing'), 'PurchaseOrders')),
  route('/inventory/assemblies', lazyRouteComponent(() => import('@/routes/assemblies'), 'Assemblies')),
  route('/inventory/counts', lazyRouteComponent(() => import('@/routes/counts'), 'Counts')),
  route('/inventory/counts/$countId', lazyRouteComponent(() => import('@/routes/counts'), 'CountPage')),
  route('/inventory/planner', lazyRouteComponent(() => import('@/routes/stock-planning'), 'Planner')),
  route('/inventory/reports', lazyRouteComponent(() => import('@/routes/stock-planning'), 'StockReports')),
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
