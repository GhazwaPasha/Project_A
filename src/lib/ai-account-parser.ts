/**
 * AI parser for chart-of-accounts fields from natural language.
 * Complements `ai-transaction-parser` (journal entries); this module targets account metadata only.
 */

import type { AccountReportCategory, AccountType } from '@/types'
import {
  allowedReportCategoriesForAccountType,
  formatReportCategoryLabel,
} from '@/lib/account-report-category'

const GOOGLE_AI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'

export interface AccountChartContextRow {
  id: number
  code: string
  name: string
  account_type: AccountType
  is_postable: boolean
  parent_id: number | null
}

export interface ParsedAccountDraft {
  name: string
  account_type: AccountType
  /** Parent account code from EXISTING chart rows only; null = top-level. */
  parent_account_code: string | null
  /** FS/P&L bucket key or null if unspecified. */
  report_category: AccountReportCategory | null
  is_postable: boolean
}

function getGoogleAIKey(): string {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_AI_KEY
  if (!apiKey) {
    throw new Error(
      'Google AI API key not configured. Please set NEXT_PUBLIC_GOOGLE_AI_KEY environment variable.'
    )
  }
  return apiKey
}

async function getAvailableModels(): Promise<string[]> {
  const apiKey = getGoogleAIKey()
  const response = await fetch(`${GOOGLE_AI_BASE_URL}/models?key=${apiKey}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch models: ${response.status} ${response.statusText}`)
  }
  const data = await response.json()
  return (
    data.models
      ?.filter(
        (model: { supportedGenerationMethods?: string[]; name: string }) =>
          model.supportedGenerationMethods?.includes('generateContent') && model.name.includes('gemini')
      )
      ?.map((model: { name: string }) => model.name.split('/').pop()) || []
  )
}

async function getBestModel(): Promise<string> {
  const models = await getAvailableModels()
  const flashModel = models.find((model) => model.includes('flash'))
  if (flashModel) return flashModel
  const proModel = models.find((model) => model.includes('pro'))
  if (proModel) return proModel
  if (models.length > 0) return models[0]
  throw new Error('No suitable models found')
}

function reportCategoryPlaybook(): string {
  const types: AccountType[] = ['asset', 'liability', 'equity', 'revenue', 'expense']
  return types
    .map((t) => {
      const allowed = allowedReportCategoriesForAccountType(t)
      return `${t}:\n${allowed.map((c) => `  - ${c} — ${formatReportCategoryLabel(c)}`).join('\n')}`
    })
    .join('\n\n')
}

function chartContextBlock(accounts: AccountChartContextRow[]): string {
  if (accounts.length === 0) return '(No existing accounts.)'
  return accounts
    .map((a) => {
      const parentHint = a.parent_id != null ? ` parent_id=${a.parent_id}` : ''
      const post = a.is_postable ? 'postable' : 'header/group (non-postable)'
      return `${a.code} — ${a.name} | type=${a.account_type} | ${post}${parentHint}`
    })
    .join('\n')
}

function extractJsonObject(text: string): string {
  const start = text.indexOf('{')
  const end = text.lastIndexOf('}') + 1
  if (start === -1 || end === 0) {
    throw new Error('No JSON found in AI response')
  }
  return text.substring(start, end)
}

function parseJsonLenient(jsonStr: string): unknown {
  let s = jsonStr
  s = s.replace(/[\u201C\u201D]/g, '"')
  s = s.replace(/[\u2018\u2019]/g, "'")
  s = s.replace(/,\s*}/g, '}')
  s = s.replace(/,\s*]/g, ']')
  try {
    return JSON.parse(s)
  } catch (e) {
    s = s
      .replace(/[\u201C\u201D]/g, '"')
      .replace(/[\u2018\u2019]/g, "'")
      .replace(/[^\x20-\x7E]/g, '')
      .replace(/\s+/g, ' ')
      .replace(/,\s*}/g, '}')
      .replace(/,\s*]/g, ']')
    try {
      return JSON.parse(s)
    } catch (e2) {
      throw new Error(`Invalid JSON from AI: ${e2}`)
    }
  }
}

const ACCOUNT_TYPES: AccountType[] = ['asset', 'liability', 'equity', 'revenue', 'expense']

function normalizeAccountType(raw: unknown): AccountType {
  const s = String(raw ?? '')
    .trim()
    .toLowerCase()
  const map: Record<string, AccountType> = {
    asset: 'asset',
    assets: 'asset',
    liability: 'liability',
    liabilities: 'liability',
    equity: 'equity',
    revenue: 'revenue',
    revenues: 'revenue',
    income: 'revenue',
    expense: 'expense',
    expenses: 'expense',
  }
  if (map[s]) return map[s]
  if (ACCOUNT_TYPES.includes(s as AccountType)) return s as AccountType
  throw new Error(`Invalid account_type in AI response: "${raw}"`)
}

