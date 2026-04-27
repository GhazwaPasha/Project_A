import { appDataRequest } from '@/lib/app-data-request'
import type {
  InventoryVoucher,
  VoucherFormData,
  VoucherFilters,
  VoucherStats,
  VoucherApprovalStats,
  VoucherAttachment,
} from '@/types'

/** Browser client: calls `/api/app-data` (and FormData upload for attachments). */
export class VoucherService {
  static async getVouchers(
    organizationId: string,
    filters?: VoucherFilters,
    limit?: number,
    offset?: number
  ): Promise<InventoryVoucher[]> {
    return appDataRequest('VoucherService', 'getVouchers', [organizationId, filters, limit, offset])
  }

  static async getVoucher(id: number): Promise<InventoryVoucher | null> {
    return appDataRequest('VoucherService', 'getVoucher', [id])
  }

  static async createVoucher(voucherData: VoucherFormData, organizationId: string): Promise<InventoryVoucher> {
    return appDataRequest('VoucherService', 'createVoucher', [voucherData, organizationId])
  }

  static async updateVoucher(id: number, voucherData: Partial<VoucherFormData>): Promise<InventoryVoucher> {
    return appDataRequest('VoucherService', 'updateVoucher', [id, voucherData])
  }

  static async deleteVoucher(id: number): Promise<void> {
    return appDataRequest('VoucherService', 'deleteVoucher', [id])
  }

  static async submitForApproval(id: number, organizationId: string): Promise<InventoryVoucher> {
    return appDataRequest('VoucherService', 'submitForApproval', [id, organizationId])
  }

  static async approveVoucher(id: number, notes?: string): Promise<InventoryVoucher> {
    return appDataRequest('VoucherService', 'approveVoucher', [id, notes])
  }

  static async rejectVoucher(id: number, reason: string): Promise<InventoryVoucher> {
    return appDataRequest('VoucherService', 'rejectVoucher', [id, reason])
  }

  static async renewExpiredVoucher(id: number, reason: string): Promise<InventoryVoucher> {
    return appDataRequest('VoucherService', 'renewExpiredVoucher', [id, reason])
  }

  static async executeVoucher(id: number, actualQuantities: { [lineId: number]: number }): Promise<InventoryVoucher> {
    return appDataRequest('VoucherService', 'executeVoucher', [id, actualQuantities])
  }

  static async postVoucher(id: number): Promise<InventoryVoucher> {
    return appDataRequest('VoucherService', 'postVoucher', [id])
  }

  static async completeVoucher(id: number): Promise<InventoryVoucher> {
    return appDataRequest('VoucherService', 'completeVoucher', [id])
  }

  static async getVoucherStats(organizationId: string): Promise<VoucherStats> {
    return appDataRequest('VoucherService', 'getVoucherStats', [organizationId])
  }

  static async getApprovalStats(organizationId: string, userId: string): Promise<VoucherApprovalStats> {
    return appDataRequest('VoucherService', 'getApprovalStats', [organizationId, userId])
  }

  static async expireOverdueVouchers(): Promise<number> {
    return appDataRequest('VoucherService', 'expireOverdueVouchers', [])
  }

  static async getExpiredVouchers(organizationId: string): Promise<InventoryVoucher[]> {
    return appDataRequest('VoucherService', 'getExpiredVouchers', [organizationId])
  }

  static async uploadAttachment(
    voucherId: number,
    file: File,
    description?: string
  ): Promise<VoucherAttachment> {
    const fd = new FormData()
    fd.append('voucherId', String(voucherId))
    fd.append('file', file)
    if (description) fd.append('description', description)
    const res = await fetch('/api/vouchers/attachments', {
      method: 'POST',
      body: fd,
      credentials: 'include',
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || res.statusText)
    }
    return res.json() as Promise<VoucherAttachment>
  }

  static async deleteAttachment(attachmentId: number): Promise<void> {
    return appDataRequest('VoucherService', 'deleteAttachment', [attachmentId])
  }
}
