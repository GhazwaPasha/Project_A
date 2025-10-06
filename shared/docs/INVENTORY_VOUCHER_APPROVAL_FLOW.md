# 📦 Inventory Voucher & Approval System - Complete Flow

## 🎯 Overview

This document outlines the **modernized inventory management system** with purchase vouchers and approval workflows for both inventory IN (purchases) and inventory OUT (issuances).

---

## 🏗️ System Architecture

### **Key Concepts**

1. **Purchase Vouchers** - Document-based inventory receiving
2. **Issuance Vouchers** - Document-based inventory issuance
3. **Multi-level Approvals** - Department + Finance authorization
4. **Status Workflow** - DRAFT → PENDING → APPROVED → POSTED → COMPLETED
5. **GL Integration** - Automatic journal entries upon approval

---

## 📊 FLOW 1: PURCHASE VOUCHER (Inventory IN)

### **Purpose**: Control inventory purchases with proper authorization

### **Workflow Steps:**

```
┌──────────────────────────────────────────────────────────────────┐
│                    PURCHASE VOUCHER LIFECYCLE                      │
└──────────────────────────────────────────────────────────────────┘

1. CREATE PURCHASE VOUCHER (Requester)
   ├─ Status: DRAFT
   ├─ Vendor details
   ├─ Items & quantities requested
   ├─ Expected costs
   ├─ Delivery date
   ├─ Purchase justification
   └─ Supporting documents (quotes, PO, etc.)

2. SUBMIT FOR APPROVAL (Requester)
   ├─ Status: DRAFT → PENDING
   ├─ Validate completeness
   ├─ Auto-assign approvers based on amount
   └─ Send notifications

3. DEPARTMENT APPROVAL (Department Manager)
   ├─ Review business need
   ├─ Check budget availability
   ├─ Options:
   │   ├─ APPROVE: Move to next level
   │   ├─ REJECT: Back to DRAFT (with reason)
   │   └─ REQUEST CHANGES: Back to DRAFT (with comments)
   └─ Timestamp & approver ID recorded

4. FINANCE APPROVAL (Finance Manager/Accountant)
   ├─ Review pricing & vendor
   ├─ Verify GL account mapping
   ├─ Check against budget
   ├─ Options:
   │   ├─ APPROVE: Status → APPROVED
   │   ├─ REJECT: Back to DRAFT
   │   └─ REQUEST CHANGES: Back to DRAFT
   └─ Timestamp & approver ID recorded

5. GOODS RECEIPT (Warehouse/Receiving)
   ├─ Status: APPROVED → RECEIVING
   ├─ Record actual quantities received
   ├─ Update actual costs (if different)
   ├─ Attach receiving documents
   ├─ Can be partial receipt
   └─ Mark as COMPLETED when fully received

6. AUTOMATIC POSTING (System)
   ├─ Status: RECEIVING → POSTED
   ├─ Update inventory quantities (quantity_in)
   ├─ Update average cost
   ├─ Create Journal Entry:
   │   ├─ Debit: Inventory Asset Account (from category)
   │   └─ Credit: Accounts Payable / Cash
   ├─ Link journal_entry_id to transaction
   └─ Generate voucher number

7. COMPLETED
   ├─ Voucher locked (no further edits)
   ├─ Inventory updated
   ├─ GL posted
   └─ Available for auditing
```

### **Status Flow Diagram:**

```
DRAFT ──submit──> PENDING ──dept_approve──> PENDING_FINANCE ──fin_approve──> APPROVED
  ↑                  |                            |                              |
  |                  |                            |                              |
  └────reject────────┴──────reject────────────────┘                              |
                                                                                  |
                                                                    receive_goods |
                                                                                  ↓
                                                                              RECEIVING
                                                                                  |
                                                                        auto_post |
                                                                                  ↓
                                                                               POSTED
                                                                                  |
                                                                       complete   |
                                                                                  ↓
                                                                             COMPLETED
```

