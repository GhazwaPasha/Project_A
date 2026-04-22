'use client'

import { useOrganization } from '@/hooks/use-organization'
import { SupplierList } from '@/components/suppliers/supplier-list'

export default function SuppliersPage() {
  const { currentOrganization } = useOrganization()

  if (!currentOrganization) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Please select an organization</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6">
      <SupplierList organizationId={currentOrganization.id} />
    </div>
  )
}
