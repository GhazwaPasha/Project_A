# 📚 Inventory Voucher - Accounting Flows & Journal Entries

## 🎯 Overview

This document details the **journal entry flows** for inventory vouchers, covering different payment methods and transaction types.

---

## 💰 PURCHASE VOUCHER - Accounting Flows

### **Scenario 1: CREDIT PURCHASE (Accounts Payable)**

When inventory is purchased on credit (payment to be made later):

#### **Purchase Voucher Details:**
- Items: Office Supplies (50 boxes @ $40 each)
- Total: $2,000
- Vendor: Office Depot
- Payment Terms: Net 30 days
- Payment Type: **CREDIT**

#### **Journal Entry (upon goods receipt & approval):**

```
Date: 2025-10-06
Voucher: PV-2025-0001
Description: Purchase of Office Supplies on credit per PV-2025-0001

Account                              Debit        Credit
─────────────────────────────────────────────────────────
1150 - Inventory - Supplies          $2,000.00
2000 - Accounts Payable                           $2,000.00
                                     ─────────    ─────────
TOTALS                               $2,000.00    $2,000.00
```

**Accounting Impact:**
- ✅ Inventory Asset INCREASES (Debit)
- ✅ Accounts Payable LIABILITY INCREASES (Credit)
- ✅ Cash unchanged (not paid yet)

**Later, when payment is made:**

```
Date: 2025-11-05 (30 days later)
Voucher: Payment voucher #PAY-2025-0123
Description: Payment to Office Depot for PV-2025-0001

Account                              Debit        Credit
─────────────────────────────────────────────────────────
2000 - Accounts Payable              $2,000.00
1000 - Cash/Bank                                  $2,000.00
                                     ─────────    ─────────
TOTALS                               $2,000.00    $2,000.00
```

**Accounting Impact:**
- ✅ Accounts Payable DECREASES (Debit - reduces liability)
- ✅ Cash DECREASES (Credit - money out)

---

### **Scenario 2: CASH PURCHASE (Immediate Payment)**

When inventory is purchased with immediate payment:

#### **Purchase Voucher Details:**
- Items: Office Supplies (50 boxes @ $40 each)
- Total: $2,000
- Vendor: Office Depot
- Payment Type: **CASH/CHECK/CARD**
- Paid immediately upon delivery

#### **Journal Entry (upon goods receipt & approval):**

```
Date: 2025-10-06
Voucher: PV-2025-0001
Description: Cash purchase of Office Supplies per PV-2025-0001

Account                              Debit        Credit
─────────────────────────────────────────────────────────
1150 - Inventory - Supplies          $2,000.00
1000 - Cash/Bank                                  $2,000.00
                                     ─────────    ─────────
TOTALS                               $2,000.00    $2,000.00
```

**Accounting Impact:**
- ✅ Inventory Asset INCREASES (Debit)
- ✅ Cash DECREASES immediately (Credit - money out)
- ✅ No Accounts Payable involved

---

### **Scenario 3: PARTIAL PAYMENT**

When a deposit is paid upfront, balance on credit:

#### **Purchase Voucher Details:**
- Items: Equipment (Total $10,000)
- Deposit Paid: $3,000 (30%)
- Balance on Credit: $7,000
- Payment Type: **PARTIAL PAYMENT**

#### **Journal Entry Option A (Two-entry method):**

**Entry 1: Record the purchase**
```
Date: 2025-10-06
Voucher: PV-2025-0002
Description: Purchase of Equipment per PV-2025-0002

Account                              Debit        Credit
─────────────────────────────────────────────────────────
1200 - Inventory - Equipment         $10,000.00
2000 - Accounts Payable                           $10,000.00
                                     ──────────   ──────────
TOTALS                               $10,000.00   $10,000.00
```

**Entry 2: Record the deposit payment**
```
Date: 2025-10-06
Voucher: PV-2025-0002-PMT
Description: Deposit payment for PV-2025-0002

Account                              Debit        Credit
─────────────────────────────────────────────────────────
2000 - Accounts Payable              $3,000.00
1000 - Cash/Bank                                  $3,000.00
                                     ─────────    ─────────
TOTALS                               $3,000.00    $3,000.00
```

**Net Result:**
- Inventory: +$10,000 (Debit)
- Cash: -$3,000 (Credit)
- Accounts Payable: +$7,000 (Credit - net after deposit)

#### **Journal Entry Option B (Single-entry method - RECOMMENDED):**

```
Date: 2025-10-06
Voucher: PV-2025-0002
Description: Purchase of Equipment with 30% deposit per PV-2025-0002

Account                              Debit        Credit
─────────────────────────────────────────────────────────
1200 - Inventory - Equipment         $10,000.00
1000 - Cash/Bank                                  $3,000.00
2000 - Accounts Payable                           $7,000.00
                                     ──────────   ──────────
TOTALS                               $10,000.00   $10,000.00
```

