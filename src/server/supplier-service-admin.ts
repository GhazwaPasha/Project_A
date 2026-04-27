import { getSql } from '@/server/pg'
import { getActingUserId } from '@/server/request-context'
import {
  Account,
  Supplier,
  SupplierAccountMappings,
  SupplierContact,
  SupplierFilters,
  SupplierFormData
} from '@/types'

type Pg = ReturnType<typeof getSql>

async function accountMapByIds(sql: Pg, ids: number[]): Promise<Map<number, Account>> {
  const u = Array.from(new Set(ids.filter((x) => x > 0)))
  if (u.length === 0) return new Map()
  const rows = (await sql<Account[]>`
    SELECT * FROM public.accounts
    WHERE id = ANY(${u}::bigint[])
  `) as Account[]
  return new Map(rows.map((a) => [a.id, a]))
}

function withMappingAccounts(
  m: SupplierAccountMappings,
  byId: Map<number, Account>
): SupplierAccountMappings {
  return {
    ...m,
    payable_account: m.payable_account_id ? byId.get(m.payable_account_id) : undefined,
    cash_account: m.cash_account_id ? byId.get(m.cash_account_id) : undefined,
    expense_account: m.expense_account_id ? byId.get(m.expense_account_id) : undefined,
    inventory_account: m.inventory_account_id ? byId.get(m.inventory_account_id) : undefined,
    freight_account: m.freight_account_id ? byId.get(m.freight_account_id) : undefined,
    tax_account: m.tax_account_id ? byId.get(m.tax_account_id) : undefined,
    discount_account: m.discount_account_id ? byId.get(m.discount_account_id) : undefined
  }
}

