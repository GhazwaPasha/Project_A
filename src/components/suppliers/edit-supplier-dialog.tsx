'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { X, Plus } from 'lucide-react'
import { SupplierService } from '@/lib/supplier-service'
import { AccountService } from '@/lib/account-service'
import { Supplier, SupplierFormData, SupplierStatus, PaymentTerms, Account } from '@/types'
import { useToast } from '@/hooks/use-toast'

const supplierSchema = z.object({
  supplier_code: z.string().min(1, 'Supplier code is required'),
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  
  // Contact information
  email: z.string().email().optional().or(z.literal('')),
  phone: z.string().optional(),
  fax: z.string().optional(),
  
  // Address information
  billing_address_line1: z.string().optional(),
  billing_address_line2: z.string().optional(),
  billing_city: z.string().optional(),
  billing_state: z.string().optional(),
  billing_postal_code: z.string().optional(),
  billing_country: z.string().optional(),
  
  shipping_address_line1: z.string().optional(),
  shipping_address_line2: z.string().optional(),
  shipping_city: z.string().optional(),
  shipping_state: z.string().optional(),
  shipping_postal_code: z.string().optional(),
  shipping_country: z.string().optional(),
  
  // Business information
  tax_id: z.string().optional(),
  registration_number: z.string().optional(),
  currency: z.string().min(3, 'Currency is required'),
  
  // Status and metadata
  status: z.enum(['active', 'inactive', 'suspended']),
  is_preferred: z.boolean(),
  notes: z.string().optional(),
  
  // Account mappings
  account_mappings: z.object({
    payable_account_id: z.number().min(1, 'Payable account is required'),
  }),
  
  // Contacts
  contacts: z.array(z.object({
    name: z.string().min(1, 'Contact name is required'),
    title: z.string().optional(),
    email: z.string().email().optional().or(z.literal('')),
    phone: z.string().optional(),
    mobile: z.string().optional(),
    fax: z.string().optional(),
    is_primary: z.boolean(),
    is_billing: z.boolean(),
    is_shipping: z.boolean(),
    is_technical: z.boolean(),
  })).optional(),
})

