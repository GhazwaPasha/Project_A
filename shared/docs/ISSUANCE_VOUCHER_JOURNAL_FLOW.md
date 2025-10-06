# 📤 Issuance Voucher - Journal Entry Flow Explained

## 🎯 Overview

**Issuance Vouchers** are used when you **take inventory OUT** of your warehouse. The key principle: **Inventory decreases, and the cost goes to a destination account** based on WHY you're taking it out.

---

## 🔄 **CORE PRINCIPLE**

```
When inventory goes OUT:
├─ Inventory Account: DECREASES (Credit)
└─ Destination Account: INCREASES (Debit)
```

**The destination account depends on WHY you're taking the inventory out.**

---

## 📊 **SCENARIO 1: SALE (Cost of Goods Sold)**

### **Situation:**
- You're fulfilling a customer order
- Taking inventory out to ship to customer
- This becomes an **expense** (COGS)

### **Issuance Voucher Details:**
```
Voucher: IV-2025-0001
Purpose: Fulfill Sales Order #SO-1234
Items: 10 boxes of Office Supplies
Cost: $40 per box = $400 total
Destination: 5100 - Cost of Goods Sold
```

### **Journal Entry:**
```
Date: 2025-10-06
Voucher: IV-2025-0001
Description: COGS for Sales Order SO-1234

Account                              Debit        Credit
─────────────────────────────────────────────────────────
5100 - Cost of Goods Sold            $400.00
1150 - Inventory - Supplies                       $400.00
                                     ────────     ────────
TOTALS                               $400.00      $400.00
```

### **What Happens:**
- ✅ **COGS Expense INCREASES** (Debit) - This reduces your profit
- ✅ **Inventory DECREASES** (Credit) - 10 boxes leave your warehouse
- ✅ **Customer gets the goods** (separate sales entry)

### **Complete Sales Flow:**
```
Step 1: Issue inventory (above entry)
Step 2: Record the sale (separate entry):
Debit:  1100 - Accounts Receivable    $800.00
Credit: 4000 - Sales Revenue                   $800.00
```

**Result:** You sold $800 worth of goods, but it cost you $400 in inventory.

---

## 🏢 **SCENARIO 2: INTERNAL USE (Department Expense)**

### **Situation:**
- Marketing department needs office supplies
- Taking inventory for internal consumption
- This becomes a **department expense**

### **Issuance Voucher Details:**
```
Voucher: IV-2025-0002
Purpose: Marketing department supplies
Items: 5 boxes of Office Supplies
Cost: $40 per box = $200 total
Cost Center: CC-MKT-01
Destination: 6100 - Office Supplies Expense
```

### **Journal Entry:**
```
Date: 2025-10-06
Voucher: IV-2025-0002
Description: Office supplies for Marketing dept
Cost Center: CC-MKT-01

Account                              Debit        Credit
─────────────────────────────────────────────────────────
6100 - Office Supplies Expense       $200.00
1150 - Inventory - Supplies                       $200.00
                                     ────────     ────────
TOTALS                               $200.00      $200.00
```

### **What Happens:**
- ✅ **Department Expense INCREASES** (Debit) - Marketing's budget is charged
- ✅ **Inventory DECREASES** (Credit) - 5 boxes leave your warehouse
- ✅ **Tracked to cost center** (CC-MKT-01) for reporting

---

## 🏭 **SCENARIO 3: PRODUCTION (Work in Progress)**

### **Situation:**
- Manufacturing department needs raw materials
- Taking inventory to make finished goods
- This becomes a **Work in Progress (WIP) asset**

### **Issuance Voucher Details:**
```
Voucher: IV-2025-0003
Purpose: Manufacturing Order #MO-1234
Items: 100 kg of Raw Material A
Cost: $15 per kg = $1,500 total
Project: PRJ-2025-WIDGET
Destination: 1300 - Work in Progress
```

### **Journal Entry:**
```
Date: 2025-10-06
Voucher: IV-2025-0003
Description: Raw materials for MO-1234
Project: PRJ-2025-WIDGET

Account                              Debit        Credit
─────────────────────────────────────────────────────────
1300 - Work in Progress              $1,500.00
1150 - Inventory - Raw Materials                  $1,500.00
                                     ─────────    ─────────
TOTALS                               $1,500.00    $1,500.00
```

