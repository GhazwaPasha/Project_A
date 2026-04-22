'use client'

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { DataService } from '@/lib/data-service'
import { Organization, User } from '@/types'
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
  const { user, isAuthenticated } = useAuthStore()
  const queryClient = useQueryClient()
  
  const [isSwitching, setIsSwitching] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  
  // Get organizations for the current user
  const {
    data: organizations = [],
    isLoading: organizationsLoading,
    error: organizationsError,
    refetch: refetchOrganizations
  } = useQuery<Organization[]>({
    queryKey: ['user-organizations', user?.id],
    queryFn: () => DataService.getUserOrganizations(user!.id),
    enabled: !!user && isAuthenticated,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: 3,
  })

  // Get current organization from localStorage
  const [currentOrganizationId, setCurrentOrganizationId] = useState<string | null>(null)
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedOrgId = localStorage.getItem('selectedOrganizationId')
      setCurrentOrganizationId(savedOrgId)
    }
  }, [])

  // Get current organization details
  const {
    data: currentOrganization,
    isLoading: currentOrgLoading,
    error: currentOrgError
  } = useQuery<Organization | null>({
    queryKey: ['current-organization', currentOrganizationId],
    queryFn: () => DataService.getOrganization(currentOrganizationId!),
    enabled: !!currentOrganizationId && !!user,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    retry: 3,
  })

  // Switch organization function
  const switchOrganization = useCallback(async (organizationId: string): Promise<boolean> => {
    if (!user) return false
    
    try {
      setIsSwitching(true)
      setError(null)
      
      // Validate organization exists
      const organization = organizations.find(org => org.id === organizationId)
      if (!organization) {
        throw new Error('Organization not found')
      }
      
      // Update localStorage
      localStorage.setItem('selectedOrganizationId', organizationId)
      setCurrentOrganizationId(organizationId)
      
      // Preload organization data
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
        queryKey: ['accounts', organizationId],
        queryFn: () => DataService.getAccounts(organizationId, true),
        staleTime: 10 * 60 * 1000,
      })
      
      // Invalidate old organization data
      const oldOrgId = currentOrganization?.id
      if (oldOrgId && oldOrgId !== organizationId) {
        queryClient.invalidateQueries({
          predicate: (query) => query.queryKey.includes(oldOrgId)
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
  }, [user, organizations, currentOrganization?.id, queryClient])

  // Refresh organizations
  const refreshOrganizations = useCallback(async () => {
    try {
      setError(null)
      await refetchOrganizations()
    } catch (err) {
      console.error('Error refreshing organizations:', err)
      setError(err as Error)
    }
  }, [refetchOrganizations])

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Auto-select first organization if none selected
  useEffect(() => {
    if (organizations.length > 0 && !currentOrganizationId && !isSwitching) {
      const firstOrg = organizations[0]
      if (firstOrg) {
        switchOrganization(firstOrg.id)
      }
    }
  }, [organizations, currentOrganizationId, isSwitching, switchOrganization])

  const isLoading = organizationsLoading || currentOrgLoading
  const contextError = error || organizationsError || currentOrgError

  const value: OrganizationContextType = {
    currentOrganization: currentOrganization || null,
    organizations,
    isLoading,
    isSwitching,
    switchOrganization,
    refreshOrganizations,
    error: contextError,
    clearError
  }

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  )
}

// Hook to use organization context
export function useOrganizationContext() {
  const context = useContext(OrganizationContext)
  if (context === undefined) {
    throw new Error('useOrganizationContext must be used within an OrganizationProvider')
  }
  return context
}

// Convenience hooks for specific data
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
