'use client'

import dynamic from 'next/dynamic'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/query-client'
import { AuthProvider } from './auth/auth-provider'
import { OrganizationProvider } from '@/contexts/organization-context'
import { AIStatusBarProvider } from '@/contexts/ai-context'
import { QueryErrorBoundary } from './error-boundaries/query-error-boundary'
import { AppThemeProvider } from '@/components/theme/theme-provider'
import { UserAccentRoot } from '@/components/theme/user-accent-root'

const RQDevtools = dynamic(
  () =>
    import('@/components/rq-devtools-lazy').then((m) => ({ default: m.RQDevtools })),
  { ssr: false },
)

const showReactQueryDevtools = process.env.NODE_ENV === 'development'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AppThemeProvider>
        <QueryErrorBoundary>
          <AuthProvider>
            <OrganizationProvider>
              <UserAccentRoot />
              <AIStatusBarProvider>{children}</AIStatusBarProvider>
            </OrganizationProvider>
          </AuthProvider>
        </QueryErrorBoundary>
        {showReactQueryDevtools ? <RQDevtools /> : null}
      </AppThemeProvider>
    </QueryClientProvider>
  )
}
