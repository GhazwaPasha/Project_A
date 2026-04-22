'use client'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { MapPin, Phone, Mail, Globe, Building, CreditCard, User } from 'lucide-react'
import { Supplier, PaymentTerms } from '@/types'

interface SupplierDetailsDialogProps {
  supplier: Supplier
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SupplierDetailsDialog({
  supplier,
  open,
  onOpenChange,
}: SupplierDetailsDialogProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'inactive':
        return 'bg-gray-100 text-gray-800'
      case 'suspended':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getPaymentTermsLabel = (terms: PaymentTerms) => {
    switch (terms) {
      case 'net_15':
        return 'Net 15'
      case 'net_30':
        return 'Net 30'
      case 'net_45':
        return 'Net 45'
      case 'net_60':
        return 'Net 60'
      case 'due_on_receipt':
        return 'Due on Receipt'
      case 'cash_on_delivery':
        return 'COD'
      case 'prepaid':
        return 'Prepaid'
      default:
        return terms
    }
  }

  const formatAddress = (address: {
    line1?: string
    line2?: string
    city?: string
    state?: string
    postal_code?: string
    country?: string
  }) => {
    const parts = [
      address.line1,
      address.line2,
      address.city,
      address.state,
      address.postal_code,
      address.country,
    ].filter(Boolean)
    return parts.join(', ') || 'Not provided'
  }

  const billingAddress = {
    line1: supplier.billing_address_line1,
    line2: supplier.billing_address_line2,
    city: supplier.billing_city,
    state: supplier.billing_state,
    postal_code: supplier.billing_postal_code,
    country: supplier.billing_country,
  }

  const shippingAddress = {
    line1: supplier.shipping_address_line1,
    line2: supplier.shipping_address_line2,
    city: supplier.shipping_city,
    state: supplier.shipping_state,
    postal_code: supplier.shipping_postal_code,
    country: supplier.shipping_country,
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Building className="h-6 w-6" />
            {supplier.name}
            {supplier.is_preferred && (
              <Badge variant="secondary">Preferred</Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            {supplier.supplier_code}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Status</label>
                  <div className="mt-1">
                    <Badge className={getStatusColor(supplier.status)}>
                      {supplier.status}
                    </Badge>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground">Currency</label>
                  <p className="mt-1 text-sm">{supplier.currency}</p>
                </div>


                <div>
                  <label className="text-sm font-medium text-muted-foreground">Current Balance</label>
                  <p className={`mt-1 text-sm font-medium ${
                    (supplier.current_balance ?? 0) > 0 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    ${(supplier.current_balance ?? 0).toLocaleString()}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground">Available Credit</label>
                  <p className="mt-1 text-sm font-medium">
                    ${((supplier.credit_limit ?? 0) - (supplier.current_balance ?? 0)).toLocaleString()}
                  </p>
                </div>
              </div>

              {supplier.description && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Description</label>
                  <p className="mt-1 text-sm">{supplier.description}</p>
                </div>
              )}

              {supplier.notes && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Notes</label>
                  <p className="mt-1 text-sm">{supplier.notes}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Phone className="h-5 w-5" />
                Contact Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

                {supplier.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{supplier.email}</p>
                      <p className="text-xs text-muted-foreground">Email</p>
                    </div>
                  </div>
                )}

                {supplier.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{supplier.phone}</p>
                      <p className="text-xs text-muted-foreground">Phone</p>
                    </div>
                  </div>
                )}

              </div>
            </CardContent>
          </Card>

          {/* Addresses */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  Billing Address
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{formatAddress(billingAddress)}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <MapPin className="h-5 w-5" />
                  Shipping Address
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{formatAddress(shippingAddress)}</p>
              </CardContent>
            </Card>
          </div>

          {/* Account Mappings */}
          {supplier.account_mappings && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <CreditCard className="h-5 w-5" />
                  Account Mappings
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  GL accounts mapped for automatic voucher creation
                </p>
              </CardHeader>
              <CardContent>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Payable Account</label>
                  <p className="mt-1 text-sm font-medium">
                    {supplier.account_mappings.payable_account?.code} - {supplier.account_mappings.payable_account?.name}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Contacts */}
          {supplier.contacts && supplier.contacts.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Contacts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {supplier.contacts.map((contact, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{contact.name}</h4>
                        <div className="flex gap-2">
                          {contact.is_primary && <Badge variant="secondary">Primary</Badge>}
                          {contact.is_billing && <Badge variant="outline">Billing</Badge>}
                          {contact.is_shipping && <Badge variant="outline">Shipping</Badge>}
                          {contact.is_technical && <Badge variant="outline">Technical</Badge>}
                        </div>
                      </div>
                      
                      {contact.title && (
                        <p className="text-sm text-muted-foreground mb-2">{contact.title}</p>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                        {contact.email && (
                          <div className="flex items-center gap-2">
                            <Mail className="h-3 w-3 text-muted-foreground" />
                            <span>{contact.email}</span>
                          </div>
                        )}
                        {contact.phone && (
                          <div className="flex items-center gap-2">
                            <Phone className="h-3 w-3 text-muted-foreground" />
                            <span>{contact.phone}</span>
                          </div>
                        )}
                        {contact.mobile && (
                          <div className="flex items-center gap-2">
                            <Phone className="h-3 w-3 text-muted-foreground" />
                            <span>{contact.mobile} (Mobile)</span>
                          </div>
                        )}
                        {contact.fax && (
                          <div className="flex items-center gap-2">
                            <Phone className="h-3 w-3 text-muted-foreground" />
                            <span>{contact.fax} (Fax)</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Business Information */}
          {(supplier.tax_id || supplier.registration_number) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Business Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {supplier.tax_id && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Tax ID</label>
                      <p className="mt-1 text-sm font-medium">{supplier.tax_id}</p>
                    </div>
                  )}

                  {supplier.registration_number && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Registration Number</label>
                      <p className="mt-1 text-sm font-medium">{supplier.registration_number}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
