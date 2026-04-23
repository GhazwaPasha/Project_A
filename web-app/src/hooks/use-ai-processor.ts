'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'

interface AIResponse {
  type: 'navigation' | 'reminder_creation' | 'report_generation' | 'info' | 'error'
  message: string
  data?: any
}

interface NavigationParams {
  page: string
  parameters?: Record<string, any>
}

export function useAIProcessor() {
  const [isProcessing, setIsProcessing] = useState(false)
  const router = useRouter()

  const processCommand = useCallback(async (command: string): Promise<AIResponse> => {
    if (!command.trim()) {
      return {
        type: 'error',
        message: 'Please enter a command.'
      }
    }

    setIsProcessing(true)

    try {
      // Parse natural-language style commands
      const response = await parseCommand(command.toLowerCase())
      
      // Execute the response
      if (response.type === 'navigation') {
        await executeNavigation(response.data)
      } else if (response.type === 'reminder_creation') {
        await executeReminderCreation(response.data)
      } else if (response.type === 'report_generation') {
        await executeReportGeneration(response.data)
      }

      return response
    } catch (error) {
      console.error('AI processing error:', error)
      return {
        type: 'error',
        message: error instanceof Error ? error.message : 'Processing error occurred'
      }
    } finally {
      setIsProcessing(false)
    }
  }, [router])

  return {
    processCommand,
    isProcessing
  }
}

// Command parsing (rule-based)
async function parseCommand(input: string): Promise<AIResponse> {
  // Check for reminder commands
  if (isReminderCommand(input)) {
    return parseReminderCommand(input)
  }
  
  // Check for navigation commands
  if (isNavigationCommand(input)) {
    return parseNavigationCommand(input)
  }
  
  // Check for report commands
  if (isReportCommand(input)) {
    return parseReportCommand(input)
  }
  
  // Default response
  return {
    type: 'info',
    message: "I didn't understand that command. Try asking me to show a specific page, create a reminder, or generate a report."
  }
}

function isReminderCommand(input: string): boolean {
  const reminderWords = ['remind', 'reminder', 'set reminder', 'create reminder', 'schedule', 'alert']
  const recurringWords = ['recurring', 'repeat', 'every', 'daily', 'weekly', 'monthly', 'regularly']
  const timeWords = ['tomorrow', 'today', 'next week', 'pm', 'am', 'hour', 'minute', 'date', 'time']
  
  const hasReminder = reminderWords.some(word => input.includes(word))
  const hasRecurring = recurringWords.some(word => input.includes(word))
  const hasTime = timeWords.some(word => input.includes(word))
  
  return hasReminder || (hasRecurring && hasTime)
}

function isNavigationCommand(input: string): boolean {
  const navWords = ['show', 'open', 'go to', 'navigate', 'take me to', 'switch to', 'display']
  const targetWords = ['dashboard', 'journal', 'accounts', 'ledger', 'reports', 'reminders', 'page', 'statement', 'balance', 'trial', 'account', 'cash flow']
  
  const hasNav = navWords.some(word => input.includes(word))
  const hasTarget = targetWords.some(word => input.includes(word))
  
  return hasNav && hasTarget
}

function isReportCommand(input: string): boolean {
  const reportWords = ['generate', 'create', 'run', 'produce', 'report', 'statement']
  const reportTypes = ['income statement', 'balance sheet', 'cash flow', 'trial balance', 'profit loss', 'p&l']
  
  const hasReport = reportWords.some(word => input.includes(word))
  const hasType = reportTypes.some(type => input.includes(type))
  
  return hasReport && hasType
}

function parseReminderCommand(input: string): AIResponse {
  const title = extractReminderTitle(input)
  const recurring = parseRecurring(input)
  const dueDateTime = parseDateTime(input, recurring)
  const priority = extractPriority(input)
  
  const reminderData = {
    id: `reminder_${Date.now()}`,
    title,
    description: `Reminder created from: ${input}`,
    due_datetime: dueDateTime,
    recurring,
    priority,
    created_datetime: new Date().toISOString(),
    completed: false
  }
  
  return {
    type: 'reminder_creation',
    data: reminderData,
    message: `✅ Recurring reminder created: ${title} - ${recurring} starting ${dueDateTime}`
  }
}

function parseNavigationCommand(input: string): AIResponse {
  const targetPage = extractTargetPage(input)
  const parameters = extractParameters(input, targetPage)
  
  return {
    type: 'navigation',
    data: {
      page: targetPage,
      parameters
    },
    message: `📍 Navigating to ${targetPage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}...`
  }
}

