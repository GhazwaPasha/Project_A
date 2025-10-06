import { useQuery } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import { Account } from '@/types'
import { useOrganization } from './use-organization'

export function useAccounts() {
  const { currentOrganization } = useOrganization()

  return useQuery({
    queryKey: ['accounts', currentOrganization?.id],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('accounts')
        .select('*')
        .eq('organization_id', currentOrganization!.id)
        .eq('is_active', true)
        .order('code')

      if (error) {
        console.error('Error fetching accounts:', error)
        throw new Error('Failed to fetch accounts')
      }

      return data as Account[]
    },
    enabled: !!currentOrganization,
    staleTime: 60000, // 1 minute
  })
}

export function useAccountsByType(accountType: string) {
  const { currentOrganization } = useOrganization()

  return useQuery({
    queryKey: ['accounts', currentOrganization?.id, accountType],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('accounts')
        .select('*')
        .eq('organization_id', currentOrganization!.id)
        .eq('account_type', accountType)
        .eq('is_active', true)
        .order('code')

      if (error) {
        console.error('Error fetching accounts by type:', error)
        throw new Error('Failed to fetch accounts')
      }

      return data as Account[]
    },
    enabled: !!currentOrganization,
    staleTime: 60000, // 1 minute
  })
}
