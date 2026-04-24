import { useQuery } from '@tanstack/react-query'
import { DataService } from '@/lib/data-service'
import { Account } from '@/types'
import { useOrganization } from './use-organization'
import { queryKeys } from '@/lib/query-keys'

export function useAccounts() {
  const { currentOrganization } = useOrganization()

  return useQuery<Account[]>({
    queryKey: queryKeys.accounts(currentOrganization?.id ?? '', true),
    queryFn: async () => {
      if (!currentOrganization?.id) return []
      return DataService.getAccounts(currentOrganization.id, true)
    },
    enabled: !!currentOrganization,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  })
}

export function useAccountsByType(accountType: string) {
  const { currentOrganization } = useOrganization()

  // Select from the shared accounts cache instead of a separate fetch
  return useQuery<Account[]>({
    queryKey: queryKeys.accountsByType(currentOrganization?.id ?? '', accountType),
    queryFn: async () => {
      if (!currentOrganization?.id) return []
      const all = await DataService.getAccounts(currentOrganization.id, true)
      return all.filter((a) => a.account_type === accountType)
    },
    enabled: !!currentOrganization,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  })
}
