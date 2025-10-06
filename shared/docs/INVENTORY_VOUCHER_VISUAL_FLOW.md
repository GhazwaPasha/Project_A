# 📊 Inventory Voucher System - Visual Flow Diagrams

## 🎨 Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      INVENTORY VOUCHER SYSTEM ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   REQUESTER  │
                              │   (Member)   │
                              └───────┬──────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ↓                                   ↓
          ┌─────────────────┐               ┌─────────────────┐
          │  PURCHASE        │               │  ISSUANCE       │
          │  VOUCHER         │               │  VOUCHER        │
          │  (Inventory IN)  │               │  (Inventory OUT)│
          └────────┬─────────┘               └────────┬────────┘
                   │                                  │
                   │  Status: DRAFT                   │  Status: DRAFT
                   │                                  │
                   ↓                                  ↓
          ┌─────────────────┐               ┌─────────────────┐
          │  Submit for     │               │  Submit for     │
          │  Approval       │               │  Approval       │
          └────────┬─────────┘               └────────┬────────┘
                   │                                  │
                   │  Status: PENDING                 │  Status: PENDING
                   │                                  │
                   ↓                                  ↓
          ┌─────────────────┐               ┌─────────────────┐
          │  DEPT MANAGER   │               │  DEPT MANAGER   │
          │  Approval       │               │  Approval       │
          └────────┬─────────┘               └────────┬────────┘
                   │                                  │
         ┌─────────┼─────────┐              ┌─────────┼─────────┐
         │         │         │              │         │         │
    APPROVE    REJECT   REQUEST         APPROVE    REJECT   REQUEST
                         CHANGES                            CHANGES
         │         │         │              │         │         │
         │         └────┐    └───────┐      │         └────┐    └───────┐
         │              ↓            ↓      │              ↓            ↓
         │         Back to DRAFT     │      │         Back to DRAFT     │
         │                           │      │                           │
         ↓              │            │      ↓              │            │
  Status: PENDING_FINANCE            │  Status: PENDING_FINANCE         │
         │              │            │      │              │            │
         ↓              │            │      ↓              │            │
  ┌─────────────────┐   │            │  ┌─────────────────┐   │        │
  │  FINANCE/       │   │            │  │  FINANCE/       │   │        │
  │  ACCOUNTANT     │   │            │  │  ACCOUNTANT     │   │        │
  │  Approval       │   │            │  │  Approval       │   │        │
  └────────┬────────┘   │            │  └────────┬────────┘   │        │
           │            │            │           │            │        │
  ┌────────┼────────┐   │            │  ┌────────┼────────┐   │        │
  │        │        │   │            │  │        │        │   │        │
APPROVE REJECT  REQUEST │            │ APPROVE REJECT  REQUEST │        │
                 CHANGES│            │                  CHANGES│        │
  │        │        │   │            │  │        │        │   │        │
  │        └────────┴───┴────────────┘  │        └────────┴───┴────────┘
  │                                     │
  ↓                                     ↓
Status: APPROVED                  Status: APPROVED
  │                                     │
  │  Ready for Execution                │  Ready for Execution
  │                                     │
  ↓                                     ↓
┌─────────────────┐               ┌─────────────────┐
│  WAREHOUSE      │               │  WAREHOUSE      │
│  Receive Goods  │               │  Issue Goods    │
└────────┬────────┘               └────────┬────────┘
         │                                 │
         │  Status: RECEIVING              │  Status: ISSUING
         │                                 │
         ↓                                 ↓
┌─────────────────┐               ┌─────────────────┐
│  AUTO POSTING   │               │  AUTO POSTING   │
│  - Update Inv   │               │  - Update Inv   │
│  - Create JE    │               │  - Create JE    │
└────────┬────────┘               └────────┬────────┘
         │                                 │
         │  Status: POSTED                 │  Status: POSTED
         │                                 │
         ↓                                 ↓