function normalizeReportCategory(
  raw: unknown,
  accountType: AccountType
): AccountReportCategory | null {
  if (raw === null || raw === undefined || raw === '' || raw === 'null') return null
  const key = String(raw).trim().toLowerCase().replace(/\s+/g, '_')
  const allowed = allowedReportCategoriesForAccountType(accountType)
  if (allowed.includes(key as AccountReportCategory)) return key as AccountReportCategory
  // fuzzy: match label text
  const lower = String(raw).toLowerCase()
  for (const c of allowed) {
    if (formatReportCategoryLabel(c).toLowerCase() === lower) return c
  }
  return null
}

/**
 * Parse natural language into structured account fields. Validates parent code against the chart when provided.
 */
export async function parseAccountFromNaturalLanguage(
  nlInput: string,
  accounts: AccountChartContextRow[],
  options?: {
    /** When editing, exclude this id from being chosen as parent (self). */
    excludeAccountId?: number
    /** Optional hint for incremental edits. */
    editingAccountSummary?: string | null
  }
): Promise<ParsedAccountDraft> {
  if (!nlInput.trim()) {
    throw new Error('Please describe the account to parse.')
  }

  const excludeId = options?.excludeAccountId
  const chartLines = accounts.filter((a) => (excludeId == null ? true : a.id !== excludeId))

  const prompt = `You are an expert accountant helping build a chart of accounts (COA).

USER REQUEST (natural language):
"${nlInput}"

${options?.editingAccountSummary ? `CONTEXT — ACCOUNT BEING EDITED:\n${options.editingAccountSummary}\n\n` : ''}
EXISTING ACCOUNTS (reference parents ONLY by exact code from this list; do not invent codes):
${chartContextBlock(chartLines)}

ACCOUNT TYPE (exactly one): asset | liability | equity | revenue | expense

HIERARCHY / LEVEL:
- "Level" is implied by the parent: top-level accounts have no parent.
- If the user places an account under another (e.g. "under 1100", "child of Current Assets", "sub-account of 4000"), set parent_account_code to that existing account's code from the list above.
- Parent and child must share the same account_type. If the user names a parent that does not exist, set parent_account_code to null.

POSTABLE VS HEADER (GROUP):
- Postable = true: leaf accounts where journal lines can be posted (e.g. "bank account we post to", "specific expense line").
- Postable = false: header / rollup / summary accounts used only for grouping (e.g. "create a header for grouping", "folder account", "non-posting category").
- If unclear, prefer postable true for operational accounts and false when the user explicitly wants a summary/header row.

REPORT CATEGORY (optional FS/P&L classification — must match account_type when set):
${reportCategoryPlaybook()}

Use report_category null when the user does not specify a section or it is unknown.

RULES:
1. Do NOT output an account code — the application assigns structured codes from type and parent when saving.
2. parent_account_code must be an exact code from EXISTING ACCOUNTS or null — never invent parent codes.
3. report_category must be one of the allowed keys for the chosen account_type, or null.
4. Respond with ONLY valid JSON (no markdown fences).

JSON SCHEMA:
{
  "name": "account title",
  "account_type": "asset|liability|equity|revenue|expense",
  "parent_account_code": "existing code string or null",
  "report_category": "snake_case key or null",
  "is_postable": true or false
}`

  try {
    const model = await getBestModel()
    const response = await fetch(
      `${GOOGLE_AI_BASE_URL}/models/${model}:generateContent?key=${getGoogleAIKey()}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
        }),
      }
    )

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Google AI API error: ${response.status} — ${errorText}`)
    }

    const result = await response.json()
    const content = result.candidates[0].content.parts[0].text as string
    const jsonStr = extractJsonObject(content)
    const parsed = parseJsonLenient(jsonStr) as Record<string, unknown>

    const name = String(parsed.name ?? '').trim()
    if (!name) throw new Error('Missing account name in AI response')

    const account_type = normalizeAccountType(parsed.account_type)
    const is_postable = Boolean(parsed.is_postable)

    let parent_account_code: string | null = null
    if (parsed.parent_account_code != null && String(parsed.parent_account_code).trim() !== '') {
      const pc = String(parsed.parent_account_code).trim()
      const parentRow = chartLines.find((a) => a.code === pc)
      if (!parentRow) {
        throw new Error(
          `Parent account code "${pc}" was not found in the chart. Choose an existing code or omit the parent.`
        )
      }
      if (parentRow.account_type !== account_type) {
        throw new Error(
          `Parent "${pc}" has type ${parentRow.account_type}, but the account is ${account_type}. Parent and child must match.`
        )
      }
      if (excludeId != null && parentRow.id === excludeId) {
        throw new Error('Cannot set an account as its own parent.')
      }
      parent_account_code = pc
    }

    const report_category = normalizeReportCategory(parsed.report_category, account_type)

    return {
      name,
      account_type,
      parent_account_code,
      report_category,
      is_postable,
    }
  } catch (error) {
    console.error('Error parsing account from NL:', error)
    throw new Error(
      error instanceof Error ? error.message : 'AI could not parse the account description.'
    )
  }
}
