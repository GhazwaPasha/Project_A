'use client'

import { useAuthStore } from '@/stores/auth-store'
import { Organization } from '@/types'

export function useOrganization() {
  const { 
    currentOrganization, 
    organizations, 
    switchOrganization, 
    isLoading 
  } = useAuthStore()

  const switchToOrganization = async (organizationId: string) => {
    return await switchOrganization(organizationId)
  }

  const getOrganizationById = (organizationId: string): Organization | undefined => {
    return organizations.find(org => org.id === organizationId)
  }

  return {
    currentOrganization,
    organizations,
    switchToOrganization,
    getOrganizationById,
    isLoading,
    hasOrganizations: organizations.length > 0
  }
}
