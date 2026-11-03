import { createRootRoute, createRoute, createRouter, lazyRouteComponent, redirect } from '@tanstack/react-router'
import { Empty } from '@/components/page'
import { Shell } from '@/components/shell'
import { Skeleton } from '@/components/ui/skeleton'
import { AgentProvider } from '@/lib/agent'
import type { Period } from '@/lib/data'

const root = createRootRoute({ component: () => <AgentProvider><Shell /></AgentProvider> })
const route = (path: string, component: ReturnType<typeof lazyRouteComponent>) =>
  createRoute({ getParentRoute: () => root, path, component })

const Home = lazyRouteComponent(() => import('@/routes/home'), 'Home')
const Journal = lazyRouteComponent(() => import('@/routes/books'), 'Journal')
const Ledger = lazyRouteComponent(() => import('@/routes/books'), 'Ledger')
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

const tree = root.addChildren([
  createRoute({ getParentRoute: () => root, path: '/', beforeLoad: () => { throw redirect({ to: '/home' }) } }),
  route('/home', Home),
  route('/journal', Journal),
  route('/ledger', Ledger),
  route('/trial-balance', TrialBalance),
  route('/reports', ReportsIndex),
  route('/reports/balance-sheet', BalanceSheetPage),
  route('/connections', Connections),
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