**Accounting Impact:**
- ✅ Inventory Asset INCREASES by full amount ($10,000)
- ✅ Cash DECREASES by deposit ($3,000)
- ✅ Accounts Payable INCREASES by balance ($7,000)

---

## 📤 ISSUANCE VOUCHER - Accounting Flows

Issuance vouchers always follow the same pattern (no payment involved):

### **Scenario 1: Issue to COGS (Sale/Cost of Goods Sold)**

When inventory is issued for a sale:

#### **Issuance Voucher Details:**
- Items: Office Supplies (10 boxes @ $40 average cost)
- Total Cost: $400
- Purpose: Fulfill sales order #SO-1234
- Destination Account: **5100 - Cost of Goods Sold**

#### **Journal Entry (upon goods issue & approval):**

```
Date: 2025-10-06
Voucher: IV-2025-0001
Description: COGS for sales order SO-1234 per IV-2025-0001

Account                              Debit        Credit
─────────────────────────────────────────────────────────
5100 - Cost of Goods Sold            $400.00
1150 - Inventory - Supplies                       $400.00
                                     ────────     ────────
TOTALS                               $400.00      $400.00
```

**Accounting Impact:**
- ✅ COGS Expense INCREASES (Debit - reduces profit)
- ✅ Inventory Asset DECREASES (Credit - inventory out)

**Note:** The actual sale entry (revenue + receivable) is separate:
```
Account                              Debit        Credit
─────────────────────────────────────────────────────────
1100 - Accounts Receivable           $800.00
4000 - Sales Revenue                              $800.00
```

---

### **Scenario 2: Issue to Department/Expense**

When inventory is issued for internal use (e.g., office supplies consumed):

#### **Issuance Voucher Details:**
- Items: Office Supplies (5 boxes @ $40 average cost)
- Total Cost: $200
- Purpose: Marketing department supplies
- Cost Center: CC-MKT-01
- Destination Account: **6100 - Office Supplies Expense**

#### **Journal Entry (upon goods issue & approval):**

```
Date: 2025-10-06
Voucher: IV-2025-0002
Description: Office supplies for Marketing dept per IV-2025-0002
Cost Center: CC-MKT-01

Account                              Debit        Credit
─────────────────────────────────────────────────────────
6100 - Office Supplies Expense       $200.00
1150 - Inventory - Supplies                       $200.00
                                     ────────     ────────
TOTALS                               $200.00      $200.00
```

**Accounting Impact:**
- ✅ Department Expense INCREASES (Debit)
- ✅ Inventory Asset DECREASES (Credit)
- ✅ Tracked to specific cost center (CC-MKT-01)

---

### **Scenario 3: Issue to Production/WIP**

When inventory is issued for manufacturing:

#### **Issuance Voucher Details:**
- Items: Raw Materials (100 kg @ $15/kg)
- Total Cost: $1,500
- Purpose: Manufacturing Order #MO-1234
- Project: PRJ-2025-WIDGET
- Destination Account: **1300 - Work in Progress**

#### **Journal Entry (upon goods issue & approval):**

```
Date: 2025-10-06
Voucher: IV-2025-0003
Description: Raw materials for MO-1234 per IV-2025-0003
Project: PRJ-2025-WIDGET

Account                              Debit        Credit
─────────────────────────────────────────────────────────
1300 - Work in Progress              $1,500.00
1150 - Inventory - Raw Materials                  $1,500.00
                                     ─────────    ─────────
TOTALS                               $1,500.00    $1,500.00
```

**Accounting Impact:**
- ✅ WIP Asset INCREASES (Debit - materials into production)
- ✅ Raw Materials Inventory DECREASES (Credit)
- ✅ Tracked to specific project (PRJ-2025-WIDGET)

**Later, when finished goods are completed:**
```
Account                              Debit        Credit
─────────────────────────────────────────────────────────
1400 - Finished Goods Inventory      $5,000.00
1300 - Work in Progress                           $5,000.00
```

---

### **Scenario 4: Issue to Waste/Loss**

When inventory is damaged, expired, or lost:

#### **Issuance Voucher Details:**
- Items: Damaged goods (20 pcs @ $25 average cost)
- Total Cost: $500
- Purpose: Damaged in transit
- Destination Account: **7200 - Inventory Loss/Shrinkage**

#### **Journal Entry (upon goods issue & approval):**