---

## 📊 FLOW 2: ISSUANCE VOUCHER (Inventory OUT)

### **Purpose**: Control inventory usage/issuance with proper authorization

### **Workflow Steps:**

```
┌──────────────────────────────────────────────────────────────────┐
│                   ISSUANCE VOUCHER LIFECYCLE                       │
└──────────────────────────────────────────────────────────────────┘

1. CREATE ISSUANCE VOUCHER (Requester)
   ├─ Status: DRAFT
   ├─ Items & quantities needed
   ├─ Purpose/destination
   ├─ Cost center/project code
   ├─ Destination GL accounts (where cost goes)
   │   ├─ COGS (for sales)
   │   ├─ Department expense
   │   ├─ Project/WIP
   │   └─ Waste/Loss account
   ├─ Required date
   └─ Justification

2. SUBMIT FOR APPROVAL (Requester)
   ├─ Status: DRAFT → PENDING
   ├─ Validate stock availability
   ├─ Auto-assign approvers
   └─ Send notifications

3. DEPARTMENT APPROVAL (Department Manager)
   ├─ Review business need
   ├─ Verify purpose
   ├─ Options:
   │   ├─ APPROVE: Move to next level
   │   ├─ REJECT: Back to DRAFT
   │   └─ REQUEST CHANGES: Back to DRAFT
   └─ Timestamp recorded

4. FINANCE APPROVAL (Finance Manager/Accountant)
   ├─ Review GL account assignment
   ├─ Verify cost allocation
   ├─ Check budget for destination account
   ├─ Options:
   │   ├─ APPROVE: Status → APPROVED
   │   ├─ REJECT: Back to DRAFT
   │   └─ REQUEST CHANGES: Back to DRAFT
   └─ Timestamp recorded

5. GOODS ISSUE (Warehouse)
   ├─ Status: APPROVED → ISSUING
   ├─ Physical release of inventory
   ├─ Record actual quantities issued
   ├─ Capture receiver signature
   ├─ Can be partial issue
   └─ Mark COMPLETED when fully issued

6. AUTOMATIC POSTING (System)
   ├─ Status: ISSUING → POSTED
   ├─ Update inventory quantities (quantity_out)
   ├─ Calculate cost (using average_unit_cost)
   ├─ Create Journal Entry:
   │   ├─ Debit: Destination Account (COGS/Expense/Project)
   │   └─ Credit: Inventory Asset Account (from category)
   ├─ Link journal_entry_id to transaction
   └─ Generate voucher number

7. COMPLETED
   ├─ Voucher locked
   ├─ Inventory reduced
   ├─ GL posted
   └─ Available for auditing
```

### **Status Flow Diagram:**

```
DRAFT ──submit──> PENDING ──dept_approve──> PENDING_FINANCE ──fin_approve──> APPROVED
  ↑                  |                            |                              |
  |                  |                            |                              |
  └────reject────────┴──────reject────────────────┘                              |
                                                                                  |
                                                                     issue_goods  |
                                                                                  ↓
                                                                               ISSUING
                                                                                  |
                                                                        auto_post |
                                                                                  ↓
                                                                               POSTED
                                                                                  |
                                                                       complete   |
                                                                                  ↓
                                                                             COMPLETED
```

---

## 🔐 Approval Rules & Permissions

### **Role-Based Approvals:**

| Role | Purchase Voucher | Issuance Voucher | Can Post |
|------|-----------------|------------------|----------|
| **Member** | Can create/view | Can create/view | No |
| **Department Manager** | Can approve (dept level) | Can approve (dept level) | No |
| **Accountant** | Can approve (finance level) | Can approve (finance level) | Yes |
| **Organization Owner** | Can approve all levels | Can approve all levels | Yes |
| **Super Admin** | Full access | Full access | Yes |

### **Approval Thresholds (Configurable):**

