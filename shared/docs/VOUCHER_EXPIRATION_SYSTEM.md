# ⏰ Voucher Expiration & Renewal System

## 🎯 Overview

**48-Hour Approval Deadline** with automatic expiration and inventory hiding for unapproved vouchers.

---

## ⏱️ **EXPIRATION RULES**

### **Approval Deadline: 48 Hours**
- Purchase Vouchers: Must be approved within 48 hours of submission
- Issuance Vouchers: Must be approved within 48 hours of submission
- **Auto-expiration** if not approved in time
- **Inventory hiding** for expired vouchers
- **Renewal process** to reactivate expired vouchers

---

## 🔄 **UPDATED STATUS WORKFLOW**

### **New Status: EXPIRED**

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
                                                                                  |
                                                                        ⏰ 48hrs   |
                                                                                  ↓
                                                                             EXPIRED
                                                                                  |
                                                                        renew     |
                                                                                  ↓
                                                                              DRAFT
```

### **Expiration Triggers:**
- **PENDING** status for 48+ hours → **EXPIRED**
- **PENDING_FINANCE** status for 48+ hours → **EXPIRED**
- **APPROVED** status for 48+ hours (if not executed) → **EXPIRED**

---

## 📊 **DATABASE SCHEMA UPDATES**

### **1. Add Expiration Fields to `inventory_vouchers`:**

```sql
-- Add expiration tracking fields
ALTER TABLE public.inventory_vouchers
ADD COLUMN submitted_at TIMESTAMP WITH TIME ZONE,  -- When submitted for approval
ADD COLUMN approval_deadline TIMESTAMP WITH TIME ZONE,  -- 48 hours from submission
ADD COLUMN expired_at TIMESTAMP WITH TIME ZONE,  -- When it expired
ADD COLUMN renewed_at TIMESTAMP WITH TIME ZONE,  -- When it was renewed
ADD COLUMN renewal_count INTEGER DEFAULT 0,  -- How many times renewed
ADD COLUMN renewal_reason TEXT;  -- Why it was renewed

-- Update status enum to include EXPIRED
ALTER TYPE public.inventory_voucher_status 
ADD VALUE 'expired';

-- Add index for expiration queries
CREATE INDEX idx_inventory_vouchers_deadline ON public.inventory_vouchers(approval_deadline);
CREATE INDEX idx_inventory_vouchers_expired ON public.inventory_vouchers(expired_at);
```

### **2. Create Expiration Tracking Table:**

```sql
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

CREATE INDEX idx_voucher_expiration_voucher ON public.voucher_expiration_log(voucher_id);
CREATE INDEX idx_voucher_expiration_expired_at ON public.voucher_expiration_log(expired_at);
```

---

## 🔧 **AUTOMATIC EXPIRATION SYSTEM**

### **1. Background Job (Every 15 minutes):**

```sql
-- Function to expire overdue vouchers
CREATE OR REPLACE FUNCTION public.expire_overdue_vouchers()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER := 0;
    voucher_record RECORD;
BEGIN
    -- Find vouchers that should be expired
    FOR voucher_record IN
        SELECT v.id, v.voucher_number, v.status, v.approval_deadline,
               v.total_estimated_cost, v.organization_id
        FROM public.inventory_vouchers v
        WHERE v.status IN ('pending', 'pending_finance', 'approved')
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
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.expire_overdue_vouchers() TO authenticated;
```

### **2. Scheduled Job Setup:**

```sql
-- Create a function to run expiration check
CREATE OR REPLACE FUNCTION public.run_voucher_expiration_check()
RETURNS void AS $$
BEGIN
    -- Expire overdue vouchers
    PERFORM public.expire_overdue_vouchers();
    
    -- Log the check
    INSERT INTO public.system_logs (action, details, created_at)
    VALUES ('voucher_expiration_check', 
            'Expired ' || public.expire_overdue_vouchers() || ' vouchers',
            NOW());
