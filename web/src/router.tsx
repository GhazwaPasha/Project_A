import { createRootRoute, createRoute, createRouter, lazyRouteComponent, redirect } from '@tanstack/react-router'
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
  income,
])

export const router = createRouter({
  routeTree: tree,
  basepath: '/app',
  defaultPreload: 'intent',
  defaultPendingMs: 80,
  defaultPendingComponent: () => <Skeleton className="h-40 w-full" />,
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
