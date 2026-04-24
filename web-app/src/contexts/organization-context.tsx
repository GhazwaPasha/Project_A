'use client'

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { DataService } from '@/lib/data-service'
import { queryKeys } from '@/lib/query-keys'
import { Organization } from '@/types'
import { useAuthStore } from '@/stores/auth-store'

interface OrganizationContextType {
  // Current organization
  currentOrganization: Organization | null
  organizations: Organization[]

  // Loading states
  isLoading: boolean
  isSwitching: boolean

  // Actions
  switchOrganization: (organizationId: string) => Promise<boolean>
  refreshOrganizations: () => Promise<void>

  // Error handling
  error: Error | null
  clearError: () => void
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined)

interface OrganizationProviderProps {
  children: React.ReactNode
}

export function OrganizationProvider({ children }: OrganizationProviderProps) {
  const { user, isAuthenticated, isLoading: authLoading, organizations: storeOrgs, currentOrganization: storeCurrent } =
    useAuthStore()
  const queryClient = useQueryClient()

  const [isSwitching, setIsSwitching] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  // Same id the auth store + localStorage use; sync immediately (no "null until useEffect" flash).
  const [currentOrganizationId, setCurrentOrganizationId] = useState<string | null>(
    () => (typeof window !== 'undefined' ? localStorage.getItem('selectedOrganizationId') : null)
  )

  const { data: orgsFromQuery, isPending: orgsPending, error: organizationsError, refetch: refetchOrganizations } =
    useQuery<Organization[]>({
      queryKey: queryKeys.userOrganizations(user?.id ?? ''),
      queryFn: () => DataService.getUserOrganizations(user!.id),
      enabled: !!user && isAuthenticated,
      staleTime: 10 * 60 * 1000,
      gcTime: 30 * 60 * 1000,
      retry: 3,
    })

  /** RQ is source of truth when it has run; before that, rehydrate from auth store (avoids "empty" UI). */
  const organizations = useMemo<Organization[]>(
    () => orgsFromQuery ?? (storeOrgs.length > 0 ? storeOrgs : []),
    [orgsFromQuery, storeOrgs]
  )

  const currentOrgPlaceholder = useMemo<Organization | null>(() => {
    if (!currentOrganizationId) return null
    if (storeCurrent?.id === currentOrganizationId) return storeCurrent
    return storeOrgs.find((o) => o.id === currentOrganizationId) ?? null
  }, [currentOrganizationId, storeCurrent, storeOrgs])

  const { data: currentFromQuery, isPending: currentOrgPending, error: currentOrgError } = useQuery<Organization | null>({
    queryKey: currentOrganizationId
      ? queryKeys.currentOrganization(currentOrganizationId)
      : ['current-organization', 'none'],
    queryFn: () => DataService.getOrganization(currentOrganizationId!),
    enabled: !!currentOrganizationId && !!user,
    placeholderData: currentOrgPlaceholder ?? undefined,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    retry: 3,
  })

  const currentOrganization = useMemo<Organization | null>(
    () => (currentFromQuery as Organization | null) ?? currentOrgPlaceholder,
    [currentFromQuery, currentOrgPlaceholder]
  )

  // Keep RQ in sync with auth store so other hooks see warm cache; reduces duplicate "loading" on route changes.
  useEffect(() => {
    if (!user?.id) return
    if (storeOrgs.length > 0) {
      queryClient.setQueryData(queryKeys.userOrganizations(user.id), storeOrgs)
    }
  }, [user?.id, storeOrgs, queryClient])

  useEffect(() => {
    if (currentOrgPlaceholder && currentOrganizationId) {
      queryClient.setQueryData(queryKeys.currentOrganization(currentOrganizationId), currentOrgPlaceholder)
    }
  }, [currentOrgPlaceholder, currentOrganizationId, queryClient])

  // If auth already resolved org id (e.g. rehydration) but state was null, align.
  useEffect(() => {
    if (currentOrganizationId) return
    if (storeCurrent?.id) {
      setCurrentOrganizationId(storeCurrent.id)
      return
    }
    if (typeof window !== 'undefined') {
      const s = localStorage.getItem('selectedOrganizationId')
      if (s) setCurrentOrganizationId(s)
    }
  }, [currentOrganizationId, storeCurrent?.id])

  // Switch organization function
  const switchOrganization = useCallback(
    async (organizationId: string): Promise<boolean> => {
      if (!user) return false

      try {
        setIsSwitching(true)
        setError(null)

        const organization = organizations.find((org) => org.id === organizationId)
        if (!organization) {
          throw new Error('Organization not found')
        }

        localStorage.setItem('selectedOrganizationId', organizationId)
        setCurrentOrganizationId(organizationId)

        await queryClient.prefetchQuery({
          queryKey: ['financial-metrics', organizationId],
          queryFn: () => DataService.getFinancialMetrics(organizationId),
          staleTime: 5 * 60 * 1000,
        })

        await queryClient.prefetchQuery({
          queryKey: ['account-balances', organizationId],
          queryFn: () => DataService.getAccountBalances(organizationId),
          staleTime: 3 * 60 * 1000,
        })

        await queryClient.prefetchQuery({
          queryKey: queryKeys.dashboardBundle(organizationId, undefined),
          queryFn: () => DataService.getDashboardBundle(organizationId, undefined, undefined),
          staleTime: 3 * 60 * 1000,
        })

        await queryClient.prefetchQuery({
          queryKey: queryKeys.accounts(organizationId, true),
          queryFn: () => DataService.getAccounts(organizationId, true),
          staleTime: 10 * 60 * 1000,
        })

        const oldOrgId = currentOrganization?.id
        if (oldOrgId && oldOrgId !== organizationId) {
          queryClient.invalidateQueries({
            predicate: (query) => query.queryKey.includes(oldOrgId),
          })
        }

        return true
      } catch (err) {
        console.error('Error switching organization:', err)
        setError(err as Error)
        return false
      } finally {
        setIsSwitching(false)
      }
    },
    [user, organizations, currentOrganization?.id, queryClient]
  )

  const refreshOrganizations = useCallback(async () => {
    try {
      setError(null)
      await refetchOrganizations()
    } catch (err) {
      console.error('Error refreshing organizations:', err)
      setError(err as Error)
    }
  }, [refetchOrganizations])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Auto-select first organization if none selected
  useEffect(() => {
    if (organizations.length > 0 && !currentOrganizationId && !isSwitching) {
      const firstOrg = organizations[0]
      if (firstOrg) {
        void switchOrganization(firstOrg.id)
      }
    }
  }, [organizations, currentOrganizationId, isSwitching, switchOrganization])

  const isLoading = useMemo(() => {
    if (!user || !isAuthenticated) return false
    if (organizations.length > 0 && currentOrganization) return false
    if (organizations.length > 0 && !currentOrganizationId) return isSwitching
    if (organizations.length === 0) {
      return (orgsPending && storeOrgs.length === 0) || (authLoading && !storeOrgs.length)
    }
    if (currentOrganizationId && (currentOrgPlaceholder || currentFromQuery)) return false
    return Boolean(
      (orgsPending && storeOrgs.length === 0) || (currentOrgPending && !currentOrgPlaceholder)
    )
  }, [
    user,
    isAuthenticated,
    organizations.length,
    currentOrganization,
    currentOrganizationId,
    isSwitching,
    orgsPending,
    storeOrgs.length,
    authLoading,
    currentOrgPlaceholder,
    currentFromQuery,
    currentOrgPending,
  ])

  const contextError = error || organizationsError || currentOrgError

  const value: OrganizationContextType = {
    currentOrganization,
    organizations,
    isLoading,
    isSwitching,
    switchOrganization,
    refreshOrganizations,
    error: contextError,
    clearError,
  }

  return <OrganizationContext.Provider value={value}>{children}</OrganizationContext.Provider>
}

export function useOrganizationContext() {
  const context = useContext(OrganizationContext)
  if (context === undefined) {
    throw new Error('useOrganizationContext must be used within an OrganizationProvider')
  }
  return context
}

export function useCurrentOrganization() {
  const { currentOrganization } = useOrganizationContext()
  return currentOrganization
}

export function useOrganizations() {
  const { organizations } = useOrganizationContext()
  return organizations
}

export function useOrganizationLoading() {
  const { isLoading, isSwitching } = useOrganizationContext()
  return { isLoading, isSwitching }
}

export function useOrganizationError() {
  const { error, clearError } = useOrganizationContext()
  return { error, clearError }
}
