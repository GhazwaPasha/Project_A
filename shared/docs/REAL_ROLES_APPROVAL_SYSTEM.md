# 🎯 Real Database Roles - Voucher Approval System

## 🎯 Overview

**Updated to match your actual database roles** from the `user_role` enum and `organization_members` table.

---

## 📊 **YOUR ACTUAL DATABASE ROLES**

Based on your database schema, you have these **4 roles**:

```sql
CREATE TYPE public.user_role AS ENUM (
    'super_admin',           -- Platform administrator with full access
    'organization_owner',    -- Full control over organization  
    'accountant',           -- Full accounting operations access
    'member'                -- Basic member access
);
```

---

## 🔄 **UPDATED APPROVAL RULES (Based on Real Roles)**

### **Role-Based Approvals (Finance Only):**

| Role | Purchase Voucher | Issuance Voucher | Can Post | Notes |
|------|-----------------|------------------|----------|-------|
| **member** | Can create/view | Can create/view | No | Any amount |
| **accountant** | Can approve | Can approve | Yes | Any amount |
| **organization_owner** | Can approve | Can approve | Yes | Any amount |
| **super_admin** | Full access | Full access | Yes | Any amount |

### **Approval Thresholds (Simplified - No Amount Limits):**

```
Purchase Amount          | Approval Required
─────────────────────────┼──────────────────────
$0 - $999,999,999        | Accountant or Organization Owner
(No amount limits)       | (Same approver for all)
```

**Note:** No owner approval needed at any amount. Accountants and Organization Owners handle everything.

---

## 🔄 **UPDATED WORKFLOW PROCESS**

### **1. Purchase Voucher Flow (Any Amount):**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ PURCHASE VOUCHER - REAL ROLES FLOW                                          │
└──────────────────────────────────────────────────────────────────────────────┘

ACTOR: Requester (member)
┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. CREATE PURCHASE VOUCHER (Any Amount)                                     │
│                                                                              │
│    Form Fields:                                                              │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Vendor Name:        [Office Depot]                           │        │
│    │ Vendor Contact:     [555-1234]                               │        │
│    │ PO Number:          [PO-2025-001]                            │        │
│    │ Payment Type:       [● Credit  ○ Cash  ○ Partial]            │        │
│    │ Expected Delivery:  [2025-10-08]                             │        │
│    │                                                               │        │
│    │ LINE ITEMS:                                                  │        │
│    │  Item          Qty Requested    Est. Cost    Total          │        │
│    │  ──────────────────────────────────────────────────────     │        │
│    │  Office Equipment [10 units]    [$1,200]    $12,000        │        │
│    │  Software Licenses [5 seats]    [$800]      $4,000         │        │
│    │  Furniture      [2 desks]       [$1,500]    $3,000         │        │
│    │                                                               │        │
│    │  Total: $19,000.00                                            │        │
│    │                                                               │        │
│    │ Justification: [Q4 IT infrastructure upgrade]                │        │
│    │                                                               │        │
│    │  [Save Draft]  [Submit for Approval]                         │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    Status: DRAFT                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Requester (member)
┌──────────────────────────────────────────────────────────────────────────────┐
│ 2. SUBMIT FOR APPROVAL (Any Amount)                                         │
│                                                                              │
│    System Actions:                                                           │
│    ✓ Validate: All required fields filled                                   │
│    ✓ Generate voucher number: PV-2025-0001                                  │
│    ✓ Assign approver: Accountant or Organization Owner                      │
│    ✓ Send notifications (email + in-app)                                    │
│    ✓ Set 48-hour deadline                                                   │
│                                                                              │
│    Status: DRAFT → PENDING_FINANCE                                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Accountant OR Organization Owner
┌──────────────────────────────────────────────────────────────────────────────┐
│ 3. FINANCE APPROVAL (Any Amount)                                            │
│                                                                              │
│    Finance Review:                                                           │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Purchase Voucher: PV-2025-0001                               │        │
│    │ Requested by: John Doe (member)                              │        │
│    │ Amount: $19,000.00 (Large Amount)                           │        │
│    │ Submitted: 2025-10-06 10:30 AM                               │        │
│    │ Deadline: 2025-10-08 10:30 AM (2 days left)                  │        │
│    │                                                               │        │
│    │ Financial Review:                                             │        │
│    │  Vendor: Office Depot (Approved Vendor) ✓                    │        │
│    │  Pricing: Within market range ✓                              │        │
│    │  GL Account: 1150 - Inventory - Equipment ✓                  │        │
│    │  Budget Available: $50,000 (sufficient) ✓                    │        │
│    │  Payment Terms: Net 30 (acceptable) ✓                        │        │
│    │                                                               │        │
│    │ Approval Comments:                                            │        │
│    │ [Approved - Large IT investment but within budget and justified] │    │
│    │                                                               │        │
│    │  [✓ APPROVE & RELEASE]  [✗ REJECT]                           │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    If APPROVE: Status → APPROVED (ready for goods receipt)                  │
│    If REJECT: Status → REJECTED (with reason)                               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓ (If Approved)
ACTOR: Warehouse / Receiving Clerk
┌──────────────────────────────────────────────────────────────────────────────┐
│ 4. GOODS RECEIPT & POSTING                                                  │
│                                                                              │
│    Receipt Form:                                                             │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Approved Purchase Voucher: PV-2025-0001                      │        │
│    │ Vendor: Office Depot                                          │        │
│    │ Amount: $19,000.00                                            │        │
│    │                                                               │        │
│    │ RECEIVING:                                                    │        │
│    │  Item                Ordered    Received    Actual Cost      │        │
│    │  ────────────────────────────────────────────────────────    │        │
│    │  Office Equipment     10 units   [10]       [$12,000.00]     │        │
│    │  Software Licenses    5 seats    [5]        [$4,000.00]      │        │
│    │  Furniture            2 desks    [2]        [$3,000.00]      │        │
│    │                                                               │        │
│    │  [✓ CONFIRM RECEIPT & POST]                                  │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    System Actions:                                                           │
│    ✓ Update inventory quantities                                            │
│    ✓ Create journal entry                                                   │
│    ✓ Link references                                                        │
│                                                                              │
│    Status: APPROVED → POSTED → COMPLETED                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### **2. Issuance Voucher Flow (Any Amount):**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ISSUANCE VOUCHER - REAL ROLES FLOW                                          │
└──────────────────────────────────────────────────────────────────────────────┘

