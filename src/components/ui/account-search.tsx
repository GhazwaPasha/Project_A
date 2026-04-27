'use client'

import * as React from "react"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { Search, Check } from "lucide-react"
import { Account } from "@/types"

interface AccountSearchProps {
  accounts: Account[]
  value: string
  onChange: (accountId: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
}

export function AccountSearch({
  accounts,
  value,
  onChange,
  placeholder = "Search accounts...",
  className,
  disabled = false
}: AccountSearchProps) {
  const [searchTerm, setSearchTerm] = React.useState('')
  const [isOpen, setIsOpen] = React.useState(false)
  const [selectedAccount, setSelectedAccount] = React.useState<Account | null>(null)
  const inputRef = React.useRef<HTMLInputElement>(null)
  const inputId = React.useMemo(() => `account-search-${Math.random().toString(36).substr(2, 9)}`, [])

  // Find selected account by ID
  React.useEffect(() => {
    if (value) {
      const account = accounts.find(acc => acc.id.toString() === value)
      setSelectedAccount(account || null)
      setSearchTerm(account ? `${account.code} - ${account.name}` : '')
    } else {
      setSelectedAccount(null)
      setSearchTerm('')
    }
  }, [value, accounts])

  // Filter accounts based on search term
  const filteredAccounts = React.useMemo(() => {
    if (!searchTerm.trim()) return accounts.slice(0, 10) // Show first 10 if no search
    
    return accounts.filter(account => 
      account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      account.code.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 10) // Limit to 10 results
  }, [accounts, searchTerm])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value
    setSearchTerm(term)
    setIsOpen(true)
    
    // If user clears the input, clear selection
    if (!term.trim()) {
      onChange('')
    }
  }

  const handleAccountSelect = (account: Account) => {
    setSelectedAccount(account)
    setSearchTerm(`${account.code} - ${account.name}`)
    onChange(account.id.toString())
    setIsOpen(false)
  }

  const handleInputFocus = () => {
    setIsOpen(true)
  }

  const handleInputBlur = (e: React.FocusEvent) => {
    // Delay closing to allow for clicks on dropdown items
    setTimeout(() => {
      setIsOpen(false)
    }, 150)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false)
      inputRef.current?.blur()
    }
  }

  return (
    <div className="md-text-field">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-4 w-4 text-on-surface-variant" />
        <Input
          ref={inputRef}
          id={inputId}
          name="account-search"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={cn("pl-12 pr-4", className)}
        />
      </div>
      
      {isOpen && filteredAccounts.length > 0 && (
        <div className="absolute z-50 w-full top-full mt-1 bg-surface-container-low border border-outline-variant rounded-lg shadow-lg max-h-60 overflow-auto backdrop-blur-sm" style={{ backgroundColor: 'var(--md-sys-color-surface-container-low)' }}>
          {filteredAccounts.map((account) => (
            <div
              key={account.id}
              className="flex items-center justify-between px-4 py-3 hover:bg-surface-container cursor-pointer transition-colors duration-150"
              onClick={() => handleAccountSelect(account)}
            >
              <div className="flex flex-col">
                <span className="font-medium text-sm text-on-surface">{account.name}</span>
                <span className="text-xs text-on-surface-variant">{account.code}</span>
              </div>
              {selectedAccount?.id === account.id && (
                <Check className="h-4 w-4 text-primary" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
