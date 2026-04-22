-- ===============================================
-- SUPPLIER MANAGEMENT SYSTEM SCHEMA
-- ===============================================
-- Supplier management with account mapping for voucher system
-- Allows accountants to map suppliers to GL accounts for easy voucher creation

-- ===============================================
-- 1. ENUMS
-- ===============================================

-- Supplier status
CREATE TYPE public.supplier_status AS ENUM (
    'active',
    'inactive',
    'suspended'
);

-- Payment terms
CREATE TYPE public.payment_terms AS ENUM (
    'net_15',      -- Net 15 days
    'net_30',      -- Net 30 days
    'net_45',      -- Net 45 days
    'net_60',      -- Net 60 days
    'due_on_receipt', -- Due on receipt
    'cash_on_delivery', -- COD
    'prepaid'      -- Prepaid
);

-- ===============================================
-- 2. SUPPLIER TABLES
-- ===============================================

-- Main suppliers table
CREATE TABLE public.suppliers (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    
    -- Basic supplier information
    supplier_code VARCHAR(50) NOT NULL,  -- Unique code like "SUP-001"
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),  -- Legal business name
    description TEXT,
    
    -- Contact information
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    fax VARCHAR(50),
    website VARCHAR(255),
    
    -- Address information
    billing_address_line1 VARCHAR(255),
    billing_address_line2 VARCHAR(255),
    billing_city VARCHAR(100),
    billing_state VARCHAR(100),
    billing_postal_code VARCHAR(20),
    billing_country VARCHAR(100),
    
    shipping_address_line1 VARCHAR(255),
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    shipping_postal_code VARCHAR(20),
    shipping_country VARCHAR(100),
    
    -- Business information
    tax_id VARCHAR(100),  -- Tax identification number
    registration_number VARCHAR(100),  -- Business registration number
    currency VARCHAR(3) DEFAULT 'USD',  -- Default currency for this supplier
    
    -- Payment terms
    payment_terms public.payment_terms DEFAULT 'net_30',
    credit_limit DECIMAL(15,2) DEFAULT 0,
    current_balance DECIMAL(15,2) DEFAULT 0,  -- Current outstanding balance
    
    -- Status and metadata
    status public.supplier_status DEFAULT 'active',
    is_preferred BOOLEAN DEFAULT false,  -- Preferred supplier flag
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES public.user_profiles(id),
    updated_by UUID REFERENCES public.user_profiles(id),
    
    -- Constraints
    UNIQUE(organization_id, supplier_code),
    UNIQUE(organization_id, name),
    CHECK (credit_limit >= 0),
    CHECK (current_balance >= 0)
);

