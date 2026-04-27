import { appDataRequest } from '@/lib/app-data-request'
import type {
  Supplier,
  SupplierFormData,
  SupplierFilters,
  SupplierAccountMappings,
  SupplierContact,
  SupplierVoucherPicker,
} from '@/types'

/** Browser client: calls `/api/app-data` (server uses service role + membership checks). */
export class SupplierService {
  static async getSuppliers(
    organizationId: string,
    filters?: SupplierFilters,
    limit?: number,
    offset?: number
  ): Promise<Supplier[]> {
    return appDataRequest('SupplierService', 'getSuppliers', [organizationId, filters, limit, offset])
  }

  static async getSupplier(id: number): Promise<Supplier | null> {
    return appDataRequest('SupplierService', 'getSupplier', [id])
  }

  static async createSupplier(supplierData: SupplierFormData, organizationId: string): Promise<Supplier> {
    return appDataRequest('SupplierService', 'createSupplier', [supplierData, organizationId])
  }

  static async updateSupplier(id: number, supplierData: Partial<SupplierFormData>): Promise<Supplier> {
    return appDataRequest('SupplierService', 'updateSupplier', [id, supplierData])
  }

  static async deleteSupplier(id: number): Promise<void> {
    return appDataRequest('SupplierService', 'deleteSupplier', [id])
  }

  static async getSupplierAccountMappings(supplierId: number): Promise<SupplierAccountMappings | null> {
    return appDataRequest('SupplierService', 'getSupplierAccountMappings', [supplierId])
  }

  static async updateSupplierAccountMappings(
    supplierId: number,
    mappings: Partial<SupplierAccountMappings>
  ): Promise<SupplierAccountMappings> {
    return appDataRequest('SupplierService', 'updateSupplierAccountMappings', [supplierId, mappings])
  }

  static async getSupplierContacts(supplierId: number): Promise<SupplierContact[]> {
    return appDataRequest('SupplierService', 'getSupplierContacts', [supplierId])
  }

  static async addSupplierContact(
    contactData: Omit<SupplierContact, 'id' | 'created_at' | 'updated_at'>
  ): Promise<SupplierContact> {
    return appDataRequest('SupplierService', 'addSupplierContact', [contactData])
  }

  static async updateSupplierContact(
    id: number,
    contactData: Partial<SupplierContact>
  ): Promise<SupplierContact> {
    return appDataRequest('SupplierService', 'updateSupplierContact', [id, contactData])
  }

  static async deleteSupplierContact(id: number): Promise<void> {
    return appDataRequest('SupplierService', 'deleteSupplierContact', [id])
  }

  static async getSupplierStats(organizationId: string): Promise<{
    total_suppliers: number
    active_suppliers: number
    inactive_suppliers: number
    preferred_suppliers: number
    total_credit_limit: number
    total_current_balance: number
  }> {
    return appDataRequest('SupplierService', 'getSupplierStats', [organizationId])
  }

  static async getSupplierForVoucher(supplierId: number): Promise<{
    supplier: Supplier
    account_mappings: SupplierAccountMappings
  } | null> {
    return appDataRequest('SupplierService', 'getSupplierForVoucher', [supplierId])
  }

  static async getSuppliersForVoucher(organizationId: string): Promise<SupplierVoucherPicker[]> {
    return appDataRequest<SupplierVoucherPicker[]>('SupplierService', 'getSuppliersForVoucher', [organizationId])
  }
}
