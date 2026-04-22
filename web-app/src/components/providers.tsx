'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from '@/lib/query-client'
import { AuthProvider } from './auth/auth-provider'
import { OrganizationProvider } from '@/contexts/organization-context'
import { AIStatusBarProvider } from '@/contexts/ai-context'
import { QueryErrorBoundary } from './error-boundaries/query-error-boundary'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <QueryErrorBoundary>
        <AuthProvider>
          <OrganizationProvider>
            <AIStatusBarProvider>{children}</AIStatusBarProvider>
          </OrganizationProvider>
        </AuthProvider>
      </QueryErrorBoundary>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
