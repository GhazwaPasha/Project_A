import { getSupabaseAdmin } from '@/server/supabase-admin'
import { getActingUserId } from '@/server/request-context'
import { 
  InventoryVoucher, 
  InventoryVoucherLine, 
  VoucherFormData, 
  VoucherFilters, 
  VoucherStats,
  VoucherApprovalStats,
  VoucherApproval,
  VoucherExpirationLog,
  VoucherAttachment
} from '@/types'

export class VoucherServiceAdmin {
  // ===============================================
  // VOUCHER CRUD OPERATIONS
  // ===============================================

  static async getVouchers(
    organizationId: string, 
    filters?: VoucherFilters,
    limit?: number,
    offset?: number
  ): Promise<InventoryVoucher[]> {
    let query = getSupabaseAdmin()
      .from('inventory_vouchers')
      .select(`
        *,
        lines:inventory_voucher_lines(*, item:inventory_items(*)),
        attachments:voucher_attachments(*),
        requested_by_user:user_profiles!requested_by(*),
        finance_approved_by_user:user_profiles!finance_approved_by(*),
        rejected_by_user:user_profiles!rejected_by(*),
        executed_by_user:user_profiles!executed_by(*),
        destination_account:accounts!destination_account_id(*),
        payment_account:accounts!payment_account_id(*),
        journal_entry:journal_entries(*)
      `)
      .eq('organization_id', organizationId)
      .order('created_at', { ascending: false })

    // Apply filters
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        query = query.in('status', filters.status)
      }
      if (filters.voucher_type && filters.voucher_type.length > 0) {
        query = query.in('voucher_type', filters.voucher_type)
      }
      if (filters.requested_by && filters.requested_by.length > 0) {
        query = query.in('requested_by', filters.requested_by)
      }
      if (filters.date_from) {
        query = query.gte('requested_date', filters.date_from)
      }
      if (filters.date_to) {
        query = query.lte('requested_date', filters.date_to)
      }
      if (filters.amount_min) {
        query = query.gte('total_estimated_cost', filters.amount_min)
      }
      if (filters.amount_max) {
        query = query.lte('total_estimated_cost', filters.amount_max)
      }
      if (filters.search) {
        query = query.or(`voucher_number.ilike.%${filters.search}%,description.ilike.%${filters.search}%,vendor_name.ilike.%${filters.search}%,purpose.ilike.%${filters.search}%`)
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
      console.error('Error fetching vouchers:', error)
      throw new Error('Failed to fetch vouchers')
    }

