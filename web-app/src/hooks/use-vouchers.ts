import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { VoucherService } from '@/lib/voucher-service'
import { 
  InventoryVoucher, 
  VoucherFormData, 
  VoucherFilters, 
  VoucherStats,
  VoucherApprovalStats
} from '@/types'
import { useOrganization } from './use-organization'

// ===============================================
// VOUCHER QUERIES
// ===============================================

export function useVouchers(filters?: VoucherFilters, limit?: number, offset?: number) {
  const { currentOrganization } = useOrganization()

  return useQuery({
    queryKey: ['vouchers', currentOrganization?.id, filters, limit, offset],
    queryFn: () => VoucherService.getVouchers(currentOrganization!.id, filters, limit, offset),
    enabled: !!currentOrganization,
    staleTime: 30000, // 30 seconds
  })
}

export function useVoucher(id: number) {
  return useQuery({
    queryKey: ['voucher', id],
    queryFn: () => VoucherService.getVoucher(id),
    enabled: !!id,
  })
}

export function useVoucherStats() {
  const { currentOrganization } = useOrganization()

  return useQuery({
    queryKey: ['voucher-stats', currentOrganization?.id],
    queryFn: () => VoucherService.getVoucherStats(currentOrganization!.id),
    enabled: !!currentOrganization,
    staleTime: 60000, // 1 minute
  })
}

export function useApprovalStats() {
  const { currentOrganization } = useOrganization()
  const { currentUser } = useOrganization()

  return useQuery({
    queryKey: ['approval-stats', currentOrganization?.id, currentUser?.id],
    queryFn: () => VoucherService.getApprovalStats(currentOrganization!.id, currentUser!.id),
    enabled: !!currentOrganization && !!currentUser,
    staleTime: 60000, // 1 minute
  })
}

export function usePendingApprovals() {
  const { currentOrganization } = useOrganization()

  return useQuery({
    queryKey: ['pending-approvals', currentOrganization?.id],
    queryFn: () => VoucherService.getVouchers(currentOrganization!.id, { status: ['pending_finance'] }),
    enabled: !!currentOrganization,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  })
}

export function useExpiredVouchers() {
  const { currentOrganization } = useOrganization()

  return useQuery({
    queryKey: ['expired-vouchers', currentOrganization?.id],
    queryFn: () => VoucherService.getExpiredVouchers(currentOrganization!.id),
    enabled: !!currentOrganization,
    staleTime: 60000, // 1 minute
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
      // Invalidate and refetch voucher queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
    },
  })
}

export function useUpdateVoucher() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<VoucherFormData> }) => 
      VoucherService.updateVoucher(id, data),
    onSuccess: (updatedVoucher) => {
      // Update the specific voucher in cache
      queryClient.setQueryData(['voucher', updatedVoucher.id], updatedVoucher)
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
    },
  })
}

export function useDeleteVoucher() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => VoucherService.deleteVoucher(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: ['voucher', deletedId] })
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
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
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
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
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
      queryClient.invalidateQueries({ queryKey: ['approval-stats'] })
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
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
      queryClient.invalidateQueries({ queryKey: ['approval-stats'] })
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
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['expired-vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
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
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
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
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
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
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
    },
  })
}

// ===============================================
// VOUCHER EXPIRATION MUTATIONS
// ===============================================

export function useExpireOverdueVouchers() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => VoucherService.expireOverdueVouchers(),
    onSuccess: (expiredCount) => {
      if (expiredCount > 0) {
        // Invalidate all voucher queries to refresh data
        queryClient.invalidateQueries({ queryKey: ['vouchers'] })
        queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
        queryClient.invalidateQueries({ queryKey: ['expired-vouchers'] })
        queryClient.invalidateQueries({ queryKey: ['voucher-stats'] })
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
  const { currentUser } = useOrganization()
  
  // This would check the user's role
  // For now, we'll assume accountants and organization owners can approve
  return currentUser?.role === 'accountant' || currentUser?.role === 'organization_owner' || currentUser?.role === 'super_admin'
}

export function useCanCreateVouchers() {
  const { currentUser } = useOrganization()
  
  // All authenticated users can create vouchers
  return !!currentUser
}