/** Collect all account id references from a mapping row for batch loading. */
function mappingAccountIds(m: SupplierAccountMappings): number[] {
  return [
    m.payable_account_id,
    m.cash_account_id,
    m.expense_account_id,
    m.inventory_account_id,
    m.freight_account_id,
    m.tax_account_id,
    m.discount_account_id
  ].filter((x): x is number => x != null && x > 0)
}

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
    const sql = getSql()
    const search = filters?.search?.trim()
    const take = limit
    const off = offset
    const usePage = take != null || (off != null && off > 0)
    const lim = usePage ? (take ?? 50) : null
    const o = off != null && off > 0 ? off : 0

    const rows = (await sql<Supplier[]>`
      SELECT s.*
      FROM public.suppliers s
      WHERE s.organization_id = ${organizationId}::uuid
        AND ${filters?.status?.length
          ? sql` s.status = ANY(${filters.status}::text[]) `
          : sql` true `}
        AND ${filters?.is_preferred !== undefined
          ? sql` s.is_preferred = ${filters.is_preferred} `
          : sql` true `}
        AND ${filters?.payment_terms?.length
          ? sql` s.payment_terms = ANY(${filters.payment_terms}::text[]) `
          : sql` true `}
        AND ${
          search
            ? sql` (
          s.name ILIKE ${`%${search}%`}
          OR s.supplier_code ILIKE ${`%${search}%`}
          OR COALESCE(s.legal_name, '') ILIKE ${`%${search}%`}
          OR COALESCE(s.contact_person, '') ILIKE ${`%${search}%`}
          OR COALESCE(s.email, '') ILIKE ${`%${search}%`}
        ) `
            : sql` true `
        }
      ORDER BY s.name ASC
      ${
        usePage && lim != null
          ? sql` LIMIT ${lim} OFFSET ${o} `
          : sql``
      }
    `) as Supplier[]

    if (rows.length === 0) return []

    const sids = rows.map((r) => r.id)
    const allMappings = (await sql<SupplierAccountMappings[]>`
      SELECT m.*
      FROM public.supplier_account_mappings m
      WHERE m.supplier_id = ANY(${sids}::bigint[])
    `) as SupplierAccountMappings[]
    const mByS = new Map<number, SupplierAccountMappings>()
    for (const m of allMappings) {
      if (!mByS.has(m.supplier_id)) mByS.set(m.supplier_id, m)
    }
    const allContacts = (await sql<SupplierContact[]>`
      SELECT c.* FROM public.supplier_contacts c
      WHERE c.supplier_id = ANY(${sids}::bigint[])
      ORDER BY c.is_primary DESC, c.name ASC
    `) as SupplierContact[]
    const cByS = new Map<number, SupplierContact[]>()
    for (const c of allContacts) {
      const a = cByS.get(c.supplier_id) ?? []
      a.push(c)
      cByS.set(c.supplier_id, a)
    }
    const allMIds = allMappings.flatMap((m) => mappingAccountIds(m))
    const accs = await accountMapByIds(sql, allMIds)
    return rows.map((s) => {
      const m = mByS.get(s.id)
      return {
        ...s,
        account_mappings: m ? withMappingAccounts(m, accs) : undefined,
        contacts: cByS.get(s.id) ?? []
      } as Supplier
    })
  }

  static async getSupplier(id: number): Promise<Supplier | null> {
    const sql = getSql()
    const rows = (await sql<Supplier[]>`
      SELECT s.* FROM public.suppliers s
      WHERE s.id = ${id}
      LIMIT 1
    `) as Supplier[]
    const s = rows[0]
    if (!s) return null

    const mRows = (await sql<SupplierAccountMappings[]>`
      SELECT m.* FROM public.supplier_account_mappings m
      WHERE m.supplier_id = ${id}
      LIMIT 1
    `) as SupplierAccountMappings[]
    const m = mRows[0] ?? null
    const cRows = (await sql<SupplierContact[]>`
      SELECT c.* FROM public.supplier_contacts c
      WHERE c.supplier_id = ${id}
      ORDER BY c.is_primary DESC, c.name ASC
    `) as SupplierContact[]

    if (!m) {
      return { ...s, account_mappings: undefined, contacts: cRows } as Supplier
    }
    const accs = await accountMapByIds(sql, mappingAccountIds(m))
    return {
      ...s,
      account_mappings: withMappingAccounts(m, accs),
      contacts: cRows
    } as Supplier
  }

  static async createSupplier(supplierData: SupplierFormData, organizationId: string): Promise<Supplier> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    if (!organizationId) throw new Error('Organization ID is required')

    const sql = getSql()
    let supplierCode = supplierData.supplier_code
    if (!supplierCode) {
      const last = (await sql<{ supplier_code: string }[]>`
        SELECT supplier_code FROM public.suppliers
        WHERE organization_id = ${organizationId}::uuid
        ORDER BY supplier_code DESC
        LIMIT 1
      `) as { supplier_code: string }[]

      if (last[0]) {
        const n = parseInt(String(last[0].supplier_code).split('-')[1] ?? '0', 10) || 0
        supplierCode = `SUP-${String(n + 1).padStart(3, '0')}`
      } else {
        supplierCode = 'SUP-001'
      }
    }

    const supRows = (await sql<Supplier[]>`
      INSERT INTO public.suppliers (
        organization_id, supplier_code, name, legal_name, description,
        contact_person, email, phone, fax, website,
        billing_address_line1, billing_address_line2, billing_city, billing_state, billing_postal_code, billing_country,
        shipping_address_line1, shipping_address_line2, shipping_city, shipping_state, shipping_postal_code, shipping_country,
        tax_id, registration_number, currency,
        payment_terms, credit_limit, status, is_preferred, notes, created_by
      ) VALUES (
        ${organizationId}::uuid,
        ${supplierCode},
        ${supplierData.name},
        ${supplierData.legal_name ?? null},
        ${supplierData.description ?? null},
        ${supplierData.contact_person ?? null},
        ${supplierData.email ?? null},
        ${supplierData.phone ?? null},
        ${supplierData.fax ?? null},
        ${supplierData.website ?? null},
        ${supplierData.billing_address_line1 ?? null},
        ${supplierData.billing_address_line2 ?? null},
        ${supplierData.billing_city ?? null},
        ${supplierData.billing_state ?? null},
        ${supplierData.billing_postal_code ?? null},
        ${supplierData.billing_country ?? null},
        ${supplierData.shipping_address_line1 ?? null},
        ${supplierData.shipping_address_line2 ?? null},
        ${supplierData.shipping_city ?? null},
        ${supplierData.shipping_state ?? null},
        ${supplierData.shipping_postal_code ?? null},
        ${supplierData.shipping_country ?? null},
        ${supplierData.tax_id ?? null},
        ${supplierData.registration_number ?? null},
        ${supplierData.currency}::text,
        ${supplierData.payment_terms}::text,
        ${supplierData.credit_limit},
        ${supplierData.status}::text,
        ${supplierData.is_preferred},
        ${supplierData.notes ?? null},
        ${acting}::uuid
      )
      RETURNING *
    `) as Supplier[]

    const supplier = supRows[0]
    if (!supplier) {
      throw new Error('Failed to create supplier')
    }

    if (supplierData.account_mappings) {
      await sql`
        INSERT INTO public.supplier_account_mappings (
          supplier_id, organization_id,
          payable_account_id, cash_account_id, expense_account_id, inventory_account_id,
          freight_account_id, tax_account_id, discount_account_id, created_by
        ) VALUES (
          ${supplier.id},
          ${organizationId}::uuid,
          ${supplierData.account_mappings.payable_account_id},
          ${supplierData.account_mappings.cash_account_id ?? null},
          ${supplierData.account_mappings.expense_account_id ?? null},
          ${supplierData.account_mappings.inventory_account_id ?? null},
          ${supplierData.account_mappings.freight_account_id ?? null},
          ${supplierData.account_mappings.tax_account_id ?? null},
          ${supplierData.account_mappings.discount_account_id ?? null},
          ${acting}::uuid
        )
      `
    }

    if (supplierData.contacts?.length) {
      for (const contact of supplierData.contacts) {
        await sql`
          INSERT INTO public.supplier_contacts (
            supplier_id, name, title, email, phone, mobile, fax,
            is_primary, is_billing, is_shipping, is_technical, created_by
          ) VALUES (
            ${supplier.id},
            ${contact.name},
            ${contact.title ?? null},
            ${contact.email ?? null},
            ${contact.phone ?? null},
            ${contact.mobile ?? null},
            ${contact.fax ?? null},
            ${contact.is_primary},
            ${contact.is_billing},
            ${contact.is_shipping},
            ${contact.is_technical},
            ${acting}::uuid
          )
        `
      }
    }

    return (await this.getSupplier(supplier.id)) as Supplier
  }

  static async updateSupplier(id: number, supplierData: Partial<SupplierFormData>): Promise<Supplier> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    const { account_mappings, contacts, ...up } = supplierData
    if (Object.keys(up).length > 0) {
      const cur = (await sql<Supplier[]>`
        SELECT * FROM public.suppliers WHERE id = ${id} LIMIT 1
      `) as Supplier[]

      if (!cur[0]) {
        throw new Error('Failed to update supplier: not found')
      }
      const merged: Record<string, unknown> = { ...(cur[0] as unknown as Record<string, unknown>) }
      for (const key of Object.keys(supplierData) as (keyof SupplierFormData)[]) {
        if (key === 'account_mappings' || key === 'contacts') {
          continue
        }
        if (Object.prototype.hasOwnProperty.call(supplierData, key)) {
          merged[key as string] = (supplierData as Record<string, unknown>)[key as string]
        }
      }
      const m = (k: string) => merged[k]
      await sql`
        UPDATE public.suppliers
        SET
          supplier_code = ${String(m('supplier_code'))},
          name = ${String(m('name'))},
          legal_name = ${(m('legal_name') as string | null) ?? null},
          description = ${(m('description') as string | null) ?? null},
          contact_person = ${(m('contact_person') as string | null) ?? null},
          email = ${(m('email') as string | null) ?? null},
          phone = ${(m('phone') as string | null) ?? null},
          fax = ${(m('fax') as string | null) ?? null},
          website = ${(m('website') as string | null) ?? null},
          billing_address_line1 = ${(m('billing_address_line1') as string | null) ?? null},
          billing_address_line2 = ${(m('billing_address_line2') as string | null) ?? null},
          billing_city = ${(m('billing_city') as string | null) ?? null},
          billing_state = ${(m('billing_state') as string | null) ?? null},
          billing_postal_code = ${(m('billing_postal_code') as string | null) ?? null},
          billing_country = ${(m('billing_country') as string | null) ?? null},
          shipping_address_line1 = ${(m('shipping_address_line1') as string | null) ?? null},
          shipping_address_line2 = ${(m('shipping_address_line2') as string | null) ?? null},
          shipping_city = ${(m('shipping_city') as string | null) ?? null},
          shipping_state = ${(m('shipping_state') as string | null) ?? null},
          shipping_postal_code = ${(m('shipping_postal_code') as string | null) ?? null},
          shipping_country = ${(m('shipping_country') as string | null) ?? null},
          tax_id = ${(m('tax_id') as string | null) ?? null},
          registration_number = ${(m('registration_number') as string | null) ?? null},
          currency = ${String(m('currency') ?? 'USD')}::text,
          payment_terms = ${String(m('payment_terms') ?? 'net_30')}::text,
          credit_limit = ${
            m('credit_limit') == null
              ? null
              : Number(m('credit_limit'))
          }::double precision,
          status = ${String(m('status') ?? 'active')}::text,
          is_preferred = ${m('is_preferred') === true},
          notes = ${(m('notes') as string | null) ?? null},
          updated_by = ${acting}::uuid,
          updated_at = now()
        WHERE id = ${id}
      `
    }

    if (account_mappings) {
      const existing = (await sql<{ c: string }[]>`
        SELECT 1 as c FROM public.supplier_account_mappings
        WHERE supplier_id = ${id} LIMIT 1
      `)
      if (existing.length) {
        await sql`
          UPDATE public.supplier_account_mappings
          SET
            payable_account_id = ${account_mappings.payable_account_id},
            cash_account_id = ${account_mappings.cash_account_id ?? null},
            expense_account_id = ${account_mappings.expense_account_id ?? null},
            inventory_account_id = ${account_mappings.inventory_account_id ?? null},
            freight_account_id = ${account_mappings.freight_account_id ?? null},
            tax_account_id = ${account_mappings.tax_account_id ?? null},
            discount_account_id = ${account_mappings.discount_account_id ?? null},
            updated_by = ${acting}::uuid,
            updated_at = now()
          WHERE supplier_id = ${id}
        `
      } else {
        const org = (await sql<{ organization_id: string }[]>`
          SELECT organization_id::text as organization_id FROM public.suppliers WHERE id = ${id} LIMIT 1
        `)[0]
        if (org) {
          await sql`
            INSERT INTO public.supplier_account_mappings (
              supplier_id, organization_id,
              payable_account_id, cash_account_id, expense_account_id, inventory_account_id,
              freight_account_id, tax_account_id, discount_account_id, created_by
            ) VALUES (
              ${id},
              ${org.organization_id}::uuid,
              ${account_mappings.payable_account_id},
              ${account_mappings.cash_account_id ?? null},
              ${account_mappings.expense_account_id ?? null},
              ${account_mappings.inventory_account_id ?? null},
              ${account_mappings.freight_account_id ?? null},
              ${account_mappings.tax_account_id ?? null},
              ${account_mappings.discount_account_id ?? null},
              ${acting}::uuid
            )
          `
        }
      }
    }

    if (contacts !== undefined) {
      await sql`DELETE FROM public.supplier_contacts WHERE supplier_id = ${id}`
      for (const contact of contacts) {
        await sql`
          INSERT INTO public.supplier_contacts (
            supplier_id, name, title, email, phone, mobile, fax,
            is_primary, is_billing, is_shipping, is_technical, created_by
          ) VALUES (
            ${id},
            ${contact.name},
            ${contact.title ?? null},
            ${contact.email ?? null},
            ${contact.phone ?? null},
            ${contact.mobile ?? null},
            ${contact.fax ?? null},
            ${contact.is_primary},
            ${contact.is_billing},
            ${contact.is_shipping},
            ${contact.is_technical},
            ${acting}::uuid
          )
        `
      }
    }

    return (await this.getSupplier(id)) as Supplier
  }

  static async deleteSupplier(id: number): Promise<void> {
    const sql = getSql()
    await sql`DELETE FROM public.suppliers WHERE id = ${id}`
  }

  // ===============================================
  // SUPPLIER ACCOUNT MAPPINGS
  // ===============================================

  static async getSupplierAccountMappings(supplierId: number): Promise<SupplierAccountMappings | null> {
    const sql = getSql()
    const mRows = (await sql<SupplierAccountMappings[]>`
      SELECT m.* FROM public.supplier_account_mappings m
      WHERE m.supplier_id = ${supplierId}
      LIMIT 1
    `) as SupplierAccountMappings[]

    const m = mRows[0] ?? null
    if (!m) return null
    const accs = await accountMapByIds(sql, mappingAccountIds(m))
    return withMappingAccounts(m, accs)
  }

  static async updateSupplierAccountMappings(
    supplierId: number,
    mappings: Partial<SupplierAccountMappings>
  ): Promise<SupplierAccountMappings> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    const rows = (await sql<SupplierAccountMappings[]>`
      UPDATE public.supplier_account_mappings
      SET
        payable_account_id = COALESCE(
          ${mappings.payable_account_id != null
            ? sql`${mappings.payable_account_id}`
            : sql`NULL`}::bigint,
          payable_account_id
        ),
        cash_account_id = ${
          mappings.cash_account_id === undefined
            ? sql`cash_account_id`
            : sql`${mappings.cash_account_id}`
        },
        expense_account_id = ${
          mappings.expense_account_id === undefined
            ? sql`expense_account_id`
            : sql`${mappings.expense_account_id}`
        },
        inventory_account_id = ${
          mappings.inventory_account_id === undefined
            ? sql`inventory_account_id`
            : sql`${mappings.inventory_account_id}`
        },
        freight_account_id = ${
          mappings.freight_account_id === undefined
            ? sql`freight_account_id`
            : sql`${mappings.freight_account_id}`
        },
        tax_account_id = ${
          mappings.tax_account_id === undefined ? sql`tax_account_id` : sql`${mappings.tax_account_id}`
        },
        discount_account_id = ${
          mappings.discount_account_id === undefined
            ? sql`discount_account_id`
            : sql`${mappings.discount_account_id}`
        },
        updated_by = ${acting}::uuid,
        updated_at = now()
      WHERE supplier_id = ${supplierId}
      RETURNING *
    `) as SupplierAccountMappings[]

    const out = rows[0]
    if (!out) {
      throw new Error('Failed to update supplier account mappings')
    }
    const accs = await accountMapByIds(sql, mappingAccountIds(out))
    return withMappingAccounts(out, accs)
  }

  // ===============================================
  // SUPPLIER CONTACTS
  // ===============================================

  static async getSupplierContacts(supplierId: number): Promise<SupplierContact[]> {
    const sql = getSql()
    return (await sql<SupplierContact[]>`
      SELECT * FROM public.supplier_contacts
      WHERE supplier_id = ${supplierId}
      ORDER BY is_primary DESC, name ASC
    `) as SupplierContact[]
  }

  static async addSupplierContact(
    contactData: Omit<SupplierContact, 'id' | 'created_at' | 'updated_at'>
  ): Promise<SupplierContact> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    const rows = (await sql<SupplierContact[]>`
      INSERT INTO public.supplier_contacts (
        supplier_id, name, title, email, phone, mobile, fax,
        is_primary, is_billing, is_shipping, is_technical, created_by
      ) VALUES (
        ${contactData.supplier_id},
        ${contactData.name},
        ${contactData.title ?? null},
        ${contactData.email ?? null},
        ${contactData.phone ?? null},
        ${contactData.mobile ?? null},
        ${contactData.fax ?? null},
        ${contactData.is_primary},
        ${contactData.is_billing},
        ${contactData.is_shipping},
        ${contactData.is_technical},
        ${acting}::uuid
      )
      RETURNING *
    `) as SupplierContact[]

    const row = rows[0]
    if (!row) throw new Error('Failed to add supplier contact')
    return row
  }

  static async updateSupplierContact(id: number, contactData: Partial<SupplierContact>): Promise<SupplierContact> {
    const sql = getSql()
    const c = contactData
    const rows = (await sql<SupplierContact[]>`
      UPDATE public.supplier_contacts
      SET
        name = COALESCE(${c.name ?? null}, name),
        title = ${c.title === undefined ? null : c.title},
        email = ${c.email === undefined ? null : c.email},
        phone = ${c.phone === undefined ? null : c.phone},
        mobile = ${c.mobile === undefined ? null : c.mobile},
        fax = ${c.fax === undefined ? null : c.fax},
        is_primary = COALESCE(${c.is_primary ?? null}, is_primary),
        is_billing = COALESCE(${c.is_billing ?? null}, is_billing),
        is_shipping = COALESCE(${c.is_shipping ?? null}, is_shipping),
        is_technical = COALESCE(${c.is_technical ?? null}, is_technical),
        updated_at = now()
      WHERE id = ${id}
      RETURNING *
    `) as SupplierContact[]

    const row = rows[0]
    if (!row) throw new Error('Failed to update supplier contact')
    return row
  }

  static async deleteSupplierContact(id: number): Promise<void> {
    const sql = getSql()
    await sql`DELETE FROM public.supplier_contacts WHERE id = ${id}`
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
    const sql = getSql()
    const data = (await sql<
      { status: string; is_preferred: boolean; credit_limit: number | null; current_balance: number | null }[]
    >`
      SELECT status, is_preferred, credit_limit, current_balance
      FROM public.suppliers
      WHERE organization_id = ${organizationId}::uuid
    `) as {
      status: string
      is_preferred: boolean
      credit_limit: number | null
      current_balance: number | null
    }[]

    return {
      total_suppliers: data.length,
      active_suppliers: data.filter((s) => s.status === 'active').length,
      inactive_suppliers: data.filter((s) => s.status === 'inactive').length,
      preferred_suppliers: data.filter((s) => s.is_preferred).length,
      total_credit_limit: data.reduce((sum, s) => sum + (s.credit_limit || 0), 0),
      total_current_balance: data.reduce((sum, s) => sum + (s.current_balance || 0), 0)
    }
  }

  // ===============================================
  // VOUCHER INTEGRATION
  // ===============================================

  static async getSupplierForVoucher(
    supplierId: number
  ): Promise<{
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

  static async getSuppliersForVoucher(organizationId: string): Promise<
    Array<{
      id: number
      supplier_code: string
      name: string
      payable_account_id: number
      cash_account_id?: number
      expense_account_id?: number
    }>
  > {
    const sql = getSql()
    const data = (await sql<
      {
        id: number
        supplier_code: string
        name: string
        payable_account_id: number | null
        cash_account_id: number | null
        expense_account_id: number | null
      }[]
    >`
      SELECT
        s.id,
        s.supplier_code,
        s.name,
        m.payable_account_id,
        m.cash_account_id,
        m.expense_account_id
      FROM public.suppliers s
      LEFT JOIN public.supplier_account_mappings m ON m.supplier_id = s.id
      WHERE s.organization_id = ${organizationId}::uuid
        AND s.status = 'active'
      ORDER BY s.name ASC
    `) as {
      id: number
      supplier_code: string
      name: string
      payable_account_id: number | null
      cash_account_id: number | null
      expense_account_id: number | null
    }[]

    return data.map((r) => ({
      id: r.id,
      supplier_code: r.supplier_code,
      name: r.name,
      payable_account_id: r.payable_account_id != null ? Number(r.payable_account_id) : 0,
      cash_account_id: r.cash_account_id != null ? Number(r.cash_account_id) : undefined,
      expense_account_id: r.expense_account_id != null ? Number(r.expense_account_id) : undefined
    }))
  }
}
