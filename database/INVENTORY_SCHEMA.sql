-- ===============================================
-- INVENTORY MANAGEMENT SYSTEM
-- ===============================================
-- Extends the existing accounting system with inventory tracking
-- Integrates with chart of accounts for automatic journal entries
-- Supports category-based account linking for IN/OUT transactions

-- ===============================================
-- 1. ENUMS
-- ===============================================

-- Inventory transaction type enum
CREATE TYPE public.inventory_transaction_type AS ENUM (
    'in',            -- Items coming IN (purchase, production, found)
    'out',           -- Items going OUT (sale, usage, consumption)
    'adjustment'     -- Manual adjustment (can be + or -)
);

-- ===============================================
-- 2. TABLES
-- ===============================================

-- Inventory categories table (maps to chart of accounts)
CREATE TABLE public.inventory_categories (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Account mappings (BOTH required)
    inventory_account_id BIGINT NOT NULL REFERENCES public.accounts(id),  -- For IN transactions (Asset)
    expense_account_id BIGINT NOT NULL REFERENCES public.accounts(id),    -- For OUT transactions (COGS/Expense)
    
    -- Optional: Parent category for hierarchy
    parent_id BIGINT REFERENCES public.inventory_categories(id),
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES public.user_profiles(id),
    
    UNIQUE(organization_id, name)
);

-- Inventory items table
CREATE TABLE public.inventory_items (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES public.inventory_categories(id),
    
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    unit_of_measure VARCHAR(50) DEFAULT 'kg',  -- kg, pcs, liters, etc.
    
    -- Stock tracking (In/Out/Available)
    quantity_in DECIMAL(15,4) DEFAULT 0,       -- Total received
    quantity_out DECIMAL(15,4) DEFAULT 0,      -- Total used/sold
    quantity_available DECIMAL(15,4) GENERATED ALWAYS AS (quantity_in - quantity_out) STORED,
    
    -- Cost tracking
    average_unit_cost DECIMAL(15,2) DEFAULT 0,
    total_value DECIMAL(15,2) GENERATED ALWAYS AS ((quantity_in - quantity_out) * average_unit_cost) STORED,
    
    -- Reorder settings (optional)
    reorder_point DECIMAL(15,4) DEFAULT 0,
    reorder_quantity DECIMAL(15,4) DEFAULT 0,
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES public.user_profiles(id),
    
    UNIQUE(organization_id, sku)
);

-- Inventory transactions table (audit trail)
CREATE TABLE public.inventory_transactions (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    item_id BIGINT NOT NULL REFERENCES public.inventory_items(id) ON DELETE CASCADE,
    transaction_type public.inventory_transaction_type NOT NULL,
    
    -- Transaction details
    quantity DECIMAL(15,4) NOT NULL,           -- Positive for IN, Negative for OUT
    unit_cost DECIMAL(15,2),                   -- Cost per unit
    total_cost DECIMAL(15,2),                  -- Total value
    
    -- Reference to journal entry (if auto-created)
    journal_entry_id BIGINT REFERENCES public.journal_entries(id),
    reference VARCHAR(100),
    description TEXT,
    
    -- Metadata
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES public.user_profiles(id)
);

-- ===============================================
-- 3. ROW LEVEL SECURITY POLICIES
-- ===============================================

ALTER TABLE public.inventory_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_transactions ENABLE ROW LEVEL SECURITY;

-- Categories: Members can read, Accountants+ can modify
CREATE POLICY "inventory_categories_select_members" ON public.inventory_categories
    FOR SELECT USING (public.is_organization_member(organization_id));

CREATE POLICY "inventory_categories_modify_accountants" ON public.inventory_categories
    FOR ALL USING (
        public.get_user_organization_role(organization_id) IN ('organization_owner', 'accountant')
    );

-- Items: Members can read, Accountants+ can modify
CREATE POLICY "inventory_items_select_members" ON public.inventory_items
    FOR SELECT USING (public.is_organization_member(organization_id));

CREATE POLICY "inventory_items_modify_accountants" ON public.inventory_items
    FOR ALL USING (
        public.get_user_organization_role(organization_id) IN ('organization_owner', 'accountant')
    );

-- Transactions: Members can read, Accountants+ can create
CREATE POLICY "inventory_transactions_select_members" ON public.inventory_transactions
    FOR SELECT USING (public.is_organization_member(organization_id));

CREATE POLICY "inventory_transactions_insert_accountants" ON public.inventory_transactions
    FOR INSERT WITH CHECK (
        public.get_user_organization_role(organization_id) IN ('organization_owner', 'accountant')
    );

-- ===============================================
-- 4. INDEXES FOR PERFORMANCE
-- ===============================================

CREATE INDEX idx_inventory_categories_org_id ON public.inventory_categories(organization_id);
CREATE INDEX idx_inventory_categories_inventory_account ON public.inventory_categories(inventory_account_id);
CREATE INDEX idx_inventory_categories_expense_account ON public.inventory_categories(expense_account_id);
CREATE INDEX idx_inventory_categories_parent_id ON public.inventory_categories(parent_id);
CREATE INDEX idx_inventory_categories_active ON public.inventory_categories(is_active);

