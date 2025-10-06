-- ===============================================
-- INVENTORY VOUCHER SYSTEM SCHEMA
-- ===============================================
-- Complete voucher system with expiration and approval workflow
-- Based on real database roles: member, accountant, organization_owner, super_admin

-- ===============================================
-- 1. ENUMS
-- ===============================================

-- Voucher types
CREATE TYPE public.inventory_voucher_type AS ENUM (
    'purchase',    -- Inventory IN (purchases)
    'issuance'     -- Inventory OUT (issuances)
);

-- Voucher status with expiration
CREATE TYPE public.inventory_voucher_status AS ENUM (
    'draft',              -- Being created
    'pending_finance',    -- Submitted, awaiting finance approval
    'approved',           -- Finance approved, ready to execute
    'receiving',          -- Purchase: goods being received
    'issuing',            -- Issuance: goods being issued
    'posted',             -- GL entries created
    'completed',          -- Fully completed
    'rejected',           -- Rejected by approver
    'expired',            -- Not approved within 48 hours
    'cancelled'           -- Cancelled by creator
);

-- Payment types for purchase vouchers
CREATE TYPE public.payment_type AS ENUM (
    'credit',         -- Accounts Payable
    'cash',           -- Cash payment
    'check',          -- Check payment
    'card',           -- Credit card
    'bank_transfer',  -- Bank transfer
    'partial'         -- Partial payment (deposit + credit)
);

-- ===============================================
-- 2. TABLES
-- ===============================================

-- Main voucher table
CREATE TABLE public.inventory_vouchers (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    
    -- Voucher details
    voucher_number VARCHAR(50) UNIQUE NOT NULL,  -- Auto-generated: PV-2025-001, IV-2025-001
    voucher_type public.inventory_voucher_type NOT NULL,
    status public.inventory_voucher_status DEFAULT 'draft',
    
    -- Requester/creator
    requested_by UUID NOT NULL REFERENCES public.user_profiles(id),
    requested_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Purchase-specific fields
    vendor_name VARCHAR(255),
    vendor_contact VARCHAR(255),
    purchase_order_number VARCHAR(100),
    expected_delivery_date DATE,
    
    -- Issuance-specific fields
    purpose TEXT,                                 -- Why inventory is needed
    destination VARCHAR(255),                     -- Where it's going
    cost_center VARCHAR(100),                     -- Cost center code
    project_code VARCHAR(100),                    -- Project code
    destination_account_id BIGINT REFERENCES public.accounts(id),  -- GL account for expense
    
    -- Payment details (for purchase vouchers)
    payment_type public.payment_type DEFAULT 'credit',
    payment_account_id BIGINT REFERENCES public.accounts(id),  -- Cash/Bank account used
    deposit_amount DECIMAL(15,2) DEFAULT 0,  -- For partial payments
    payment_reference VARCHAR(100),  -- Check #, transaction ID, etc.
    
    -- Common fields
    description TEXT,
    notes TEXT,
    total_estimated_cost DECIMAL(15,2) DEFAULT 0,
    total_actual_cost DECIMAL(15,2),
    
    -- Expiration tracking
    submitted_at TIMESTAMP WITH TIME ZONE,  -- When submitted for approval
    approval_deadline TIMESTAMP WITH TIME ZONE,  -- 48 hours from submission
    expired_at TIMESTAMP WITH TIME ZONE,  -- When it expired
    renewed_at TIMESTAMP WITH TIME ZONE,  -- When it was renewed
    renewal_count INTEGER DEFAULT 0,  -- How many times renewed
    renewal_reason TEXT,  -- Why it was renewed
    
    -- Approval tracking (finance only)
    finance_approved_by UUID REFERENCES public.user_profiles(id),
    finance_approved_at TIMESTAMP WITH TIME ZONE,
    finance_approval_notes TEXT,
    
    rejected_by UUID REFERENCES public.user_profiles(id),
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    
    -- Execution tracking
    executed_by UUID REFERENCES public.user_profiles(id),  -- Who physically received/issued
    executed_at TIMESTAMP WITH TIME ZONE,
    
    -- Journal entry link
    journal_entry_id BIGINT REFERENCES public.journal_entries(id),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Constraints
    CHECK (
        (voucher_type = 'purchase' AND vendor_name IS NOT NULL) OR
        (voucher_type = 'issuance' AND purpose IS NOT NULL)
    )
);