    return data || []
  }

  static async getVoucher(id: number): Promise<InventoryVoucher | null> {
    const { data, error } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .select(`
        *,
        lines:inventory_voucher_lines(*, item:inventory_items(*)),
        attachments:voucher_attachments(*),
        requested_by_user:user_profiles!requested_by(*),
        finance_approved_by_user:user_profiles!finance_approved_by(*),
        rejected_by_user:user_profiles!rejected_by(*),
        executed_by_user:user_profiles!executed_by(*),
        destination_account:accounts!destination_account_id(*),
        payment_account:accounts!payment_account_id(*),
        journal_entry:journal_entries(*)
      `)
      .eq('id', id)
      .single()

    if (error) {
      console.error('Error fetching voucher:', error)
      throw new Error('Failed to fetch voucher')
    }

    return data
  }

  static async createVoucher(voucherData: VoucherFormData, organizationId: string): Promise<InventoryVoucher> {
    const userId = getActingUserId()
    if (!userId) throw new Error('User not authenticated')

    if (!organizationId) throw new Error('Organization ID is required')

    // Generate voucher number (temporary simple generation)
    const timestamp = Date.now().toString().slice(-6)
    const voucherNumber = `${voucherData.voucher_type.toUpperCase()}-${timestamp}`
    
    console.log('Generated voucher number:', voucherNumber)

    // If supplier is selected, get supplier account mappings
    let supplierAccountMappings = null
    if (voucherData.supplier_id) {
      try {
        const { SupplierServiceAdmin } = await import('./supplier-service-admin')
        supplierAccountMappings = await SupplierServiceAdmin.getSupplierAccountMappings(voucherData.supplier_id)
      } catch (error) {
        console.warn('Could not load supplier account mappings:', error)
      }
    }

    // Create voucher
    console.log('Creating voucher with data:', {
      organization_id: organizationId,
      voucher_number: voucherNumber,
      voucher_type: voucherData.voucher_type,
      status: 'draft',
      requested_by: userId,
      total_estimated_cost: voucherData.lines.reduce((sum, line) => 
        sum + (line.quantity_requested * (line.unit_cost_estimated || 0)), 0
      )
    })

    const { data: voucher, error: voucherError } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .insert({
        organization_id: organizationId,
        voucher_number: voucherNumber,
        voucher_type: voucherData.voucher_type,
        status: 'draft',
        requested_by: userId,
        requested_date: new Date().toISOString().split('T')[0],
        
        // Purchase fields
        vendor_name: voucherData.vendor_name,
        vendor_contact: voucherData.vendor_contact,
        purchase_order_number: voucherData.purchase_order_number,
        expected_delivery_date: voucherData.expected_delivery_date,
        
        // Issuance fields
        purpose: voucherData.purpose,
        destination: voucherData.destination,
        cost_center: voucherData.cost_center,
        project_code: voucherData.project_code,
        destination_account_id: voucherData.destination_account_id,
        
        // Payment details
        payment_type: voucherData.payment_type,
        payment_account_id: voucherData.payment_account_id,
        deposit_amount: voucherData.deposit_amount || 0,
        payment_reference: voucherData.payment_reference,
        
        // Common fields
        description: voucherData.description,
        notes: voucherData.notes,
        total_estimated_cost: voucherData.lines.reduce((sum, line) => 
          sum + (line.quantity_requested * (line.unit_cost_estimated || 0)), 0
        )
      })
      .select()
      .single()

    console.log('Voucher creation result:', { voucher, voucherError })

    if (voucherError) {
      console.error('Error creating voucher:', voucherError)
      throw new Error(`Failed to create voucher: ${voucherError.message}`)
    }

    // Create voucher lines
    if (voucherData.lines.length > 0) {
      const linesData = voucherData.lines.map((line, index) => ({
        voucher_id: voucher.id,
        line_number: index + 1,
        item_id: line.item_id,
        quantity_requested: line.quantity_requested,
        unit_cost_estimated: line.unit_cost_estimated,
        notes: line.notes
      }))

      console.log('Lines data to insert:', linesData)

      const { error: linesError } = await getSupabaseAdmin()
        .from('inventory_voucher_lines')
        .insert(linesData)

      console.log('Lines creation result:', { linesError })

      if (linesError) {
        console.error('Error creating voucher lines:', linesError)
        throw new Error(`Failed to create voucher lines: ${linesError.message}`)
      }
    }

    // Return the created voucher with relations
    console.log('Voucher created successfully, fetching full details for ID:', voucher.id)
    const fullVoucher = await this.getVoucher(voucher.id)
    console.log('Full voucher details:', fullVoucher)
    if (!fullVoucher) {
      throw new Error('Failed to load created voucher')
    }
    return fullVoucher
  }

  static async updateVoucher(id: number, voucherData: Partial<VoucherFormData>): Promise<InventoryVoucher> {
    const { data, error } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .update({
        ...voucherData,
        total_estimated_cost: voucherData.lines ? 
          voucherData.lines.reduce((sum, line) => 
            sum + (line.quantity_requested * (line.unit_cost_estimated || 0)), 0
          ) : undefined,
        updated_at: new Date().toISOString()
      })
      .eq('id', id)
      .select()
      .single()

    if (error) {
      console.error('Error updating voucher:', error)
      throw new Error('Failed to update voucher')
    }

    // Update lines if provided
    if (voucherData.lines) {
      // Delete existing lines
      await getSupabaseAdmin()
        .from('inventory_voucher_lines')
        .delete()
        .eq('voucher_id', id)

      // Insert new lines
      if (voucherData.lines.length > 0) {
        const linesData = voucherData.lines.map((line, index) => ({
          voucher_id: id,
          line_number: index + 1,
          item_id: line.item_id,
          quantity_requested: line.quantity_requested,
          unit_cost_estimated: line.unit_cost_estimated,
          notes: line.notes
        }))

        const { error: linesError } = await getSupabaseAdmin()
          .from('inventory_voucher_lines')
          .insert(linesData)

        if (linesError) {
          console.error('Error updating voucher lines:', linesError)
          throw new Error('Failed to update voucher lines')
        }
      }
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async deleteVoucher(id: number): Promise<void> {
    const { error } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .delete()
      .eq('id', id)

    if (error) {
      console.error('Error deleting voucher:', error)
      throw new Error('Failed to delete voucher')
    }
  }

  // ===============================================
  // VOUCHER WORKFLOW OPERATIONS
  // ===============================================

  static async submitForApproval(id: number, organizationId: string): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    if (!organizationId) throw new Error('Organization ID is required')

    // Find an approver (accountant or organization_owner)
    let approverId = null
    
    // First try to find an accountant
    const { data: accountant, error: accountantError } = await getSupabaseAdmin()
      .from('organization_members')
      .select('user_id')
      .eq('organization_id', organizationId)
      .eq('role', 'accountant')
      .eq('is_active', true)
      .limit(1)
      .single()

    if (accountant && !accountantError) {
      approverId = accountant.user_id
    } else {
      // If no accountant, try to find organization owner
      const { data: owner, error: ownerError } = await getSupabaseAdmin()
        .from('organization_members')
        .select('user_id')
        .eq('organization_id', organizationId)
        .eq('role', 'organization_owner')
        .eq('is_active', true)
        .limit(1)
        .single()

      if (owner && !ownerError) {
        approverId = owner.user_id
      }
    }

    // If still no approver found, proceed without one (system will handle it later)
    console.log('Approver assigned:', approverId || 'No approver found - will be handled by system')

    // Set approval deadline (48 hours from now)
    const deadline = new Date()
    deadline.setHours(deadline.getHours() + 48)

    const updateData: any = {
      status: 'pending_finance',
      submitted_at: new Date().toISOString(),
      approval_deadline: deadline.toISOString(),
      updated_at: new Date().toISOString()
    }

    // Add approver if found
    if (approverId) {
      updateData.finance_approved_by = approverId
    }

    // First check if the voucher exists
    const { data: existingVoucher, error: fetchError } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .select('id, status')
      .eq('id', id)
      .single()

    console.log('Existing voucher check:', { existingVoucher, fetchError })

    if (fetchError) {
      console.error('Error fetching voucher:', fetchError)
      console.error('This might mean the inventory_vouchers table does not exist yet')
      console.error('Please run the database setup script: python backend/setup_voucher_system.py')
      throw new Error(`Voucher not found: ${fetchError.message}. The voucher system may not be set up yet.`)
    }

    if (!existingVoucher) {
      throw new Error('Voucher not found')
    }

    console.log('Updating voucher with ID:', id)
    console.log('Update data:', updateData)

    const { data, error } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .update(updateData)
      .eq('id', id)
      .select()
      .single()

    console.log('Update result:', { data, error })

    if (error) {
      console.error('Error submitting voucher for approval:', error)
      console.error('Error details:', JSON.stringify(error, null, 2))
      console.error('Update data that failed:', updateData)
      throw new Error(`Failed to submit voucher for approval: ${error.message || 'Unknown error'}`)
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async approveVoucher(id: number, notes?: string): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    // Update voucher status
    const { data, error } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .update({
        status: 'approved',
        finance_approved_by: acting,
        finance_approved_at: new Date().toISOString(),
        finance_approval_notes: notes,
        updated_at: new Date().toISOString()
      })
      .eq('id', id)
      .select()
      .single()

    if (error) {
      console.error('Error approving voucher:', error)
      throw new Error('Failed to approve voucher')
    }

    // Log approval
    await getSupabaseAdmin()
      .from('voucher_approvals')
      .insert({
        voucher_id: id,
        approver_id: acting,
        action: 'approved',
        comments: notes
      })

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async rejectVoucher(id: number, reason: string): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    // Update voucher status
    const { data, error } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .update({
        status: 'rejected',
        rejected_by: acting,
        rejected_at: new Date().toISOString(),
        rejection_reason: reason,
        updated_at: new Date().toISOString()
      })
      .eq('id', id)
      .select()
      .single()

    if (error) {
      console.error('Error rejecting voucher:', error)
      throw new Error('Failed to reject voucher')
    }

    // Log rejection
    await getSupabaseAdmin()
      .from('voucher_approvals')
      .insert({
        voucher_id: id,
        approver_id: acting,
        action: 'rejected',
        comments: reason
      })

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async renewExpiredVoucher(id: number, reason: string): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    const { data, error } = await getSupabaseAdmin().rpc('renew_expired_voucher', {
      voucher_id: id,
      renewed_by: acting,
      renewal_reason: reason
    })

    if (error) {
      console.error('Error renewing voucher:', error)
      throw new Error('Failed to renew voucher')
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  // ===============================================
  // VOUCHER EXECUTION OPERATIONS
  // ===============================================

  static async executeVoucher(id: number, actualQuantities: { [lineId: number]: number }): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    // Get voucher details
    const voucher = await this.getVoucher(id)
    if (!voucher) throw new Error('Voucher not found')

    // Update voucher status
    const newStatus = voucher.voucher_type === 'purchase' ? 'receiving' : 'issuing'
    
    const { error: voucherError } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .update({
        status: newStatus,
        executed_by: acting,
        executed_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .eq('id', id)

    if (voucherError) {
      console.error('Error executing voucher:', voucherError)
      throw new Error('Failed to execute voucher')
    }

    // Update line quantities
    for (const [lineId, quantity] of Object.entries(actualQuantities)) {
      await getSupabaseAdmin()
        .from('inventory_voucher_lines')
        .update({
          quantity_actual: quantity
        })
        .eq('id', parseInt(lineId))
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async postVoucher(id: number): Promise<InventoryVoucher> {
    // This would integrate with your journal entry system
    // For now, just update the status
    const { error } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .update({
        status: 'posted',
        updated_at: new Date().toISOString()
      })
      .eq('id', id)

    if (error) {
      console.error('Error posting voucher:', error)
      throw new Error('Failed to post voucher')
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async completeVoucher(id: number): Promise<InventoryVoucher> {
    const { error } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .update({
        status: 'completed',
        updated_at: new Date().toISOString()
      })
      .eq('id', id)

    if (error) {
      console.error('Error completing voucher:', error)
      throw new Error('Failed to complete voucher')
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  // ===============================================
  // VOUCHER STATISTICS
  // ===============================================

  static async getVoucherStats(organizationId: string): Promise<VoucherStats> {
    const { data, error } = await getSupabaseAdmin()
      .from('inventory_vouchers')
      .select('status, total_estimated_cost, submitted_at, finance_approved_at')
      .eq('organization_id', organizationId)

    if (error) {
      console.error('Error fetching voucher stats:', error)
      throw new Error('Failed to fetch voucher stats')
    }

    const stats = {
      total_vouchers: data.length,
      pending_approval: data.filter(v => v.status === 'pending_finance').length,
      approved: data.filter(v => v.status === 'approved').length,
      rejected: data.filter(v => v.status === 'rejected').length,
      expired: data.filter(v => v.status === 'expired').length,
      completed: data.filter(v => v.status === 'completed').length,
      total_value: data.reduce((sum, v) => sum + (v.total_estimated_cost || 0), 0),
      average_approval_time_hours: 0,
      approval_rate_percent: 0
    }

    // Calculate approval rate
    const totalSubmitted = data.filter(v => v.status !== 'draft').length
    const totalApproved = data.filter(v => v.status === 'approved' || v.status === 'completed').length
    stats.approval_rate_percent = totalSubmitted > 0 ? (totalApproved / totalSubmitted) * 100 : 0

    // Calculate average approval time
    const approvedVouchers = data.filter(v => v.status === 'approved' && v.submitted_at && v.finance_approved_at)
    if (approvedVouchers.length > 0) {
      const totalHours = approvedVouchers.reduce((sum, v) => {
        const submitted = new Date(v.submitted_at!)
        const approved = new Date(v.finance_approved_at!)
        return sum + (approved.getTime() - submitted.getTime()) / (1000 * 60 * 60)
      }, 0)
      stats.average_approval_time_hours = totalHours / approvedVouchers.length
    }

    return stats
  }

  static async getApprovalStats(organizationId: string, userId: string): Promise<VoucherApprovalStats> {
    const { data, error } = await getSupabaseAdmin()
      .from('voucher_approvals')
      .select(`
        action,
        created_at,
        voucher:inventory_vouchers(total_estimated_cost, submitted_at)
      `)
      .eq('approver_id', userId)
      .eq('voucher.organization_id', organizationId)

    if (error) {
      console.error('Error fetching approval stats:', error)
      throw new Error('Failed to fetch approval stats')
    }

    const voucherCost = (row: (typeof data)[number]) => {
      const v = row.voucher as
        | { total_estimated_cost?: number }
        | { total_estimated_cost?: number }[]
        | null
        | undefined
      const x = Array.isArray(v) ? v[0] : v
      return x?.total_estimated_cost ?? 0
    }

    const approved = data.filter((a) => a.action === 'approved')
    const rejected = data.filter((a) => a.action === 'rejected')
    const largeAmounts = approved.filter((a) => voucherCost(a) > 10000)

    return {
      total_approved: approved.length,
      total_rejected: rejected.length,
      average_time_hours: 0, // Calculate from submitted_at to approved_at
      total_value: approved.reduce((sum, a) => sum + voucherCost(a), 0),
      pending: 0, // Get from pending vouchers
      fastest_approval_minutes: 0,
      large_amounts_count: largeAmounts.length,
      average_large_amount:
        largeAmounts.length > 0 ? largeAmounts.reduce((sum, a) => sum + voucherCost(a), 0) / largeAmounts.length : 0,
    }
  }

  // ===============================================
  // VOUCHER EXPIRATION
  // ===============================================

  static async expireOverdueVouchers(): Promise<number> {
    const { data, error } = await getSupabaseAdmin().rpc('expire_overdue_vouchers')

    if (error) {
      console.error('Error expiring vouchers:', error)
      throw new Error('Failed to expire overdue vouchers')
    }

    return data || 0
  }

  static async getExpiredVouchers(organizationId: string): Promise<InventoryVoucher[]> {
    return this.getVouchers(organizationId, { status: ['expired'] })
  }

  // ===============================================
  // VOUCHER ATTACHMENTS
  // ===============================================

  static async uploadAttachment(
    voucherId: number, 
    file: File, 
    description?: string
  ): Promise<VoucherAttachment> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')

    // Upload file to storage
    const fileName = `${voucherId}/${Date.now()}-${file.name}`
    const { data: uploadData, error: uploadError } = await getSupabaseAdmin().storage
      .from('voucher-attachments')
      .upload(fileName, file)

    if (uploadError) {
      console.error('Error uploading file:', uploadError)
      throw new Error('Failed to upload file')
    }

    // Create attachment record
    const { data, error } = await getSupabaseAdmin()
      .from('voucher_attachments')
      .insert({
        voucher_id: voucherId,
        file_name: file.name,
        file_path: uploadData.path,
        file_type: file.type,
        file_size: file.size,
        description,
        uploaded_by: acting
      })
      .select()
      .single()

    if (error) {
      console.error('Error creating attachment record:', error)
      throw new Error('Failed to create attachment record')
    }

    return data
  }

  static async deleteAttachment(attachmentId: number): Promise<void> {
    // Get attachment details
    const { data: attachment } = await getSupabaseAdmin()
      .from('voucher_attachments')
      .select('file_path')
      .eq('id', attachmentId)
      .single()

    if (attachment) {
      // Delete from storage
      await getSupabaseAdmin().storage
        .from('voucher-attachments')
        .remove([attachment.file_path])
    }

    // Delete from database
    const { error } = await getSupabaseAdmin()
      .from('voucher_attachments')
      .delete()
      .eq('id', attachmentId)

    if (error) {
      console.error('Error deleting attachment:', error)
      throw new Error('Failed to delete attachment')
    }
  }
}
