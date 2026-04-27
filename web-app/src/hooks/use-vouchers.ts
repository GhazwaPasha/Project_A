import { useQuery, useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { VoucherService } from '@/lib/voucher-service'
import { 
  InventoryVoucher, 
  VoucherFormData, 
  VoucherFilters, 
  VoucherStats,
  VoucherApprovalStats
} from '@/types'
import { useCurrentOrganization } from '@/contexts/organization-context'
import { useAuthStore } from '@/stores/auth-store'
import { hasOrgDataPermission } from '@/lib/organization-permissions'
import { queryKeys } from '@/lib/query-keys'

/** Keeps inventory voucher lists, stats, and Approvals (pending / expired) in sync. */
export function invalidateVoucherRelatedQueries(queryClient: QueryClient, orgId: string | undefined) {
  if (!orgId) return
  for (const prefix of queryKeys.voucherQueryPrefixes(orgId)) {
    void queryClient.invalidateQueries({ queryKey: [...prefix] })
  }
}

// ===============================================
// VOUCHER QUERIES
// ===============================================

export function useVouchers(filters?: VoucherFilters, limit?: number, offset?: number) {
  const currentOrganization = useCurrentOrganization()

  return useQuery<InventoryVoucher[]>({
    queryKey: queryKeys.vouchers(currentOrganization?.id || '', filters, limit, offset),
    queryFn: () => VoucherService.getVouchers(currentOrganization!.id, filters, limit, offset),
    enabled: !!currentOrganization,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useVoucher(id: number) {
  return useQuery<InventoryVoucher | null>({
    queryKey: queryKeys.voucher(id),
    queryFn: () => VoucherService.getVoucher(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useVoucherStats() {
  const currentOrganization = useCurrentOrganization()

  return useQuery<VoucherStats>({
    queryKey: queryKeys.voucherStats(currentOrganization?.id || ''),
    queryFn: () => VoucherService.getVoucherStats(currentOrganization!.id),
    enabled: !!currentOrganization,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useApprovalStats() {
  const currentOrganization = useCurrentOrganization()
  const { user } = useAuthStore()

  return useQuery<VoucherApprovalStats>({
    queryKey: queryKeys.voucherApprovalStats(currentOrganization?.id || ''),
    queryFn: () => VoucherService.getApprovalStats(currentOrganization!.id, user!.id),
    enabled: !!currentOrganization && !!user,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function usePendingApprovals() {
  const currentOrganization = useCurrentOrganization()

  return useQuery<InventoryVoucher[]>({
    queryKey: ['pending-approvals', currentOrganization?.id],
    queryFn: () => VoucherService.getVouchers(currentOrganization!.id, { status: ['pending_finance'] }),
    enabled: !!currentOrganization,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 60 * 1000, // Refetch every minute
  })
}

export function useExpiredVouchers() {
  const currentOrganization = useCurrentOrganization()

  return useQuery<InventoryVoucher[]>({
    queryKey: ['expired-vouchers', currentOrganization?.id],
    queryFn: () => VoucherService.getExpiredVouchers(currentOrganization!.id),
    enabled: !!currentOrganization,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

// ===============================================
// VOUCHER MUTATIONS
// ===============================================

export function useCreateVoucher(organizationId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (voucherData: VoucherFormData) => VoucherService.createVoucher(voucherData, organizationId),
    onSuccess: () => {
      invalidateVoucherRelatedQueries(queryClient, organizationId)
    },
  })
}

export function useUpdateVoucher() {
  const queryClient = useQueryClient()
  const orgId = useCurrentOrganization()?.id

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<VoucherFormData> }) => 
      VoucherService.updateVoucher(id, data),
    onSuccess: (updatedVoucher) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', updatedVoucher.id], updatedVoucher)
      invalidateVoucherRelatedQueries(queryClient, updatedVoucher.organization_id || orgId)
    },
  })
}

export function useDeleteVoucher() {
  const queryClient = useQueryClient()
  const orgId = useCurrentOrganization()?.id

  return useMutation({
    mutationFn: (id: number) => VoucherService.deleteVoucher(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: ['voucher', deletedId] })
      invalidateVoucherRelatedQueries(queryClient, orgId)
    },
  })
}

// ===============================================
// VOUCHER WORKFLOW MUTATIONS
// ===============================================

export function useSubmitForApproval(organizationId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => VoucherService.submitForApproval(id, organizationId),
    onSuccess: (updatedVoucher) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', updatedVoucher.id], updatedVoucher)
      invalidateVoucherRelatedQueries(
        queryClient,
        updatedVoucher.organization_id || organizationId
      )
    },
  })
}

export function useApproveVoucher() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, notes }: { id: number; notes?: string }) => 
      VoucherService.approveVoucher(id, notes),
    onSuccess: (updatedVoucher) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', updatedVoucher.id], updatedVoucher)
      invalidateVoucherRelatedQueries(queryClient, updatedVoucher.organization_id)
    },
  })
}

