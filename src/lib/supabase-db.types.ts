/** Supabase-js `Database` shape for **server-only** service-role typing (legacy tables). */
export type Database = {
  public: {
    Views: Record<string, never>
    Functions: Record<string, never>
    CompositeTypes: Record<string, never>
    Tables: {
      organizations: {
        Row: {
          id: string
          name: string
          description: string | null
          settings: any
          created_at: string
          updated_at: string
          is_active: boolean
        }
        Insert: {
          id?: string
          name: string
          description?: string | null
          settings?: any
          created_at?: string
          updated_at?: string
          is_active?: boolean
        }
        Update: {
          id?: string
          name?: string
          description?: string | null
          settings?: any
          created_at?: string
          updated_at?: string
          is_active?: boolean
        }
      }
      user_profiles: {
        Row: {
          id: string
          email: string
          full_name: string | null
          avatar_url: string | null
          phone: string | null
          is_super_admin: boolean
          preferences: any
          created_at: string
          updated_at: string
          last_sign_in_at: string | null
        }
        Insert: {
          id: string
          email: string
          full_name?: string | null
          avatar_url?: string | null
          phone?: string | null
          is_super_admin?: boolean
          preferences?: any
          created_at?: string
          updated_at?: string
          last_sign_in_at?: string | null
        }
        Update: {
          id?: string
          email?: string
          full_name?: string | null
          avatar_url?: string | null
          phone?: string | null
          is_super_admin?: boolean
          preferences?: any
          created_at?: string
          updated_at?: string
          last_sign_in_at?: string | null
        }
      }
      organization_members: {
        Row: {
          id: string
          organization_id: string
          user_id: string
          role: 'super_admin' | 'organization_owner' | 'accountant' | 'member'
          invited_by: string | null
          invited_at: string
          joined_at: string | null
          is_active: boolean
          permissions: any
        }
        Insert: {
          id?: string
          organization_id: string
          user_id: string
          role?: 'super_admin' | 'organization_owner' | 'accountant' | 'member'
          invited_by?: string | null
          invited_at?: string
          joined_at?: string | null
          is_active?: boolean
          permissions?: any
        }
        Update: {
          id?: string
          organization_id?: string
          user_id?: string
          role?: 'super_admin' | 'organization_owner' | 'accountant' | 'member'
          invited_by?: string | null
          invited_at?: string
          joined_at?: string | null
          is_active?: boolean
          permissions?: any
        }
      }
      accounts: {
        Row: {
          id: number
          organization_id: string
          code: string
          name: string
          account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
          parent_id: number | null
          description: string | null
          is_active: boolean
          group: string | null
          report_category:
            | 'current_asset'
            | 'fixed_asset'
            | 'other_asset'
            | 'current_liability'
            | 'long_term_liability'
            | 'other_liability'
            | 'owners_equity'
            | 'retained_earnings'
            | 'other_equity'
            | 'operating_revenue'
            | 'other_revenue'
            | 'cost_of_sales'
            | 'operating_expense'
            | 'other_expense'
            | null
          is_postable: boolean
          created_at: string
          updated_at: string
          created_by: string | null
        }
        Insert: {
          id?: number
          organization_id: string
          code: string
          name: string
          account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
          parent_id?: number | null
          description?: string | null
          is_active?: boolean
          group?: string | null
          report_category?:
            | 'current_asset'
            | 'fixed_asset'
            | 'other_asset'
            | 'current_liability'
            | 'long_term_liability'
            | 'other_liability'
            | 'owners_equity'
            | 'retained_earnings'
            | 'other_equity'
            | 'operating_revenue'
            | 'other_revenue'
            | 'cost_of_sales'
            | 'operating_expense'
            | 'other_expense'
            | null
          is_postable?: boolean
          created_at?: string
          updated_at?: string
          created_by?: string | null
        }
        Update: {
          id?: number
          organization_id?: string
          code?: string
          name?: string
          account_type?: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
          parent_id?: number | null
          description?: string | null
          is_active?: boolean
          group?: string | null
          report_category?:
            | 'current_asset'
            | 'fixed_asset'
            | 'other_asset'
            | 'current_liability'
            | 'long_term_liability'
            | 'other_liability'
            | 'owners_equity'
            | 'retained_earnings'
            | 'other_equity'
            | 'operating_revenue'
            | 'other_revenue'
            | 'cost_of_sales'
            | 'operating_expense'
            | 'other_expense'
            | null
          is_postable?: boolean
          created_at?: string
          updated_at?: string
          created_by?: string | null
        }
        Relationships: []
      }
      journal_entries: {
        Row: {
          id: number
          organization_id: string
          entry_number: string
          entry_date: string
          description: string
          reference: string | null
          total_amount: number
          is_posted: boolean
          created_at: string
          updated_at: string
          created_by: string | null
          posted_by: string | null
          posted_at: string | null
        }
        Insert: {
          id?: number
          organization_id: string
          entry_number: string
          entry_date: string
          description: string
          reference?: string | null
          total_amount?: number
          is_posted?: boolean
          created_at?: string
          updated_at?: string
          created_by?: string | null
          posted_by?: string | null
          posted_at?: string | null
        }
        Update: {
          id?: number
          organization_id?: string
          entry_number?: string
          entry_date?: string
          description?: string
          reference?: string | null
          total_amount?: number
          is_posted?: boolean
          created_at?: string
          updated_at?: string
          created_by?: string | null
          posted_by?: string | null
          posted_at?: string | null
        }
      }
      journal_entry_lines: {
        Row: {
          id: number
          journal_entry_id: number
          account_id: number
          description: string | null
          debit_amount: number
          credit_amount: number
          line_order: number
        }
        Insert: {
          id?: number
          journal_entry_id: number
          account_id: number
          description?: string | null
          debit_amount?: number
          credit_amount?: number
          line_order?: number
        }
        Update: {
          id?: number
          journal_entry_id?: number
          account_id?: number
          description?: string | null
          debit_amount?: number
          credit_amount?: number
          line_order?: number
        }
      }
    }
    Enums: {
      user_role: 'super_admin' | 'organization_owner' | 'accountant' | 'member'
      account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
      entry_type: 'debit' | 'credit'
    }
  }
}