```
Purchase Amount          | Approval Required
─────────────────────────┼──────────────────────
$0 - $1,000             | Department Manager only
$1,001 - $5,000         | Department + Finance
$5,001+                 | Department + Finance + Owner
```

---

## 💾 Database Schema Changes

### **New Tables:**

#### 1. `inventory_vouchers`
Main voucher table for both purchase and issuance

```sql
CREATE TYPE public.inventory_voucher_type AS ENUM ('purchase', 'issuance');

CREATE TYPE public.inventory_voucher_status AS ENUM (
    'draft',              -- Being created
    'pending',            -- Submitted, awaiting approval
    'pending_finance',    -- Dept approved, awaiting finance
    'approved',           -- Fully approved, ready to execute
    'receiving',          -- Purchase: goods being received
    'issuing',            -- Issuance: goods being issued
    'posted',             -- GL entries created
    'completed',          -- Fully completed
    'rejected',           -- Rejected by approver
    'cancelled'           -- Cancelled by creator
);

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
    
    -- Common fields
    description TEXT,
    notes TEXT,
    total_estimated_cost DECIMAL(15,2) DEFAULT 0,
    total_actual_cost DECIMAL(15,2),
    
    -- Approval tracking
    dept_approved_by UUID REFERENCES public.user_profiles(id),
    dept_approved_at TIMESTAMP WITH TIME ZONE,
    dept_approval_notes TEXT,
    
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

CREATE INDEX idx_inventory_vouchers_org ON public.inventory_vouchers(organization_id);
CREATE INDEX idx_inventory_vouchers_status ON public.inventory_vouchers(status);
CREATE INDEX idx_inventory_vouchers_type ON public.inventory_vouchers(voucher_type);
CREATE INDEX idx_inventory_vouchers_number ON public.inventory_vouchers(voucher_number);
CREATE INDEX idx_inventory_vouchers_requested_by ON public.inventory_vouchers(requested_by);
```

#### 2. `inventory_voucher_lines`
Line items for each voucher

```sql
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

CREATE INDEX idx_inventory_voucher_lines_voucher ON public.inventory_voucher_lines(voucher_id);
CREATE INDEX idx_inventory_voucher_lines_item ON public.inventory_voucher_lines(item_id);
```

#### 3. `inventory_voucher_approvals`
Approval history/audit trail

```sql
CREATE TABLE public.inventory_voucher_approvals (
    id BIGSERIAL PRIMARY KEY,
    voucher_id BIGINT NOT NULL REFERENCES public.inventory_vouchers(id) ON DELETE CASCADE,
    
    -- Approval details
    approval_level VARCHAR(50) NOT NULL,  -- 'department', 'finance', 'owner'
    approver_id UUID NOT NULL REFERENCES public.user_profiles(id),
    action VARCHAR(20) NOT NULL,          -- 'approved', 'rejected', 'requested_changes'
    comments TEXT,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_voucher_approvals_voucher ON public.inventory_voucher_approvals(voucher_id);
CREATE INDEX idx_voucher_approvals_approver ON public.inventory_voucher_approvals(approver_id);
```

#### 4. `inventory_voucher_attachments`
Supporting documents

```sql
CREATE TABLE public.inventory_voucher_attachments (
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

CREATE INDEX idx_voucher_attachments_voucher ON public.inventory_voucher_attachments(voucher_id);
```

---

## 🔗 Integration with Existing System

### **Modified Tables:**

#### `inventory_transactions` - Add voucher link

```sql
ALTER TABLE public.inventory_transactions 
ADD COLUMN voucher_id BIGINT REFERENCES public.inventory_vouchers(id);

CREATE INDEX idx_inventory_transactions_voucher ON public.inventory_transactions(voucher_id);
```

### **Functions to Create:**

