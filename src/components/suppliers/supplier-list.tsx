'use client'

import { useState, useEffect } from 'react'
import { Plus, Search, Filter, MoreHorizontal, Edit, Trash2, Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { SupplierService } from '@/lib/supplier-service'
import { Supplier, SupplierFilters, SupplierStatus, PaymentTerms } from '@/types'
import { CreateSupplierDialog } from './create-supplier-dialog'
import { EditSupplierDialog } from './edit-supplier-dialog'
import { SupplierDetailsDialog } from './supplier-details-dialog'
import { useToast } from '@/hooks/use-toast'

interface SupplierListProps {
  organizationId: string
}

function isSchemaNotReadyError(error: unknown): boolean {
  const c = (error as { code?: string; status?: number; body?: { code?: string } })?.code
  const bc = (error as { body?: { code?: string } })?.body?.code
  if (c === 'SCHEMA_NOT_READY' || bc === 'SCHEMA_NOT_READY') return true
  const m = (error as Error)?.message ?? ''
  return m.includes('does not exist') || m.includes('SCHEMA_NOT_READY')
}

export function SupplierList({ organizationId }: SupplierListProps) {
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [schemaNotReady, setSchemaNotReady] = useState(false)
  const [filters, setFilters] = useState<SupplierFilters>({})
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showDetailsDialog, setShowDetailsDialog] = useState(false)
  const { toast } = useToast()

  const loadSuppliers = async () => {
    try {
      setLoading(true)
      setLoadError(null)
      setSchemaNotReady(false)
      const data = await SupplierService.getSuppliers(organizationId, filters)
      setSuppliers(data)
    } catch (error) {
      console.error('Error loading suppliers:', error)
      const snr = isSchemaNotReadyError(error)
      setSchemaNotReady(snr)
      if (snr) {
        setLoadError('Suppliers require database setup (migrations) on this environment.')
        setSuppliers([])
      } else {
        setLoadError('Failed to load suppliers.')
        toast({
          title: 'Error',
          description: 'Failed to load suppliers',
          variant: 'destructive',
        })
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSuppliers()
  }, [organizationId, filters])

  const handleDeleteSupplier = async (supplier: Supplier) => {
    if (!confirm(`Are you sure you want to delete supplier "${supplier.name}"?`)) {
      return
    }

    try {
      await SupplierService.deleteSupplier(supplier.id)
      toast({
        title: 'Success',
        description: 'Supplier deleted successfully',
      })
      loadSuppliers()
    } catch (error) {
      console.error('Error deleting supplier:', error)
      toast({
        title: 'Error',
        description: 'Failed to delete supplier',
        variant: 'destructive',
      })
    }
  }

  const handleEditSupplier = (supplier: Supplier) => {
    setSelectedSupplier(supplier)
    setShowEditDialog(true)
  }

  const handleViewSupplier = (supplier: Supplier) => {
    setSelectedSupplier(supplier)
    setShowDetailsDialog(true)
  }

  const getStatusColor = (status: SupplierStatus) => {
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

  const getPaymentTermsLabel = (terms: PaymentTerms | undefined) => {
    if (!terms) return '—'
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

  return (
    <div className="space-y-6">
      {loadError && (
        <p
          className="rounded-md border border-amber-500/50 bg-amber-500/10 px-4 py-3 text-sm text-amber-950 dark:text-amber-100"
          role="status"
        >
          {loadError}
        </p>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Suppliers</h1>
          <p className="text-muted-foreground">
            Manage your suppliers and their account mappings
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)} disabled={schemaNotReady}>
          <Plus className="h-4 w-4 mr-2" />
          Add Supplier
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="supplier-filter-search">
                Search
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="supplier-filter-search"
                  name="supplierFilterSearch"
                  placeholder="Search suppliers..."
                  value={filters.search || ''}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" id="supplier-filter-status-label">
                Status
              </label>
              <Select
                value={filters.status?.[0] || 'all'}
                onValueChange={(value) =>
                  setFilters({
                    ...filters,
                    status: value === 'all' ? undefined : [value as SupplierStatus],
                  })
                }
              >
                <SelectTrigger aria-labelledby="supplier-filter-status-label">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" id="supplier-filter-terms-label">
                Payment Terms
              </label>
              <Select
                value={filters.payment_terms?.[0] || 'all'}
                onValueChange={(value) =>
                  setFilters({
                    ...filters,
                    payment_terms: value === 'all' ? undefined : [value as PaymentTerms],
                  })
                }
              >
                <SelectTrigger aria-labelledby="supplier-filter-terms-label">
                  <SelectValue placeholder="All terms" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All terms</SelectItem>
                  <SelectItem value="net_15">Net 15</SelectItem>
                  <SelectItem value="net_30">Net 30</SelectItem>
                  <SelectItem value="net_45">Net 45</SelectItem>
                  <SelectItem value="net_60">Net 60</SelectItem>
                  <SelectItem value="due_on_receipt">Due on Receipt</SelectItem>
                  <SelectItem value="cash_on_delivery">COD</SelectItem>
                  <SelectItem value="prepaid">Prepaid</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" id="supplier-filter-preferred-label">
                Preferred
              </label>
              <Select
                value={filters.is_preferred?.toString() || 'all'}
                onValueChange={(value) =>
                  setFilters({
                    ...filters,
                    is_preferred: value === 'all' ? undefined : value === 'true',
                  })
                }
              >
                <SelectTrigger aria-labelledby="supplier-filter-preferred-label">
                  <SelectValue placeholder="All suppliers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All suppliers</SelectItem>
                  <SelectItem value="true">Preferred only</SelectItem>
                  <SelectItem value="false">Non-preferred only</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Suppliers Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Payment Terms</TableHead>
                <TableHead>Credit Limit</TableHead>
                <TableHead>Balance</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    Loading suppliers...
                  </TableCell>
                </TableRow>
              ) : suppliers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    No suppliers found
                  </TableCell>
                </TableRow>
              ) : (
                suppliers.map((supplier) => (
                  <TableRow key={supplier.id}>
                    <TableCell className="font-medium">
                      {supplier.supplier_code}
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{supplier.name}</div>
                        {supplier.is_preferred && (
                          <Badge variant="secondary" className="text-xs">
                            Preferred
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        {supplier.contact_person && (
                          <div className="font-medium">{supplier.contact_person}</div>
                        )}
                        {supplier.email && (
                          <div className="text-sm text-muted-foreground">
                            {supplier.email}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(supplier.status)}>
                        {supplier.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {getPaymentTermsLabel(supplier.payment_terms)}
                    </TableCell>
                    <TableCell>
                      ${(supplier.credit_limit ?? 0).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <span className={(supplier.current_balance ?? 0) > 0 ? 'text-red-600' : 'text-green-600'}>
                        ${(supplier.current_balance ?? 0).toLocaleString()}
                      </span>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewSupplier(supplier)}>
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleEditSupplier(supplier)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDeleteSupplier(supplier)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Dialogs */}
      <CreateSupplierDialog
        organizationId={organizationId}
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={loadSuppliers}
      />

      {selectedSupplier && (
        <>
          <EditSupplierDialog
            supplier={selectedSupplier}
            open={showEditDialog}
            onOpenChange={setShowEditDialog}
            onSuccess={loadSuppliers}
          />

          <SupplierDetailsDialog
            supplier={selectedSupplier}
            open={showDetailsDialog}
            onOpenChange={setShowDetailsDialog}
          />
        </>
      )}
    </div>
  )
}
