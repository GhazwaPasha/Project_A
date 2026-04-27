'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Search, 
  Download,
  Upload,
  RefreshCw,
  Plus,
  Edit,
  Trash2,
  Eye,
  ChevronRight,
  ChevronDown,
  Building2,
  DollarSign,
  FileText,
  Settings,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Info,
  LayoutList,
  Share2,
  Sparkles,
} from 'lucide-react'
import { cn, formatDate } from '@/lib/utils'
import { useOrganizationFormatters } from '@/hooks/use-organization-formatters'
import { accountTypeBadgeClass } from '@/lib/account-type-badges'
import { DataService } from '@/lib/data-service'
import {
  allowedReportCategoriesForAccountType,
  formatReportCategoryLabel,
} from '@/lib/account-report-category'
import {
  parseAccountFromNaturalLanguage,
  type AccountChartContextRow,
} from '@/lib/ai-account-parser'
import { Account, AccountReportCategory, AccountType } from '@/types'
import { useOrganization } from '@/hooks/use-organization'
import { useOrgDataPermission, useOrgMemberRoleResolved } from '@/hooks/use-org-permissions'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AccountsGraphView } from '@/components/accounts/accounts-graph-view'

// Enhanced account interface with hierarchy support
interface HierarchicalAccount extends Account {
  level: number
  is_postable: boolean
  parent_code?: string
  group_inherited?: boolean
  balance?: number
  debit_balance?: number
  credit_balance?: number
  transaction_count?: number
  last_transaction_date?: string | null
  children?: HierarchicalAccount[]
  isExpanded?: boolean
  isSelected?: boolean
}

interface AccountFormData {
  name: string
  account_type: AccountType
  parent_id: number | null
  /** Empty string = unspecified (NULL in DB). */
  report_category: '' | AccountReportCategory
  is_postable: boolean
}

/** Postable / Group pills — outline only */
const accountMetaBadgeClass =
  'inline-flex items-center rounded-md border border-outline-variant px-2 py-0.5 text-xs font-medium text-on-surface bg-transparent'