function parseReportCommand(input: string): AIResponse {
  const reportType = extractReportType(input)
  const parameters = extractDateParameters(input)
  
  return {
    type: 'report_generation',
    data: {
      reportType,
      parameters
    },
    message: `📊 Generating ${reportType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}...`
  }
}

function extractReminderTitle(input: string): string {
  if (input.includes('income statement')) return 'Monthly Income Statement Generation'
  if (input.includes('balance sheet')) return 'Balance Sheet Report Generation'
  if (input.includes('cash flow')) return 'Cash Flow Statement Generation'
  if (input.includes('trial balance')) return 'Trial Balance Report Generation'
  if (input.includes('report') && input.includes('monthly')) return 'Monthly Financial Reports'
  if (input.includes('meeting')) return 'Meeting Reminder'
  if (input.includes('deadline')) return 'Deadline Reminder'
  if (input.includes('closing') || input.includes('month end')) return 'Month-End Closing Reminder'
  return 'General Reminder'
}

function parseRecurring(input: string): string {
  if (input.includes('every month') || input.includes('monthly') || input.includes('each month')) return 'monthly'
  if (input.includes('every week') || input.includes('weekly') || input.includes('each week')) return 'weekly'
  if (input.includes('every day') || input.includes('daily') || input.includes('each day')) return 'daily'
  if (input.includes('recurring') || input.includes('repeat')) return 'monthly'
  return 'none'
}

function parseDateTime(input: string, recurring: string): string {
  const now = new Date()
  
  if (recurring === 'monthly') {
    if (input.includes('1st') || input.includes('first')) {
      const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1)
      if (input.includes('9am') || input.includes('09:00') || input.includes('morning')) {
        return nextMonth.toISOString().replace('T00:00:00', 'T09:00:00').split('T')[0] + ' 09:00'
      } else if (input.includes('5pm') || input.includes('17:00') || input.includes('evening')) {
        return nextMonth.toISOString().replace('T00:00:00', 'T17:00:00').split('T')[0] + ' 17:00'
      } else {
        return nextMonth.toISOString().replace('T00:00:00', 'T09:00:00').split('T')[0] + ' 09:00'
      }
    }
  }
  
  if (input.includes('tomorrow')) {
    const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000)
    if (input.includes('4pm') || input.includes('16:')) {
      return tomorrow.toISOString().replace('T00:00:00', 'T16:00:00').split('T')[0] + ' 16:00'
    } else if (input.includes('morning') || input.includes('9am')) {
      return tomorrow.toISOString().replace('T00:00:00', 'T09:00:00').split('T')[0] + ' 09:00'
    } else {
      return tomorrow.toISOString().replace('T00:00:00', 'T16:00:00').split('T')[0] + ' 16:00'
    }
  }
  
  if (input.includes('today')) {
    if (input.includes('5pm') || input.includes('17:')) {
      return now.toISOString().replace('T00:00:00', 'T17:00:00').split('T')[0] + ' 17:00'
    } else {
      return now.toISOString().replace('T00:00:00', 'T17:00:00').split('T')[0] + ' 17:00'
    }
  }
  
  if (input.includes('next week')) {
    const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
    return nextWeek.toISOString().replace('T00:00:00', 'T09:00:00').split('T')[0] + ' 09:00'
  }
  
  // Default to tomorrow 4pm
  const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000)
  return tomorrow.toISOString().replace('T00:00:00', 'T16:00:00').split('T')[0] + ' 16:00'
}

function extractPriority(input: string): string {
  if (input.includes('urgent') || input.includes('critical') || input.includes('important') || input.includes('asap')) return 'high'
  if (input.includes('low priority') || input.includes('when possible') || input.includes('optional')) return 'low'
  return 'medium'
}

function extractTargetPage(input: string): string {
  const pagePatterns = {
    'reports': ['income statement', 'profit loss', 'p&l', 'pnl', 'balance sheet', 'financial position', 'cash flow', 'cashflow', 'trial balance', 'trial', 'report', 'statement'],
    'ledger': ['ledger', 'account ledger', 'show account', 'open account', 'cash', 'bank', 'sales', 'expense', 'revenue'],
    'home': ['dashboard', 'home', 'overview', 'main'],
    'journal': ['journal', 'entries', 'transactions'],
    'accounts': ['chart of accounts', 'accounts', 'account list'],
    'trial_balance': ['trial balance page'],
    'reminders': ['reminders', 'tasks', 'notifications'],
    'period_closing': ['period closing', 'month end', 'year end'],
    'settings': ['settings', 'preferences', 'config']
  }
  
  for (const [page, keywords] of Object.entries(pagePatterns)) {
    if (keywords.some(keyword => input.includes(keyword))) {
      return page
    }
  }
  
  return 'home'
}