export function useRejectVoucher() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => 
      VoucherService.rejectVoucher(id, reason),
    onSuccess: (updatedVoucher) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', updatedVoucher.id], updatedVoucher)
      invalidateVoucherRelatedQueries(queryClient, updatedVoucher.organization_id)
    },
  })
}

export function useRenewVoucher() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => 
      VoucherService.renewExpiredVoucher(id, reason),
    onSuccess: (updatedVoucher) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', updatedVoucher.id], updatedVoucher)
      invalidateVoucherRelatedQueries(queryClient, updatedVoucher.organization_id)
    },
  })
}

// ===============================================
// VOUCHER EXECUTION MUTATIONS
// ===============================================

export function useExecuteVoucher() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, actualQuantities }: { id: number; actualQuantities: { [lineId: number]: number } }) => 
      VoucherService.executeVoucher(id, actualQuantities),
    onSuccess: (updatedVoucher) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', updatedVoucher.id], updatedVoucher)
      invalidateVoucherRelatedQueries(queryClient, updatedVoucher.organization_id)
    },
  })
}

export function usePostVoucher() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => VoucherService.postVoucher(id),
    onSuccess: (updatedVoucher) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', updatedVoucher.id], updatedVoucher)
      invalidateVoucherRelatedQueries(queryClient, updatedVoucher.organization_id)
    },
  })
}

export function useCompleteVoucher() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => VoucherService.completeVoucher(id),
    onSuccess: (updatedVoucher) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', updatedVoucher.id], updatedVoucher)
      invalidateVoucherRelatedQueries(queryClient, updatedVoucher.organization_id)
    },
  })
}

// ===============================================
// VOUCHER EXPIRATION MUTATIONS
// ===============================================

export function useExpireOverdueVouchers() {
  const queryClient = useQueryClient()
  const orgId = useCurrentOrganization()?.id

  return useMutation({
    mutationFn: () => VoucherService.expireOverdueVouchers(),
    onSuccess: (expiredCount) => {
      if (expiredCount > 0) {
        if (orgId) {
          invalidateVoucherRelatedQueries(queryClient, orgId)
        } else {
          void queryClient.invalidateQueries({ queryKey: ['vouchers'] })
          void queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
          void queryClient.invalidateQueries({ queryKey: ['expired-vouchers'] })
        }
      }
      return expiredCount
    },
  })
}

// ===============================================
// VOUCHER ATTACHMENT MUTATIONS
// ===============================================

export function useUploadAttachment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ voucherId, file, description }: { voucherId: number; file: File; description?: string }) => 
      VoucherService.uploadAttachment(voucherId, file, description),
    onSuccess: (attachment, { voucherId }) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', voucherId], (old: InventoryVoucher | undefined) => {
        if (!old) return old
        return {
          ...old,
          attachments: [...(old.attachments || []), attachment]
        }
      })
    },
  })
}

export function useDeleteAttachment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (attachmentId: number) => VoucherService.deleteAttachment(attachmentId),
    onSuccess: (_, attachmentId) => {
      // Remove from all voucher caches
      queryClient.setQueriesData({ queryKey: ['voucher'] }, (old: InventoryVoucher | undefined) => {
        if (!old) return old
        return {
          ...old,
          attachments: old.attachments?.filter(a => a.id !== attachmentId) || []
        }
      })
    },
  })
}

// ===============================================
// UTILITY HOOKS
// ===============================================

export function useVoucherStatusColor(status: string) {
  const statusColors: Record<string, string> = {
    draft: 'text-gray-600 bg-gray-100',
    pending_finance: 'text-yellow-700 bg-yellow-100',
    approved: 'text-green-700 bg-green-100',
    receiving: 'text-blue-700 bg-blue-100',
    issuing: 'text-blue-700 bg-blue-100',
    posted: 'text-purple-700 bg-purple-100',
    completed: 'text-green-700 bg-green-100',
    rejected: 'text-red-700 bg-red-100',
    expired: 'text-red-700 bg-red-100',
    cancelled: 'text-gray-700 bg-gray-100',
  }

  return statusColors[status] || 'text-gray-600 bg-gray-100'
}

export function useVoucherStatusIcon(status: string) {
  const statusIcons: Record<string, string> = {
    draft: '📝',
    pending_finance: '⏳',
    approved: '✅',
    receiving: '📦',
    issuing: '📤',
    posted: '📊',
    completed: '🎉',
    rejected: '❌',
    expired: '⏰',
    cancelled: '🚫',
  }

  return statusIcons[status] || '❓'
}

export function useCanApproveVouchers() {
  const user = useAuthStore((s) => s.user)
  return !!user
}

export function useCanCreateVouchers() {
  const { user } = useAuthStore()
  const role = useAuthStore((s) => s.currentOrgMemberRole)
  const isSuper = useAuthStore((s) => s.profile?.is_super_admin) === true
  const resolved = useAuthStore((s) => s.orgMemberRoleResolved)
  if (!user) return false
  if (isSuper) return true
  if (!resolved) return true
  if (!role) return false
  return hasOrgDataPermission(role, 'voucher.write', { isPlatformSuperAdmin: false })
}
