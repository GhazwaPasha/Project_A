# Supplier Management System

A comprehensive supplier management system integrated with the voucher system for streamlined purchase order processing and account mapping.

## Overview

The Supplier Management System allows accountants to:

- **Manage Suppliers**: Create, edit, and maintain supplier information
- **Map GL Accounts**: Link suppliers to specific General Ledger accounts
- **Streamline Vouchers**: Auto-populate voucher fields when selecting suppliers
- **Track Balances**: Monitor supplier credit limits and current balances
- **Manage Contacts**: Store multiple contacts per supplier with role assignments

## Features

### 🏢 Supplier Management
- Complete supplier profiles with business information
- Contact management with role-based assignments
- Address management (billing and shipping)
- Payment terms and credit limit tracking
- Supplier status management (active, inactive, suspended)
- Preferred supplier designation

### 💳 Account Mapping
- **Payable Account**: Where supplier invoices are recorded
- **Cash Account**: Default cash/bank account for payments
- **Expense Account**: Default expense account for purchases
- **Inventory Account**: Inventory account for purchases
- **Freight Account**: Freight charges account
- **Tax Account**: Tax liability account
- **Discount Account**: Purchase discounts account

### 🔄 Voucher Integration
- Auto-populate vendor information when selecting suppliers
- Pre-fill account mappings for faster voucher creation
- Maintain supplier-specific payment terms
- Track supplier-specific purchase history

## Database Schema

### Core Tables

#### `suppliers`
Main supplier information table with comprehensive business details.

```sql
CREATE TABLE public.suppliers (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL,
    supplier_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    -- Contact information
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    -- Address information
    billing_address_line1 VARCHAR(255),
    billing_city VARCHAR(100),
    -- Payment terms
    payment_terms payment_terms DEFAULT 'net_30',
    credit_limit DECIMAL(15,2) DEFAULT 0,
    current_balance DECIMAL(15,2) DEFAULT 0,
    -- Status
    status supplier_status DEFAULT 'active',
    is_preferred BOOLEAN DEFAULT false,
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

#### `supplier_account_mappings`
Links suppliers to GL accounts for automatic voucher creation.

```sql
CREATE TABLE public.supplier_account_mappings (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL,
    organization_id UUID NOT NULL,
    payable_account_id BIGINT NOT NULL,
    cash_account_id BIGINT,
    expense_account_id BIGINT,
    inventory_account_id BIGINT,
    freight_account_id BIGINT,
    tax_account_id BIGINT,
    discount_account_id BIGINT
);
```

#### `supplier_contacts`
Multiple contacts per supplier with role assignments.

```sql
CREATE TABLE public.supplier_contacts (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    -- Contact type flags
    is_primary BOOLEAN DEFAULT false,
    is_billing BOOLEAN DEFAULT false,
    is_shipping BOOLEAN DEFAULT false,
    is_technical BOOLEAN DEFAULT false
);
```

## API Reference

### SupplierService

#### Get Suppliers
```typescript
const suppliers = await SupplierService.getSuppliers(organizationId, filters)
```

#### Create Supplier
```typescript
const supplier = await SupplierService.createSupplier(supplierData, organizationId)
```

#### Update Supplier
```typescript
const supplier = await SupplierService.updateSupplier(id, supplierData)
```

#### Get Supplier Account Mappings
```typescript
const mappings = await SupplierService.getSupplierAccountMappings(supplierId)
```

#### Get Suppliers for Voucher
```typescript
const suppliers = await SupplierService.getSuppliersForVoucher(organizationId)
```

## Usage Guide

### 1. Setup

Run the setup script to create the necessary database tables:

```bash
python scripts/setup_supplier_system.py
```

### 2. Create a Supplier

1. Navigate to the Suppliers page
2. Click "Add Supplier"
3. Fill in basic information (name, contact details, etc.)
4. Set up account mappings in the "Account Mapping" tab
5. Add contacts in the "Contacts" tab
6. Save the supplier

### 3. Account Mapping

When creating a supplier, map the following accounts:

- **Payable Account** (Required): Where supplier invoices are recorded
- **Cash Account**: Default cash/bank account for payments
- **Expense Account**: Default expense account for purchases
- **Inventory Account**: Inventory account for purchases
- **Freight Account**: Freight charges account
- **Tax Account**: Tax liability account
- **Discount Account**: Purchase discounts account

### 4. Using Suppliers in Vouchers

When creating purchase vouchers:

1. Select a supplier from the dropdown
2. The system will auto-populate:
   - Vendor name
   - Vendor contact
   - Destination account (from expense account mapping)
   - Payment account (from cash account mapping)
3. Complete the remaining voucher details
4. Submit the voucher

## Components

### SupplierList
Main component for displaying and managing suppliers.

```tsx
<SupplierList organizationId={organizationId} />
```

### CreateSupplierDialog
Dialog for creating new suppliers with comprehensive form.

```tsx
<CreateSupplierDialog
  organizationId={organizationId}
  open={showCreateDialog}
  onOpenChange={setShowCreateDialog}
  onSuccess={loadSuppliers}
/>
```

### EnhancedCreateVoucherDialog
Enhanced voucher creation dialog with supplier integration.

```tsx
<EnhancedCreateVoucherDialog
  voucherType="purchase"
  open={showVoucherDialog}
  onOpenChange={setShowVoucherDialog}
  onSuccess={loadVouchers}
  items={inventoryItems}
/>
```

## Security

- Row Level Security (RLS) enabled on all tables
- Users can only access suppliers in their organizations
- Only accountants and organization owners can manage suppliers
- Account mappings are protected by organization membership

## Integration Points

### Voucher System
- Auto-populates vendor information
- Pre-fills account mappings
- Maintains supplier-specific settings

### Account System
- Links to existing chart of accounts
- Validates account types for proper mapping
- Ensures account accessibility

### Organization System
- Multi-tenant support
- Organization-specific supplier data
- Role-based access control

## Best Practices

### Supplier Management
1. **Use consistent naming**: Follow a naming convention for supplier codes
2. **Complete profiles**: Fill in all available information for better tracking
3. **Regular updates**: Keep supplier information current
4. **Account mapping**: Ensure all necessary accounts are mapped

### Account Mapping
1. **Required mappings**: Always map payable accounts
2. **Logical grouping**: Use appropriate account types for each mapping
3. **Regular review**: Periodically review and update mappings
4. **Documentation**: Document any special mapping requirements

### Voucher Creation
1. **Select suppliers**: Always select suppliers when available
2. **Verify mappings**: Check that account mappings are correct
3. **Review details**: Verify auto-populated information
4. **Maintain consistency**: Use the same supplier for recurring purchases

## Troubleshooting

### Common Issues

1. **Suppliers not loading**: Check organization membership and RLS policies
2. **Account mapping errors**: Verify account IDs and organization membership
3. **Voucher integration issues**: Ensure supplier has proper account mappings
4. **Permission errors**: Verify user has accountant or owner role

### Debug Steps

1. Check browser console for error messages
2. Verify database connection and RLS policies
3. Confirm user permissions and organization membership
4. Check account accessibility and mapping validity

## Future Enhancements

- Supplier performance tracking
- Automated supplier evaluation
- Integration with external supplier databases
- Advanced reporting and analytics
- Supplier portal for self-service
- Automated payment processing
- Supplier risk assessment
- Contract management integration