1. **`create_purchase_voucher()`** - Create new purchase voucher
2. **`approve_voucher()`** - Approve voucher at any level
3. **`reject_voucher()`** - Reject voucher with reason
4. **`receive_goods()`** - Record goods receipt
5. **`issue_goods()`** - Record goods issue
6. **`post_voucher_to_gl()`** - Create journal entry & update inventory
7. **`get_pending_approvals()`** - Get vouchers awaiting approval
8. **`get_voucher_history()`** - Get complete audit trail

---

## 📱 UI Components Needed

### **New Pages/Dialogs:**

1. **Purchase Voucher List** (`/dashboard/inventory/purchases`)
   - Grid view of all purchase vouchers
   - Filters: Status, Date range, Vendor
   - Quick actions: Create, View, Approve

2. **Issuance Voucher List** (`/dashboard/inventory/issuances`)
   - Grid view of all issuance vouchers
   - Filters: Status, Date range, Purpose
   - Quick actions: Create, View, Approve

3. **Voucher Detail Dialog**
   - Header info (voucher number, status, requester)
   - Line items table
   - Approval history timeline
   - Attachments section
   - Action buttons (Approve/Reject/Edit)

4. **Approval Dashboard** (`/dashboard/inventory/approvals`)
   - Pending approvals requiring user action
   - Grouped by type and priority
   - Bulk approval capability

5. **Modified Inventory Page**
   - Add "Vouchers" tab alongside Items/Categories/Transactions
   - Dashboard cards: Pending Purchases, Pending Issuances, Awaiting My Approval

---

## 🎯 Benefits Summary

### **Control & Compliance:**
✅ No unauthorized inventory movement
✅ Budget enforcement before spending
✅ Multi-level authorization
✅ Complete audit trail
✅ Separation of duties

### **Operational:**
✅ Clear requisition process
✅ Vendor management integration
✅ Partial receipts/issues supported
✅ Real-time approval status
✅ Document attachment support

### **Financial:**
✅ GL posting only after approval
✅ Accurate cost tracking
✅ Budget vs. actual comparison
✅ Cost center/project allocation
✅ Proper account mapping validation

### **Reporting:**
✅ Approval time tracking
✅ Pending commitment reporting
✅ Voucher aging analysis
✅ Approver performance metrics
✅ Variance analysis (estimated vs. actual)

---

## 📈 Implementation Phases

### **Phase 1: Database & Backend** (Week 1)
- Create new tables & enums
- Write stored procedures
- Set up RLS policies
- Create API endpoints

### **Phase 2: Purchase Vouchers** (Week 2)
- Purchase voucher UI
- Approval workflow
- Goods receipt
- GL posting

### **Phase 3: Issuance Vouchers** (Week 3)
- Issuance voucher UI
- Approval workflow
- Goods issue
- GL posting

### **Phase 4: Dashboards & Reports** (Week 4)
- Approval dashboard
- Pending commitments report
- Audit trail viewer
- Performance analytics

### **Phase 5: Advanced Features** (Week 5)
- Email notifications
- Mobile approvals
- Budget integration
- Vendor portal

---

## 🚀 Next Steps

1. **Review & Approve** this flow
2. **Define approval thresholds** for your organization
3. **Identify approvers** and their roles
4. **Prioritize** which flow to implement first (Purchase or Issuance)
5. **Start implementation** with database schema

---

## 💬 Discussion Points

### Questions to Consider:

1. **Approval Levels**: Do you need more than 2 levels? (e.g., GM approval for large amounts)
2. **Thresholds**: What dollar amounts trigger different approval levels?
3. **Partial Receipts**: How important is partial receipt/issue capability?
4. **Budget Integration**: Should vouchers check budget availability automatically?
5. **Vendor Management**: Need a full vendor master table?
6. **Auto-numbering**: Voucher number format preference? (PV-YYYY-#### or other)
7. **Notifications**: Email, in-app, or both?
8. **Mobile**: Priority for mobile approval interface?
9. **Backward Compatibility**: Keep direct transaction entry for small/quick adjustments?
10. **Migration**: How to handle existing inventory data?

---

**Ready to discuss and refine! 🎉**