CREATE INDEX idx_inventory_items_org_id ON public.inventory_items(organization_id);
CREATE INDEX idx_inventory_items_category_id ON public.inventory_items(category_id);
CREATE INDEX idx_inventory_items_sku ON public.inventory_items(organization_id, sku);
CREATE INDEX idx_inventory_items_active ON public.inventory_items(is_active);

CREATE INDEX idx_inventory_transactions_org_id ON public.inventory_transactions(organization_id);
CREATE INDEX idx_inventory_transactions_item_id ON public.inventory_transactions(item_id);
CREATE INDEX idx_inventory_transactions_date ON public.inventory_transactions(transaction_date);
CREATE INDEX idx_inventory_transactions_type ON public.inventory_transactions(transaction_type);
CREATE INDEX idx_inventory_transactions_journal_entry ON public.inventory_transactions(journal_entry_id);

-- ===============================================
-- 5. TRIGGERS
-- ===============================================

CREATE TRIGGER update_inventory_categories_updated_at 
    BEFORE UPDATE ON public.inventory_categories 
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_inventory_items_updated_at 
    BEFORE UPDATE ON public.inventory_items 
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ===============================================
-- 6. HELPER FUNCTIONS
-- ===============================================

-- Function to update inventory quantities when transaction is created
CREATE OR REPLACE FUNCTION public.update_inventory_quantities()
RETURNS TRIGGER AS $$
BEGIN
    -- Update quantity_in or quantity_out based on quantity sign
    IF NEW.quantity > 0 THEN
        -- Positive = IN
        UPDATE public.inventory_items
        SET quantity_in = quantity_in + NEW.quantity
        WHERE id = NEW.item_id;
    ELSE
        -- Negative = OUT
        UPDATE public.inventory_items
        SET quantity_out = quantity_out + ABS(NEW.quantity)
        WHERE id = NEW.item_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update quantities when transaction is created
CREATE TRIGGER trigger_update_inventory_quantities
    AFTER INSERT ON public.inventory_transactions
    FOR EACH ROW
    EXECUTE FUNCTION public.update_inventory_quantities();

-- Function to get low stock items (optional helper)
CREATE OR REPLACE FUNCTION public.get_low_stock_items(org_id UUID)
RETURNS TABLE (
    id BIGINT,
    organization_id UUID,
    category_id BIGINT,
    sku VARCHAR,
    name VARCHAR,
    description TEXT,
    unit_of_measure VARCHAR,
    quantity_in DECIMAL,
    quantity_out DECIMAL,
    quantity_available DECIMAL,
    average_unit_cost DECIMAL,
    total_value DECIMAL,
    reorder_point DECIMAL,
    reorder_quantity DECIMAL,
    is_active BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.organization_id,
        i.category_id,
        i.sku,
        i.name,
        i.description,
        i.unit_of_measure,
        i.quantity_in,
        i.quantity_out,
        i.quantity_available,
        i.average_unit_cost,
        i.total_value,
        i.reorder_point,
        i.reorder_quantity,
        i.is_active,
        i.created_at,
        i.updated_at,
        i.created_by
    FROM public.inventory_items i
    WHERE i.organization_id = org_id
    AND i.is_active = true
    AND i.reorder_point > 0
    AND i.quantity_available <= i.reorder_point
    ORDER BY i.quantity_available ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===============================================
-- 7. GRANT PERMISSIONS
-- ===============================================

-- Grant access to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON public.inventory_categories TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.inventory_items TO authenticated;
GRANT SELECT, INSERT ON public.inventory_transactions TO authenticated;

-- Grant sequence usage
GRANT USAGE, SELECT ON SEQUENCE public.inventory_categories_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.inventory_items_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.inventory_transactions_id_seq TO authenticated;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION public.update_inventory_quantities() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_low_stock_items(UUID) TO authenticated;

-- ===============================================
-- INVENTORY SCHEMA COMPLETE
-- ===============================================

SELECT 'Inventory management schema created successfully!' as status,
       '3 tables: inventory_categories, inventory_items, inventory_transactions' as tables,
       'Category-based account linking for IN/OUT transactions' as features,
       'All RLS policies active' as security;

-- ===============================================
-- USAGE EXAMPLES
-- ===============================================

/*

1. CREATE A CATEGORY (e.g., Meats)
   - Links to TWO accounts:
     - Inventory Account: 1110 - Inventory - Meats (Asset, for purchases)
     - Expense Account: 5100 - COGS - Meats (Expense, for usage/sales)

2. CREATE INVENTORY ITEMS
   - Each item belongs to a category
   - Inherits account mappings from category
   - Tracks: SKU, Name, Quantity In/Out/Available, Cost

3. RECORD TRANSACTIONS
   - IN Transaction (Purchase):
     * Increases quantity_in
     * Posts to inventory_account (Asset)
   
   - OUT Transaction (Sale/Use):
     * Increases quantity_out
     * Posts to expense_account (COGS)

4. AUTOMATIC FEATURES
   - quantity_available = quantity_in - quantity_out (auto-calculated)
   - total_value = quantity_available × average_unit_cost (auto-calculated)
   - Low stock alerts when quantity_available <= reorder_point

*/