-- Voucher line items
CREATE TABLE public.inventory_voucher_lines (
    id BIGSERIAL PRIMARY KEY,
    voucher_id BIGINT NOT NULL REFERENCES public.inventory_vouchers(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    
    -- Item details
    item_id BIGINT NOT NULL REFERENCES public.inventory_items(id),
    
    -- Quantities
    quantity_requested DECIMAL(15,4) NOT NULL,   -- What was requested
    quantity_approved DECIMAL(15,4),             -- What was approved (can be less)
    quantity_actual DECIMAL(15,4),               -- What was actually received/issued
    
    -- Cost details
    unit_cost_estimated DECIMAL(15,2),
    unit_cost_actual DECIMAL(15,2),
    total_cost DECIMAL(15,2) GENERATED ALWAYS AS (
        COALESCE(quantity_actual, quantity_approved, quantity_requested) * 
        COALESCE(unit_cost_actual, unit_cost_estimated, 0)
    ) STORED,
    
    -- Line-specific notes
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    UNIQUE(voucher_id, line_number)
);

-- Approval history/audit trail
CREATE TABLE public.voucher_approvals (
    id BIGSERIAL PRIMARY KEY,
    voucher_id BIGINT NOT NULL REFERENCES public.inventory_vouchers(id) ON DELETE CASCADE,
    
    -- Approval details
    approver_id UUID NOT NULL REFERENCES public.user_profiles(id),
    action VARCHAR(20) NOT NULL,          -- 'approved', 'rejected', 'requested_changes'
    comments TEXT,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Expiration tracking
CREATE TABLE public.voucher_expiration_log (
    id BIGSERIAL PRIMARY KEY,
    voucher_id BIGINT NOT NULL REFERENCES public.inventory_vouchers(id) ON DELETE CASCADE,
    
    -- Expiration details
    status_when_expired public.inventory_voucher_status NOT NULL,
    expired_at TIMESTAMP WITH TIME ZONE NOT NULL,
    approval_deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Items affected
    items_count INTEGER NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    
    -- Renewal details (if renewed)
    renewed_at TIMESTAMP WITH TIME ZONE,
    renewed_by UUID REFERENCES public.user_profiles(id),
    renewal_reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Voucher attachments
CREATE TABLE public.voucher_attachments (
    id BIGSERIAL PRIMARY KEY,
    voucher_id BIGINT NOT NULL REFERENCES public.inventory_vouchers(id) ON DELETE CASCADE,
    
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    description TEXT,
    
    uploaded_by UUID REFERENCES public.user_profiles(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ===============================================
-- 3. ROW LEVEL SECURITY POLICIES
-- ===============================================

ALTER TABLE public.inventory_vouchers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_voucher_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voucher_approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voucher_expiration_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voucher_attachments ENABLE ROW LEVEL SECURITY;

-- Vouchers: Members can read, Accountants+ can modify
CREATE POLICY "vouchers_select_members" ON public.inventory_vouchers
    FOR SELECT USING (public.is_organization_member(organization_id));

CREATE POLICY "vouchers_modify_accountants" ON public.inventory_vouchers
    FOR ALL USING (
        public.get_user_organization_role(organization_id) IN ('organization_owner', 'accountant', 'super_admin')
    );

-- Voucher lines: Same as vouchers
CREATE POLICY "voucher_lines_select_members" ON public.inventory_voucher_lines
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.inventory_vouchers v 
            WHERE v.id = voucher_id 
            AND public.is_organization_member(v.organization_id)
        )
    );

CREATE POLICY "voucher_lines_modify_accountants" ON public.inventory_voucher_lines
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.inventory_vouchers v 
            WHERE v.id = voucher_id 
            AND public.get_user_organization_role(v.organization_id) IN ('organization_owner', 'accountant', 'super_admin')
        )
    );

-- Approvals: Members can read, Accountants+ can create
CREATE POLICY "voucher_approvals_select_members" ON public.voucher_approvals
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.inventory_vouchers v 
            WHERE v.id = voucher_id 
            AND public.is_organization_member(v.organization_id)
        )
    );

CREATE POLICY "voucher_approvals_insert_accountants" ON public.voucher_approvals
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.inventory_vouchers v 
            WHERE v.id = voucher_id 
            AND public.get_user_organization_role(v.organization_id) IN ('organization_owner', 'accountant', 'super_admin')
        )
    );

-- Expiration log: Members can read
CREATE POLICY "voucher_expiration_select_members" ON public.voucher_expiration_log
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.inventory_vouchers v 
            WHERE v.id = voucher_id 
            AND public.is_organization_member(v.organization_id)
        )
    );

