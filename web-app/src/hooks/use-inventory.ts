import { useQuery } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import { InventoryItem, InventoryCategory } from '@/types'
import { useOrganization } from './use-organization'

export function useInventoryItems() {
  const { currentOrganization } = useOrganization()

  return useQuery({
    queryKey: ['inventory-items', currentOrganization?.id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('inventory_items')
        .select(`
          *,
          category:inventory_categories(*)
        `)
        .eq('organization_id', currentOrganization!.id)
        .order('name')

      if (error) {
        console.error('Error fetching inventory items:', error)
        throw new Error('Failed to fetch inventory items')
      }

      return data as InventoryItem[]
    },
    enabled: !!currentOrganization,
    staleTime: 30000, // 30 seconds
  })
}

export function useInventoryCategories() {
  const { currentOrganization } = useOrganization()

  return useQuery({
    queryKey: ['inventory-categories', currentOrganization?.id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('inventory_categories')
        .select(`
          *,
          inventory_account:accounts!inventory_account_id(*),
          expense_account:accounts!expense_account_id(*)
        `)
        .eq('organization_id', currentOrganization!.id)
        .order('name')

      if (error) {
        console.error('Error fetching inventory categories:', error)
        throw new Error('Failed to fetch inventory categories')
      }

      return data as InventoryCategory[]
    },
    enabled: !!currentOrganization,
    staleTime: 60000, // 1 minute
  })
}
