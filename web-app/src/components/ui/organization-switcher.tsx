'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronDown, Check } from 'lucide-react'
import { useOrganization } from '@/hooks/use-organization'
import { Organization } from '@/types'

interface OrganizationSwitcherProps {
  className?: string
}

export function OrganizationSwitcher({ className = '' }: OrganizationSwitcherProps) {
  const router = useRouter()
  const [isOpen, setIsOpen] = useState(false)
  const [isSwitching, setIsSwitching] = useState(false)
  const { 
    currentOrganization, 
    organizations, 
    switchToOrganization,
    isLoading,
    hasOrganizations
  } = useOrganization()

  const handleOrganizationSwitch = async (organization: Organization) => {
    if (organization.id === currentOrganization?.id) {
      setIsOpen(false)
      return
    }

    try {
      setIsSwitching(true)
      // switchToOrganization handles prefetch of new org data + invalidation of old org queries
      await switchToOrganization(organization.id)
    } catch (error) {
      console.error('Error switching organization:', error)
    } finally {
      setIsSwitching(false)
      setIsOpen(false)
    }
  }

  const handleCreateOrganization = () => {
    setIsOpen(false)
    router.push('/organization/new')
  }

  if (isLoading) {
    return (
      <div className={`md-chip selected ${className}`}>
        <span className="md-label-medium">Loading...</span>
      </div>
    )
  }

  if (!hasOrganizations) {
    return (
      <button
        type="button"
        onClick={() => router.push('/organization/new')}
        className={`md-chip selected text-left transition-colors duration-200 cursor-pointer ${className}`}
      >
        <span className="md-label-medium">Create organization</span>
      </button>
    )
  }

  if (!currentOrganization) {
    return (
      <div className={`md-chip selected ${className}`}>
        <span className="md-label-medium">No Organization</span>
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md-chip selected transition-colors duration-200 cursor-pointer"
        disabled={isSwitching}
      >
        <span className="md-label-medium text-inherit max-w-[14rem] truncate">
          {currentOrganization?.name || 'Select Organization'}
        </span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-inherit transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown Menu */}
          <div className="absolute top-full left-0 mt-2 w-80 bg-surface rounded-xl shadow-lg border border-outline-variant z-20 overflow-hidden" style={{ backgroundColor: 'var(--md-sys-color-surface)' }}>
            <div className="p-2">
              {/* Header */}
              <div className="px-3 py-2 border-b border-outline-variant">
                <h3 className="md-title-small text-on-surface">Switch Organization</h3>
                <p className="md-body-small text-on-surface-variant mt-1">
                  Choose an organization to work with
                </p>
              </div>

              {/* Organizations List */}
              <div className="py-2">
                {organizations.map((org) => (
                  <div
                    key={org.id}
                    onClick={() => !isSwitching && handleOrganizationSwitch(org)}
                    className="w-full flex items-center justify-between px-3 py-3 hover:bg-secondary-container hover:text-on-secondary-container transition-colors duration-200 rounded-lg cursor-pointer"
                    style={{ opacity: isSwitching ? 0.6 : 1 }}
                  >
                    <div className="text-left">
                      <div className="md-label-large text-on-surface">
                        {org.name}
                      </div>
                    </div>
                    {currentOrganization?.id === org.id && (
                      <Check className="w-4 h-4 text-primary" />
                    )}
                  </div>
                ))}
              </div>

              {/* Create Organization Button */}
              <div className="border-t border-outline-variant pt-2">
                <div
                  onClick={handleCreateOrganization}
                  className="w-full flex items-center px-3 py-3 hover:bg-secondary-container hover:text-on-secondary-container transition-colors duration-200 rounded-lg cursor-pointer"
                >
                  <span className="md-label-large text-on-surface">
                    Create New Organization
                  </span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
