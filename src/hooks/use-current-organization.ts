'use client'

/**
 * Current organization for the session — always use this (not a Zustand-only selector) so
 * you get the same object RQ + {@link OrganizationProvider} resolve.
 */
export { useCurrentOrganization } from '@/contexts/organization-context'