export function Win11AccountsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [accounts, setAccounts] = useState<HierarchicalAccount[]>([])
  const [flatAccounts, setFlatAccounts] = useState<HierarchicalAccount[]>([])
  const [selectedAccount, setSelectedAccount] = useState<HierarchicalAccount | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const { currentOrganization } = useOrganization()
  const { formatCurrency } = useOrganizationFormatters()
  const roleResolved = useOrgMemberRoleResolved()
  const canEditChart = useOrgDataPermission('chart.write')
  const canExportData = useOrgDataPermission('data.export')
  const chartEditDisabled = !roleResolved || !canEditChart
  const exportDisabled = !roleResolved || !canExportData
  const chartEditTitle = !roleResolved
    ? 'Checking your access…'
    : !canEditChart
      ? 'Your role cannot edit the chart of accounts'
      : undefined
  const exportTitle = !roleResolved
    ? 'Checking your access…'
    : !canExportData
      ? 'Your role cannot export'
      : undefined
  const [formData, setFormData] = useState<AccountFormData>({
    name: '',
    account_type: 'asset',
    parent_id: null,
    report_category: '',
    is_postable: true
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [expandedAccounts, setExpandedAccounts] = useState<Set<number>>(new Set())
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importPreview, setImportPreview] = useState<any[]>([])
  const [importErrors, setImportErrors] = useState<string[]>([])
  const [isImporting, setIsImporting] = useState(false)
  const [showSearchField, setShowSearchField] = useState(false)
  const [viewMode, setViewMode] = useState<'list' | 'graph'>('list')
  const [coaAiInput, setCoaAiInput] = useState('')
  const [coaAiLoading, setCoaAiLoading] = useState(false)
  const [coaAiProgress, setCoaAiProgress] = useState(0)

  // Load data on component mount and when organization changes
  useEffect(() => {
    if (currentOrganization) {
      loadData()
    }
  }, [currentOrganization])

  const loadData = async () => {
    if (!currentOrganization) return
    
    try {
      setLoading(true)
      
      // Load accounts using the unified method for current organization
      const allAccounts = await DataService.getAccounts(currentOrganization.id, true)
      
      // Convert to hierarchical structure
      const hierarchicalAccounts = buildAccountHierarchy(allAccounts)
      setAccounts(hierarchicalAccounts)
      const codeById = new Map(allAccounts.map((a) => [a.id, a.code]))
      setFlatAccounts(flattenHierarchy(hierarchicalAccounts, codeById))
      
      // Auto-expand top-level accounts
      const topLevelIds = new Set(allAccounts.filter(acc => !acc.parent_id).map(acc => acc.id))
      setExpandedAccounts(topLevelIds)
      
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const buildAccountHierarchy = (flatAccounts: Account[]): HierarchicalAccount[] => {
    const accountMap = new Map<number, HierarchicalAccount>()
    const rootAccounts: HierarchicalAccount[] = []

    // First pass: create map and add children array
    flatAccounts.forEach(account => {
      accountMap.set(account.id, {
        ...account,
        level: 1,
        is_postable: account.is_postable,
        children: [],
        isExpanded: false,
        isSelected: false,
      })
    })

    // Second pass: build hierarchy
    flatAccounts.forEach(account => {
      const accountWithChildren = accountMap.get(account.id)!
      
      if (account.parent_id && accountMap.has(account.parent_id)) {
        const parent = accountMap.get(account.parent_id)!
        parent.children!.push(accountWithChildren)
      } else {
        rootAccounts.push(accountWithChildren)
      }
    })

    // Sort accounts by code at each level
    const sortAccounts = (accs: HierarchicalAccount[]) => {
      accs.sort((a, b) => a.code.localeCompare(b.code))
      accs.forEach(acc => {
        if (acc.children && acc.children.length > 0) {
          sortAccounts(acc.children)
        }
      })
    }

    sortAccounts(rootAccounts)

    const assignLevels = (accs: HierarchicalAccount[], depth: number) => {
      accs.forEach((a) => {
        a.level = depth
        if (a.children && a.children.length > 0) {
          assignLevels(a.children, depth + 1)
        }
      })
    }
    assignLevels(rootAccounts, 1)

    return rootAccounts
  }

  const flattenHierarchy = (
    nodes: HierarchicalAccount[],
    codeById: Map<number, string>
  ): HierarchicalAccount[] => {
    const out: HierarchicalAccount[] = []
    const walk = (list: HierarchicalAccount[]) => {
      list.forEach((node) => {
        const { children, ...rest } = node
        const parent_code = node.parent_id ? codeById.get(node.parent_id) : undefined
        out.push({
          ...rest,
          parent_code,
          children: [],
          isExpanded: false,
          isSelected: false,
        })
        if (children?.length) walk(children)
      })
    }
    walk(nodes)
    return out
  }

  const filteredAccounts = accounts.filter(account => {
    const matchesSearch = account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         account.code.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  const toggleExpanded = (accountId: number) => {
    setExpandedAccounts(prev => {
      const newSet = new Set(prev)
      if (newSet.has(accountId)) {
        newSet.delete(accountId)
      } else {
        newSet.add(accountId)
      }
      return newSet
    })
  }

  const selectAccount = (account: HierarchicalAccount) => {
    setSelectedAccount(account)
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    if (!formData.name.trim()) {
      errors.name = 'Account name is required'
    }

    if (!formData.account_type) {
      errors.account_type = 'Account type is required'
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleCreateAccount = async () => {
    if (!validateForm() || !currentOrganization) return

    try {
      const newAccount = await DataService.createAccount({
        organization_id: currentOrganization.id,
        name: formData.name,
        account_type: formData.account_type,
        parent_id: formData.parent_id,
        description: null,
        group: null,
        report_category: formData.report_category ? formData.report_category : null,
        is_active: true,
        is_postable: formData.is_postable,
        created_by: (await DataService.getCurrentUser())?.id || null
      })

      if (newAccount) {
        await loadData()
        setShowCreateModal(false)
        resetForm()
      }
    } catch (error) {
      console.error('Error creating account:', error)
    }
  }

  const handleUpdateAccount = async () => {
    if (!validateForm() || !selectedAccount || !currentOrganization) return

    try {
      const updatedAccount = await DataService.updateAccount(selectedAccount.id, {
        name: formData.name,
        account_type: formData.account_type,
        parent_id: formData.parent_id,
        description: null,
        report_category: formData.report_category ? formData.report_category : null,
        is_postable: formData.is_postable
      })

      if (updatedAccount) {
        await loadData()
        setShowEditModal(false)
        setSelectedAccount(null)
        resetForm()
      }
    } catch (error) {
      console.error('Error updating account:', error)
    }
  }

  const handleDeleteAccount = async (accountId: number) => {
    if (!currentOrganization) return
    if (!roleResolved || !canEditChart) return

    if (confirm('Are you sure you want to delete this account? This action cannot be undone.')) {
      try {
        // Check if account has children
        const hasChildren = flatAccounts.some(acc => acc.parent_id === accountId)
        if (hasChildren) {
          alert('Cannot delete account with child accounts. Please delete child accounts first.')
          return
        }

        // Check if account has transactions
        const account = flatAccounts.find(acc => acc.id === accountId)
        if (account && account.transaction_count && account.transaction_count > 0) {
          alert('Cannot delete account with transactions. Please deactivate instead.')
          return
        }

        // Delete the account
        const success = await DataService.deleteAccount(accountId)
        if (success) {
          await loadData()
          setSelectedAccount(null)
        } else {
          alert('Failed to delete account. Please try again.')
        }
      } catch (error) {
        console.error('Error deleting account:', error)
        alert('Error deleting account. Please try again.')
      }
    }
  }

  const handleExportAccounts = () => {
    if (!roleResolved || !canExportData) return
    const exportData = flatAccounts.map(account => ({
      'Account Code': account.code,
      'Account Name': account.name,
      'Account Type': account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1),
      'Parent Code': account.parent_code || '',
      'Level': account.level,
      'Postable': account.is_postable ? 'Yes' : 'No',
      'Report category': account.report_category
        ? formatReportCategoryLabel(account.report_category)
        : account.group
          ? account.group.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())
          : '',
      'Transaction Count': account.transaction_count || 0,
      'Last Transaction': account.last_transaction_date ? formatDate(account.last_transaction_date) : ''
    }))

    const csvContent = [
      Object.keys(exportData[0]).join(','),
      ...exportData.map(row => Object.values(row).map(value => `"${value}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `chart_of_accounts_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handleImportAccounts = () => {
    if (!roleResolved || !canEditChart) return
    setShowImportModal(true)
    setImportFile(null)
    setImportPreview([])
    setImportErrors([])
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setImportFile(file)
    setImportErrors([])

    // Parse CSV file
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string
        const lines = text.split('\n').filter(line => line.trim())
        
        if (lines.length < 2) {
          setImportErrors(['File must contain at least a header row and one data row'])
          return
        }

        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
        const requiredColumns = ['Name', 'Type']
        const missingColumns = requiredColumns.filter(col => !headers.includes(col))
        
        if (missingColumns.length > 0) {
          setImportErrors([`Missing required columns: ${missingColumns.join(', ')}`])
          return
        }

        const data = lines.slice(1).map((line, index) => {
          const values = line.split(',').map(v => v.trim().replace(/"/g, ''))
          const row: any = {}
          headers.forEach((header, i) => {
            row[header] = values[i] || ''
          })
          row._rowIndex = index + 2 // +2 because we skip header and arrays are 0-indexed
          return row
        })

        setImportPreview(data)
      } catch (error) {
        setImportErrors([`Error parsing file: ${error}`])
      }
    }
    reader.readAsText(file)
  }

  const handleImportConfirm = async () => {
    if (!importFile || !currentOrganization || importPreview.length === 0) return

    setIsImporting(true)
    const errors: string[] = []
    let successCount = 0
    let skippedCount = 0

    try {
      let mergedAccounts = await DataService.getAccounts(currentOrganization.id, false)
      const existingNames = new Set(mergedAccounts.map((acc) => acc.name.toLowerCase()))
      const codeToAccount = new Map(mergedAccounts.map((a) => [a.code, a]))
      const nameToAccount = new Map(mergedAccounts.map((a) => [a.name.toLowerCase(), a]))

      type ImportRow = (typeof importPreview)[number]
      let pending: ImportRow[] = [...importPreview]
      const validTypes = ['asset', 'liability', 'equity', 'revenue', 'expense']
      const maxIter = importPreview.length + 15
      let iter = 0

      while (pending.length > 0 && iter < maxIter) {
        iter++
        const nextRound: ImportRow[] = []
        let progressed = false

        for (const row of pending) {
          try {
            const name = row.Name?.trim()
            const accountType = row.Type?.trim().toLowerCase()

            if (!name || !accountType) {
              errors.push(`Row ${row._rowIndex}: Missing required fields (Name, Type)`)
              continue
            }

            if (!validTypes.includes(accountType)) {
              errors.push(
                `Row ${row._rowIndex}: Invalid account type '${accountType}'. Must be one of: ${validTypes.join(', ')}`
              )
              continue
            }

            if (existingNames.has(name.toLowerCase())) {
              skippedCount++
              progressed = true
              continue
            }

            const parentCode = row['Parent Code']?.trim()
            const parentName = row['Parent Name']?.trim()

            let parentId: number | null = null
            if (parentCode) {
              const p = codeToAccount.get(parentCode)
              if (!p) {
                nextRound.push(row)
                continue
              }
              parentId = p.id
            } else if (parentName) {
              const p = nameToAccount.get(parentName.toLowerCase())
              if (!p) {
                nextRound.push(row)
                continue
              }
              parentId = p.id
            }

            if (parentId != null) {
              const pAcc = mergedAccounts.find((a) => a.id === parentId)
              if (pAcc && pAcc.account_type !== accountType) {
                errors.push(
                  `Row ${row._rowIndex}: Parent account type (${pAcc.account_type}) must match row type (${accountType}).`
                )
                continue
              }
            }

            const rawReportCat = row['Report category']?.trim() || row['Report Category']?.trim()
            const isPostable =
              row['Is Postable']?.toLowerCase() === 'yes' ||
              row['Is Postable']?.toLowerCase() === 'true' ||
              row['Is Postable'] === '1'

            let reportCategory: AccountReportCategory | null = null
            if (rawReportCat) {
              const allowed = allowedReportCategoriesForAccountType(accountType as AccountType)
              if (!allowed.includes(rawReportCat as AccountReportCategory)) {
                errors.push(
                  `Row ${row._rowIndex}: Invalid Report category "${rawReportCat}" for type ${accountType}. Use one of: ${allowed.join(', ')}`
                )
                continue
              }
              reportCategory = rawReportCat as AccountReportCategory
            }

            const newAccount = await DataService.createAccount({
              organization_id: currentOrganization.id,
              name,
              account_type: accountType as AccountType,
              parent_id: parentId,
              description: row.Description?.trim() || null,
              group: null,
              report_category: reportCategory,
              is_postable: isPostable,
              is_active: true,
              created_by: (await DataService.getCurrentUser())?.id || null,
            })

            if (newAccount) {
              successCount++
              existingNames.add(name.toLowerCase())
              mergedAccounts = [...mergedAccounts, newAccount]
              codeToAccount.set(newAccount.code, newAccount)
              nameToAccount.set(newAccount.name.toLowerCase(), newAccount)
              progressed = true
            } else {
              errors.push(`Row ${row._rowIndex}: Failed to create account '${name}'`)
            }
          } catch (error) {
            errors.push(`Row ${row._rowIndex}: ${error}`)
          }
        }

        if (!progressed && nextRound.length === pending.length && nextRound.length > 0) {
          for (const row of nextRound) {
            errors.push(
              `Row ${row._rowIndex}: Could not resolve parent — use Parent Code from your chart or Parent Name matching an existing account or a row imported earlier in this file.`
            )
          }
          break
        }

        pending = nextRound
      }

      if (pending.length > 0 && iter >= maxIter) {
        for (const row of pending) {
          errors.push(`Row ${row._rowIndex}: Import stopped — check parent references for cycles or typos.`)
        }
      }

      setImportErrors(errors)
      
      if (successCount > 0) {
        await loadData() // Refresh the accounts list
      }

      // Show results
      const resultMessage = `Import completed:\n\n✅ Successfully imported: ${successCount} accounts\n⏭️ Skipped (already exist): ${skippedCount} accounts\n❌ Errors: ${errors.length} accounts`
      alert(resultMessage)

    } catch (error) {
      console.error('Import error:', error)
      setImportErrors([`Import failed: ${error}`])
    } finally {
      setIsImporting(false)
    }
  }

  const handleImportCancel = () => {
    setShowImportModal(false)
    setImportFile(null)
    setImportPreview([])
    setImportErrors([])
  }

  const resetForm = () => {
    setFormData({
      name: '',
      account_type: 'asset',
      parent_id: null,
      report_category: '',
      is_postable: true
    })
    setFormErrors({})
    setCoaAiInput('')
    setCoaAiProgress(0)
  }

  const chartContextRowsForAI = (): AccountChartContextRow[] =>
    flatAccounts.map((a) => ({
      id: a.id,
      code: a.code,
      name: a.name,
      account_type: a.account_type,
      is_postable: a.is_postable,
      parent_id: a.parent_id ?? null,
    }))

  const openCreateModal = () => {
    if (!roleResolved || !canEditChart) return
    resetForm()
    setShowCreateModal(true)
  }

  const openEditModal = (account: HierarchicalAccount) => {
    if (!roleResolved || !canEditChart) return
    setFormData({
      name: account.name,
      account_type: account.account_type,
      parent_id: account.parent_id,
      report_category: (account.report_category || '') as '' | AccountReportCategory,
      is_postable: account.is_postable
    })
    setFormErrors({})
    setCoaAiInput('')
    setCoaAiProgress(0)
    setShowEditModal(true)
  }

  const handleCoaAiFill = async (isEdit: boolean) => {
    if (!coaAiInput.trim()) return
    try {
      setCoaAiLoading(true)
      setCoaAiProgress(0)
      setFormErrors((prev) => {
        const next = { ...prev }
        delete next.coa_ai
        return next
      })
      const progressInterval = setInterval(() => {
        setCoaAiProgress((prev) => (prev >= 90 ? prev : prev + Math.random() * 15))
      }, 200)

      const editingSummary =
        isEdit && selectedAccount
          ? `${selectedAccount.code} — ${selectedAccount.name} (type: ${selectedAccount.account_type})`
          : null

      const parsed = await parseAccountFromNaturalLanguage(coaAiInput, chartContextRowsForAI(), {
        excludeAccountId: isEdit && selectedAccount ? selectedAccount.id : undefined,
        editingAccountSummary: editingSummary,
      })
      clearInterval(progressInterval)
      setCoaAiProgress(100)

      let parent_id: number | null = null
      if (parsed.parent_account_code) {
        const p = flatAccounts.find(
          (a) => a.code === parsed.parent_account_code && a.account_type === parsed.account_type
        )
        parent_id = p ? p.id : null
      }

      setFormData({
        name: parsed.name,
        account_type: parsed.account_type,
        parent_id,
        report_category: (parsed.report_category ?? '') as '' | AccountReportCategory,
        is_postable: parsed.is_postable,
      })
      setCoaAiInput('')
    } catch (e) {
      console.error(e)
      setFormErrors((prev) => ({
        ...prev,
        coa_ai: e instanceof Error ? e.message : 'AI parse failed',
      }))
    } finally {
      setCoaAiLoading(false)
      setCoaAiProgress(0)
    }
  }

  const renderAccountItem = (account: HierarchicalAccount, level: number = 0) => {
    const hasChildren = account.children && account.children.length > 0
    const isExpanded = expandedAccounts.has(account.id)
    const isSelected = selectedAccount?.id === account.id

    return (
      <div key={account.id}>
        <div 
          className={`flex items-center p-3 rounded-lg cursor-pointer transition-all duration-200 ${
            isSelected 
              ? 'bg-primary-container text-on-primary-container' 
              : 'hover:bg-surface-container'
          }`}
          style={{ paddingLeft: `${12 + (level * 24)}px` }}
          onClick={() => selectAccount(account)}
        >
          <div className="flex items-center flex-1 min-w-0">
            {hasChildren ? (
              <div
                onClick={(e) => {
                  e.stopPropagation()
                  toggleExpanded(account.id)
                }}
                className="mr-2 p-1 rounded cursor-pointer hover:bg-gray-100 transition-colors"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </div>
            ) : (
              <div className="w-6 mr-2" />
            )}
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-3">
                <span className="font-mono text-sm text-on-surface-variant min-w-0">
                  {account.code}
                </span>
                <span className="md-body-medium text-on-surface truncate">
                  {account.name}
                </span>
                <span className={accountTypeBadgeClass(account.account_type)}>
                  {account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)}
                </span>
                {account.is_postable && (
                  <span className={accountMetaBadgeClass}>Postable</span>
                )}
                {(account.report_category || account.group) && (
                  <span className={accountMetaBadgeClass}>
                    {account.report_category
                      ? formatReportCategoryLabel(account.report_category)
                      : account.group!.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
            </div>
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div>
            {account.children!.map((child: HierarchicalAccount) => renderAccountItem(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  const renderFormModal = (isEdit: boolean) => {
    const modalTitle = isEdit ? 'Edit Account' : 'Create New Account'
    const handleSubmit = isEdit ? handleUpdateAccount : handleCreateAccount

     return (
       <div className="fixed inset-0 z-50 flex items-center justify-center bg-[color-mix(in_srgb,var(--md-sys-color-scrim)_42%,transparent)] backdrop-blur-[1px]">
         <div className="m3-accounts-dialog w-full max-w-md rounded-2xl p-6 mx-4">
          <div className="flex items-center justify-between mb-6 gap-3">
            <h2 className="md-headline-small text-on-surface">{modalTitle}</h2>
            <button
              type="button"
              onClick={() => {
                setShowCreateModal(false)
                setShowEditModal(false)
                resetForm()
              }}
              className="rounded-full p-2 text-on-surface-variant transition-colors hover:bg-[color-mix(in_srgb,var(--md-sys-color-on-surface)_8%,transparent)] hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--md-sys-color-primary)_45%,transparent)]"
              aria-label="Close"
            >
              <X className="h-5 w-5" aria-hidden />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label htmlFor="account-ai-input" className="md-text-field-label block">
                AI assistant
              </label>
              <p className="md-body-small text-on-surface-variant mb-2">
                Describe the account (type, parent, postable vs header, report section). AI fills the fields below; the account code is assigned automatically when you save.
              </p>
              <div className="flex gap-2">
                <Input
                  id="account-ai-input"
                  placeholder='e.g. "6100 office rent expense, operating expense, postable"'
                  value={coaAiInput}
                  onChange={(e) => setCoaAiInput(e.target.value)}
                  className="flex-1"
                  disabled={coaAiLoading}
                  autoComplete="off"
                />
                {coaAiLoading ? (
                  <div className="relative h-10 w-32 overflow-hidden rounded-lg border border-outline bg-surface-container-highest">
                    <div
                      className="absolute inset-0 bg-primary transition-all duration-300 ease-out"
                      style={{ width: `${coaAiProgress}%` }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="relative z-10 text-sm font-medium text-on-primary">
                        {coaAiProgress < 100 ? 'Thinking…' : 'Done'}
                      </span>
                    </div>
                  </div>
                ) : (
                  <Button
                    type="button"
                    className="md-button h-10 shrink-0 border-0 bg-primary px-4 text-on-primary hover:opacity-90"
                    onClick={() => handleCoaAiFill(isEdit)}
                    disabled={!coaAiInput.trim()}
                  >
                    <span className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4" aria-hidden />
                      AI fill
                    </span>
                  </Button>
                )}
              </div>
              {formErrors.coa_ai && (
                <p className="md-text-field-helper error mt-1">{formErrors.coa_ai}</p>
              )}
            </div>

            <div>
              <span className="md-text-field-label block">Account code</span>
              {isEdit && selectedAccount ? (
                <p
                  className="mt-1 rounded-lg border border-outline-variant bg-surface-container-high px-3 py-2 font-mono text-sm text-on-surface"
                  aria-live="polite"
                >
                  {selectedAccount.code}
                </p>
              ) : (
                <p className="md-body-small text-on-surface-variant mt-1">
                  Assigned automatically from account type and parent (e.g. assets use 1000–1999).
                </p>
              )}
            </div>

            <div>
              <label htmlFor="account-form-name" className="md-text-field-label block">
                Account Name *
              </label>
              <Input
                id="account-form-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Cash"
                autoComplete="off"
                className={cn('md-text-field-input', formErrors.name && 'error')}
              />
              {formErrors.name && (
                <p className="md-text-field-helper error mt-1">{formErrors.name}</p>
              )}
            </div>

            <div>
              <label htmlFor="account-form-type" className="md-text-field-label block">
                Account Type *
              </label>
              <select
                id="account-form-type"
                value={formData.account_type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    account_type: e.target.value as AccountType,
                    report_category: '',
                  })
                }
                className="m3-native-select"
              >
                <option value="asset">Asset</option>
                <option value="liability">Liability</option>
                <option value="equity">Equity</option>
                <option value="revenue">Revenue</option>
                <option value="expense">Expense</option>
              </select>
              {formErrors.account_type && (
                <p className="md-text-field-helper error mt-1">{formErrors.account_type}</p>
              )}
            </div>

            <div>
              <label htmlFor="account-form-parent" className="md-text-field-label block">
                Parent Account
              </label>
              <select
                id="account-form-parent"
                value={formData.parent_id || ''}
                onChange={(e) => setFormData({ ...formData, parent_id: e.target.value ? parseInt(e.target.value) : null })}
                className="m3-native-select"
              >
                <option value="">No Parent (Top Level)</option>
                {flatAccounts
                  .filter(
                    (acc) =>
                      acc.account_type === formData.account_type && acc.id !== selectedAccount?.id
                  )
                  .map(acc => (
                    <option key={acc.id} value={acc.id}>
                      {'  '.repeat(acc.level - 1)}{acc.code} - {acc.name}
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label htmlFor="account-form-report-category" className="md-text-field-label block">
                Report category
              </label>
              <select
                id="account-form-report-category"
                value={formData.report_category}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    report_category: e.target.value as '' | AccountReportCategory,
                  })
                }
                className="m3-native-select"
              >
                <option value="">Default (unspecified)</option>
                {allowedReportCategoriesForAccountType(formData.account_type).map((c) => (
                  <option key={c} value={c}>
                    {formatReportCategoryLabel(c)}
                  </option>
                ))}
              </select>
              <p className="md-body-small text-on-surface-variant mt-1">
                Used for balance sheet sections and income statement lines (COGS vs operating expense, etc.).
              </p>
             </div>
 
             <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="is_postable"
                checked={formData.is_postable}
                onChange={(e) => setFormData({ ...formData, is_postable: e.target.checked })}
                className="h-4 w-4 shrink-0 rounded border-[var(--md-sys-color-outline)] bg-[var(--md-sys-color-surface-container-highest)] text-[var(--md-sys-color-primary)] accent-[var(--md-sys-color-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--md-sys-color-primary)_45%,transparent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--md-sys-color-surface)]"
              />
              <label htmlFor="is_postable" className="md-body-medium text-on-surface cursor-pointer select-none">
                Postable
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <Button
              type="button"
              className="md-button"
              onClick={() => {
                setShowCreateModal(false)
                setShowEditModal(false)
                resetForm()
              }}
            >
              Cancel
            </Button>
            <Button type="button" className="md-button" onClick={handleSubmit}>
              <Save className="w-4 h-4 mr-2" aria-hidden />
              {isEdit ? 'Update' : 'Create'}
            </Button>
          </div>
        </div>
      </div>
    )
  }

  const renderImportModal = () => {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-surface rounded-2xl p-6 w-full max-w-4xl mx-4 shadow-2xl border border-outline-variant max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="md-headline-small text-on-surface">Import Accounts</h2>
            <button
              onClick={handleImportCancel}
              className="p-2 hover:bg-surface-container-highest rounded-full"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-6">
            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-on-surface-variant mb-2">
                Select CSV File
              </label>
              <div className="border-2 border-dashed border-outline-variant rounded-lg p-6 text-center hover:border-primary transition-colors">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center space-y-2"
                >
                  <Upload className="w-8 h-8 text-on-surface-variant" />
                  <span className="text-sm text-on-surface-variant">
                    {importFile ? importFile.name : 'Click to select CSV file'}
                  </span>
                  <span className="text-xs text-on-surface-variant">
                    Supported format: CSV with columns Name, Type (required); codes are assigned on import
                  </span>
                </label>
              </div>
            </div>

            {/* File Format Info */}
            <div className="bg-surface-container p-4 rounded-lg">
              <h3 className="text-sm font-medium text-on-surface mb-2">Required CSV Format</h3>
              <div className="text-xs text-on-surface-variant space-y-1">
                <p><strong>Required columns:</strong> Name, Type</p>
                <p>
                  <strong>Optional columns:</strong> Parent Code (existing chart), Parent Name (exact match to
                  another row or existing account), Report category, Description, Is Postable — Code column is ignored
                </p>
                <p><strong>Account Types:</strong> asset, liability, equity, revenue, expense</p>
                <p><strong>Is Postable:</strong> yes/no, true/false, or 1/0</p>
              </div>
            </div>

            {/* Errors */}
            {importErrors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-red-800 mb-2">Import Errors</h3>
                <ul className="text-xs text-red-700 space-y-1">
                  {importErrors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Preview */}
            {importPreview.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-on-surface mb-2">
                  Preview ({importPreview.length} accounts)
                </h3>
                <div className="border border-outline-variant rounded-lg overflow-hidden">
                  <div className="max-h-60 overflow-y-auto">
                    <table className="w-full text-xs">
                      <thead className="bg-surface-container-highest sticky top-0">
                        <tr>
                          <th className="text-left p-2 font-medium">Name</th>
                          <th className="text-left p-2 font-medium">Type</th>
                          <th className="text-left p-2 font-medium">Parent Code</th>
                          <th className="text-left p-2 font-medium">Parent Name</th>
                          <th className="text-left p-2 font-medium">Group</th>
                          <th className="text-left p-2 font-medium">Postable</th>
                        </tr>
                      </thead>
                      <tbody>
                        {importPreview.slice(0, 10).map((row, index) => (
                          <tr key={index} className="border-t border-outline-variant">
                            <td className="p-2">{row.Name}</td>
                            <td className="p-2">{row.Type}</td>
                            <td className="p-2">{row['Parent Code'] || '-'}</td>
                            <td className="p-2">{row['Parent Name'] || '-'}</td>
                            <td className="p-2">{row.Group || '-'}</td>
                            <td className="p-2">{row['Is Postable'] || 'Yes'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {importPreview.length > 10 && (
                      <div className="p-2 text-center text-xs text-on-surface-variant bg-surface-container">
                        ... and {importPreview.length - 10} more rows
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={handleImportCancel}
                disabled={isImporting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleImportConfirm}
                disabled={!importFile || importPreview.length === 0 || isImporting}
                className="min-w-[120px]"
              >
                {isImporting ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Import Accounts
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-on-surface-variant">Loading accounts...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      {roleResolved && (!canEditChart || !canExportData) && (
        <div className="px-6 pt-4">
          <Alert className="border-primary/30 bg-primary-container/30">
            <Info className="h-4 w-4" />
            <AlertDescription>
              <span className="text-on-surface">
                {!canEditChart
                  ? 'You can browse the chart. Creating, editing, or deleting accounts is limited to Owner and Accountant. '
                  : null}
                {!canExportData
                  ? 'Export is not available for your current role. '
                  : null}
              </span>
            </AlertDescription>
          </Alert>
        </div>
      )}
      {/* Fixed Header */}
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="md-headline-small text-on-background">Chart of Accounts</h1>
              <p className="md-body-medium text-on-surface-variant mt-1">
                Manage your account structure and hierarchy
                {flatAccounts.length > 0 && (
                  <span className="ml-2 text-sm">
                    • {flatAccounts.length} accounts • {flatAccounts.filter(acc => acc.is_postable).length} postable
                  </span>
                )}
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-2">
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <div className={`transition-all duration-200 overflow-hidden ${
                  showSearchField 
                    ? 'w-60 sm:w-80 opacity-100 translate-x-0' 
                    : 'w-0 opacity-0 -translate-x-4'
                }`}>
                  <input
                    type="text"
                    placeholder="Search accounts by name or code..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-60 sm:w-80 h-10 px-4 bg-surface-container rounded-2xl border border-outline text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                    aria-label="Search accounts"
                    autoFocus={showSearchField}
                  />
                </div>
                <Button
                  type="button"
                  className="md-button md-button-icon"
                  onClick={() => setShowSearchField(!showSearchField)}
                  title="Search"
                >
                  <Search className="w-4 h-4" aria-hidden />
                </Button>
                <Button
                  onClick={openCreateModal}
                  className="md-button"
                  disabled={chartEditDisabled}
                  title={chartEditTitle}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Account
                </Button>
                <Button
                  type="button"
                  onClick={loadData}
                  className="md-button md-button-icon"
                  title="Refresh"
                >
                  <RefreshCw className="w-4 h-4" aria-hidden />
                </Button>
                <Button
                  type="button"
                  className="md-button md-button-icon"
                  onClick={handleImportAccounts}
                  disabled={chartEditDisabled}
                  title={!roleResolved ? 'Checking your access…' : !canEditChart ? 'Your role cannot import into the chart' : undefined}
                >
                  <Upload className="w-4 h-4" aria-hidden />
                </Button>
                <Button
                  type="button"
                  className="md-button md-button-icon"
                  onClick={handleExportAccounts}
                  disabled={exportDisabled}
                  title={exportTitle}
                >
                  <Download className="w-4 h-4" aria-hidden />
                </Button>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Main Content */}
      <div className="px-6 py-6">
        {filteredAccounts.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-primary-container rounded-3xl flex items-center justify-center mb-6">
              <Building2 className="w-10 h-10 text-on-primary-container" />
            </div>
            <h3 className="md-headline-small text-on-surface mb-3">No accounts found</h3>
            <p className="md-body-large text-on-surface-variant text-center mb-8 max-w-md">
              {searchTerm
                ? 'Try adjusting your search or filter criteria.'
                : 'Get started by creating your first account.'
              }
            </p>
            <Button
              onClick={openCreateModal}
              className="md-button"
              disabled={chartEditDisabled}
              title={chartEditTitle}
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Account
            </Button>
          </div>
        ) : (
          /* Accounts List */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Accounts Tree */}
            <div className="lg:col-span-2">
              <Card className="md-card-expressive">
                <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:space-y-0">
                  <div className="min-w-0">
                    <CardTitle className="md-title-large text-on-surface">
                      {viewMode === 'list' ? 'Account Hierarchy' : 'Account graph'}
                    </CardTitle>
                  </div>
                  <div
                    className="flex shrink-0 items-center gap-1"
                    role="group"
                    aria-label="Chart view"
                  >
                    <button
                      type="button"
                      onClick={() => setViewMode('list')}
                      title="List and tree"
                      aria-pressed={viewMode === 'list'}
                      className="accounts-chart-view-toggle transition-colors"
                    >
                      <span className="sr-only">List view</span>
                      <LayoutList
                        className="h-5 w-5"
                        strokeWidth={viewMode === 'list' ? 2.25 : 1.75}
                        aria-hidden
                      />
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewMode('graph')}
                      title="Graph view"
                      aria-pressed={viewMode === 'graph'}
                      className="accounts-chart-view-toggle transition-colors"
                    >
                      <span className="sr-only">Graph view</span>
                      <Share2
                        className="h-5 w-5"
                        strokeWidth={viewMode === 'graph' ? 2.25 : 1.75}
                        aria-hidden
                      />
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  {viewMode === 'list' ? (
                    <div className="h-[calc(100vh-16rem)] overflow-y-auto">
                      {filteredAccounts.map((account) => renderAccountItem(account))}
                    </div>
                  ) : (
                    <div className="p-0 px-0 pb-1">
                      <AccountsGraphView
                        flatAccounts={flatAccounts}
                        searchTerm={searchTerm}
                        selectedId={selectedAccount?.id ?? null}
                        onSelect={(a) => selectAccount(a as HierarchicalAccount)}
                      />
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Account Details */}
            <div className="lg:col-span-1">
              {selectedAccount ? (
                <Card className="md-card-expressive">
                  <CardHeader>
                    <CardTitle className="md-title-large text-on-surface">Account Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Account Code</label>
                        <p className="text-lg font-mono text-on-surface">{selectedAccount.code}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Account Name</label>
                        <p className="text-lg text-on-surface">{selectedAccount.name}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Account Type</label>
                        <span className={accountTypeBadgeClass(selectedAccount.account_type)}>
                          {selectedAccount.account_type.charAt(0).toUpperCase() + selectedAccount.account_type.slice(1)}
                        </span>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Level</label>
                        <p className="text-sm text-on-surface">Level {selectedAccount.level}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-on-surface-variant">Postable</label>
                        <p className="mt-1 text-sm text-on-surface">
                          {selectedAccount.is_postable ? (
                            <span className={cn(accountMetaBadgeClass, 'gap-1')}>
                              <CheckCircle className="w-3.5 h-3.5 shrink-0 text-on-surface-variant" aria-hidden />
                              Yes
                            </span>
                          ) : (
                            <span className={cn(accountMetaBadgeClass, 'gap-1')}>
                              <AlertCircle className="w-3.5 h-3.5 shrink-0 text-on-surface-variant" aria-hidden />
                              No
                            </span>
                          )}
                        </p>
                      </div>
                      {(selectedAccount.report_category || selectedAccount.group) && (
                        <div>
                          <label className="text-sm font-medium text-on-surface-variant">
                            Report category
                          </label>
                          <p className="mt-1 text-sm text-on-surface">
                            <span className={accountMetaBadgeClass}>
                              {selectedAccount.report_category
                                ? formatReportCategoryLabel(selectedAccount.report_category)
                                : selectedAccount.group!.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                            </span>
                          </p>
                      </div>
                       )}
                      <div className="pt-4 border-t border-outline-variant">
                        <div className="flex space-x-2">
                          <Button 
                            variant="outline" 
                            className="flex-1"
                            disabled={chartEditDisabled}
                            title={chartEditTitle}
                            onClick={() => openEditModal(selectedAccount)}
                          >
                            <Edit className="w-4 h-4 mr-2" />
                            Edit
                          </Button>
                          <Button 
                            variant="outline" 
                            className="flex-1 text-red-600 hover:bg-red-50 hover:border-red-300"
                            disabled={chartEditDisabled}
                            title={chartEditTitle}
                            onClick={() => handleDeleteAccount(selectedAccount.id)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="md-card-expressive">
                  <CardContent className="p-6 text-center">
                    <FileText className="w-12 h-12 text-on-surface-variant mx-auto mb-4" />
                    <h3 className="md-title-medium text-on-surface mb-2">Select an Account</h3>
                    <p className="text-sm text-on-surface-variant">
                      Click on any account to view its details and manage settings.
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreateModal && renderFormModal(false)}
      {showEditModal && renderFormModal(true)}
      {showImportModal && renderImportModal()}
    </div>
  )
}