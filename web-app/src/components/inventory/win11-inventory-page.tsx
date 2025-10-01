'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { 
  Search, RefreshCw, Plus, Edit, Trash2, Save, X, Package,
  AlertTriangle, DollarSign, Boxes, Check
} from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { DataService } from '@/lib/data-service'
import { InventoryCategory, InventoryItem, InventoryTransaction, Account } from '@/types'
import { useOrganization } from '@/hooks/use-organization'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { AccountSelect } from '@/components/ui/account-select'

interface EditingItem {
  id: number | null
  sku: string
  name: string
  description: string
  category_id: string
  unit_of_measure: string
  average_unit_cost: string
  reorder_point: string
}

interface EditingCategory {
  id: number | null
  name: string
  inventory_account_id: string
  expense_account_id: string
}

export function Win11InventoryPage() {
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [activeView, setActiveView] = useState<'items' | 'categories' | 'transactions'>('items')
  const [categories, setCategories] = useState<InventoryCategory[]>([])
  const [items, setItems] = useState<InventoryItem[]>([])
  const [transactions, setTransactions] = useState<InventoryTransaction[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [editingItem, setEditingItem] = useState<EditingItem | null>(null)
  const [editingCategory, setEditingCategory] = useState<EditingCategory | null>(null)
  const [isCreatingItem, setIsCreatingItem] = useState(false)
  const [isCreatingCategory, setIsCreatingCategory] = useState(false)
  const [transactionForm, setTransactionForm] = useState({
    item_id: '', 
    transaction_type: 'in' as 'in' | 'out' | 'adjustment', 
    quantity: '', 
    unit_cost: '',
    description: '', 
    reference: '', 
    transaction_date: new Date().toISOString().split('T')[0]
  })
  const { currentOrganization } = useOrganization()

  useEffect(() => {
    if (currentOrganization) loadData()
  }, [currentOrganization])

  const loadData = async () => {
    if (!currentOrganization) return
    try {
      setLoading(true)
      const [categoriesData, itemsData, transactionsData, accountsData] = await Promise.all([
        DataService.getInventoryCategories(currentOrganization.id, true),
        DataService.getInventoryItems(currentOrganization.id, true),
        DataService.getInventoryTransactions(currentOrganization.id, undefined, 100),
        DataService.getAccounts(currentOrganization.id, true)
      ])
      setCategories(categoriesData)
      setItems(itemsData)
      setTransactions(transactionsData)
      setAccounts(accountsData)
    } catch (error) {
      console.error('Error loading inventory data:', error)
    } finally {
      setLoading(false)
    }
  }

  const totalValue = items.reduce((sum, item) => sum + item.total_value, 0)
  const totalItems = items.length
  const totalQuantity = items.reduce((sum, item) => sum + item.quantity_available, 0)
  const lowStockCount = items.filter(i => i.reorder_point > 0 && i.quantity_available <= i.reorder_point).length
  const filteredItems = items.filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.sku.toLowerCase().includes(searchTerm.toLowerCase())
  )
  const filteredCategories = categories.filter(category =>
    category.name.toLowerCase().includes(searchTerm.toLowerCase())
  )
  const filteredTransactions = transactions.filter(transaction =>
    transaction.item?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transaction.reference?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const startCreatingItem = () => {
    setEditingItem({
      id: null, sku: '', name: '', description: '', category_id: '',
      unit_of_measure: 'kg', average_unit_cost: '0', reorder_point: '0'
    })
    setIsCreatingItem(true)
  }

  const startEditingItem = (item: InventoryItem) => {
    setEditingItem({
      id: item.id, sku: item.sku, name: item.name, description: item.description || '',
      category_id: item.category_id.toString(), unit_of_measure: item.unit_of_measure,
      average_unit_cost: item.average_unit_cost.toString(), reorder_point: item.reorder_point.toString()
    })
    setIsCreatingItem(false)
  }

  const saveItem = async () => {
    if (!editingItem || !currentOrganization) return
    const itemData = {
      organization_id: currentOrganization.id, 
      sku: editingItem.sku, 
      name: editingItem.name,
      description: editingItem.description || null, 
      category_id: parseInt(editingItem.category_id),
      unit_of_measure: editingItem.unit_of_measure, 
      quantity_in: 0, 
      quantity_out: 0,
      average_unit_cost: parseFloat(editingItem.average_unit_cost) || 0,
      reorder_point: parseFloat(editingItem.reorder_point) || 0, 
      reorder_quantity: 0,
      is_active: true, 
      created_by: null
    }
    try {
      if (isCreatingItem) await DataService.createInventoryItem(itemData)
      else if (editingItem.id) await DataService.updateInventoryItem(editingItem.id, itemData)
      setEditingItem(null)
      setIsCreatingItem(false)
      loadData()
    } catch (error) {
      console.error('Error saving item:', error)
    }
  }

  const deleteItem = async (itemId: number) => {
    if (!confirm('Delete this item?')) return
    await DataService.deleteInventoryItem(itemId)
    loadData()
  }

  const startCreatingCategory = () => {
    setEditingCategory({
      id: null, name: '', inventory_account_id: '', expense_account_id: ''
    })
    setIsCreatingCategory(true)
  }

  const startEditingCategory = (category: InventoryCategory) => {
    setEditingCategory({
      id: category.id, name: category.name,
      inventory_account_id: category.inventory_account_id.toString(),
      expense_account_id: category.expense_account_id.toString()
    })
    setIsCreatingCategory(false)
  }

  const saveCategory = async () => {
    if (!editingCategory || !currentOrganization) return
    const categoryData = {
      organization_id: currentOrganization.id, 
      name: editingCategory.name,
      description: null,
      inventory_account_id: parseInt(editingCategory.inventory_account_id),
      expense_account_id: parseInt(editingCategory.expense_account_id),
      parent_id: null, 
      is_active: true, 
      created_by: null
    }
    try {
      if (isCreatingCategory) await DataService.createInventoryCategory(categoryData)
      else if (editingCategory.id) await DataService.updateInventoryCategory(editingCategory.id, categoryData)
      setEditingCategory(null)
      setIsCreatingCategory(false)
      loadData()
    } catch (error) {
      console.error('Error saving category:', error)
    }
  }

  const deleteCategory = async (categoryId: number) => {
    if (!confirm('Delete this category?')) return
    await DataService.deleteInventoryCategory(categoryId)
    loadData()
  }

  const createTransaction = async () => {
    if (!currentOrganization || !transactionForm.item_id || !transactionForm.quantity) return
    const quantity = parseFloat(transactionForm.quantity)
    const unitCost = parseFloat(transactionForm.unit_cost) || 0
    const finalQuantity = transactionForm.transaction_type === 'out' ? -Math.abs(quantity) : Math.abs(quantity)
    const transactionData = {
      organization_id: currentOrganization.id, 
      item_id: parseInt(transactionForm.item_id),
      transaction_type: transactionForm.transaction_type, 
      quantity: finalQuantity,
      unit_cost: unitCost > 0 ? unitCost : null, 
      total_cost: unitCost > 0 ? Math.abs(quantity) * unitCost : null,
      description: transactionForm.description || null, 
      reference: transactionForm.reference || null,
      transaction_date: transactionForm.transaction_date, 
      journal_entry_id: null, 
      created_by: null
    }
    try {
      await DataService.createInventoryTransaction(transactionData)
      setTransactionForm({
        item_id: '', transaction_type: 'in', quantity: '', unit_cost: '',
        description: '', reference: '', transaction_date: new Date().toISOString().split('T')[0]
      })
      loadData()
    } catch (error) {
      console.error('Error creating transaction:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold win11-text-primary">Inventory Management</h1>
          <p className="win11-text-secondary">Track stock levels, categories, and movements</p>
        </div>
        <Button variant="outline" onClick={loadData}>
          <RefreshCw className="mr-2 h-4 w-4" />Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="md-card-expressive">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-on-surface-variant">Total Value</p>
                <p className="text-2xl font-bold">{formatCurrency(totalValue)}</p>
              </div>
              <DollarSign className="h-8 w-8 text-primary" />
            </div>
          </CardContent>
        </Card>
        <Card className="md-card-expressive">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-on-surface-variant">Total Items</p>
                <p className="text-2xl font-bold">{totalItems}</p>
              </div>
              <Package className="h-8 w-8 text-secondary" />
            </div>
          </CardContent>
        </Card>
        <Card className="md-card-expressive">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-on-surface-variant">Total Quantity</p>
                <p className="text-2xl font-bold">{totalQuantity.toFixed(2)}</p>
              </div>
              <Boxes className="h-8 w-8 text-tertiary" />
            </div>
          </CardContent>
        </Card>
        <Card className="md-card-expressive border-error/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-error">Low Stock</p>
                <p className="text-2xl font-bold text-error">{lowStockCount}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-error" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-2">
        <button
          className={`px-4 py-2 font-medium transition-colors ${
            activeView === 'items' ? 'border-b-2 border-primary text-primary' : 'text-on-surface-variant hover:text-on-surface'
          }`}
          onClick={() => setActiveView('items')}
        >Items</button>
        <button
          className={`px-4 py-2 font-medium transition-colors ${
            activeView === 'categories' ? 'border-b-2 border-primary text-primary' : 'text-on-surface-variant hover:text-on-surface'
          }`}
          onClick={() => setActiveView('categories')}
        >Categories</button>
        <button
          className={`px-4 py-2 font-medium transition-colors ${
            activeView === 'transactions' ? 'border-b-2 border-primary text-primary' : 'text-on-surface-variant hover:text-on-surface'
          }`}
          onClick={() => setActiveView('transactions')}
        >Transactions</button>
      </div>

      {activeView === 'items' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Inventory Items</h2>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-on-surface-variant" />
                <Input placeholder="Search items..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10 w-64" />
              </div>
              <Button onClick={startCreatingItem} size="sm">
                <Plus className="mr-2 h-4 w-4" />Add Item
              </Button>
            </div>
          </div>
          
          <div className="border border-outline rounded-lg overflow-hidden bg-surface">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-surface-container-highest border-b border-outline">
                  <tr>
                    <th className="border-r border-outline px-3 py-2 text-left text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-24">SKU</th>
                    <th className="border-r border-outline px-3 py-2 text-left text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-48">Name</th>
                    <th className="border-r border-outline px-3 py-2 text-left text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-32">Category</th>
                    <th className="border-r border-outline px-3 py-2 text-center text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-16">Unit</th>
                    <th className="border-r border-outline px-3 py-2 text-right text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-20">In</th>
                    <th className="border-r border-outline px-3 py-2 text-right text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-20">Out</th>
                    <th className="border-r border-outline px-3 py-2 text-right text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-24">Available</th>
                    <th className="border-r border-outline px-3 py-2 text-right text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-24">Cost</th>
                    <th className="border-r border-outline px-3 py-2 text-right text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-24">Value</th>
                    <th className="px-3 py-2 text-center text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-20">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-surface">
                  {isCreatingItem && editingItem && (
                    <tr className="bg-primary-container/5 border-b border-outline">
                      <td className="border-r border-outline px-3 py-2">
                        <Input value={editingItem.sku} onChange={(e) => setEditingItem({ ...editingItem, sku: e.target.value })} 
                          placeholder="SKU" className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container" />
                      </td>
                      <td className="border-r border-outline px-3 py-2">
                        <Input value={editingItem.name} onChange={(e) => setEditingItem({ ...editingItem, name: e.target.value })} 
                          placeholder="Item name" className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container" />
                      </td>
                      <td className="border-r border-outline px-3 py-2">
                        <Select value={editingItem.category_id} onValueChange={(v) => setEditingItem({ ...editingItem, category_id: v })}>
                          <SelectTrigger className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container">
                            <SelectValue placeholder="Select" />
                          </SelectTrigger>
                          <SelectContent>{categories.map(c => <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>)}</SelectContent>
                        </Select>
                      </td>
                      <td className="border-r border-outline px-3 py-2 text-center">
                        <Select value={editingItem.unit_of_measure} onValueChange={(v) => setEditingItem({ ...editingItem, unit_of_measure: v })}>
                          <SelectTrigger className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="kg">kg</SelectItem>
                            <SelectItem value="pcs">pcs</SelectItem>
                            <SelectItem value="box">box</SelectItem>
                            <SelectItem value="liter">L</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="border-r border-outline px-3 py-2 text-right text-xs text-on-surface-variant">0.00</td>
                      <td className="border-r border-outline px-3 py-2 text-right text-xs text-on-surface-variant">0.00</td>
                      <td className="border-r border-outline px-3 py-2 text-right text-xs font-medium">0.00</td>
                      <td className="border-r border-outline px-3 py-2">
                        <Input type="number" step="0.01" value={editingItem.average_unit_cost}
                          onChange={(e) => setEditingItem({ ...editingItem, average_unit_cost: e.target.value })} 
                          className="h-7 text-xs text-right border-0 bg-transparent focus:bg-surface-container" />
                      </td>
                      <td className="border-r border-outline px-3 py-2 text-right text-xs font-medium">$0.00</td>
                      <td className="px-3 py-2 text-center">
                        <div className="flex gap-1 justify-center">
                          <Button size="sm" onClick={saveItem} className="h-6 w-6 p-0">
                            <Check className="h-3 w-3" />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => { setEditingItem(null); setIsCreatingItem(false) }} className="h-6 w-6 p-0">
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )}
                  {filteredItems.map(item => {
                    const isEditing = editingItem?.id === item.id
                    const isLowStock = item.reorder_point > 0 && item.quantity_available <= item.reorder_point
                    if (isEditing && editingItem) {
                      return (
                        <tr key={item.id} className="bg-primary-container/5 border-b border-outline">
                          <td className="border-r border-outline px-3 py-2 text-xs font-mono text-on-surface-variant">{item.sku}</td>
                          <td className="border-r border-outline px-3 py-2">
                            <Input value={editingItem.name} onChange={(e) => setEditingItem({ ...editingItem, name: e.target.value })} 
                              className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container" />
                          </td>
                          <td className="border-r border-outline px-3 py-2">
                            <Select value={editingItem.category_id} onValueChange={(v) => setEditingItem({ ...editingItem, category_id: v })}>
                              <SelectTrigger className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>{categories.map(c => <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>)}</SelectContent>
                            </Select>
                          </td>
                          <td className="border-r border-outline px-3 py-2 text-center">
                            <Select value={editingItem.unit_of_measure} onValueChange={(v) => setEditingItem({ ...editingItem, unit_of_measure: v })}>
                              <SelectTrigger className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="kg">kg</SelectItem>
                                <SelectItem value="pcs">pcs</SelectItem>
                                <SelectItem value="box">box</SelectItem>
                                <SelectItem value="liter">L</SelectItem>
                              </SelectContent>
                            </Select>
                          </td>
                          <td className="border-r border-outline px-3 py-2 text-right text-xs text-green-600">{item.quantity_in.toFixed(2)}</td>
                          <td className="border-r border-outline px-3 py-2 text-right text-xs text-red-600">{item.quantity_out.toFixed(2)}</td>
                          <td className="border-r border-outline px-3 py-2 text-right text-xs font-medium">{item.quantity_available.toFixed(2)}</td>
                          <td className="border-r border-outline px-3 py-2">
                            <Input type="number" step="0.01" value={editingItem.average_unit_cost}
                              onChange={(e) => setEditingItem({ ...editingItem, average_unit_cost: e.target.value })} 
                              className="h-7 text-xs text-right border-0 bg-transparent focus:bg-surface-container" />
                          </td>
                          <td className="border-r border-outline px-3 py-2 text-right text-xs font-medium">{formatCurrency(item.total_value)}</td>
                          <td className="px-3 py-2 text-center">
                            <div className="flex gap-1 justify-center">
                              <Button size="sm" onClick={saveItem} className="h-6 w-6 p-0">
                                <Check className="h-3 w-3" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => setEditingItem(null)} className="h-6 w-6 p-0">
                                <X className="h-3 w-3" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      )
                    }
                    return (
                      <tr key={item.id} className="border-b border-outline hover:bg-surface-container/30 group">
                        <td className="border-r border-outline px-3 py-2 text-xs font-mono text-on-surface-variant">{item.sku}</td>
                        <td className="border-r border-outline px-3 py-2 text-xs font-medium text-on-surface group-hover:bg-surface-container/20">
                          <div className="flex items-center gap-2">
                            <span>{item.name}</span>
                            {isLowStock && <AlertTriangle className="h-3 w-3 text-error flex-shrink-0" />}
                          </div>
                        </td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-on-surface-variant">{item.category?.name || '-'}</td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-center text-on-surface-variant">{item.unit_of_measure}</td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-right text-green-600 font-mono">{item.quantity_in.toFixed(2)}</td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-right text-red-600 font-mono">{item.quantity_out.toFixed(2)}</td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-right font-medium font-mono">
                          <span className={isLowStock ? 'text-error' : 'text-on-surface'}>{item.quantity_available.toFixed(2)}</span>
                        </td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-right font-mono">{formatCurrency(item.average_unit_cost)}</td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-right font-medium font-mono">{formatCurrency(item.total_value)}</td>
                        <td className="px-3 py-2 text-center">
                          <div className="flex gap-1 justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button size="sm" variant="ghost" onClick={() => startEditingItem(item)} className="h-6 w-6 p-0">
                              <Edit className="h-3 w-3" />
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => deleteItem(item.id)} className="h-6 w-6 p-0">
                              <Trash2 className="h-3 w-3 text-error" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeView === 'categories' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Inventory Categories</h2>
            <Button onClick={startCreatingCategory} size="sm">
              <Plus className="mr-2 h-4 w-4" />Add Category
            </Button>
          </div>
          
          <div className="border border-outline rounded-lg overflow-hidden bg-surface">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-surface-container-highest border-b border-outline">
                  <tr>
                    <th className="border-r border-outline px-3 py-2 text-left text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-56">Name</th>
                    <th className="border-r border-outline px-3 py-2 text-left text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-64">Inventory Account</th>
                    <th className="border-r border-outline px-3 py-2 text-left text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-64">Expense Account</th>
                    <th className="border-r border-outline px-3 py-2 text-center text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-24">Items</th>
                    <th className="border-r border-outline px-3 py-2 text-right text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-32">Value</th>
                    <th className="px-3 py-2 text-center text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-24">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-surface">
                  {isCreatingCategory && editingCategory && (
                    <tr className="bg-primary-container/5 border-b border-outline">
                      <td className="border-r border-outline px-3 py-2">
                        <Input value={editingCategory.name} onChange={(e) => setEditingCategory({ ...editingCategory, name: e.target.value })} 
                          placeholder="Category name" className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container" />
                      </td>
                      <td className="border-r border-outline px-3 py-2">
                        <AccountSelect accounts={accounts} value={editingCategory.inventory_account_id}
                          onChange={(v) => setEditingCategory({ ...editingCategory, inventory_account_id: v })} 
                          placeholder="Select account" className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container" />
                      </td>
                      <td className="border-r border-outline px-3 py-2">
                        <AccountSelect accounts={accounts} value={editingCategory.expense_account_id}
                          onChange={(v) => setEditingCategory({ ...editingCategory, expense_account_id: v })} 
                          placeholder="Select account" className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container" />
                      </td>
                      <td className="border-r border-outline px-3 py-2 text-center text-xs text-on-surface-variant">0</td>
                      <td className="border-r border-outline px-3 py-2 text-right text-xs font-medium">$0.00</td>
                      <td className="px-3 py-2 text-center">
                        <div className="flex gap-1 justify-center">
                          <Button size="sm" onClick={saveCategory} className="h-6 w-6 p-0">
                            <Check className="h-3 w-3" />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => { setEditingCategory(null); setIsCreatingCategory(false) }} className="h-6 w-6 p-0">
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )}
                  {filteredCategories.map(category => {
                    const isEditing = editingCategory?.id === category.id
                    if (isEditing && editingCategory) {
                      return (
                        <tr key={category.id} className="bg-primary-container/5 border-b border-outline">
                          <td className="border-r border-outline px-3 py-2">
                            <Input value={editingCategory.name} onChange={(e) => setEditingCategory({ ...editingCategory, name: e.target.value })} 
                              className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container" />
                          </td>
                          <td className="border-r border-outline px-3 py-2">
                            <AccountSelect accounts={accounts} value={editingCategory.inventory_account_id}
                              onChange={(v) => setEditingCategory({ ...editingCategory, inventory_account_id: v })} 
                              placeholder="Select" className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container" />
                          </td>
                          <td className="border-r border-outline px-3 py-2">
                            <AccountSelect accounts={accounts} value={editingCategory.expense_account_id}
                              onChange={(v) => setEditingCategory({ ...editingCategory, expense_account_id: v })} 
                              placeholder="Select" className="h-7 text-xs border-0 bg-transparent focus:bg-surface-container" />
                          </td>
                          <td className="border-r border-outline px-3 py-2 text-center text-xs text-on-surface-variant">0</td>
                          <td className="border-r border-outline px-3 py-2 text-right text-xs font-medium">$0.00</td>
                          <td className="px-3 py-2 text-center">
                            <div className="flex gap-1 justify-center">
                              <Button size="sm" onClick={saveCategory} className="h-6 w-6 p-0">
                                <Check className="h-3 w-3" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => setEditingCategory(null)} className="h-6 w-6 p-0">
                                <X className="h-3 w-3" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      )
                    }
                    return (
                      <tr key={category.id} className="border-b border-outline hover:bg-surface-container/30 group">
                        <td className="border-r border-outline px-3 py-2 text-xs font-medium text-on-surface group-hover:bg-surface-container/20">{category.name}</td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-on-surface-variant font-mono">
                          {category.inventory_account ? `${category.inventory_account.code} - ${category.inventory_account.name}` : '-'}
                        </td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-on-surface-variant font-mono">
                          {category.expense_account ? `${category.expense_account.code} - ${category.expense_account.name}` : '-'}
                        </td>
                        <td className="border-r border-outline px-3 py-2 text-center text-xs text-on-surface-variant">0</td>
                        <td className="border-r border-outline px-3 py-2 text-right text-xs font-medium font-mono">$0.00</td>
                        <td className="px-3 py-2 text-center">
                          <div className="flex gap-1 justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button size="sm" variant="ghost" onClick={() => startEditingCategory(category)} className="h-6 w-6 p-0">
                              <Edit className="h-3 w-3" />
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => deleteCategory(category.id)} className="h-6 w-6 p-0">
                              <Trash2 className="h-3 w-3 text-error" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeView === 'transactions' && (
        <div className="space-y-4">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Record Transaction</h2>
            <div className="border border-outline rounded-lg p-4 bg-surface-container/30">
              <div className="grid grid-cols-7 gap-3">
                <div>
                  <Label className="text-xs font-medium text-on-surface-variant">Item</Label>
                  <Select value={transactionForm.item_id} onValueChange={(v) => setTransactionForm({ ...transactionForm, item_id: v })}>
                    <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Select item" /></SelectTrigger>
                    <SelectContent>{items.map(i => <SelectItem key={i.id} value={i.id.toString()}>{i.name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs font-medium text-on-surface-variant">Type</Label>
                  <Select value={transactionForm.transaction_type} onValueChange={(v: any) => setTransactionForm({ ...transactionForm, transaction_type: v })}>
                    <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="in">IN</SelectItem>
                      <SelectItem value="out">OUT</SelectItem>
                      <SelectItem value="adjustment">Adjustment</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs font-medium text-on-surface-variant">Quantity</Label>
                  <Input type="number" placeholder="Qty" value={transactionForm.quantity}
                    onChange={(e) => setTransactionForm({ ...transactionForm, quantity: e.target.value })} 
                    className="h-8 text-xs" />
                </div>
                <div>
                  <Label className="text-xs font-medium text-on-surface-variant">Unit Cost</Label>
                  <Input type="number" placeholder="Cost" value={transactionForm.unit_cost}
                    onChange={(e) => setTransactionForm({ ...transactionForm, unit_cost: e.target.value })} 
                    className="h-8 text-xs" />
                </div>
                <div>
                  <Label className="text-xs font-medium text-on-surface-variant">Reference</Label>
                  <Input placeholder="Ref" value={transactionForm.reference}
                    onChange={(e) => setTransactionForm({ ...transactionForm, reference: e.target.value })} 
                    className="h-8 text-xs" />
                </div>
                <div>
                  <Label className="text-xs font-medium text-on-surface-variant">Date</Label>
                  <Input type="date" value={transactionForm.transaction_date}
                    onChange={(e) => setTransactionForm({ ...transactionForm, transaction_date: e.target.value })} 
                    className="h-8 text-xs" />
                </div>
                <div className="flex items-end">
                  <Button onClick={createTransaction} className="w-full h-8 text-xs">
                    <Check className="mr-2 h-3 w-3" />Record
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Transaction History</h2>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-on-surface-variant" />
                <Input placeholder="Search transactions..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10 w-64" />
              </div>
            </div>
            
            <div className="border border-outline rounded-lg overflow-hidden bg-surface">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead className="bg-surface-container-highest border-b border-outline">
                    <tr>
                      <th className="border-r border-outline px-3 py-2 text-left text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-24">Date</th>
                      <th className="border-r border-outline px-3 py-2 text-center text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-20">Type</th>
                      <th className="border-r border-outline px-3 py-2 text-left text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-48">Item</th>
                      <th className="border-r border-outline px-3 py-2 text-right text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-20">Qty</th>
                      <th className="border-r border-outline px-3 py-2 text-right text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-24">Cost</th>
                      <th className="border-r border-outline px-3 py-2 text-right text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-24">Total</th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-on-surface-variant bg-surface-container-highest w-32">Ref</th>
                    </tr>
                  </thead>
                  <tbody className="bg-surface">
                    {filteredTransactions.map(txn => (
                      <tr key={txn.id} className="border-b border-outline hover:bg-surface-container/30 group">
                        <td className="border-r border-outline px-3 py-2 text-xs text-on-surface-variant font-mono">
                          {new Date(txn.transaction_date).toLocaleDateString()}
                        </td>
                        <td className="border-r border-outline px-3 py-2 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            txn.transaction_type === 'in' ? 'bg-green-100 text-green-700' : 
                            txn.transaction_type === 'out' ? 'bg-red-100 text-red-700' : 
                            'bg-yellow-100 text-yellow-700'
                          }`}>{txn.transaction_type.toUpperCase()}</span>
                        </td>
                        <td className="border-r border-outline px-3 py-2 text-xs font-medium text-on-surface group-hover:bg-surface-container/20">
                          {txn.item?.name}
                        </td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-right font-mono">
                          <span className={txn.quantity >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {txn.quantity >= 0 ? '+' : ''}{txn.quantity.toFixed(2)}
                          </span>
                        </td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-right font-mono text-on-surface-variant">
                          {txn.unit_cost ? formatCurrency(txn.unit_cost) : '-'}
                        </td>
                        <td className="border-r border-outline px-3 py-2 text-xs text-right font-medium font-mono text-on-surface">
                          {txn.total_cost ? formatCurrency(txn.total_cost) : '-'}
                        </td>
                        <td className="px-3 py-2 text-xs text-on-surface-variant">
                          {txn.reference || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}