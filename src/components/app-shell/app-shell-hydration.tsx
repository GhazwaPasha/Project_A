'use client'

import type { DehydratedState } from '@tanstack/react-query'
import { HydrationBoundary } from '@tanstack/react-query'

type Props = {
  state: DehydratedState
  children: React.ReactNode
}

/**
 * Merges server-prefetched React Query state into the root `QueryClient` on mount.
 * Used for `user-organizations` in the (app) layout.
 */
export function AppShellHydration({ state, children }: Props) {
  return <HydrationBoundary state={state}>{children}</HydrationBoundary>
}