END;
$$ LANGUAGE plpgsql;
```

---

## 👁️ **INVENTORY HIDING SYSTEM**

### **1. Modified Inventory Queries:**

```sql
-- Function to get available inventory (excluding expired voucher items)
CREATE OR REPLACE FUNCTION public.get_available_inventory(org_id UUID)
RETURNS TABLE (
    item_id BIGINT,
    sku VARCHAR,
    name VARCHAR,
    quantity_available DECIMAL,
    total_value DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.sku,
        i.name,
        i.quantity_available,
        i.total_value
    FROM public.inventory_items i
    WHERE i.organization_id = org_id
    AND i.is_active = true
    AND i.id NOT IN (
        -- Exclude items in expired vouchers
        SELECT DISTINCT vl.item_id
        FROM public.inventory_voucher_lines vl
        JOIN public.inventory_vouchers v ON vl.voucher_id = v.id
        WHERE v.organization_id = org_id
        AND v.status = 'expired'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get inventory with expired items (for admin view)
CREATE OR REPLACE FUNCTION public.get_inventory_with_expired(org_id UUID)
RETURNS TABLE (
    item_id BIGINT,
    sku VARCHAR,
    name VARCHAR,
    quantity_available DECIMAL,
    total_value DECIMAL,
    is_in_expired_voucher BOOLEAN,
    expired_voucher_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.sku,
        i.name,
        i.quantity_available,
        i.total_value,
        CASE WHEN ev.item_id IS NOT NULL THEN true ELSE false END,
        COALESCE(ev.expired_count, 0)
    FROM public.inventory_items i
    LEFT JOIN (
        SELECT 
            vl.item_id,
            COUNT(DISTINCT v.id) as expired_count
        FROM public.inventory_voucher_lines vl
        JOIN public.inventory_vouchers v ON vl.voucher_id = v.id
        WHERE v.organization_id = org_id
        AND v.status = 'expired'
        GROUP BY vl.item_id
    ) ev ON i.id = ev.item_id
    WHERE i.organization_id = org_id
    AND i.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

## 🔄 **VOUCHER RENEWAL SYSTEM**

### **1. Renewal Process:**

```sql
-- Function to renew an expired voucher
CREATE OR REPLACE FUNCTION public.renew_expired_voucher(
    voucher_id BIGINT,
    renewed_by UUID,
    renewal_reason TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### **2. Renewal UI Form:**

```
┌──────────────────────────────────────────────────────────────┐
│ Renew Expired Voucher                                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Voucher: PV-2025-0001 (EXPIRED)                             │
│ Original Submission: 2025-10-04 10:30 AM                    │
│ Expired: 2025-10-06 10:30 AM (48 hours ago)                 │
│ Renewal Count: 2 (previously renewed)                       │
│                                                              │
│ Items in Voucher:                                            │
│ ├─ Office Supplies (50 boxes) - $2,000                      │
│ └─ Printer Toner (10 units) - $1,450                        │
│                                                              │
│ Renewal Reason:                                              │
│ [_________________________________________]                  │
│                                                              │
│ ⚠️  WARNING: Renewing will make these items                  │
│    available for other vouchers again!                      │
│                                                              │
│ [Cancel]  [Renew Voucher]                                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 **UPDATED VOUCHER SUBMISSION LOGIC**

### **When Submitting for Approval:**

```javascript
function submitVoucherForApproval(voucherId) {
  const now = new Date();
  const deadline = new Date(now.getTime() + (48 * 60 * 60 * 1000)); // 48 hours
  
  // Update voucher with deadline
  await updateVoucher(voucherId, {
    status: 'pending',
    submitted_at: now,
    approval_deadline: deadline,
    updated_at: now
  });
  
  // Send notifications to approvers
  await notifyApprovers(voucherId, deadline);
  
  // Schedule expiration check (if not already scheduled)
  await scheduleExpirationCheck(voucherId, deadline);
}
```

---

## 🎯 **UI UPDATES NEEDED**

### **1. Voucher List with Expiration Status:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Voucher List                                    [Filter: All ▼] [Refresh]    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 🟡 PV-2025-0003    $12,450.00    PENDING     ⏰ 2 hours left    [View]      │
│ 🟢 IV-2025-0012    $3,750.00     APPROVED    ⏰ 6 hours left    [View]      │
│ 🔴 PV-2025-0001    $2,000.00     EXPIRED     ⏰ 2 days ago      [Renew]     │
│ 🔴 IV-2025-0008    $1,200.00     EXPIRED     ⏰ 1 day ago       [Renew]     │
│                                                                              │
│ Expired Vouchers (2) - Items hidden from inventory                          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### **2. Expiration Dashboard:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Voucher Expiration Dashboard                                  [Refresh]      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ ⏰ Pending Approval (3)                                                      │
│ ├─ PV-2025-0003 - $12,450 - 2 hours left - [Urgent]                        │
│ ├─ IV-2025-0012 - $3,750 - 6 hours left                                    │
│ └─ PV-2025-0005 - $8,200 - 12 hours left                                   │
│                                                                              │
│ 🔴 Expired Vouchers (2)                                                     │
│ ├─ PV-2025-0001 - $2,000 - 2 days ago - [Renew]                            │
│ └─ IV-2025-0008 - $1,200 - 1 day ago - [Renew]                             │
│                                                                              │
│ 📊 This Month Stats:                                                        │
│ ├─ Total Submitted: 45                                                      │
│ ├─ Approved on Time: 42 (93%)                                               │
│ ├─ Expired: 3 (7%)                                                          │
│ └─ Average Approval Time: 18 hours                                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### **3. Inventory Page with Expired Items:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Inventory Items                               [Show Expired ▼] [Refresh]     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ SKU        Name                Available    Value      Status               │
│ ──────────────────────────────────────────────────────────────────────────  │
│ OFF-001    Office Supplies     450 boxes    $18,000    ✅ Available         │
│ TON-002    Printer Toner       200 units    $8,000     ✅ Available         │
│ PAP-003    Paper Reams         150 reams    $1,500     ✅ Available         │
│                                                                              │
│ ──────────────────────────────────────────────────────────────────────────  │
│ 🔴 HIDDEN ITEMS (In Expired Vouchers):                                      │
│ OFF-004    Special Paper       50 boxes     $2,000     ❌ In PV-2025-0001   │
│ TON-005    Color Toner         20 units     $1,200     ❌ In IV-2025-0008   │
│                                                                              │
│ [Renew All Expired Vouchers] [View Expired Vouchers]                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔔 **NOTIFICATION SYSTEM**

### **Email Notifications:**

```
Subject: ⏰ Voucher PV-2025-0003 Expires in 2 Hours

Dear Approver,

The following voucher is approaching its 48-hour approval deadline:

Voucher: PV-2025-0003
Amount: $12,450.00
Submitted: 2025-10-04 10:30 AM
Deadline: 2025-10-06 10:30 AM (2 hours left)
Items: Office Equipment, Software Licenses

Please approve or reject this voucher before it expires.

[Approve Now] [View Details] [Reject]

If this voucher expires, the items will be hidden from inventory and the voucher will need to be renewed.

Best regards,
Accountuitive System
```

### **In-App Notifications:**

```
🔔 Notifications (3)

⏰ PV-2025-0003 expires in 2 hours
   Office Equipment purchase - $12,450
   [Approve] [View]

⏰ IV-2025-0012 expires in 6 hours  
   Raw materials for production - $3,750
   [Approve] [View]

🔴 PV-2025-0001 expired 2 days ago
   Special paper - $2,000 (items hidden)
   [Renew] [View]
```

---

## 📈 **REPORTING & ANALYTICS**

### **1. Expiration Report:**

```sql
-- Voucher expiration analytics
SELECT 
    DATE_TRUNC('day', submitted_at) as submission_date,
    COUNT(*) as total_submitted,
    COUNT(CASE WHEN status != 'expired' THEN 1 END) as approved_on_time,
    COUNT(CASE WHEN status = 'expired' THEN 1 END) as expired,
    ROUND(
        COUNT(CASE WHEN status != 'expired' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as approval_rate_percent,
    AVG(EXTRACT(EPOCH FROM (COALESCE(approved_at, expired_at) - submitted_at))/3600) as avg_hours_to_resolution
FROM public.inventory_vouchers
WHERE submitted_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', submitted_at)
ORDER BY submission_date DESC;
```

### **2. Hidden Inventory Report:**

```sql
-- Items hidden due to expired vouchers
SELECT 
    i.sku,
    i.name,
    COUNT(DISTINCT v.id) as expired_voucher_count,
    SUM(vl.quantity_requested) as total_quantity_hidden,
    SUM(vl.quantity_requested * COALESCE(vl.unit_cost_estimated, 0)) as total_value_hidden
FROM public.inventory_items i
JOIN public.inventory_voucher_lines vl ON i.id = vl.item_id
JOIN public.inventory_vouchers v ON vl.voucher_id = v.id
WHERE v.status = 'expired'
GROUP BY i.id, i.sku, i.name
ORDER BY total_value_hidden DESC;
```

---

## ⚙️ **SYSTEM CONFIGURATION**

### **Configurable Settings:**

```sql
-- System configuration table
CREATE TABLE public.system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Insert default settings
INSERT INTO public.system_config (key, value, description) VALUES
('voucher_approval_deadline_hours', '48', 'Hours before voucher expires'),
('voucher_expiration_check_interval_minutes', '15', 'How often to check for expired vouchers'),
('voucher_renewal_max_count', '3', 'Maximum number of times a voucher can be renewed'),
('voucher_expiration_notification_hours', '2,6,12,24', 'When to send expiration warnings');
```

---

## 🎯 **BENEFITS OF THIS SYSTEM**

### **1. Prevents Stale Vouchers:**
- ✅ No vouchers sitting in pending state forever
- ✅ Forces timely decision making
- ✅ Keeps approval queue clean

### **2. Inventory Protection:**
- ✅ Prevents double-booking of inventory
- ✅ Hides items from expired vouchers
- ✅ Clear visibility of what's available

### **3. Accountability:**
- ✅ Tracks approval performance
- ✅ Identifies bottlenecks
- ✅ Measures system efficiency

### **4. Flexibility:**
- ✅ Renewal process for legitimate delays
- ✅ Reason tracking for renewals
- ✅ Configurable deadlines

---

## ✅ **IMPLEMENTATION CHECKLIST**

- [ ] Add expiration fields to `inventory_vouchers` table
- [ ] Create `voucher_expiration_log` table
- [ ] Implement `expire_overdue_vouchers()` function
- [ ] Set up scheduled job (every 15 minutes)
- [ ] Modify inventory queries to hide expired items
- [ ] Create renewal function and UI
- [ ] Add expiration notifications (email + in-app)
- [ ] Update voucher list UI with expiration status
- [ ] Create expiration dashboard
- [ ] Add expiration analytics and reports
- [ ] Test expiration and renewal flows

---

**This system ensures timely approvals while maintaining inventory accuracy! 🎉**

The 48-hour deadline creates urgency for approvers while the renewal process provides flexibility for legitimate delays. The inventory hiding prevents double-booking and maintains data integrity.