interface EditSupplierDialogProps {
  supplier: Supplier
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

export function EditSupplierDialog({
  supplier,
  open,
  onOpenChange,
  onSuccess,
}: EditSupplierDialogProps) {
  const [loading, setLoading] = useState(false)
  const [accounts, setAccounts] = useState<Account[]>([])
  const { toast } = useToast()

  const form = useForm<SupplierFormData>({
    resolver: zodResolver(supplierSchema),
    defaultValues: {
      supplier_code: supplier.supplier_code,
      name: supplier.name,
      description: supplier.description || '',
      email: supplier.email || '',
      phone: supplier.phone || '',
      fax: supplier.fax || '',
      billing_address_line1: supplier.billing_address_line1 || '',
      billing_address_line2: supplier.billing_address_line2 || '',
      billing_city: supplier.billing_city || '',
      billing_state: supplier.billing_state || '',
      billing_postal_code: supplier.billing_postal_code || '',
      billing_country: supplier.billing_country || '',
      shipping_address_line1: supplier.shipping_address_line1 || '',
      shipping_address_line2: supplier.shipping_address_line2 || '',
      shipping_city: supplier.shipping_city || '',
      shipping_state: supplier.shipping_state || '',
      shipping_postal_code: supplier.shipping_postal_code || '',
      shipping_country: supplier.shipping_country || '',
      tax_id: supplier.tax_id || '',
      registration_number: supplier.registration_number || '',
      currency: supplier.currency,
      status: supplier.status,
      is_preferred: supplier.is_preferred,
      notes: supplier.notes || '',
      account_mappings: {
        payable_account_id: supplier.account_mappings?.payable_account_id || 0,
      },
      contacts: supplier.contacts?.map(contact => ({
        name: contact.name,
        title: contact.title || '',
        email: contact.email || '',
        phone: contact.phone || '',
        mobile: contact.mobile || '',
        fax: contact.fax || '',
        is_primary: contact.is_primary,
        is_billing: contact.is_billing,
        is_shipping: contact.is_shipping,
        is_technical: contact.is_technical,
      })) || [],
    },
  })

  const loadAccounts = async () => {
    try {
      const data = await AccountService.getAccounts(supplier.organization_id)
      setAccounts(data)
    } catch (error) {
      console.error('Error loading accounts:', error)
      toast({
        title: 'Error',
        description: 'Failed to load accounts',
        variant: 'destructive',
      })
    }
  }

  useEffect(() => {
    if (open) {
      loadAccounts()
    }
  }, [open, supplier.organization_id])

  const onSubmit = async (data: SupplierFormData) => {
    try {
      setLoading(true)
      await SupplierService.updateSupplier(supplier.id, data)
      toast({
        title: 'Success',
        description: 'Supplier updated successfully',
      })
      onSuccess()
      onOpenChange(false)
    } catch (error) {
      console.error('Error updating supplier:', error)
      toast({
        title: 'Error',
        description: 'Failed to update supplier',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const addContact = () => {
    const currentContacts = form.getValues('contacts') || []
    form.setValue('contacts', [
      ...currentContacts,
      {
        name: '',
        title: '',
        email: '',
        phone: '',
        mobile: '',
        fax: '',
        is_primary: false,
        is_billing: false,
        is_shipping: false,
        is_technical: false,
      },
    ])
  }

  const removeContact = (index: number) => {
    const currentContacts = form.getValues('contacts') || []
    form.setValue('contacts', currentContacts.filter((_, i) => i !== index))
  }

  const getAccountOptions = (accountType?: string) => {
    return accounts.filter(account => 
      account.is_active && 
      (!accountType || account.account_type === accountType)
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Supplier</DialogTitle>
          <DialogDescription>
            Update supplier information and account mappings.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-6">

              {/* Basic Information */}
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="supplier_code"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Supplier Code *</FormLabel>
                          <FormControl>
                            <Input placeholder="SUP-001" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Name *</FormLabel>
                          <FormControl>
                            <Input placeholder="Supplier Name" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="currency"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Currency *</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select currency" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="USD">USD</SelectItem>
                              <SelectItem value="EUR">EUR</SelectItem>
                              <SelectItem value="GBP">GBP</SelectItem>
                              <SelectItem value="CAD">CAD</SelectItem>
                              <SelectItem value="AUD">AUD</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email</FormLabel>
                          <FormControl>
                            <Input type="email" placeholder="john@supplier.com" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="phone"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Phone</FormLabel>
                          <FormControl>
                            <Input placeholder="+1-555-0123" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="status"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Status *</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select status" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="active">Active</SelectItem>
                              <SelectItem value="inactive">Inactive</SelectItem>
                              <SelectItem value="suspended">Suspended</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Description</FormLabel>
                        <FormControl>
                          <Textarea placeholder="Supplier description..." {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="flex items-center space-x-4">
                    <FormField
                      control={form.control}
                      name="is_preferred"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center space-x-3 space-y-0">
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel>Preferred Supplier</FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Address Information */}
              <Card>
                <CardHeader>
                  <CardTitle>Address Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h4 className="text-sm font-medium mb-4">Billing Address</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="billing_address_line1"
                        render={({ field }) => (
                          <FormItem className="md:col-span-2">
                            <FormLabel>Address Line 1</FormLabel>
                            <FormControl>
                              <Input placeholder="123 Business St" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="billing_address_line2"
                        render={({ field }) => (
                          <FormItem className="md:col-span-2">
                            <FormLabel>Address Line 2</FormLabel>
                            <FormControl>
                              <Input placeholder="Suite 100" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="billing_city"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>City</FormLabel>
                            <FormControl>
                              <Input placeholder="New York" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="billing_state"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>State</FormLabel>
                            <FormControl>
                              <Input placeholder="NY" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="billing_postal_code"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Postal Code</FormLabel>
                            <FormControl>
                              <Input placeholder="10001" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="billing_country"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Country</FormLabel>
                            <FormControl>
                              <Input placeholder="USA" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium mb-4">Shipping Address</h4>
                    <p className="text-sm text-muted-foreground mb-4">
                      Leave blank if same as billing address
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="shipping_address_line1"
                        render={({ field }) => (
                          <FormItem className="md:col-span-2">
                            <FormLabel>Address Line 1</FormLabel>
                            <FormControl>
                              <Input placeholder="123 Business St" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="shipping_address_line2"
                        render={({ field }) => (
                          <FormItem className="md:col-span-2">
                            <FormLabel>Address Line 2</FormLabel>
                            <FormControl>
                              <Input placeholder="Suite 100" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="shipping_city"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>City</FormLabel>
                            <FormControl>
                              <Input placeholder="New York" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="shipping_state"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>State</FormLabel>
                            <FormControl>
                              <Input placeholder="NY" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="shipping_postal_code"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Postal Code</FormLabel>
                            <FormControl>
                              <Input placeholder="10001" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="shipping_country"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Country</FormLabel>
                            <FormControl>
                              <Input placeholder="USA" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium mb-4">Business Information</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="tax_id"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Tax ID</FormLabel>
                            <FormControl>
                              <Input placeholder="12-3456789" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="registration_number"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Registration Number</FormLabel>
                            <FormControl>
                              <Input placeholder="REG123456" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <FormField
                      control={form.control}
                      name="notes"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Notes</FormLabel>
                          <FormControl>
                            <Textarea placeholder="Additional notes..." {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Account Mapping */}
              <Card>
                <CardHeader>
                  <CardTitle>Account Mapping</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Map GL accounts for automatic voucher creation
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="account_mappings.payable_account_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Payable Account *</FormLabel>
                        <Select onValueChange={(value) => field.onChange(parseInt(value))} value={field.value.toString()}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select payable account" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {getAccountOptions('liability').map((account) => (
                              <SelectItem key={account.id} value={account.id.toString()}>
                                {account.code} - {account.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              {/* Contacts */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Supplier Contacts</CardTitle>
                    <Button type="button" onClick={addContact} size="sm">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Contact
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {form.watch('contacts')?.map((contact, index) => (
                    <Card key={index}>
                      <CardHeader className="pb-4">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">Contact {index + 1}</CardTitle>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeContact(index)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name={`contacts.${index}.name`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Name *</FormLabel>
                                <FormControl>
                                  <Input placeholder="John Smith" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name={`contacts.${index}.title`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Title</FormLabel>
                                <FormControl>
                                  <Input placeholder="Sales Manager" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name={`contacts.${index}.email`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Email</FormLabel>
                                <FormControl>
                                  <Input type="email" placeholder="john@supplier.com" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name={`contacts.${index}.phone`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Phone</FormLabel>
                                <FormControl>
                                  <Input placeholder="+1-555-0123" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name={`contacts.${index}.mobile`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Mobile</FormLabel>
                                <FormControl>
                                  <Input placeholder="+1-555-0123" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name={`contacts.${index}.fax`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Fax</FormLabel>
                                <FormControl>
                                  <Input placeholder="+1-555-0124" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>

                        <div className="flex flex-wrap gap-4">
                          <FormField
                            control={form.control}
                            name={`contacts.${index}.is_primary`}
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center space-x-3 space-y-0">
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                                <div className="space-y-1 leading-none">
                                  <FormLabel>Primary</FormLabel>
                                </div>
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name={`contacts.${index}.is_billing`}
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center space-x-3 space-y-0">
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                                <div className="space-y-1 leading-none">
                                  <FormLabel>Billing</FormLabel>
                                </div>
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name={`contacts.${index}.is_shipping`}
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center space-x-3 space-y-0">
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                                <div className="space-y-1 leading-none">
                                  <FormLabel>Shipping</FormLabel>
                                </div>
                              </FormItem>
                            )}
                          />

                          <FormField
                            control={form.control}
                            name={`contacts.${index}.is_technical`}
                            render={({ field }) => (
                              <FormItem className="flex flex-row items-center space-x-3 space-y-0">
                                <FormControl>
                                  <Switch
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                  />
                                </FormControl>
                                <div className="space-y-1 leading-none">
                                  <FormLabel>Technical</FormLabel>
                                </div>
                              </FormItem>
                            )}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  {(!form.watch('contacts') || form.watch('contacts').length === 0) && (
                    <div className="text-center py-8 text-muted-foreground">
                      No contacts added yet. Click "Add Contact" to get started.
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? 'Updating...' : 'Update Supplier'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