```
Date: 2025-10-06
Voucher: IV-2025-0004
Description: Damaged inventory write-off per IV-2025-0004

Account                              Debit        Credit
─────────────────────────────────────────────────────────
7200 - Inventory Loss/Shrinkage      $500.00
1150 - Inventory                                  $500.00
                                     ────────     ────────
TOTALS                               $500.00      $500.00
```

**Accounting Impact:**
- ✅ Loss/Shrinkage Expense INCREASES (Debit - reduces profit)
- ✅ Inventory Asset DECREASES (Credit - inventory written off)

---

## 🔄 COMPLETE PURCHASE FLOW COMPARISON

### **CREDIT PURCHASE FLOW:**

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Purchase on Credit                                  │
├─────────────────────────────────────────────────────────────┤
│ Debit:  1150 - Inventory           $2,000                   │
│ Credit: 2000 - Accounts Payable            $2,000           │
│                                                              │
│ Result: Inventory ↑  Cash unchanged  A/P Liability ↑        │
└─────────────────────────────────────────────────────────────┘
                          ↓
                    (30 days later)
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Pay the Invoice                                     │
├─────────────────────────────────────────────────────────────┤
│ Debit:  2000 - Accounts Payable    $2,000                   │
│ Credit: 1000 - Cash                         $2,000          │
│                                                              │
│ Result: A/P Liability ↓  Cash ↓                             │
└─────────────────────────────────────────────────────────────┘
```

### **CASH PURCHASE FLOW:**

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Cash Purchase (Single Entry)                        │
├─────────────────────────────────────────────────────────────┤
│ Debit:  1150 - Inventory           $2,000                   │
│ Credit: 1000 - Cash                         $2,000          │
│                                                              │
│ Result: Inventory ↑  Cash ↓  (No A/P involved)              │
└─────────────────────────────────────────────────────────────┘
```

**Key Difference:** Credit purchases create a liability (A/P), cash purchases don't.

---

## 💾 Database Schema Addition

To support different payment types, we need to add fields to `inventory_vouchers`:

```sql
ALTER TABLE public.inventory_vouchers
ADD COLUMN payment_type VARCHAR(20) DEFAULT 'credit' 
  CHECK (payment_type IN ('credit', 'cash', 'check', 'card', 'bank_transfer', 'partial'));

ADD COLUMN payment_account_id BIGINT REFERENCES public.accounts(id);  -- Cash/Bank account used

ADD COLUMN deposit_amount DECIMAL(15,2) DEFAULT 0;  -- For partial payments

ADD COLUMN payment_reference VARCHAR(100);  -- Check #, transaction ID, etc.
```

### **Field Usage:**

| Payment Type | payment_account_id | deposit_amount | Journal Entry Credit Account |
|--------------|-------------------|----------------|------------------------------|
| **credit** | NULL | 0 | Accounts Payable |
| **cash** | Cash account ID | Full amount | Cash/Bank (specified account) |
| **check** | Bank account ID | Full amount | Bank (specified account) |
| **card** | Card account ID | Full amount | Credit Card Payable |
| **partial** | Bank account ID | Deposit amount | Split: Cash (partial) + A/P (balance) |

---

## 🎯 Updated Purchase Voucher Form

The form should include payment details:

```
┌──────────────────────────────────────────────────────────────┐
│ Purchase Voucher Form                                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Vendor Information:                                          │
│ ├─ Vendor Name:     [Office Depot]                          │
│ ├─ Vendor Contact:  [555-1234]                              │
│ └─ PO Number:       [PO-2025-001]                           │
│                                                              │
│ Payment Details:                                             │
│ ├─ Payment Type:    [● Credit  ○ Cash  ○ Check  ○ Card     │
│ │                    ○ Partial Payment]                     │
│ │                                                            │
│ └─ If Cash/Check/Card selected:                             │
│    ├─ Payment Account: [1000 - Main Operating Account ▼]   │
│    ├─ Payment Reference: [Check #1234 / Trans ID]          │
│    └─ Payment Date: [2025-10-06]                           │
│                                                              │
│ └─ If Partial Payment selected:                             │
│    ├─ Payment Account: [1000 - Main Operating Account ▼]   │
│    ├─ Deposit Amount: [$3,000.00]                          │
│    ├─ Deposit %: [30%]                                      │
│    ├─ Balance on Credit: [$7,000.00] (auto-calculated)     │
│    └─ Payment Reference: [Trans #ABC123]                   │
│                                                              │
│ Line Items:                                                  │
│ [Item selection grid...]                                     │
│                                                              │
│ Total Amount: $10,000.00                                     │
│                                                              │
│ [Save Draft]  [Submit for Approval]                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Automatic Journal Entry Logic

### **Pseudo-code for Purchase Voucher Posting:**

```javascript
function createPurchaseJournalEntry(voucher) {
  const lines = [];
  
  // DEBIT: Inventory (always)
  for (const item of voucher.items) {
    lines.push({
      account_id: item.category.inventory_account_id,  // From category
      debit: item.total_actual_cost,
      credit: 0,
      description: `Purchase: ${item.name}`
    });
  }
  
  // CREDIT: Depends on payment type
  switch (voucher.payment_type) {
    case 'credit':
      // Credit to Accounts Payable
      lines.push({
        account_id: ACCOUNTS_PAYABLE_ID,  // e.g., 2000
        debit: 0,
        credit: voucher.total_actual_cost,
        description: `Payable to ${voucher.vendor_name}`
      });
      break;
      
    case 'cash':
    case 'check':
    case 'card':
    case 'bank_transfer':
      // Credit to Cash/Bank account
      lines.push({
        account_id: voucher.payment_account_id,
        debit: 0,
        credit: voucher.total_actual_cost,
        description: `Payment to ${voucher.vendor_name}`
      });
      break;
      
    case 'partial':
      // Credit split: Cash + A/P
      lines.push({
        account_id: voucher.payment_account_id,
        debit: 0,
        credit: voucher.deposit_amount,
        description: `Deposit to ${voucher.vendor_name}`
      });
      
      const balance = voucher.total_actual_cost - voucher.deposit_amount;
      lines.push({
        account_id: ACCOUNTS_PAYABLE_ID,
        debit: 0,
        credit: balance,
        description: `Balance payable to ${voucher.vendor_name}`
      });
      break;
  }
  
  // Create journal entry
  return createJournalEntry({
    entry_date: voucher.executed_at,
    description: `Purchase per ${voucher.voucher_number}`,
    reference: voucher.voucher_number,
    lines: lines
  });
}
```

---

## 📊 Chart of Accounts Setup

### **Typical Account Structure:**

```
ASSETS
├─ 1000 - Cash and Cash Equivalents
│  ├─ 1010 - Petty Cash
│  ├─ 1020 - Main Operating Account
│  ├─ 1030 - Payroll Account
│  └─ 1040 - Credit Card Clearing
│
├─ 1100 - Accounts Receivable
│
├─ 1150 - Inventory
│  ├─ 1151 - Inventory - Raw Materials
│  ├─ 1152 - Inventory - Supplies
│  ├─ 1153 - Inventory - Finished Goods
│  └─ 1154 - Inventory - Equipment
│
├─ 1300 - Work in Progress
└─ 1400 - Finished Goods

LIABILITIES
├─ 2000 - Accounts Payable
├─ 2100 - Credit Card Payable
├─ 2200 - Accrued Expenses
└─ 2300 - Short-term Debt

EXPENSES
├─ 5100 - Cost of Goods Sold
│  ├─ 5110 - COGS - Materials
│  ├─ 5120 - COGS - Labor
│  └─ 5130 - COGS - Overhead
│
├─ 6100 - Operating Expenses
│  ├─ 6110 - Office Supplies Expense
│  ├─ 6120 - Marketing Expense
│  └─ 6130 - Utilities
│
└─ 7200 - Inventory Loss/Shrinkage
```

---

## 📋 Summary Table

### **Purchase Voucher Journal Entries:**

| Payment Type | Debit | Credit 1 | Credit 2 | Notes |
|--------------|-------|----------|----------|-------|
| **Credit** | Inventory | Accounts Payable | - | 2-step: purchase now, pay later |
| **Cash** | Inventory | Cash/Bank | - | 1-step: immediate payment |
| **Check** | Inventory | Bank Account | - | 1-step: check payment |
| **Card** | Inventory | Credit Card Payable | - | 1-step: card payment |
| **Partial** | Inventory | Cash (deposit) | A/P (balance) | 1-step: split payment |

### **Issuance Voucher Journal Entries:**

| Purpose | Debit | Credit | Notes |
|---------|-------|--------|-------|
| **Sale (COGS)** | 5100 - COGS | Inventory | Expense to income statement |
| **Internal Use** | 6xxx - Expense | Inventory | Department/cost center expense |
| **Production** | 1300 - WIP | Inventory | Asset transfer (WIP) |
| **Waste/Loss** | 7200 - Loss | Inventory | Write-off expense |

---

## ✅ Implementation Checklist

- [ ] Add payment type fields to `inventory_vouchers` table
- [ ] Update purchase voucher form with payment options
- [ ] Implement smart journal entry creation logic
- [ ] Add payment account dropdown (filtered to cash/bank accounts)
- [ ] Support partial payment calculations
- [ ] Create A/P aging report (for credit purchases)
- [ ] Link to payment voucher system (for settling A/P)
- [ ] Add payment tracking dashboard

---

**Ready to implement! 🚀**