### **What Happens:**
- ✅ **WIP Asset INCREASES** (Debit) - Materials go into production
- ✅ **Raw Materials Inventory DECREASES** (Credit) - 100 kg leaves warehouse
- ✅ **Tracked to project** (PRJ-2025-WIDGET) for project costing

### **Later, when production is complete:**
```
Debit:  1400 - Finished Goods        $5,000.00
Credit: 1300 - Work in Progress                  $5,000.00
```

**Result:** Raw materials ($1,500) + labor + overhead = Finished goods ($5,000)

---

## 💸 **SCENARIO 4: WASTE/LOSS (Write-off)**

### **Situation:**
- Inventory is damaged, expired, or lost
- Taking inventory out because it's worthless
- This becomes a **loss expense**

### **Issuance Voucher Details:**
```
Voucher: IV-2025-0004
Purpose: Damaged goods write-off
Items: 20 pieces of damaged products
Cost: $25 per piece = $500 total
Reason: Damaged in transit
Destination: 7200 - Inventory Loss/Shrinkage
```

### **Journal Entry:**
```
Date: 2025-10-06
Voucher: IV-2025-0004
Description: Damaged inventory write-off

Account                              Debit        Credit
─────────────────────────────────────────────────────────
7200 - Inventory Loss/Shrinkage      $500.00
1150 - Inventory                                  $500.00
                                     ────────     ────────
TOTALS                               $500.00      $500.00
```

### **What Happens:**
- ✅ **Loss Expense INCREASES** (Debit) - This reduces your profit
- ✅ **Inventory DECREASES** (Credit) - 20 pieces written off
- ✅ **No revenue generated** - pure loss

---

## 🎯 **DESTINATION ACCOUNTS BY PURPOSE**

| Purpose | Destination Account | Account Type | Impact on P&L |
|---------|-------------------|--------------|---------------|
| **Sale** | 5100 - Cost of Goods Sold | Expense | Reduces profit |
| **Internal Use** | 6xxx - Department Expense | Expense | Reduces profit |
| **Production** | 1300 - Work in Progress | Asset | No P&L impact |
| **Waste/Loss** | 7200 - Inventory Loss | Expense | Reduces profit |
| **Transfer** | 1150 - Other Location | Asset | No P&L impact |
| **Sample** | 6100 - Marketing Expense | Expense | Reduces profit |

---

## 🔄 **COMPLETE ISSUANCE FLOW**

### **Step-by-Step Process:**

```
1. CREATE ISSUANCE VOUCHER
   ├─ Select items to issue
   ├─ Choose destination account
   ├─ Specify purpose/justification
   └─ Status: DRAFT

2. SUBMIT FOR APPROVAL
   ├─ Validate stock availability
   ├─ Check destination account
   └─ Status: PENDING

3. DEPARTMENT APPROVAL
   ├─ Verify business need
   ├─ Check if purpose is valid
   └─ Status: PENDING_FINANCE

4. FINANCE APPROVAL
   ├─ Verify destination account
   ├─ Check cost allocation
   └─ Status: APPROVED

5. PHYSICAL ISSUE
   ├─ Warehouse releases goods
   ├─ Record actual quantities
   ├─ Capture receiver signature
   └─ Status: ISSUING

6. AUTOMATIC POSTING
   ├─ System creates journal entry
   ├─ Updates inventory quantities
   ├─ Links to voucher
   └─ Status: POSTED

7. COMPLETED
   ├─ Voucher locked
   ├─ Full audit trail
   └─ Status: COMPLETED
```

---

## 📋 **ISSUANCE VOUCHER FORM**

