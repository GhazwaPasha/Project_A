import { useQuery } from '@tanstack/react-query'
import { DataService } from '@/lib/data-service'
import { Account } from '@/types'
import { useOrganization } from './use-organization'

export function useAccounts() {
  const { currentOrganization } = useOrganization()

  return useQuery<Account[]>({
    queryKey: ['accounts', currentOrganization?.id],
    queryFn: async () => {
      if (!currentOrganization?.id) return []
      return DataService.getAccounts(currentOrganization.id, true)
    },
    enabled: !!currentOrganization,
    staleTime: 60000,
  })
}

export function useAccountsByType(accountType: string) {
  const { currentOrganization } = useOrganization()

  return useQuery<Account[]>({
    queryKey: ['accounts', currentOrganization?.id, accountType],
    queryFn: async () => {
      if (!currentOrganization?.id) return []
      const all = await DataService.getAccounts(currentOrganization.id, true)
      return all.filter((a) => a.account_type === accountType)
    },
    enabled: !!currentOrganization,
    staleTime: 60000,
  })
}
