'use client'

import { useOrganization } from '@/hooks/use-organization'
import { SupplierList } from '@/components/suppliers/supplier-list'

export default function SuppliersPage() {
  const { currentOrganization } = useOrganization()

  if (!currentOrganization) {
    return (
      <div className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">
        <div className="flex min-h-[40vh] flex-col items-center justify-center gap-2 rounded-lg border border-border bg-card/30 px-6 py-12 text-center">
          <p className="text-sm font-medium text-foreground">No workspace selected</p>
          <p className="max-w-sm text-sm text-muted-foreground">
            Choose an organization in the header to manage suppliers.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">
      <SupplierList organizationId={currentOrganization.id} />
    </div>
  )
}
