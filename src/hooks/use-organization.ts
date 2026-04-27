'use client'

import { useOrganizationContext } from '@/contexts/organization-context'
import { Organization } from '@/types'

export function useOrganization() {
  const {
    currentOrganization,
    organizations,
    switchOrganization,
    isLoading,
    error,
    clearError
  } = useOrganizationContext()

  const getOrganizationById = (organizationId: string): Organization | undefined => {
    return organizations.find(org => org.id === organizationId)
  }

  return {
    currentOrganization,
    organizations,
    switchToOrganization: switchOrganization,
    getOrganizationById,
    isLoading,
    hasOrganizations: organizations.length > 0,
    error,
    clearError
  }
}
