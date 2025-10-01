# 📦 Inventory Management System - Complete Documentation

## 🎯 Overview

The Inventory Management System is a comprehensive module that extends your accounting software with full inventory tracking capabilities. It seamlessly integrates with your existing chart of accounts, providing automatic journal entry creation and real-time stock management.

---

## 🏗️ Architecture

### **Key Concepts**

1. **Categories** → Link to Chart of Accounts
   - Each category maps to TWO accounts:
     - **IN Account** (Asset): Debited when purchasing inventory
     - **OUT Account** (COGS/Expense): Debited when selling/using inventory

2. **Items** → Belong to Categories
   - Track stock levels (In, Out, Available)
   - Automatic value calculation
   - Low stock alerts

3. **Transactions** → Record Movement
   - **IN**: Purchases, receipts, adjustments (increase stock)
   - **OUT**: Sales, usage, consumption (decrease stock)
   - **ADJUSTMENT**: Manual corrections

---

## 📊 Database Schema

### **Tables Created**

#### 1. `inventory_categories`
Organizes inventory into categories, each linked to specific GL accounts.

```sql
CREATE TABLE public.inventory_categories (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    inventory_account_id BIGINT NOT NULL,  -- Asset account for purchases
    expense_account_id BIGINT NOT NULL,    -- COGS/Expense account for usage
    parent_id BIGINT,                      -- For hierarchy
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**Key Fields:**
- `inventory_account_id`: Where purchases are recorded (Asset)
- `expense_account_id`: Where COGS/usage is recorded (Expense)
- `parent_id`: Optional hierarchy support

#### 2. `inventory_items`
Individual inventory items (SKUs).

```sql
CREATE TABLE public.inventory_items (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL,
    category_id BIGINT NOT NULL,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    unit_of_measure VARCHAR(50) DEFAULT 'kg',
    
    -- Stock tracking
    quantity_in DECIMAL(15,4) DEFAULT 0,
    quantity_out DECIMAL(15,4) DEFAULT 0,
    quantity_available DECIMAL(15,4) GENERATED ALWAYS AS (quantity_in - quantity_out) STORED,
    
    -- Cost tracking
    average_unit_cost DECIMAL(15,2) DEFAULT 0,
    total_value DECIMAL(15,2) GENERATED ALWAYS AS ((quantity_in - quantity_out) * average_unit_cost) STORED,
    
    -- Reorder alerts
    reorder_point DECIMAL(15,4) DEFAULT 0,
    reorder_quantity DECIMAL(15,4) DEFAULT 0,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**Key Fields:**
- `quantity_in`: Cumulative total received
- `quantity_out`: Cumulative total used/sold
- `quantity_available`: Auto-calculated (in - out)
- `total_value`: Auto-calculated (available × cost)

#### 3. `inventory_transactions`
Complete audit trail of all inventory movements.

```sql
CREATE TABLE public.inventory_transactions (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL,
    item_id BIGINT NOT NULL,
    transaction_type inventory_transaction_type NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,        -- Positive for IN, Negative for OUT
    unit_cost DECIMAL(15,2),
    total_cost DECIMAL(15,2),
    journal_entry_id BIGINT,                -- Links to auto-created journal entry
    reference VARCHAR(100),
    description TEXT,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**Transaction Types:**
- `in`: Receiving stock (purchases, production)
- `out`: Using stock (sales, consumption)
- `adjustment`: Manual corrections

---

## 🔄 How It Works

### **Example: Restaurant Inventory**

#### **Step 1: Create Categories**

```
Category: "Meats"
├─ IN Account:  1110 - Inventory - Meats (Asset)
└─ OUT Account: 5100 - COGS - Meats (Expense)

Category: "Vegetables"
├─ IN Account:  1120 - Inventory - Vegetables (Asset)
└─ OUT Account: 5200 - COGS - Vegetables (Expense)
```

#### **Step 2: Add Inventory Items**

```
Item: Beef Ribeye
├─ SKU: BEEF-RIB-001
├─ Category: Meats
├─ Unit: kg
├─ Reorder Point: 50 kg
└─ Reorder Quantity: 100 kg
```

#### **Step 3: Record Transactions**

**Purchase (IN Transaction):**
```
Date: 2025-10-01
Type: IN
Item: Beef Ribeye
Quantity: +100 kg
Unit Cost: $15/kg
Total: $1,500

Result:
├─ quantity_in: 100 kg
├─ quantity_out: 0 kg
├─ quantity_available: 100 kg
└─ total_value: $1,500

Automatic Journal Entry:
Debit:  1110 - Inventory - Meats    $1,500
Credit: 2000 - Accounts Payable     $1,500
```

**Sale/Usage (OUT Transaction):**
```
Date: 2025-10-02
Type: OUT
Item: Beef Ribeye
Quantity: -30 kg (negative)
Unit Cost: $15/kg
Total: $450

Result:
├─ quantity_in: 100 kg (unchanged)
├─ quantity_out: 30 kg
├─ quantity_available: 70 kg
└─ total_value: $1,050

Automatic Journal Entry:
Debit:  5100 - COGS - Meats         $450
Credit: 1110 - Inventory - Meats    $450
```

---

## 🎨 User Interface

### **5 Main Tabs**

#### 1. **Overview Tab**
- Key metrics cards (Total Value, Total Items, Low Stock alerts)
- Low stock alerts list
- Recent transactions

#### 2. **Items Tab**
- Full list of inventory items
- Search by SKU, name, or category
- Inline editing
- Create new items
- Shows: In, Out, Available, Unit Cost, Total Value

#### 3. **Categories Tab**
- Manage inventory categories
- Configure account mappings
- Create/edit/delete categories

#### 4. **Stock Levels Tab**
- Current stock for all items
- Side-by-side view of In/Out/Available
- Quick stock check

#### 5. **Transactions Tab**
- Complete transaction history
- Filter by item, date, type
- Record new transactions (IN/OUT/Adjustment)

---

## 🔐 Security & Permissions

### **Row Level Security (RLS)**

Following your existing security model:

- **Members**: Can view all inventory data
- **Accountants**: Can create/edit items, categories, and transactions
- **Organization Owners**: Full access
- **Super Admins**: Full access across all organizations

### **Policies Applied:**

```sql
-- Reading inventory
FOR SELECT: public.is_organization_member(organization_id)

-- Modifying inventory
FOR ALL: public.get_user_organization_role(organization_id) 
         IN ('organization_owner', 'accountant')
```

---

## 📈 Features

### ✅ **Core Features**

- **Category-based Account Linking**: Map inventory categories to GL accounts
- **Automatic Stock Tracking**: In/Out/Available quantities auto-calculated
- **Cost Tracking**: Average unit cost and total inventory value
- **Transaction History**: Complete audit trail of all movements
- **Low Stock Alerts**: Automated alerts when stock falls below reorder point
- **Multi-tenant**: Full organization isolation with RLS
- **Real-time Updates**: Instant stock level updates

### ✅ **Accounting Integration**

- **Automatic Journal Entries**: Create GL entries for inventory transactions
- **Flexible Account Mapping**: Different categories can use different accounts
- **COGS Tracking**: Automatic cost of goods sold calculation
- **Sub-account Support**: Supports detailed GL account structures

### ✅ **User Experience**

- **Modern UI**: Material Design 3 components matching your existing app
- **Tab-based Navigation**: Organized, intuitive interface
- **Inline Editing**: Quick updates without dialogs
- **Search & Filter**: Fast item lookup
- **Import/Export**: CSV support (future enhancement)

---

## 🚀 Getting Started

### **Step 1: Run Database Migration**

Execute the SQL script in your Supabase SQL editor:

```bash
backend/database/INVENTORY_SCHEMA.sql
```

This creates:
- 3 tables
- 1 enum type
- RLS policies
- Indexes
- Triggers
- Helper functions

### **Step 2: Create Your First Category**

1. Navigate to: `/dashboard/inventory`
2. Click **Categories** tab
3. Click **Add Category**
4. Fill in:
   - Name: "Meats"
   - Description: "Fresh and frozen meat products"
   - IN Account: Select your inventory asset account (e.g., 1110)
   - OUT Account: Select your COGS expense account (e.g., 5100)
5. Click **Create**

### **Step 3: Add Inventory Items**

1. Click **Items** tab
2. Click **Add Item**
3. Fill in:
   - SKU: "BEEF-RIB-001"
   - Name: "Beef Ribeye Steak"
   - Category: "Meats"
   - Unit of Measure: "kg"
   - Unit Cost: $15.00
   - Reorder Point: 50
   - Reorder Quantity: 100
4. Click **Create**

### **Step 4: Record Your First Transaction**

1. Click **Transactions** tab
2. Click **New Transaction**
3. Fill in:
   - Item: "Beef Ribeye Steak"
   - Type: "IN - Receive Stock"
   - Quantity: 100
   - Unit Cost: $15.00
   - Date: Today
   - Reference: "PO-12345"
4. Click **Create Transaction**

You'll see:
- Stock levels updated instantly
- Transaction appears in history
- Available quantity is now 100 kg

---

## 📝 Best Practices

### **1. Category Organization**

```
✅ Good Category Structure:
├─ Meats
│  ├─ Beef (sub-category)
│  ├─ Chicken
│  └─ Lamb
├─ Vegetables
│  ├─ Fresh
│  └─ Frozen
└─ Dairy

❌ Too Generic:
├─ Food
└─ Supplies
```

### **2. SKU Naming Convention**

```
✅ Good SKUs:
- BEEF-RIB-001 (Category-Type-Number)
- VEG-TOM-500G (Product-Item-Size)
- DAI-MLK-1L (Clear, structured)

❌ Bad SKUs:
- Item1
- Product
- ABC123 (no meaning)
```

### **3. Account Mapping**

```
✅ Proper Mapping:
Category: Meats
├─ IN:  1110 - Inventory - Meats (Asset)
└─ OUT: 5100 - COGS - Meats (Expense)

Category: Office Supplies
├─ IN:  1150 - Inventory - Supplies (Asset)
└─ OUT: 6200 - Office Supplies Expense (Expense)

❌ Wrong Mapping:
├─ IN:  5000 - COGS (Wrong! Should be Asset)
└─ OUT: 1000 - Cash (Wrong! Should be Expense)
```

### **4. Transaction Recording**

- **Record purchases immediately** to maintain accurate stock levels
- **Use reference numbers** (PO numbers, invoice numbers)
- **Add descriptions** for adjustments to maintain audit trail
- **Count stock regularly** and record adjustments

---

## 🔧 Maintenance

### **Low Stock Alerts**

Items appear in low stock alerts when:
```
quantity_available <= reorder_point
```

Review the Overview tab daily to catch low stock items.

### **Stock Counting**

Periodic physical counts:
1. Count actual stock
2. Compare with `quantity_available`
3. If different, create an **Adjustment** transaction
4. Document reason in description

### **Data Integrity**

The system maintains data integrity through:
- Foreign key constraints
- Check constraints
- Automatic triggers
- RLS policies

---

## 📊 Reports & Analytics

### **Available Metrics**

1. **Total Inventory Value**: Sum of all `total_value` fields
2. **Stock by Category**: Group items by category
3. **Turnover Rate**: `quantity_out / quantity_in` over time
4. **Low Stock Items**: Items below reorder point
5. **Transaction History**: Complete audit trail

### **Future Enhancements**

- Inventory valuation reports (FIFO/LIFO/Weighted Average)
- Stock movement analysis
- Slow-moving inventory identification
- Reorder suggestions
- Barcode/QR code scanning

---

## 🐛 Troubleshooting

### **Issue: Can't create category**

**Solution**: Ensure you have selected both IN and OUT accounts. Both are required.

### **Issue: Low stock alert not showing**

**Solution**: Check that `reorder_point` is set to a value greater than 0.

### **Issue: Quantity not updating**

**Solution**: Verify the transaction was created successfully. Check the Transactions tab for the record.

### **Issue: Permission denied**

**Solution**: Only Accountants and Organization Owners can modify inventory. Check your role.

---

## 📞 Support

### **Technical Details**

- **Database**: PostgreSQL (Supabase)
- **Frontend**: Next.js 15, React 19, TypeScript
- **UI Framework**: Radix UI, Tailwind CSS
- **State Management**: React Query
- **Security**: Row Level Security (RLS)

### **File Structure**

```
web-app/
├─ src/
│  ├─ app/dashboard/inventory/page.tsx
│  ├─ components/inventory/
│  │  ├─ win11-inventory-page.tsx
│  │  ├─ category-dialog.tsx
│  │  ├─ item-dialog.tsx
│  │  ├─ transaction-dialog.tsx
│  │  ├─ items-table.tsx
│  │  ├─ categories-table.tsx
│  │  └─ transactions-table.tsx
│  ├─ types/index.ts (inventory types)
│  └─ lib/data-service.ts (inventory methods)

backend/
└─ database/
   ├─ INVENTORY_SCHEMA.sql
   └─ INVENTORY_SYSTEM_DOCUMENTATION.md (this file)
```

---

## 🎉 Summary

Your inventory system is now fully integrated with your accounting software, providing:

✅ **Seamless Integration**: Categories link directly to your chart of accounts  
✅ **Automatic Accounting**: Transactions create journal entries automatically  
✅ **Real-time Tracking**: Instant stock level updates  
✅ **Multi-tenant**: Full organization isolation  
✅ **Secure**: Row Level Security matching your existing system  
✅ **User-friendly**: Modern, intuitive interface  
✅ **Scalable**: Designed to grow with your business  

**Ready to start tracking inventory!** 📦

---

*Last Updated: October 2025*  
*Version: 1.0*