ACTOR: Requester (member)
┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. CREATE ISSUANCE VOUCHER (Any Amount)                                     │
│                                                                              │
│    Form Fields:                                                              │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Purpose: [Large Manufacturing Order #MO-2025-001]           │        │
│    │ Destination: [Production Floor - All Lines]                 │        │
│    │ Cost Center: [CC-PROD-01]                                   │        │
│    │ Project Code: [PRJ-2025-MAJOR-PRODUCT]                      │        │
│    │                                                               │        │
│    │ DESTINATION ACCOUNT:                                         │        │
│    │ [1300 - Work in Progress ▼]                                 │        │
│    │                                                               │        │
│    │ LINE ITEMS:                                                  │        │
│    │  Item              Qty Needed    Available    Est. Cost      │        │
│    │  ──────────────────────────────────────────────────────────  │        │
│    │  Raw Material A    500 kg        [450 kg]    [$7,500]      │        │
│    │  Component B       200 pcs       [200 pcs]   [$9,000]      │        │
│    │  Special Parts     50 units      [60 units]  [$5,000]      │        │
│    │                                                               │        │
│    │  Total Cost: $21,500.00                                       │        │
│    │                                                               │        │
│    │ Justification: [Major product launch - Q4 production]        │        │
│    │                                                               │        │
│    │  [Save Draft]  [Submit for Approval]                         │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    Status: DRAFT                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Requester (member)
┌──────────────────────────────────────────────────────────────────────────────┐
│ 2. SUBMIT FOR APPROVAL (Any Amount)                                         │
│                                                                              │
│    System Actions:                                                           │
│    ✓ Validate: All required fields filled                                   │
│    ✓ Validate: Stock availability (with warning if low)                     │
│    ✓ Validate: Destination GL account exists                                │
│    ✓ Generate voucher number: IV-2025-0001                                  │
│    ✓ Assign approver: Accountant or Organization Owner                      │
│    ✓ Send notifications                                                     │
│    ✓ Set 48-hour deadline                                                   │
│                                                                              │
│    Status: DRAFT → PENDING_FINANCE                                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Accountant OR Organization Owner
┌──────────────────────────────────────────────────────────────────────────────┐
│ 3. FINANCE APPROVAL (Any Amount)                                            │
│                                                                              │
│    Finance Review:                                                           │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Issuance Voucher: IV-2025-0001                               │        │
│    │ Requested by: Mike Johnson (member)                          │        │
│    │ Purpose: Major Manufacturing Order #MO-2025-001              │        │
│    │ Cost Center: CC-PROD-01                                       │        │
│    │ Amount: $21,500.00 (Large Amount)                            │        │
│    │ Deadline: 2025-10-08 10:30 AM (2 days left)                  │        │
│    │                                                               │        │
│    │ Financial Review:                                             │        │
│    │  GL Account Check:                                            │        │
│    │    Destination: 1300 - Work in Progress ✓                     │        │
│    │    Source: 1150 - Inventory (auto-credited) ✓                │        │
│    │                                                               │        │
│    │  Budget Check:                                                │        │
│    │    Cost Center: CC-PROD-01                                    │        │
│    │    Budget Available: $100,000                                 │        │
│    │    This Issue: $21,500                                        │        │
│    │    Remaining: $78,500 ✓                                       │        │
│    │                                                               │        │
│    │  Cost Allocation: ✓ Correct                                  │        │
│    │  Project Code: ✓ Valid (PRJ-2025-MAJOR-PRODUCT)              │        │
│    │                                                               │        │
│    │ Approval Comments:                                            │        │
│    │ [Approved - Large production order but within budget and justified] │
│    │                                                               │        │
│    │  [✓ APPROVE & RELEASE]  [✗ REJECT]                           │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    If APPROVE: Status → APPROVED (ready for goods issue)                    │
│    If REJECT: Status → REJECTED (with reason)                               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓ (If Approved)
ACTOR: Warehouse / Inventory Clerk
┌──────────────────────────────────────────────────────────────────────────────┐
│ 4. GOODS ISSUE & POSTING                                                     │
│                                                                              │
│    Issue Form:                                                               │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Approved Issuance Voucher: IV-2025-0001                      │        │
│    │ Purpose: Major Manufacturing Order #MO-2025-001               │        │
│    │ Issue To: Production Floor - All Lines                        │        │
│    │ Amount: $21,500.00                                            │        │
│    │                                                               │        │
│    │ ISSUING:                                                      │        │
│    │  Item              Requested    Issued      Actual Cost       │        │
│    │  ────────────────────────────────────────────────────────     │        │
│    │  Raw Material A    500 kg       [500]      [$7,500.00]       │        │
│    │  Component B       200 pcs      [200]      [$9,000.00]       │        │
│    │  Special Parts     50 units     [50]       [$5,000.00]       │        │
│    │                                                               │        │
│    │  Received By: Mike Johnson                                    │        │
│    │  Signature: [✍]  Time: [2025-10-06 14:30]                    │        │
│    │                                                               │        │
│    │  [✓ CONFIRM ISSUE & POST]                                     │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    System Actions:                                                           │
│    ✓ Update inventory quantities                                            │
│    ✓ Create journal entry                                                   │
│    ✓ Link references                                                        │
│                                                                              │
│    Status: APPROVED → POSTED → COMPLETED                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📱 **UPDATED UI COMPONENTS**

### **1. Voucher List (Real Roles):**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Voucher List                                    [Filter: All ▼] [Refresh]    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 🟡 PV-2025-0003    $19,000.00    PENDING_FINANCE    ⏰ 2 hours left    [View]│
│ 🟡 PV-2025-0004    $45,000.00    PENDING_FINANCE    ⏰ 6 hours left    [View]│
│ 🟢 IV-2025-0012    $21,500.00    APPROVED          ⏰ 8 hours left    [View]│
│ 🔴 PV-2025-0001    $2,000.00     EXPIRED           ⏰ 2 days ago      [Renew]│
│ ✅ IV-2025-0008    $1,200.00     COMPLETED         ✓ Done            [View] │
│                                                                              │
│ Awaiting Approval (2) - Any Amount                                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### **2. Approval Dashboard (Real Roles):**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Approval Dashboard (Accountant/Organization Owner)           [Refresh]      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ ⏰ Pending My Approval (3) - Any Amount                                      │
│                                                                              │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 🟡 PV-2025-0003                              $19,000.00    Priority: High│ │
│ │    Purchase Voucher - IT Equipment                                     │ │
│ │    Requested by: John Doe (member)                                     │ │
│ │    Submitted: 2 hours ago                                               │ │
│ │    Deadline: 46 hours left                                              │ │
│ │    [Quick Approve] [View Details] [Reject]                              │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 🟡 PV-2025-0004                              $45,000.00    Priority: High│ │
│ │    Purchase Voucher - Manufacturing Equipment                          │ │
│ │    Requested by: Mike Johnson (member)                                 │ │
│ │    Submitted: 6 hours ago                                               │ │
│ │    Deadline: 42 hours left                                              │ │
│ │    [Quick Approve] [View Details] [Reject]                              │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 🟢 IV-2025-0012                              $21,500.00    Priority: High│ │
│ │    Issuance Voucher - Major Production Order                           │ │
│ │    Requested by: Sarah Lee (member)                                    │ │
│ │    Submitted: 8 hours ago                                               │ │
│ │    Deadline: 40 hours left                                              │ │
│ │    [Quick Approve] [View Details] [Reject]                              │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ Recently Approved by Me (10)                                   [View All]   │
│                                                                              │
│ • PV-2025-0002 - Approved 2 hours ago - $5,200.00                          │
│ • IV-2025-0011 - Approved yesterday - $1,850.00                            │
│ • PV-2025-0001 - Approved 3 days ago - $15,000.00                          │
│                                                                              │
│ ──────────────────────────────────────────────────────────────────────────│
│                                                                              │
│ My Approval Stats (This Month)                                             │
│                                                                              │
│ Total Approved: 24      Total Rejected: 2      Avg Time: 4.2 hours         │
│ Total Value: $156,450   Pending: 3             Fastest: 15 min             │
│ Large Amounts (>$10K): 8                      Avg Large Amount: $25,000     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### **3. Member View (Create Vouchers):**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ My Vouchers (member)                                        [Create New]    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 🟡 PV-2025-0003    $19,000.00    PENDING_FINANCE    ⏰ 2 hours left    [View]│
│ 🟡 IV-2025-0012    $21,500.00    PENDING_FINANCE    ⏰ 8 hours left    [View]│
│ ✅ PV-2025-0001    $2,000.00     COMPLETED         ✓ Done            [View] │
│ ✅ IV-2025-0008    $1,200.00     COMPLETED         ✓ Done            [View] │
│                                                                              │
│ My Voucher Stats:                                                            │
│ ├─ Total Created: 15                                                         │
│ ├─ Pending Approval: 2                                                       │
│ ├─ Approved: 12                                                              │
│ ├─ Rejected: 1                                                               │
│ └─ Total Value: $89,500                                                      │
│                                                                              │
│ [Create Purchase Voucher] [Create Issuance Voucher]                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔔 **UPDATED NOTIFICATIONS**

### **Email Notifications (Real Roles):**

```
Subject: ⏰ Voucher PV-2025-0003 Needs Approval ($19,000)

Dear Finance Team,

A new voucher requires your approval:

Voucher: PV-2025-0003
Type: Purchase Voucher
Amount: $19,000.00 (Large Amount)
Requested by: John Doe (member)
Submitted: 2025-10-06 10:30 AM
Deadline: 2025-10-08 10:30 AM (48 hours)

Items: IT Equipment, Software Licenses, Furniture
Justification: Q4 IT infrastructure upgrade

Please review and approve or reject this voucher.

[Approve Now] [View Details] [Reject]

Best regards,
Accountuitive System
```

### **In-App Notifications (Real Roles):**

```
🔔 Notifications (3)

⏰ PV-2025-0003 needs approval - $19,000 (Large)
   IT Equipment - Requested by John Doe (member)
   [Approve] [View]

⏰ PV-2025-0004 needs approval - $45,000 (Large)
   Manufacturing Equipment - Requested by Mike Johnson (member)
   [Approve] [View]

⏰ IV-2025-0012 needs approval - $21,500 (Large)
   Major Production Order - Requested by Sarah Lee (member)
   [Approve] [View]

✅ PV-2025-0002 approved - $5,200
   Approved 2 hours ago
   [View]

🔴 PV-2025-0001 expired - $2,000
   Expired 2 days ago (items hidden)
   [Renew] [View]
```

---

## 📊 **UPDATED DATABASE FUNCTIONS**

### **Approval Assignment Logic:**

```sql
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
```

### **Permission Check Function:**

```sql
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
```

---

## 🎯 **BENEFITS OF REAL ROLES SYSTEM**

### **1. Matches Your Database:**
- ✅ **Uses actual roles** from your `user_role` enum
- ✅ **Leverages existing** `organization_members` table
- ✅ **Consistent with** current permission system
- ✅ **No new roles** needed

### **2. Clear Role Hierarchy:**
- ✅ **member** → Can create vouchers
- ✅ **accountant** → Can approve vouchers
- ✅ **organization_owner** → Can approve vouchers
- ✅ **super_admin** → Full access

### **3. Simple Assignment:**
- ✅ **Accountants first** (primary approvers)
- ✅ **Organization owners** as backup
- ✅ **No complex routing** logic needed

### **4. Existing Integration:**
- ✅ **Uses `get_user_organization_role()`** function
- ✅ **Leverages RLS policies** already in place
- ✅ **Consistent with** inventory permissions

---

## ✅ **IMPLEMENTATION CHECKLIST**

- [ ] Update approval assignment logic (accountant/org_owner)
- [ ] Modify permission checks to use real roles
- [ ] Update UI to show correct role names
- [ ] Test with actual database roles
- [ ] Verify RLS policies work with voucher system
- [ ] Update notifications to use real role names
- [ ] Test approval workflow with different roles

---

## 🎯 **SUMMARY**

**Real Roles Approval System:**

1. **member** → Creates vouchers (any amount)
2. **accountant** → Approves vouchers (any amount)
3. **organization_owner** → Approves vouchers (any amount)
4. **super_admin** → Full access

**Key Benefits:**
- ✅ **Matches your actual database** roles
- ✅ **Uses existing** permission system
- ✅ **No new roles** required
- ✅ **Simple assignment** logic
- ✅ **Consistent with** current system

**This system perfectly aligns with your existing database structure and role system!** 🎉

---

**Ready to implement this real roles approval system? This will integrate seamlessly with your existing user management!**
