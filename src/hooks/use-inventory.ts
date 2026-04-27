import { useQuery } from '@tanstack/react-query'
import { DataService } from '@/lib/data-service'
import { InventoryItem, InventoryCategory, InventoryTransaction } from '@/types'
import { useCurrentOrganization } from '@/contexts/organization-context'
import { queryKeys } from '@/lib/query-keys'

export function useInventoryItems() {
  const currentOrganization = useCurrentOrganization()

  return useQuery<InventoryItem[]>({
    queryKey: queryKeys.inventoryItems(currentOrganization?.id || '', true),
    queryFn: () => DataService.getInventoryItems(currentOrganization!.id, true),
    enabled: !!currentOrganization,
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

export function useInventoryCategories() {
  const currentOrganization = useCurrentOrganization()

  return useQuery<InventoryCategory[]>({
    queryKey: queryKeys.inventoryCategories(currentOrganization?.id || '', true),
    queryFn: () => DataService.getInventoryCategories(currentOrganization!.id, true),
    enabled: !!currentOrganization,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

const DEFAULT_TX_LIMIT = 200

export function useInventoryTransactions(limit: number = DEFAULT_TX_LIMIT) {
  const currentOrganization = useCurrentOrganization()
  return useQuery<InventoryTransaction[]>({
    queryKey: queryKeys.inventoryTransactions(currentOrganization?.id || '', undefined, limit),
    queryFn: () => DataService.getInventoryTransactions(currentOrganization!.id, undefined, limit),
    enabled: !!currentOrganization,
    staleTime: 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}