function extractParameters(input: string, targetPage: string): Record<string, any> {
  const params: Record<string, any> = {}
  
  if (targetPage === 'ledger') {
    const accountName = extractAccountName(input)
    if (accountName) {
      params.account_name = accountName
      params.specific_account = true
    }
  }
  
  if (targetPage === 'reports') {
    const reportType = extractReportType(input)
    if (reportType) {
      params.report_type = reportType
    }
  }
  
  const dateParams = extractDateParameters(input)
  if (Object.keys(dateParams).length > 0) {
    Object.assign(params, dateParams)
  }
  
  return params
}

function extractAccountName(input: string): string {
  // Simple account name extraction - in a real app, this would be more sophisticated
  const patterns = [
    /show (?:me )?(.+?)(?:\s+account|\s+ledger|$)/,
    /open (?:the )?(.+?)(?:\s+account|\s+ledger|$)/,
    /(?:account|ledger) (?:for )?(.+?)(?:\s|$)/,
    /(.+?)(?:\s+account|\s+ledger)(?:\s|$)/
  ]
  
  for (const pattern of patterns) {
    const match = input.match(pattern)
    if (match) {
      const accountName = match[1].trim()
      if (accountName && accountName.length > 1) {
        return accountName
      }
    }
  }
  
  return ''
}

function extractReportType(input: string): string {
  const reportMapping = {
    'income_statement': ['income statement', 'profit loss', 'p&l', 'pnl'],
    'balance_sheet': ['balance sheet', 'financial position'],
    'cash_flow': ['cash flow', 'cashflow'],
    'trial_balance': ['trial balance', 'trial'],
    'general_ledger': ['general ledger', 'gl']
  }
  
  for (const [reportId, keywords] of Object.entries(reportMapping)) {
    if (keywords.some(keyword => input.includes(keyword))) {
      return reportId
    }
  }
  
  return 'income_statement'
}

function extractDateParameters(input: string): Record<string, string> {
  const today = new Date()
  
  if (input.includes('last month')) {
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate())
    const startOfLastMonth = new Date(lastMonth.getFullYear(), lastMonth.getMonth(), 1)
    return {
      start_date: startOfLastMonth.toISOString().split('T')[0],
      end_date: lastMonth.toISOString().split('T')[0]
    }
  }
  
  if (input.includes('this month') || input.includes('current month')) {
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
    return {
      start_date: startOfMonth.toISOString().split('T')[0],
      end_date: today.toISOString().split('T')[0]
    }
  }
  
  if (input.includes('last year')) {
    const lastYear = today.getFullYear() - 1
    return {
      start_date: `${lastYear}-01-01`,
      end_date: `${lastYear}-12-31`
    }
  }
  
  if (input.includes('this year') || input.includes('current year')) {
    return {
      start_date: `${today.getFullYear()}-01-01`,
      end_date: today.toISOString().split('T')[0]
    }
  }
  
  return {}
}

// Execution functions
async function executeNavigation(data: NavigationParams) {
  const { page, parameters } = data
  
  // Map page names to routes
  const routeMap: Record<string, string> = {
    'home': '/home',
    'dashboard': '/home',
    'journal': '/journal',
    'ledger': '/ledger',
    'accounts': '/accounts',
    'trial_balance': '/trial-balance',
    'reports': '/reports',
    'reminders': '/reminders',
    'period_closing': '/period-closing',
    'settings': '/settings'
  }
  
  const route = routeMap[page] || '/home'
  
  // Navigate to the page
  if (typeof window !== 'undefined') {
    window.location.href = route
  }
}

async function executeReminderCreation(data: any) {
  // In a real app, this would create a reminder via API
  console.log('Creating reminder:', data)
  
  // For now, just show a success message
  if (typeof window !== 'undefined' && (window as any).aiStatusBar) {
    (window as any).aiStatusBar.showNotification('Reminder Created', data.title, 'success')
  }
}

async function executeReportGeneration(data: any) {
  // In a real app, this would generate a report via API
  console.log('Generating report:', data)
  
  // For now, just show a success message
  if (typeof window !== 'undefined' && (window as any).aiStatusBar) {
    (window as any).aiStatusBar.showNotification('Report Generated', data.reportType, 'success')
  }
}