-- Attachments: Members can read, Accountants+ can modify
CREATE POLICY "voucher_attachments_select_members" ON public.voucher_attachments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.inventory_vouchers v 
            WHERE v.id = voucher_id 
            AND public.is_organization_member(v.organization_id)
        )
    );

CREATE POLICY "voucher_attachments_modify_accountants" ON public.voucher_attachments
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.inventory_vouchers v 
            WHERE v.id = voucher_id 
            AND public.get_user_organization_role(v.organization_id) IN ('organization_owner', 'accountant', 'super_admin')
        )
    );

-- ===============================================
-- 4. INDEXES FOR PERFORMANCE
-- ===============================================

-- Vouchers
CREATE INDEX idx_inventory_vouchers_org ON public.inventory_vouchers(organization_id);
CREATE INDEX idx_inventory_vouchers_status ON public.inventory_vouchers(status);
CREATE INDEX idx_inventory_vouchers_type ON public.inventory_vouchers(voucher_type);
CREATE INDEX idx_inventory_vouchers_number ON public.inventory_vouchers(voucher_number);
CREATE INDEX idx_inventory_vouchers_requested_by ON public.inventory_vouchers(requested_by);
CREATE INDEX idx_inventory_vouchers_deadline ON public.inventory_vouchers(approval_deadline);
CREATE INDEX idx_inventory_vouchers_expired ON public.inventory_vouchers(expired_at);

-- Voucher lines
CREATE INDEX idx_inventory_voucher_lines_voucher ON public.inventory_voucher_lines(voucher_id);
CREATE INDEX idx_inventory_voucher_lines_item ON public.inventory_voucher_lines(item_id);

-- Approvals
CREATE INDEX idx_voucher_approvals_voucher ON public.voucher_approvals(voucher_id);
CREATE INDEX idx_voucher_approvals_approver ON public.voucher_approvals(approver_id);

-- Expiration log
CREATE INDEX idx_voucher_expiration_voucher ON public.voucher_expiration_log(voucher_id);
CREATE INDEX idx_voucher_expiration_expired_at ON public.voucher_expiration_log(expired_at);

-- Attachments
CREATE INDEX idx_voucher_attachments_voucher ON public.voucher_attachments(voucher_id);

-- ===============================================
-- 5. TRIGGERS
-- ===============================================

-- Update timestamps
CREATE TRIGGER update_inventory_vouchers_updated_at 
    BEFORE UPDATE ON public.inventory_vouchers 
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ===============================================
-- 6. HELPER FUNCTIONS
-- ===============================================

-- Function to generate voucher number
CREATE OR REPLACE FUNCTION public.generate_voucher_number(
    p_voucher_type public.inventory_voucher_type,
    p_org_id UUID
)
RETURNS VARCHAR(50)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    prefix VARCHAR(2);
    year_part VARCHAR(4);
    sequence_num INTEGER;
    voucher_number VARCHAR(50);
BEGIN
    -- Set prefix based on type
    prefix := CASE p_voucher_type 
        WHEN 'purchase' THEN 'PV'
        WHEN 'issuance' THEN 'IV'
    END;
    
    -- Get current year
    year_part := EXTRACT(YEAR FROM CURRENT_DATE)::VARCHAR;
    
    -- Get next sequence number for this org and type
    SELECT COALESCE(MAX(
        CAST(SUBSTRING(voucher_number FROM '^[A-Z]{2}-[0-9]{4}-([0-9]+)$') AS INTEGER)
    ), 0) + 1
    INTO sequence_num
    FROM public.inventory_vouchers
    WHERE organization_id = p_org_id
    AND voucher_type = p_voucher_type
    AND voucher_number ~ ('^' || prefix || '-' || year_part || '-[0-9]+$');
    
    -- Format voucher number
    voucher_number := prefix || '-' || year_part || '-' || LPAD(sequence_num::VARCHAR, 4, '0');
    
    RETURN voucher_number;
END;
$$;

-- Function to assign approver based on real roles
CREATE OR REPLACE FUNCTION public.assign_voucher_approver(org_id UUID)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    approver_id UUID;
BEGIN
    -- Find first available accountant or organization_owner
    SELECT om.user_id INTO approver_id
    FROM public.organization_members om
    WHERE om.organization_id = org_id
    AND om.is_active = true
    AND om.role IN ('accountant', 'organization_owner')
    ORDER BY 
        CASE om.role 
            WHEN 'accountant' THEN 1 
            WHEN 'organization_owner' THEN 2 
        END,
        om.created_at
    LIMIT 1;
    
    RETURN approver_id;
