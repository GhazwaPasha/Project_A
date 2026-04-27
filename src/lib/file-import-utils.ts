/**
 * File Import Utilities for Web App
 * Handles CSV and Excel file imports for bulk entry
 */

export interface ImportedEntry {
  date: string
  description: string
  debitAccount: string
  creditAccount: string
  amount: string
}

export interface ImportResult {
  success: boolean
  entries: ImportedEntry[]
  errors: string[]
  totalRows: number
  validRows: number
}

/**
 * Parse CSV content into entries
 */
export function parseCSVContent(csvContent: string): ImportResult {
  const lines = csvContent.split('\n').filter(line => line.trim())
  if (lines.length === 0) {
    return {
      success: false,
      entries: [],
      errors: ['File is empty'],
      totalRows: 0,
      validRows: 0
    }
  }

  // Parse header row
  const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
  const requiredColumns = ['Date', 'Description', 'Debit Account', 'Credit Account', 'Amount']
  
  // Check for required columns
  const missingColumns = requiredColumns.filter(col => !headers.includes(col))
  if (missingColumns.length > 0) {
    return {
      success: false,
      entries: [],
      errors: [`Missing required columns: ${missingColumns.join(', ')}`],
      totalRows: lines.length - 1,
      validRows: 0
    }
  }

  // Get column indices
  const dateIndex = headers.indexOf('Date')
  const descriptionIndex = headers.indexOf('Description')
  const debitAccountIndex = headers.indexOf('Debit Account')
  const creditAccountIndex = headers.indexOf('Credit Account')
  const amountIndex = headers.indexOf('Amount')

  const entries: ImportedEntry[] = []
  const errors: string[] = []

  // Parse data rows
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    const columns = parseCSVLine(line)
    
    if (columns.length < requiredColumns.length) {
      errors.push(`Row ${i + 1}: Insufficient columns`)
      continue
    }

    const entry: ImportedEntry = {
      date: columns[dateIndex]?.trim() || '',
      description: columns[descriptionIndex]?.trim() || '',
      debitAccount: columns[debitAccountIndex]?.trim() || '',
      creditAccount: columns[creditAccountIndex]?.trim() || '',
      amount: columns[amountIndex]?.trim() || ''
    }

    // Validate entry
    const validationError = validateImportedEntry(entry, i + 1)
    if (validationError) {
      errors.push(validationError)
      continue
    }

    entries.push(entry)
  }

  return {
    success: errors.length === 0 || entries.length > 0,
    entries,
    errors,
    totalRows: lines.length - 1,
    validRows: entries.length
  }
}

/**
 * Parse a single CSV line handling quoted fields
 */
function parseCSVLine(line: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  
  result.push(current.trim())
  return result
}

/**
 * Validate an imported entry
 */
function validateImportedEntry(entry: ImportedEntry, rowNumber: number): string | null {
  if (!entry.date) {
    return `Row ${rowNumber}: Date is required`
  }
  
  if (!entry.description) {
    return `Row ${rowNumber}: Description is required`
  }
  
  if (!entry.debitAccount) {
    return `Row ${rowNumber}: Debit Account is required`
  }
  
  if (!entry.creditAccount) {
    return `Row ${rowNumber}: Credit Account is required`
  }
  
  if (!entry.amount) {
    return `Row ${rowNumber}: Amount is required`
  }
  
  // Validate amount is numeric
  const amount = parseFloat(entry.amount.replace(/[,$]/g, ''))
  if (isNaN(amount) || amount <= 0) {
    return `Row ${rowNumber}: Amount must be a positive number`
  }
  
  // Validate date format
  const dateRegex = /^\d{4}-\d{2}-\d{2}$|^\d{2}\/\d{2}\/\d{4}$|^\d{2}-\d{2}-\d{4}$/
  if (!dateRegex.test(entry.date)) {
    return `Row ${rowNumber}: Date must be in YYYY-MM-DD, MM/DD/YYYY, or MM-DD-YYYY format`
  }
  
  return null
}

/**
 * Parse Excel file content (simplified - would need proper Excel parsing library)
 */
export function parseExcelContent(excelContent: ArrayBuffer): Promise<ImportResult> {
  // This is a simplified implementation
  // In a real implementation, you would use a library like 'xlsx' to parse Excel files
  return new Promise((resolve) => {
    // For now, return an error suggesting CSV format
    resolve({
      success: false,
      entries: [],
      errors: ['Excel import not yet implemented. Please use CSV format.'],
      totalRows: 0,
      validRows: 0
    })
  })
}

/**
 * Handle file upload and parsing
 */
export async function handleFileImport(file: File): Promise<ImportResult> {
  const fileName = file.name.toLowerCase()
  
  if (fileName.endsWith('.csv')) {
    const content = await readFileAsText(file)
    return parseCSVContent(content)
  } else if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) {
    const content = await readFileAsArrayBuffer(file)
    return parseExcelContent(content)
  } else {
    return {
      success: false,
      entries: [],
      errors: ['Unsupported file format. Please use CSV or Excel files.'],
      totalRows: 0,
      validRows: 0
    }
  }
}

/**
 * Read file as text
 */
function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string || '')
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsText(file)
  })
}

/**
 * Read file as ArrayBuffer
 */
function readFileAsArrayBuffer(file: File): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as ArrayBuffer || new ArrayBuffer(0))
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsArrayBuffer(file)
  })
}

/**
 * Generate CSV template for download
 */
export function generateCSVTemplate(): string {
  const headers = ['Date', 'Description', 'Debit Account', 'Credit Account', 'Amount']
  const sampleRows = [
    ['2024-01-15', 'Office supplies purchase', 'Office Supplies', 'Cash at Bank', '150.00'],
    ['2024-01-16', 'Client payment received', 'Cash at Bank', 'Service Revenue', '500.00'],
    ['2024-01-17', 'Rent payment', 'Rent Expense', 'Cash at Bank', '1200.00']
  ]
  
  const csvContent = [
    headers.join(','),
    ...sampleRows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')
  
  return csvContent
}

/**
 * Download CSV template
 */
export function downloadCSVTemplate(): void {
  const csvContent = generateCSVTemplate()
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'journal_entries_template.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
