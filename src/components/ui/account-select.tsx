'use client'

import * as React from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Account } from "@/types"

interface AccountSelectProps {
  accounts: Account[]
  value: string
  onChange: (accountId: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
}

export function AccountSelect({
  accounts,
  value,
  onChange,
  placeholder = "Select account",
  className,
  disabled = false
}: AccountSelectProps) {
  const selectedAccount = React.useMemo(() => {
    return accounts.find(acc => acc.id.toString() === value) || null
  }, [accounts, value])

  const displayValue = selectedAccount 
    ? `${selectedAccount.code} - ${selectedAccount.name}`
    : ""

  return (
    <Select 
      value={value} 
      onValueChange={onChange}
      disabled={disabled}
    >
      <SelectTrigger 
        id={`account-select-${Math.random().toString(36).substr(2, 9)}`}
        name="account-select"
        className={`!bg-transparent !border-0 !shadow-none focus:!bg-surface-container focus:!ring-0 focus:!ring-offset-0 hover:!bg-transparent active:!bg-transparent dark:!bg-transparent dark:hover:!bg-transparent dark:active:!bg-transparent dark:focus:!bg-surface-container ${className || ''}`}
        style={{ 
          backgroundColor: 'transparent !important',
          color: 'inherit !important'
        }}
      >
        <SelectValue placeholder={placeholder}>
          {displayValue}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {accounts.map((account) => (
          <SelectItem key={account.id} value={account.id.toString()}>
            <div className="flex flex-col">
              <span className="font-medium text-sm">{account.name}</span>
              <span className="text-xs text-muted-foreground">{account.code}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