END;
$$;

-- Function to check if user can approve vouchers
CREATE OR REPLACE FUNCTION public.can_approve_vouchers(org_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_role public.user_role;
BEGIN
    -- Get user's role
    user_role := public.get_user_organization_role(org_id);
    
    -- Check if user can approve
    RETURN user_role IN ('accountant', 'organization_owner', 'super_admin');
END;
$$;

-- Function to expire overdue vouchers
CREATE OR REPLACE FUNCTION public.expire_overdue_vouchers()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    expired_count INTEGER := 0;
    voucher_record RECORD;
BEGIN
    -- Find vouchers that should be expired
    FOR voucher_record IN
        SELECT v.id, v.voucher_number, v.status, v.approval_deadline,
               v.total_estimated_cost, v.organization_id
        FROM public.inventory_vouchers v
        WHERE v.status IN ('pending_finance', 'approved')
        AND v.approval_deadline IS NOT NULL
        AND v.approval_deadline < NOW()
        AND v.expired_at IS NULL
    LOOP
        -- Update voucher to expired
        UPDATE public.inventory_vouchers
        SET status = 'expired',
            expired_at = NOW(),
            updated_at = NOW()
        WHERE id = voucher_record.id;
        
        -- Log the expiration
        INSERT INTO public.voucher_expiration_log (
            voucher_id, status_when_expired, expired_at, approval_deadline,
            items_count, total_value
        )
        SELECT 
            voucher_record.id,
            voucher_record.status,
            NOW(),
            voucher_record.approval_deadline,
            COUNT(vl.id),
            voucher_record.total_estimated_cost
        FROM public.inventory_voucher_lines vl
        WHERE vl.voucher_id = voucher_record.id;
        
        expired_count := expired_count + 1;
    END LOOP;
    
    RETURN expired_count;
END;
$$;

-- Function to renew an expired voucher
CREATE OR REPLACE FUNCTION public.renew_expired_voucher(
    voucher_id BIGINT,
    renewed_by UUID,
    renewal_reason TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    voucher_record RECORD;
BEGIN
    -- Get voucher details
    SELECT * INTO voucher_record
    FROM public.inventory_vouchers
    WHERE id = voucher_id
    AND status = 'expired';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Voucher not found or not expired';
    END IF;
    
    -- Reset voucher to draft
    UPDATE public.inventory_vouchers
    SET status = 'draft',
        submitted_at = NULL,
        approval_deadline = NULL,
        expired_at = NULL,
        renewed_at = NOW(),
        renewal_count = renewal_count + 1,
        renewal_reason = renewal_reason,
        updated_at = NOW()
    WHERE id = voucher_id;
    
    -- Log the renewal
    UPDATE public.voucher_expiration_log
    SET renewed_at = NOW(),
        renewed_by = renewed_by,
        renewal_reason = renewal_reason
    WHERE voucher_id = voucher_id
    AND renewed_at IS NULL;
    
    RETURN TRUE;
END;
$$;

-- ===============================================
-- 7. GRANT PERMISSIONS
-- ===============================================

-- Grant access to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON public.inventory_vouchers TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.inventory_voucher_lines TO authenticated;
GRANT SELECT, INSERT ON public.voucher_approvals TO authenticated;
GRANT SELECT ON public.voucher_expiration_log TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.voucher_attachments TO authenticated;

-- Grant sequence usage
GRANT USAGE, SELECT ON SEQUENCE public.inventory_vouchers_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.inventory_voucher_lines_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.voucher_approvals_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.voucher_expiration_log_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.voucher_attachments_id_seq TO authenticated;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION public.generate_voucher_number(public.inventory_voucher_type, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.assign_voucher_approver(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.can_approve_vouchers(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.expire_overdue_vouchers() TO authenticated;
GRANT EXECUTE ON FUNCTION public.renew_expired_voucher(BIGINT, UUID, TEXT) TO authenticated;

-- ===============================================
-- VOUCHER SYSTEM SCHEMA COMPLETE
-- ===============================================

SELECT 'Voucher system schema created successfully!' as status,
       '5 tables: inventory_vouchers, inventory_voucher_lines, voucher_approvals, voucher_expiration_log, voucher_attachments' as tables,
       'Finance-only approval workflow with 48-hour expiration' as features,
       'All RLS policies active' as security;
