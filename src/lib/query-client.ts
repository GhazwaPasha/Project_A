import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 2 * 60 * 1000, // 2 minutes - shorter stale time for better UX
      gcTime: 15 * 60 * 1000, // 15 minutes - keep unused data in cache longer
      retry: (failureCount) => failureCount < 3,
      retryDelay: (attemptIndex) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
      refetchOnWindowFocus: false, // avoid duplicate `/api/app-data` bursts on tab focus
      refetchOnMount: false,
      refetchOnReconnect: true, // Refetch on network reconnection
      refetchInterval: false, // Don't poll
      refetchIntervalInBackground: false, // Don't poll in background
      // Add timeout to prevent infinite loading
      networkMode: 'online',
    },
    mutations: {
      retry: (failureCount) => failureCount < 1,
      retryDelay: () => 2000,
    },
  },
})