┌─────────────────┐               ┌─────────────────┐
│   COMPLETED     │               │   COMPLETED     │
│   (Locked)      │               │   (Locked)      │
└─────────────────┘               └─────────────────┘
```

---

## 🛒 Purchase Voucher Detailed Flow

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          PURCHASE VOUCHER WORKFLOW                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝

ACTOR: Requester (Any Member)
┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. CREATE PURCHASE VOUCHER                                                   │
│                                                                              │
│    Form Fields:                                                              │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Vendor Name:        [___________________________]            │        │
│    │ Vendor Contact:     [___________________________]            │        │
│    │ PO Number:          [___________________________]            │        │
│    │ Expected Delivery:  [___________________________]            │        │
│    │ Description:        [___________________________]            │        │
│    │                                                               │        │
│    │ LINE ITEMS:                                                  │        │
│    │  Item          Qty Requested    Est. Cost    Total          │        │
│    │  ──────────────────────────────────────────────────────     │        │
│    │  [Select]      [_____]          [_____]      $_____         │        │
│    │  [Select]      [_____]          [_____]      $_____         │        │
│    │                                                               │        │
│    │  [+ Add Line]                    TOTAL: $_________           │        │
│    │                                                               │        │
│    │ Justification:      [___________________________]            │        │
│    │ Attachments:        [📎 Upload PO, Quotes]                   │        │
│    │                                                               │        │
│    │  [Save Draft]  [Submit for Approval]                         │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    Status: DRAFT                                                             │
│    Voucher #: (Auto-generated on submit)                                     │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Requester
┌──────────────────────────────────────────────────────────────────────────────┐
│ 2. SUBMIT FOR APPROVAL                                                       │
│                                                                              │
│    System Actions:                                                           │
│    ✓ Validate: All required fields filled                                   │
│    ✓ Generate voucher number: PV-2025-0001                                  │
│    ✓ Check approval threshold:                                              │
│        If amount < $1,000    → Dept Manager only                            │
│        If amount < $5,000    → Dept + Finance                               │
│        If amount > $5,000    → Dept + Finance + Owner                       │
│    ✓ Assign approvers                                                       │
│    ✓ Send notifications (email + in-app)                                    │
│                                                                              │
│    Status: DRAFT → PENDING                                                  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Department Manager
┌──────────────────────────────────────────────────────────────────────────────┐
│ 3. DEPARTMENT APPROVAL                                                       │
│                                                                              │
│    Approval View:                                                            │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Purchase Voucher: PV-2025-0001                               │        │
│    │ Requested by: John Doe (Sales Dept)                          │        │
│    │ Date: 2025-10-06                                             │        │
│    │ Total: $3,450.00                                             │        │
│    │                                                               │        │
│    │ Items:                                                        │        │
│    │  • Office Supplies (50 boxes) - $2,000                       │        │
│    │  • Printer Toner (10 units) - $1,450                         │        │
│    │                                                               │        │
│    │ Justification: Q4 sales campaign materials                   │        │
│    │                                                               │        │
│    │ Budget Check: ✓ Within department budget                     │        │
│    │                                                               │        │
│    │ Approval Comments:                                            │        │
│    │ [_________________________________________]                   │        │
│    │                                                               │        │
│    │  [✓ APPROVE]  [✗ REJECT]  [↩ REQUEST CHANGES]               │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    If APPROVE: Status → PENDING_FINANCE                                     │
│    If REJECT: Status → REJECTED (with reason)                               │
│    If REQUEST CHANGES: Status → DRAFT (with comments)                       │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓ (If Approved)
ACTOR: Finance Manager / Accountant
┌──────────────────────────────────────────────────────────────────────────────┐
│ 4. FINANCE APPROVAL                                                          │
│                                                                              │
│    Finance Review:                                                           │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Purchase Voucher: PV-2025-0001                               │        │
│    │ Department Approved: ✓ Jane Smith (Dept Mgr)                 │        │
│    │ Approved at: 2025-10-06 10:30 AM                             │        │
│    │                                                               │        │
│    │ Financial Review:                                             │        │
│    │  Vendor: Office Depot (Approved Vendor) ✓                    │        │
│    │  Pricing: Within market range ✓                              │        │
│    │  GL Account: 1150 - Inventory - Supplies ✓                   │        │
│    │  Budget Available: $15,450 (sufficient) ✓                    │        │
│    │                                                               │        │
│    │ Approval Comments:                                            │        │
│    │ [_________________________________________]                   │        │
│    │                                                               │        │
│    │  [✓ APPROVE & RELEASE]  [✗ REJECT]                           │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    If APPROVE: Status → APPROVED (ready for goods receipt)                  │
│    If REJECT: Status → REJECTED                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓ (If Approved)
ACTOR: Warehouse / Receiving Clerk
┌──────────────────────────────────────────────────────────────────────────────┐
│ 5. GOODS RECEIPT                                                             │
│                                                                              │
│    Receipt Form:                                                             │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Approved Purchase Voucher: PV-2025-0001                      │        │
│    │ Vendor: Office Depot                                          │        │
│    │                                                               │        │
│    │ RECEIVING:                                                    │        │
│    │  Item                Ordered    Received    Actual Cost      │        │
│    │  ────────────────────────────────────────────────────────    │        │
│    │  Office Supplies     50 boxes   [50]       [$2,000.00]      │        │
│    │  Printer Toner       10 units   [10]       [$1,450.00]      │        │
│    │                                                               │        │
│    │  Total Received: $3,450.00                                   │        │
│    │                                                               │        │
│    │ Receipt Notes:                                                │        │
│    │ [All items in good condition]                                │        │
│    │                                                               │        │
│    │ Attachments: [📎 Upload Delivery Note, Invoice]             │        │
│    │                                                               │        │
│    │  [ ] Partial Receipt  [✓] Complete Receipt                   │        │
│    │                                                               │        │
│    │  [✓ CONFIRM RECEIPT & POST]                                  │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    Status: APPROVED → RECEIVING → POSTED                                    │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: System (Automatic)
┌──────────────────────────────────────────────────────────────────────────────┐
│ 6. AUTOMATIC POSTING                                                         │
│                                                                              │
│    System Actions:                                                           │
│                                                                              │
│    ① Update Inventory:                                                      │
│       Office Supplies:                                                       │
│         quantity_in: 0 → 50                                                 │
│         quantity_available: 0 → 50                                          │
│       Printer Toner:                                                         │
│         quantity_in: 0 → 10                                                 │
│         quantity_available: 0 → 10                                          │
│                                                                              │
│    ② Create Inventory Transactions:                                         │
│       Transaction #1: Office Supplies IN, +50 boxes, $2,000                 │
│       Transaction #2: Printer Toner IN, +10 units, $1,450                   │
│                                                                              │
│    ③ Create Journal Entry (JE-2025-0245):                                   │
│       Date: 2025-10-06                                                       │
│       Description: Purchase per PV-2025-0001 - Office Supplies              │
│                                                                              │
│       Account                              Debit        Credit              │
│       ───────────────────────────────────────────────────────────           │
│       1150 - Inventory - Supplies          $3,450.00                        │
│       2000 - Accounts Payable                           $3,450.00           │
│                                            ─────────    ─────────           │
│       TOTALS                               $3,450.00    $3,450.00           │
│                                                                              │
│    ④ Link References:                                                       │
│       inventory_transactions.voucher_id = PV-2025-0001                      │
│       inventory_transactions.journal_entry_id = JE-2025-0245                │
│       inventory_vouchers.journal_entry_id = JE-2025-0245                    │
│                                                                              │
│    Status: POSTED → COMPLETED                                               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 7. COMPLETED                                                                 │
│                                                                              │
│    ✓ Voucher locked (read-only)                                             │
│    ✓ Inventory updated                                                      │
│    ✓ GL posted                                                              │
│    ✓ Full audit trail available                                             │
│    ✓ Reports updated                                                        │
│                                                                              │
│    Status: COMPLETED                                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📤 Issuance Voucher Detailed Flow

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          ISSUANCE VOUCHER WORKFLOW                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝

ACTOR: Requester (Any Member)
┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. CREATE ISSUANCE VOUCHER                                                   │
│                                                                              │
│    Form Fields:                                                              │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Purpose:            [Manufacturing Order #MO-1234]           │        │
│    │ Destination:        [Production Floor - Assembly Line 2]     │        │
│    │ Cost Center:        [CC-PROD-01]                             │        │
│    │ Project Code:       [PRJ-2025-WIDGET]                        │        │
│    │ Required Date:      [___________________________]            │        │
│    │                                                               │        │
│    │ Destination GL Account:                                       │        │
│    │ [5300 - Manufacturing Overhead ▼]                            │        │
│    │                                                               │        │
│    │ LINE ITEMS:                                                  │        │
│    │  Item              Qty Needed    Available    Est. Cost      │        │
│    │  ──────────────────────────────────────────────────────────  │        │
│    │  Raw Material A    [100 kg]      [450 kg]    $_____         │        │
│    │  Component B       [50 pcs]      [200 pcs]   $_____         │        │
│    │                                                               │        │
│    │  [+ Add Line]                    TOTAL: $_________           │        │
│    │                                                               │        │
│    │ Stock Check: ✓ All items available                           │        │
│    │                                                               │        │
│    │ Justification:      [___________________________]            │        │
│    │                                                               │        │
│    │  [Save Draft]  [Submit for Approval]                         │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    Status: DRAFT                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Requester
┌──────────────────────────────────────────────────────────────────────────────┐
│ 2. SUBMIT FOR APPROVAL                                                       │
│                                                                              │
│    System Actions:                                                           │
│    ✓ Validate: All required fields filled                                   │
│    ✓ Validate: Stock availability (with warning if low)                     │
│    ✓ Validate: Destination GL account exists                                │
│    ✓ Generate voucher number: IV-2025-0001                                  │
│    ✓ Assign approvers based on cost center                                  │
│    ✓ Send notifications                                                     │
│                                                                              │
│    Status: DRAFT → PENDING                                                  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Department Manager (Production)
┌──────────────────────────────────────────────────────────────────────────────┐
│ 3. DEPARTMENT APPROVAL                                                       │
│                                                                              │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Issuance Voucher: IV-2025-0001                               │        │
│    │ Requested by: Mike Johnson (Production Supervisor)            │        │
│    │ Purpose: Manufacturing Order #MO-1234                         │        │
│    │ Cost Center: CC-PROD-01 (Your department)                     │        │
│    │                                                               │        │
│    │ Items to Issue:                                               │        │
│    │  • Raw Material A: 100 kg (Est. $1,500)                      │        │
│    │  • Component B: 50 pcs (Est. $2,250)                         │        │
│    │                                                               │        │
│    │ Stock Check: ✓ All available                                 │        │
│    │                                                               │        │
│    │ Purpose Valid? [✓] Yes  [ ] No                                │        │
│    │                                                               │        │
│    │ Comments:                                                     │        │
│    │ [Approved for MO-1234 - Q4 Widget Production]                │        │
│    │                                                               │        │
│    │  [✓ APPROVE]  [✗ REJECT]                                     │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    Status: PENDING → PENDING_FINANCE                                        │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Finance Manager / Accountant
┌──────────────────────────────────────────────────────────────────────────────┐
│ 4. FINANCE APPROVAL                                                          │
│                                                                              │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Issuance Voucher: IV-2025-0001                               │        │
│    │ Department Approved: ✓ Sarah Lee (Production Mgr)            │        │
│    │                                                               │        │
│    │ Financial Review:                                             │        │
│    │  GL Account Check:                                            │        │
│    │    Destination: 5300 - Manufacturing Overhead ✓               │        │
│    │    Source: 1150 - Inventory (auto-credited) ✓                │        │
│    │                                                               │        │
│    │  Budget Check:                                                │        │
│    │    Cost Center: CC-PROD-01                                    │        │
│    │    Budget Available: $25,000                                  │        │
│    │    This Issue: $3,750                                         │        │
│    │    Remaining: $21,250 ✓                                       │        │
│    │                                                               │        │
│    │  Cost Allocation: ✓ Correct                                  │        │
│    │  Project Code: ✓ Valid (PRJ-2025-WIDGET)                     │        │
│    │                                                               │        │
│    │ Comments:                                                     │        │
│    │ [Approved - properly allocated to project]                   │        │
│    │                                                               │        │
│    │  [✓ APPROVE & RELEASE]                                        │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    Status: PENDING_FINANCE → APPROVED                                       │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: Warehouse / Inventory Clerk
┌──────────────────────────────────────────────────────────────────────────────┐
│ 5. GOODS ISSUE                                                               │
│                                                                              │
│    Issue Form:                                                               │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ Approved Issuance Voucher: IV-2025-0001                      │        │
│    │ Purpose: Manufacturing Order #MO-1234                         │        │
│    │ Issue To: Production Floor - Assembly Line 2                  │        │
│    │                                                               │        │
│    │ ISSUING:                                                      │        │
│    │  Item              Requested    Issued      Actual Cost       │        │
│    │  ────────────────────────────────────────────────────────     │        │
│    │  Raw Material A    100 kg       [100]       [$1,500.00]      │        │
│    │  Component B       50 pcs       [50]        [$2,250.00]      │        │
│    │                                                               │        │
│    │  Total Issued: $3,750.00                                      │        │
│    │                                                               │        │
│    │ Received By:                                                  │        │
│    │ Name: [Mike Johnson]                                          │        │
│    │ Signature: [✍]                                                │        │
│    │ Time: [2025-10-06 14:30]                                      │        │
│    │                                                               │        │
│    │ Issue Notes:                                                  │        │
│    │ [Items issued for MO-1234, all in good condition]            │        │
│    │                                                               │        │
│    │  [✓ CONFIRM ISSUE & POST]                                     │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                              │
│    Status: APPROVED → ISSUING → POSTED                                      │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
ACTOR: System (Automatic)
┌──────────────────────────────────────────────────────────────────────────────┐
│ 6. AUTOMATIC POSTING                                                         │
│                                                                              │
│    System Actions:                                                           │
│                                                                              │
│    ① Update Inventory:                                                      │
│       Raw Material A:                                                        │
│         quantity_out: 0 → 100                                               │
│         quantity_available: 450 → 350                                       │
│       Component B:                                                           │
│         quantity_out: 0 → 50                                                │
│         quantity_available: 200 → 150                                       │
│                                                                              │
│    ② Create Inventory Transactions:                                         │
│       Transaction #1: Raw Material A OUT, -100 kg, $1,500                   │
│       Transaction #2: Component B OUT, -50 pcs, $2,250                      │
│                                                                              │
│    ③ Create Journal Entry (JE-2025-0246):                                   │
│       Date: 2025-10-06                                                       │
│       Description: Issue per IV-2025-0001 - MO-1234 Production              │
│       Reference: PRJ-2025-WIDGET                                             │
│                                                                              │
│       Account                              Debit        Credit              │
│       ───────────────────────────────────────────────────────────           │
│       5300 - Manufacturing Overhead        $3,750.00                        │
│       1150 - Inventory                                  $3,750.00           │
│                                            ─────────    ─────────           │
│       TOTALS                               $3,750.00    $3,750.00           │
│                                                                              │
│       Cost Center: CC-PROD-01                                                │
│       Project: PRJ-2025-WIDGET                                               │
│                                                                              │
│    ④ Link References:                                                       │
│       inventory_transactions.voucher_id = IV-2025-0001                      │
│       inventory_transactions.journal_entry_id = JE-2025-0246                │
│       inventory_vouchers.journal_entry_id = JE-2025-0246                    │
│                                                                              │
│    Status: POSTED → COMPLETED                                               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 7. COMPLETED                                                                 │
│                                                                              │
│    ✓ Voucher locked                                                         │
│    ✓ Inventory reduced                                                      │
│    ✓ GL posted with correct cost center & project                           │
│    ✓ Full audit trail available                                             │
│    ✓ Signature captured                                                     │
│                                                                              │
│    Status: COMPLETED                                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Approval Dashboard UI

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Pending Approvals Dashboard                                  [Refresh]      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Awaiting My Approval (5)                       [All] [Purchase] [Issuance] │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 🟡 PV-2025-0003                              $12,450.00    Priority: High│ │
│  │    Purchase Voucher - Office Equipment                                  │ │
│  │    Requested by: Jane Smith (IT Dept)                                   │ │
│  │    Pending: 2 days                                                      │ │
│  │    [View Details] [Quick Approve] [Reject]                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 🟢 IV-2025-0012                              $3,750.00    Priority: Normal│ │
│  │    Issuance Voucher - Raw Materials                                     │ │
│  │    Requested by: Mike Johnson (Production)                              │ │
│  │    Dept Approved: ✓ Sarah Lee                                           │ │
│  │    Pending: 6 hours                                                     │ │
│  │    [View Details] [Quick Approve] [Reject]                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ... (3 more)                                                                │
│                                                                              │
│  ──────────────────────────────────────────────────────────────────────────│
│                                                                              │
│  Recently Approved by Me (10)                                   [View All]   │
│                                                                              │
│  • PV-2025-0002 - Approved 2 hours ago - $5,200.00                          │
│  • IV-2025-0011 - Approved yesterday - $1,850.00                            │
│  • PV-2025-0001 - Approved 3 days ago - $3,450.00                           │
│                                                                              │
│  ──────────────────────────────────────────────────────────────────────────│
│                                                                              │
│  My Approval Stats (This Month)                                             │
│                                                                              │
│  Total Approved: 24      Total Rejected: 2      Avg Time: 4.2 hours         │
│  Total Value: $156,450   Pending: 5             Fastest: 15 min             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Quick Status Reference

```
┌─────────────────────────────────────────────────────────────┐
│                    STATUS MEANINGS                           │
├─────────────────────────────────────────────────────────────┤
│  DRAFT           → Being created, can edit freely            │
│  PENDING         → Awaiting department approval              │
│  PENDING_FINANCE → Dept approved, awaiting finance           │
│  APPROVED        → Fully approved, ready for execution       │
│  RECEIVING       → Goods being received (purchase)           │
│  ISSUING         → Goods being issued (issuance)             │
│  POSTED          → GL entry created, in progress             │
│  COMPLETED       → Fully done, locked                        │
│  REJECTED        → Rejected by approver                      │
│  CANCELLED       → Cancelled by creator                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    COLOR CODING                              │
├─────────────────────────────────────────────────────────────┤
│  🔵 DRAFT         → Blue (in progress)                       │
│  🟡 PENDING       → Yellow (needs action)                    │
│  🟠 PENDING_FINANCE → Orange (escalated)                    │
│  🟢 APPROVED       → Green (ready to go)                    │
│  🔄 RECEIVING/ISSUING → Spinning (in progress)              │
│  ✅ COMPLETED      → Check mark (done)                       │
│  ❌ REJECTED       → Red X (denied)                          │
│  ⚫ CANCELLED      → Gray (cancelled)                        │
└─────────────────────────────────────────────────────────────┘
```

---

**End of Visual Flow Documentation** 🎉

