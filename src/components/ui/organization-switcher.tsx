'use client'

import { useState, type KeyboardEvent } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronDown, Check } from 'lucide-react'
import { useOrganization } from '@/hooks/use-organization'
import { Organization } from '@/types'
import { cn } from '@/lib/utils'

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

  const switcherSurfaceClass = cn(
    'ai-status-bar-container relative flex h-9 items-center rounded-lg border',
    'bg-[var(--md-sys-color-surface-container-highest)]',
    'border-[var(--md-sys-color-outline)]',
    'hover:bg-[var(--md-sys-color-surface-container-high)]',
    'hover:border-[var(--md-sys-color-outline)]',
    'focus:bg-[var(--md-sys-color-surface-container-highest)]',
    'focus:border-[var(--md-sys-color-primary)]',
    'focus:ring-1 focus:ring-primary/30',
    'transition-colors duration-200'
  )

  const handleTriggerKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (isSwitching) return

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      setIsOpen((open) => !open)
    }
  }

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
      <div className={cn(switcherSurfaceClass, 'justify-center px-3 py-1.5', className)}>
        <span className="text-sm font-medium text-on-surface">Loading...</span>
      </div>
    )
  }

  if (!hasOrganizations) {
    return (
      <div
        role="button"
        tabIndex={0}
        onClick={() => router.push('/organization/new')}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            router.push('/organization/new')
          }
        }}
        className={cn(switcherSurfaceClass, 'cursor-pointer justify-center px-3 py-1.5', className)}
      >
        <span className="text-sm font-medium text-on-surface">Create organization</span>
      </div>
    )
  }

  if (!currentOrganization) {
    return (
      <div className={cn(switcherSurfaceClass, 'justify-center px-3 py-1.5', className)}>
        <span className="text-sm font-medium text-on-surface">No Organization</span>
      </div>
    )
  }

  return (
    <div className={cn('relative', className)}>
      <div
        role="button"
        tabIndex={isSwitching ? -1 : 0}
        onClick={() => {
          if (!isSwitching) {
            setIsOpen(!isOpen)
          }
        }}
        onKeyDown={handleTriggerKeyDown}
        aria-disabled={isSwitching}
        aria-expanded={isOpen}
        className={cn(
          switcherSurfaceClass,
          'min-w-[150px] max-w-[240px] cursor-pointer justify-center px-8 py-1.5',
          isSwitching && 'cursor-not-allowed opacity-75'
        )}
      >
        <span className="w-full truncate text-center text-sm font-medium text-on-surface">
          {currentOrganization?.name || 'Select Organization'}
        </span>
        <ChevronDown
          className={`absolute right-3 h-4 w-4 shrink-0 text-on-surface-variant transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </div>

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