```
┌──────────────────────────────────────────────────────────────┐
│ Issuance Voucher Form                                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Purpose: [Manufacturing Order #MO-1234]                     │
│ Destination: [Production Floor - Assembly Line 2]           │
│ Cost Center: [CC-PROD-01]                                   │
│ Project Code: [PRJ-2025-WIDGET]                             │
│                                                              │
│ DESTINATION ACCOUNT:                                         │
│ [1300 - Work in Progress ▼]                                 │
│                                                              │
│ LINE ITEMS:                                                  │
│  Item              Qty Needed    Available    Est. Cost     │
│  ──────────────────────────────────────────────────────────  │
│  Raw Material A    [100 kg]      [450 kg]    [$1,500]      │
│  Component B       [50 pcs]      [200 pcs]   [$2,250]      │
│                                                              │
│  Total Cost: $3,750.00                                       │
│                                                              │
│ Justification: [Required for Q4 widget production]          │
│                                                              │
│ Stock Check: ✓ All items available                          │
│                                                              │
│ [Save Draft]  [Submit for Approval]                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 🧮 **AUTOMATIC JOURNAL ENTRY LOGIC**

### **Pseudo-code for Issuance Voucher Posting:**

```javascript
function createIssuanceJournalEntry(voucher) {
  const lines = [];
  
  // DEBIT: Destination account (from voucher)
  lines.push({
    account_id: voucher.destination_account_id,  // User selected
    debit: voucher.total_actual_cost,
    credit: 0,
    description: `Issue: ${voucher.purpose}`,
    cost_center: voucher.cost_center,
    project_code: voucher.project_code
  });
  
  // CREDIT: Inventory account (from item category)
  for (const item of voucher.items) {
    lines.push({
      account_id: item.category.inventory_account_id,  // From category
      debit: 0,
      credit: item.total_actual_cost,
      description: `Issue: ${item.name}`,
      cost_center: voucher.cost_center,
      project_code: voucher.project_code
    });
  }
  
  // Create journal entry
  return createJournalEntry({
    entry_date: voucher.executed_at,
    description: `Issue per ${voucher.voucher_number}`,
    reference: voucher.voucher_number,
    lines: lines
  });
}
```

---

## 📊 **REAL-WORLD EXAMPLES**

### **Example 1: Restaurant Kitchen**
```
Situation: Chef needs ingredients for tonight's service
Items: 5 kg beef, 2 kg vegetables, 1 kg spices
Total Cost: $150
Destination: 5100 - Cost of Goods Sold

Journal Entry:
Debit:  5100 - COGS - Food          $150.00
Credit: 1150 - Inventory - Food               $150.00
```

### **Example 2: Office Supplies**
```
Situation: HR department needs paper for printing
Items: 10 reams of paper
Total Cost: $80
Destination: 6100 - Office Supplies Expense

Journal Entry:
Debit:  6100 - Office Supplies Exp  $80.00
Credit: 1150 - Inventory - Supplies          $80.00
```

### **Example 3: Manufacturing**
```
Situation: Production line needs components
Items: 100 screws, 50 bolts, 25 washers
Total Cost: $500
Destination: 1300 - Work in Progress

Journal Entry:
Debit:  1300 - Work in Progress     $500.00
Credit: 1150 - Inventory - Components        $500.00
```

### **Example 4: Damaged Goods**
```
Situation: 20 units damaged in warehouse
Items: 20 damaged products
Total Cost: $1,000
Destination: 7200 - Inventory Loss

Journal Entry:
Debit:  7200 - Inventory Loss       $1,000.00
Credit: 1150 - Inventory - Products            $1,000.00
```

---

## 🎯 **KEY PRINCIPLES**

### **1. Always Reduce Inventory**
- Every issuance voucher reduces your inventory asset
- This is tracked in the `quantity_out` field

### **2. Destination Account Varies by Purpose**
- **Sale** → COGS (expense)
- **Internal Use** → Department expense
- **Production** → WIP (asset)
- **Waste** → Loss (expense)

### **3. Cost Tracking**
- Use average unit cost from inventory
- Track to cost centers and projects
- Maintain full audit trail

### **4. Approval Required**
- No unauthorized inventory movement
- Business justification required
- Proper account assignment verified

---

## ✅ **SUMMARY**

**Issuance Vouchers follow this simple pattern:**

```
Inventory OUT = Debit Destination Account + Credit Inventory Account
```

**The destination account tells you WHY the inventory left:**
- **COGS** = You sold it
- **Department Expense** = You used it internally  
- **WIP** = You're making something with it
- **Loss** = You wrote it off

**This creates proper cost allocation and maintains accurate inventory records!** 🎉

---

**Ready to implement this flow? The system will automatically create the correct journal entries based on the destination account you select!**
