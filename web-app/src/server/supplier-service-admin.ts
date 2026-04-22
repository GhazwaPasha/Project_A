import { getSupabaseAdmin } from '@/server/supabase-admin'
import { getActingUserId } from '@/server/request-context'
import { 
  Supplier, 
  SupplierFormData, 
  SupplierFilters, 
  SupplierAccountMappings,
  SupplierContact,
  Account
} from '@/types'

export class SupplierServiceAdmin {
  // ===============================================
  // SUPPLIER CRUD OPERATIONS
  // ===============================================

  static async getSuppliers(
    organizationId: string, 
    filters?: SupplierFilters,
    limit?: number,
    offset?: number
  ): Promise<Supplier[]> {
    let query = getSupabaseAdmin()
      .from('suppliers')
      .select(`
        *,
        account_mappings:supplier_account_mappings(
          *,
          payable_account:accounts!payable_account_id(*),
          cash_account:accounts!cash_account_id(*),
          expense_account:accounts!expense_account_id(*),
          inventory_account:accounts!inventory_account_id(*),
          freight_account:accounts!freight_account_id(*),
          tax_account:accounts!tax_account_id(*),
          discount_account:accounts!discount_account_id(*)
        ),
        contacts:supplier_contacts(*)
      `)
      .eq('organization_id', organizationId)
      .order('name', { ascending: true })

    // Apply filters
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        query = query.in('status', filters.status)
      }
      if (filters.is_preferred !== undefined) {
        query = query.eq('is_preferred', filters.is_preferred)
      }
      if (filters.payment_terms && filters.payment_terms.length > 0) {
        query = query.in('payment_terms', filters.payment_terms)
      }
      if (filters.search) {
        query = query.or(`
          supplier_code.ilike.%${filters.search}%,
          name.ilike.%${filters.search}%,
          legal_name.ilike.%${filters.search}%,
          contact_person.ilike.%${filters.search}%,
          email.ilike.%${filters.search}%
        `)
      }
    }

    if (limit) {
      query = query.limit(limit)
    }
    if (offset) {
      query = query.range(offset, offset + (limit || 50) - 1)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching suppliers:', error)
      throw new Error('Failed to fetch suppliers')
    }

    return data || []
  }

  static async getSupplier(id: number): Promise<Supplier | null> {
    const { data, error } = await getSupabaseAdmin()
      .from('suppliers')
      .select(`
        *,
        account_mappings:supplier_account_mappings(
          *,
          payable_account:accounts!payable_account_id(*),
          cash_account:accounts!cash_account_id(*),
          expense_account:accounts!expense_account_id(*),
          inventory_account:accounts!inventory_account_id(*),
          freight_account:accounts!freight_account_id(*),
          tax_account:accounts!tax_account_id(*),
          discount_account:accounts!discount_account_id(*)
        ),
        contacts:supplier_contacts(*)
      `)
      .eq('id', id)
      .single()

    if (error) {
      console.error('Error fetching supplier:', error)
      throw new Error('Failed to fetch supplier')
    }

    return data
  }

  static async createSupplier(supplierData: SupplierFormData, organizationId: string): Promise<Supplier> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    if (!organizationId) throw new Error('Organization ID is required')

    // Generate supplier code if not provided
    let supplierCode = supplierData.supplier_code
    if (!supplierCode) {
      const { data: lastSupplier } = await getSupabaseAdmin()
        .from('suppliers')
        .select('supplier_code')
        .eq('organization_id', organizationId)
        .order('supplier_code', { ascending: false })
        .limit(1)
        .single()

      if (lastSupplier) {
        const lastNumber = parseInt(lastSupplier.supplier_code.split('-')[1]) || 0
        supplierCode = `SUP-${String(lastNumber + 1).padStart(3, '0')}`
      } else {
        supplierCode = 'SUP-001'
      }
    }

    // Create supplier
    const { data: supplier, error: supplierError } = await getSupabaseAdmin()
      .from('suppliers')
      .insert({
        organization_id: organizationId,
        supplier_code: supplierCode,
        name: supplierData.name,
        legal_name: supplierData.legal_name,
        description: supplierData.description,
        
        // Contact information
        contact_person: supplierData.contact_person,
        email: supplierData.email,
        phone: supplierData.phone,
        fax: supplierData.fax,
        website: supplierData.website,
        
        // Address information
        billing_address_line1: supplierData.billing_address_line1,
        billing_address_line2: supplierData.billing_address_line2,
        billing_city: supplierData.billing_city,
        billing_state: supplierData.billing_state,
        billing_postal_code: supplierData.billing_postal_code,
        billing_country: supplierData.billing_country,
        
        shipping_address_line1: supplierData.shipping_address_line1,
        shipping_address_line2: supplierData.shipping_address_line2,
        shipping_city: supplierData.shipping_city,
        shipping_state: supplierData.shipping_state,
        shipping_postal_code: supplierData.shipping_postal_code,
        shipping_country: supplierData.shipping_country,
        
        // Business information
        tax_id: supplierData.tax_id,
        registration_number: supplierData.registration_number,
        currency: supplierData.currency,
        
        // Payment terms
        payment_terms: supplierData.payment_terms,
        credit_limit: supplierData.credit_limit,
        
        // Status and metadata
        status: supplierData.status,
        is_preferred: supplierData.is_preferred,
        notes: supplierData.notes,
        
        created_by: acting
      })
      .select()
      .single()

    if (supplierError) {
      console.error('Error creating supplier:', supplierError)
      throw new Error(`Failed to create supplier: ${supplierError.message}`)
    }

    // Create account mappings
    if (supplierData.account_mappings) {
      const { error: mappingError } = await getSupabaseAdmin()
        .from('supplier_account_mappings')
        .insert({
          supplier_id: supplier.id,
          organization_id: organizationId,
          payable_account_id: supplierData.account_mappings.payable_account_id,
          cash_account_id: supplierData.account_mappings.cash_account_id,
          expense_account_id: supplierData.account_mappings.expense_account_id,
          inventory_account_id: supplierData.account_mappings.inventory_account_id,
          freight_account_id: supplierData.account_mappings.freight_account_id,
          tax_account_id: supplierData.account_mappings.tax_account_id,
          discount_account_id: supplierData.account_mappings.discount_account_id,
          created_by: acting
        })

      if (mappingError) {
        console.error('Error creating supplier account mappings:', mappingError)
        throw new Error(`Failed to create supplier account mappings: ${mappingError.message}`)
      }
    }

    // Create contacts
    if (supplierData.contacts && supplierData.contacts.length > 0) {
      const contactsData = supplierData.contacts.map(contact => ({
        supplier_id: supplier.id,
        name: contact.name,
        title: contact.title,
        email: contact.email,
        phone: contact.phone,
        mobile: contact.mobile,
        fax: contact.fax,
        is_primary: contact.is_primary,
        is_billing: contact.is_billing,
        is_shipping: contact.is_shipping,
        is_technical: contact.is_technical,
        created_by: acting,
      }))

      const { error: contactsError } = await getSupabaseAdmin()
        .from('supplier_contacts')
        .insert(contactsData)

      if (contactsError) {
        console.error('Error creating supplier contacts:', contactsError)
        throw new Error(`Failed to create supplier contacts: ${contactsError.message}`)
      }
    }

    // Return the created supplier with relations
    return this.getSupplier(supplier.id) as Promise<Supplier>
  }

  static async updateSupplier(id: number, supplierData: Partial<SupplierFormData>): Promise<Supplier> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    // Update supplier
    const { error: supplierError } = await getSupabaseAdmin()
      .from('suppliers')
      .update({
        ...supplierData,
        updated_by: acting,
        updated_at: new Date().toISOString()
      })
      .eq('id', id)

    if (supplierError) {
      console.error('Error updating supplier:', supplierError)
      throw new Error(`Failed to update supplier: ${supplierError.message}`)
    }

    // Update account mappings if provided
    if (supplierData.account_mappings) {
      const { error: mappingError } = await getSupabaseAdmin()
        .from('supplier_account_mappings')
        .update({
          payable_account_id: supplierData.account_mappings.payable_account_id,
          cash_account_id: supplierData.account_mappings.cash_account_id,
          expense_account_id: supplierData.account_mappings.expense_account_id,
          inventory_account_id: supplierData.account_mappings.inventory_account_id,
          freight_account_id: supplierData.account_mappings.freight_account_id,
          tax_account_id: supplierData.account_mappings.tax_account_id,
          discount_account_id: supplierData.account_mappings.discount_account_id,
          updated_by: acting,
          updated_at: new Date().toISOString()
        })
        .eq('supplier_id', id)

      if (mappingError) {
        console.error('Error updating supplier account mappings:', mappingError)
        throw new Error(`Failed to update supplier account mappings: ${mappingError.message}`)
      }
    }

    // Update contacts if provided
    if (supplierData.contacts) {
      // Delete existing contacts
      await getSupabaseAdmin()
        .from('supplier_contacts')
        .delete()
        .eq('supplier_id', id)

      // Insert new contacts
      if (supplierData.contacts.length > 0) {
        const contactsData = supplierData.contacts.map(contact => ({
          supplier_id: id,
          name: contact.name,
          title: contact.title,
          email: contact.email,
          phone: contact.phone,
          mobile: contact.mobile,
          fax: contact.fax,
          is_primary: contact.is_primary,
          is_billing: contact.is_billing,
          is_shipping: contact.is_shipping,
          is_technical: contact.is_technical,
          created_by: acting,
        }))

        const { error: contactsError } = await getSupabaseAdmin()
          .from('supplier_contacts')
          .insert(contactsData)

        if (contactsError) {
          console.error('Error updating supplier contacts:', contactsError)
          throw new Error(`Failed to update supplier contacts: ${contactsError.message}`)
        }
      }
    }

    return this.getSupplier(id) as Promise<Supplier>
  }

  static async deleteSupplier(id: number): Promise<void> {
    const { error } = await getSupabaseAdmin()
      .from('suppliers')
      .delete()
      .eq('id', id)

    if (error) {
      console.error('Error deleting supplier:', error)
      throw new Error('Failed to delete supplier')
    }
  }

  // ===============================================
  // SUPPLIER ACCOUNT MAPPINGS
  // ===============================================

  static async getSupplierAccountMappings(supplierId: number): Promise<SupplierAccountMappings | null> {
    const { data, error } = await getSupabaseAdmin()
      .from('supplier_account_mappings')
      .select(`
        *,
        payable_account:accounts!payable_account_id(*),
        cash_account:accounts!cash_account_id(*),
        expense_account:accounts!expense_account_id(*),
        inventory_account:accounts!inventory_account_id(*),
        freight_account:accounts!freight_account_id(*),
        tax_account:accounts!tax_account_id(*),
        discount_account:accounts!discount_account_id(*)
      `)
      .eq('supplier_id', supplierId)
      .single()

    if (error) {
      console.error('Error fetching supplier account mappings:', error)
      throw new Error('Failed to fetch supplier account mappings')
    }

    return data
  }

  static async updateSupplierAccountMappings(
    supplierId: number, 
    mappings: Partial<SupplierAccountMappings>
  ): Promise<SupplierAccountMappings> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    const { data, error } = await getSupabaseAdmin()
      .from('supplier_account_mappings')
      .update({
        ...mappings,
        updated_by: acting,
        updated_at: new Date().toISOString()
      })
      .eq('supplier_id', supplierId)
      .select()
      .single()

    if (error) {
      console.error('Error updating supplier account mappings:', error)
      throw new Error('Failed to update supplier account mappings')
    }

    return data
  }

  // ===============================================
  // SUPPLIER CONTACTS
  // ===============================================

  static async getSupplierContacts(supplierId: number): Promise<SupplierContact[]> {
    const { data, error } = await getSupabaseAdmin()
      .from('supplier_contacts')
      .select('*')
      .eq('supplier_id', supplierId)
      .order('is_primary', { ascending: false })
      .order('name', { ascending: true })

    if (error) {
      console.error('Error fetching supplier contacts:', error)
      throw new Error('Failed to fetch supplier contacts')
    }

    return data || []
  }

  static async addSupplierContact(contactData: Omit<SupplierContact, 'id' | 'created_at' | 'updated_at'>): Promise<SupplierContact> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    const { data, error } = await getSupabaseAdmin()
      .from('supplier_contacts')
      .insert({
        ...contactData,
        created_by: acting,
      })
      .select()
      .single()

    if (error) {
      console.error('Error adding supplier contact:', error)
      throw new Error('Failed to add supplier contact')
    }

    return data
  }

  static async updateSupplierContact(id: number, contactData: Partial<SupplierContact>): Promise<SupplierContact> {
    const { data, error } = await getSupabaseAdmin()
      .from('supplier_contacts')
      .update({
        ...contactData,
        updated_at: new Date().toISOString()
      })
      .eq('id', id)
      .select()
      .single()

    if (error) {
      console.error('Error updating supplier contact:', error)
      throw new Error('Failed to update supplier contact')
    }

    return data
  }

  static async deleteSupplierContact(id: number): Promise<void> {
    const { error } = await getSupabaseAdmin()
      .from('supplier_contacts')
      .delete()
      .eq('id', id)

    if (error) {
      console.error('Error deleting supplier contact:', error)
      throw new Error('Failed to delete supplier contact')
    }
  }

  // ===============================================
  // SUPPLIER STATISTICS
  // ===============================================

  static async getSupplierStats(organizationId: string): Promise<{
    total_suppliers: number
    active_suppliers: number
    inactive_suppliers: number
    preferred_suppliers: number
    total_credit_limit: number
    total_current_balance: number
  }> {
    const { data, error } = await getSupabaseAdmin()
      .from('suppliers')
      .select('status, is_preferred, credit_limit, current_balance')
      .eq('organization_id', organizationId)

    if (error) {
      console.error('Error fetching supplier stats:', error)
      throw new Error('Failed to fetch supplier stats')
    }

    return {
      total_suppliers: data.length,
      active_suppliers: data.filter(s => s.status === 'active').length,
      inactive_suppliers: data.filter(s => s.status === 'inactive').length,
      preferred_suppliers: data.filter(s => s.is_preferred).length,
      total_credit_limit: data.reduce((sum, s) => sum + (s.credit_limit || 0), 0),
      total_current_balance: data.reduce((sum, s) => sum + (s.current_balance || 0), 0)
    }
  }

  // ===============================================
  // VOUCHER INTEGRATION
  // ===============================================

  static async getSupplierForVoucher(supplierId: number): Promise<{
    supplier: Supplier
    account_mappings: SupplierAccountMappings
  } | null> {
    const supplier = await this.getSupplier(supplierId)
    if (!supplier) return null

    const accountMappings = await this.getSupplierAccountMappings(supplierId)
    if (!accountMappings) return null

    return {
      supplier,
      account_mappings: accountMappings
    }
  }

  static async getSuppliersForVoucher(organizationId: string): Promise<Array<{
    id: number
    supplier_code: string
    name: string
    payable_account_id: number
    cash_account_id?: number
    expense_account_id?: number
  }>> {
    const { data, error } = await getSupabaseAdmin()
      .from('suppliers')
      .select(`
        id,
        supplier_code,
        name,
        account_mappings:supplier_account_mappings(
          payable_account_id,
          cash_account_id,
          expense_account_id
        )
      `)
      .eq('organization_id', organizationId)
      .eq('status', 'active')
      .order('name', { ascending: true })

    if (error) {
      console.error('Error fetching suppliers for voucher:', error)
      throw new Error('Failed to fetch suppliers for voucher')
    }

    return (
      data?.map((supplier) => {
        const m = supplier.account_mappings as
          | { payable_account_id?: number; cash_account_id?: number; expense_account_id?: number }
          | { payable_account_id?: number; cash_account_id?: number; expense_account_id?: number }[]
          | null
          | undefined
        const mapping = Array.isArray(m) ? m[0] : m
        return {
          id: supplier.id,
          supplier_code: supplier.supplier_code,
          name: supplier.name,
          payable_account_id: mapping?.payable_account_id ?? 0,
          cash_account_id: mapping?.cash_account_id,
          expense_account_id: mapping?.expense_account_id,
        }
      }) || []
    )
  }
}