-- Supplier account mappings
CREATE TABLE public.supplier_account_mappings (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL REFERENCES public.suppliers(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    
    -- Account mappings
    payable_account_id BIGINT NOT NULL REFERENCES public.accounts(id),  -- Accounts Payable account
    cash_account_id BIGINT REFERENCES public.accounts(id),  -- Default cash/bank account for payments
    expense_account_id BIGINT REFERENCES public.accounts(id),  -- Default expense account for purchases
    inventory_account_id BIGINT REFERENCES public.accounts(id),  -- Inventory account for purchases
    
    -- Additional mappings for specific scenarios
    freight_account_id BIGINT REFERENCES public.accounts(id),  -- Freight charges
    tax_account_id BIGINT REFERENCES public.accounts(id),  -- Tax account
    discount_account_id BIGINT REFERENCES public.accounts(id),  -- Purchase discounts
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES public.user_profiles(id),
    updated_by UUID REFERENCES public.user_profiles(id),
    
    -- Constraints
    UNIQUE(supplier_id),  -- One mapping per supplier
    CHECK (payable_account_id IS NOT NULL)  -- Payable account is required
);

-- Supplier contacts (multiple contacts per supplier)
CREATE TABLE public.supplier_contacts (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL REFERENCES public.suppliers(id) ON DELETE CASCADE,
    
    -- Contact details
    name VARCHAR(255) NOT NULL,
    title VARCHAR(100),  -- Job title
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    fax VARCHAR(50),
    
    -- Contact type
    is_primary BOOLEAN DEFAULT false,  -- Primary contact
    is_billing BOOLEAN DEFAULT false,  -- Billing contact
    is_shipping BOOLEAN DEFAULT false,  -- Shipping contact
    is_technical BOOLEAN DEFAULT false,  -- Technical contact
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES public.user_profiles(id)
);

-- ===============================================
-- 3. INDEXES
-- ===============================================

-- Suppliers indexes
CREATE INDEX idx_suppliers_organization_id ON public.suppliers(organization_id);
CREATE INDEX idx_suppliers_status ON public.suppliers(status);
CREATE INDEX idx_suppliers_name ON public.suppliers(name);
CREATE INDEX idx_suppliers_code ON public.suppliers(supplier_code);

-- Supplier account mappings indexes
CREATE INDEX idx_supplier_account_mappings_supplier_id ON public.supplier_account_mappings(supplier_id);
CREATE INDEX idx_supplier_account_mappings_organization_id ON public.supplier_account_mappings(organization_id);

-- Supplier contacts indexes
CREATE INDEX idx_supplier_contacts_supplier_id ON public.supplier_contacts(supplier_id);
CREATE INDEX idx_supplier_contacts_primary ON public.supplier_contacts(supplier_id, is_primary) WHERE is_primary = true;

-- ===============================================
-- 4. TRIGGERS
-- ===============================================

-- Update updated_at timestamp
CREATE TRIGGER update_suppliers_updated_at
    BEFORE UPDATE ON public.suppliers
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_supplier_account_mappings_updated_at
    BEFORE UPDATE ON public.supplier_account_mappings
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_supplier_contacts_updated_at
    BEFORE UPDATE ON public.supplier_contacts
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ===============================================
-- 5. RLS POLICIES
-- ===============================================

-- Enable RLS
ALTER TABLE public.suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supplier_account_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supplier_contacts ENABLE ROW LEVEL SECURITY;

-- Suppliers policies
CREATE POLICY "Users can view suppliers in their organizations" ON public.suppliers
    FOR SELECT USING (
        organization_id IN (
            SELECT organization_id 
            FROM public.organization_members 
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

CREATE POLICY "Accountants and owners can manage suppliers" ON public.suppliers
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id 
            FROM public.organization_members 
            WHERE user_id = auth.uid() 
            AND is_active = true 
            AND role IN ('accountant', 'organization_owner')
        )
    );

-- Supplier account mappings policies
CREATE POLICY "Users can view supplier account mappings in their organizations" ON public.supplier_account_mappings
    FOR SELECT USING (
        organization_id IN (
            SELECT organization_id 
            FROM public.organization_members 
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

CREATE POLICY "Accountants and owners can manage supplier account mappings" ON public.supplier_account_mappings
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id 
            FROM public.organization_members 
            WHERE user_id = auth.uid() 
            AND is_active = true 
            AND role IN ('accountant', 'organization_owner')
        )
    );

-- Supplier contacts policies
CREATE POLICY "Users can view supplier contacts in their organizations" ON public.supplier_contacts
    FOR SELECT USING (
        supplier_id IN (
            SELECT id 
            FROM public.suppliers 
            WHERE organization_id IN (
                SELECT organization_id 
                FROM public.organization_members 
                WHERE user_id = auth.uid() AND is_active = true
            )
        )
    );

CREATE POLICY "Accountants and owners can manage supplier contacts" ON public.supplier_contacts
    FOR ALL USING (
        supplier_id IN (
            SELECT id 
            FROM public.suppliers 
            WHERE organization_id IN (
                SELECT organization_id 
                FROM public.organization_members 
                WHERE user_id = auth.uid() 
                AND is_active = true 
                AND role IN ('accountant', 'organization_owner')
            )
        )
    );

-- ===============================================
-- 6. HELPER FUNCTIONS
-- ===============================================

-- Function to get supplier account mappings
CREATE OR REPLACE FUNCTION public.get_supplier_account_mappings(supplier_id_param BIGINT)
RETURNS TABLE (
    supplier_id BIGINT,
    payable_account_id BIGINT,
    cash_account_id BIGINT,
    expense_account_id BIGINT,
    inventory_account_id BIGINT,
    freight_account_id BIGINT,
    tax_account_id BIGINT,
    discount_account_id BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sam.supplier_id,
        sam.payable_account_id,
        sam.cash_account_id,
        sam.expense_account_id,
        sam.inventory_account_id,
        sam.freight_account_id,
        sam.tax_account_id,
        sam.discount_account_id
    FROM public.supplier_account_mappings sam
    WHERE sam.supplier_id = supplier_id_param;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update supplier balance
CREATE OR REPLACE FUNCTION public.update_supplier_balance(
    supplier_id_param BIGINT,
    amount DECIMAL(15,2)
)
RETURNS VOID AS $$
BEGIN
    UPDATE public.suppliers 
    SET 
        current_balance = current_balance + amount,
        updated_at = now()
    WHERE id = supplier_id_param;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===============================================
-- 7. SAMPLE DATA (Optional)
-- ===============================================

-- Insert sample suppliers (commented out - uncomment if needed)
/*
INSERT INTO public.suppliers (
    organization_id, supplier_code, name, legal_name, 
    contact_person, email, phone, billing_address_line1, 
    billing_city, billing_state, billing_postal_code, 
    billing_country, payment_terms, credit_limit, 
    created_by
) VALUES 
(
    'your-org-id-here', 'SUP-001', 'ABC Office Supplies', 'ABC Office Supplies Inc.',
    'John Smith', 'john@abcoffice.com', '+1-555-0123',
    '123 Business St', 'New York', 'NY', '10001', 'USA',
    'net_30', 50000.00, 'your-user-id-here'
),
(
    'your-org-id-here', 'SUP-002', 'Tech Solutions Ltd', 'Tech Solutions Limited',
    'Sarah Johnson', 'sarah@techsolutions.com', '+1-555-0456',
    '456 Tech Ave', 'San Francisco', 'CA', '94105', 'USA',
    'net_15', 100000.00, 'your-user-id-here'
);
*/
