/**
 * AI Transaction Parser for Web App
 * Parses natural language transaction descriptions into structured journal entry data
 * Matches desktop app functionality exactly
 */

export interface ParsedTransaction {
  date?: string | null
  description: string
  debit_account_code: string
  credit_account_code: string
  amount: number
}

export interface Account {
  id: number
  code: string
  name: string
  account_type: string
}

// Google AI API configuration
const GOOGLE_AI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'

/**
 * Get Google AI API key from environment
 */
function getGoogleAIKey(): string {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_AI_KEY
  if (!apiKey) {
    throw new Error('Google AI API key not configured. Please set NEXT_PUBLIC_GOOGLE_AI_KEY environment variable.')
  }
  return apiKey
}

/**
 * Fetch available models from Google AI
 */
async function getAvailableModels(): Promise<string[]> {
  const apiKey = getGoogleAIKey()
  const response = await fetch(`${GOOGLE_AI_BASE_URL}/models?key=${apiKey}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch models: ${response.status} ${response.statusText}`)
  }
  
  const data = await response.json()
  return data.models
    ?.filter((model: any) => 
      model.supportedGenerationMethods?.includes('generateContent') &&
      model.name.includes('gemini')
    )
    ?.map((model: any) => model.name.split('/').pop()) || []
}

/**
 * Get the best available model for generation
 */
async function getBestModel(): Promise<string> {
  const models = await getAvailableModels()
  console.log('Available models:', models)
  
  // Prefer flash models for speed, fallback to pro
  const flashModel = models.find(model => model.includes('flash'))
  if (flashModel) return flashModel
  
  const proModel = models.find(model => model.includes('pro'))
  if (proModel) return proModel
  
  // Fallback to first available model
  if (models.length > 0) return models[0]
  
  throw new Error('No suitable models found')
}

/**
 * Parse natural language transaction using Google AI with chart of accounts playbook
 */
export async function parseTransaction(
  nlInput: string, 
  accounts: Account[]
): Promise<ParsedTransaction> {
  if (!nlInput.trim()) {
    throw new Error('Please enter a description to parse.')
  }

  try {
    // Get the best available model
    const model = await getBestModel()
    console.log('Using model:', model)
    
    // Create chart of accounts context for AI playbook
    const chartOfAccounts = accounts.map(acc => `${acc.code} - ${acc.name} (${acc.account_type})`).join('\n')
    
    const prompt = `You are an expert accountant following GAAP principles and Business Entity Concept. Create a proper double-entry journal entry using ONLY the accounts provided in the chart of accounts below.

Transaction Description: "${nlInput}"

CHART OF POSTABLE ACCOUNTS (You MUST use ONLY these exact account codes - these are the ONLY accounts you can post to):
${chartOfAccounts}

ACCOUNTING RULES:
- Assets: DEBIT to increase, CREDIT to decrease
- Liabilities: CREDIT to increase, DEBIT to decrease  
- Equity: CREDIT to increase, DEBIT to decrease
- Revenue: CREDIT to increase, DEBIT to decrease
- Expenses: DEBIT to increase, CREDIT to decrease

BUSINESS ENTITY CONCEPT:
The business is a separate entity from its owner. All transactions must be analyzed to determine if they benefit the business or the owner personally.

ANALYSIS FRAMEWORK:
1. WHO is the beneficiary of this transaction?
   - If the BUSINESS benefits → Business transaction
   - If the OWNER personally benefits → Personal transaction

2. WHAT is the nature of the expense?
   - Business operations, client relations, employee costs → Business
   - Personal consumption, personal gifts, personal meals → Personal

3. HOW does this affect the business?
   - Generates revenue, reduces business costs, improves business operations → Business
   - Reduces owner's equity, personal consumption, personal benefit → Personal

ACCOUNTING TREATMENT:
PERSONAL TRANSACTIONS:
- Nature: Owner's personal consumption or personal benefit
- Effect: Reduces owner's equity in the business
- Treatment: DEBIT [Owner's Drawings] + CREDIT [Cash/Bank Account]
- Examples: Personal meals, personal gifts, personal expenses, owner's personal purchases

BUSINESS TRANSACTIONS:
- Nature: Business operations, client relations, employee costs
- Effect: Business expense or business asset
- Treatment: DEBIT [Appropriate Business Account] + CREDIT [Cash/Bank Account]
- Examples: Office supplies, client entertainment, employee meals, business equipment

MANDATORY ANALYSIS PROCESS:
Before creating any journal entry, you MUST answer these questions:

1. WHO is the beneficiary of this transaction?
   - If the answer is "the owner personally" or "the individual personally" → PERSONAL TRANSACTION
   - If the answer is "the business" or "business operations" → BUSINESS TRANSACTION

2. For PERSONAL TRANSACTIONS:
   - DEBIT: Owner's Drawings (or similar equity account)
   - CREDIT: Cash/Bank Account
   - NEVER use expense accounts for personal transactions

3. For BUSINESS TRANSACTIONS:
   - DEBIT: Appropriate business expense/asset account
   - CREDIT: Cash/Bank Account

CRITICAL REQUIREMENTS:
1. You MUST select account codes ONLY from the POSTABLE chart of accounts provided above
2. You MUST NOT create or generate new account codes
3. You MUST find the appropriate accounts from the provided POSTABLE accounts list
4. You MUST follow proper double-entry accounting principles
5. You MUST ensure debits equal credits
6. You MUST analyze WHO benefits from the transaction
7. You MUST use Owner's Drawings for personal transactions
8. You MUST use business expense accounts only for business transactions
9. You MUST use the exact account codes as they appear in the chart
10. ONLY use accounts from the POSTABLE ACCOUNTS list provided - no other accounts are allowed

ACCOUNT SELECTION RULES:
- For personal transactions: Find "Owner's Drawings" or similar equity account from the POSTABLE accounts chart
- For cash/bank transactions: Find "Cash" or "Bank" account from the POSTABLE accounts chart
- For business expenses: Find appropriate expense account from the POSTABLE accounts chart
- NEVER invent account codes that don't exist in the provided POSTABLE accounts chart
- If you cannot find a suitable postable account, you MUST return an error

REMEMBER: Personal meals, personal gifts, personal expenses = Owner's Drawings, NOT expense accounts!

🚫 DATE RULE: 
- ONLY include a date if the user explicitly mentions a specific date
- If no date is mentioned, set "date" to null
- DO NOT generate dates that aren't explicitly mentioned

JSON RESPONSE FORMAT:
{
    "date": null (ONLY if user mentions a specific date, otherwise null),
    "description": "Clear description of the transaction",
    "debit_account_code": "Account code from chart of accounts (e.g., '6001', '1120')",
    "credit_account_code": "Account code from chart of accounts (e.g., '1001', '2001')", 
    "amount": number (without currency symbols)
}

Respond with ONLY the JSON object, no explanations.`

    const data = {
      "contents": [
        {
          "parts": [
            {
              "text": prompt
            }
          ]
        }
      ]
    }
    
    const response = await fetch(`${GOOGLE_AI_BASE_URL}/models/${model}:generateContent?key=${getGoogleAIKey()}`, {
      method: 'POST',
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('Google AI API error response:', errorText)
      throw new Error(`Google AI API error: ${response.status} ${response.statusText} - ${errorText}`)
    }
    
    const result = await response.json()
    const content = result.candidates[0].content.parts[0].text
    
    // Extract JSON from response (matches desktop app logic exactly)
    const start = content.indexOf('{')
    const end = content.lastIndexOf('}') + 1
    if (start === -1 || end === 0) {
      throw new Error("No JSON found in AI response")
    }
    
    let jsonStr = content.substring(start, end)
    
    // Clean up common JSON formatting issues (enhanced cleaning)
    // CRITICAL: Handle Unicode smart quotes FIRST before any other replacements
    jsonStr = jsonStr.replace(/[\u201C\u201D]/g, '"')  // Replace smart double quotes with regular quotes
    jsonStr = jsonStr.replace(/[\u2018\u2019]/g, "'")  // Replace smart single quotes/apostrophes with regular apostrophes
    jsonStr = jsonStr.replace(/,\s*}/g, '}')  // Remove trailing commas before }
    jsonStr = jsonStr.replace(/,\s*]/g, ']')  // Remove trailing commas before ]
    
    let parsed: any
    try {
      parsed = JSON.parse(jsonStr)
    } catch (e) {
      // Log the problematic JSON for debugging
      console.error('AI returned invalid JSON:', jsonStr)
      console.error('JSON parse error:', e)
      
      // Try a more aggressive cleanup
      jsonStr = jsonStr
        .replace(/[\u201C\u201D]/g, '"')  // Replace smart double quotes with regular quotes
        .replace(/[\u2018\u2019]/g, "'")  // Replace smart single quotes/apostrophes with regular apostrophes
        .replace(/[^\x20-\x7E]/g, '')  // Remove non-printable characters
        .replace(/\s+/g, ' ')  // Normalize whitespace
        .replace(/,\s*}/g, '}')  // Remove trailing commas
        .replace(/,\s*]/g, ']')  // Remove trailing commas
      
      try {
        parsed = JSON.parse(jsonStr)
      } catch (e2) {
        throw new Error(`Invalid JSON from AI after cleanup: ${e2}. Original: ${jsonStr}`)
      }
    }
    
    // Ensure required fields exist (matches desktop app validation)
    const requiredFields = ['description', 'debit_account_code', 'credit_account_code', 'amount']
    for (const field of requiredFields) {
      if (!(field in parsed)) {
        throw new Error(`Missing required field: ${field}`)
      }
    }
    
    // Handle date field properly (matches desktop app logic exactly)
    let dateValue = parsed.date
    if (dateValue === null || dateValue === "null" || dateValue === "") {
      parsed.date = '' // Empty string means no date specified
    } else if (typeof dateValue === 'string' && dateValue.trim()) {
      // Validate date format if a date was provided
      try {
        new Date(dateValue.trim()).toISOString().split('T')[0] // Validate YYYY-MM-DD format
        parsed.date = dateValue.trim()
      } catch {
        // Invalid date format, treat as no date specified
        parsed.date = ''
      }
    } else {
      parsed.date = ''
    }
    
    // Ensure amount is a number (matches desktop app)
    const amount = parseFloat(parsed.amount)
    if (isNaN(amount) || amount <= 0) {
      throw new Error("Invalid amount: must be a positive number")
    }
    parsed.amount = amount
    
    return parsed as ParsedTransaction

  } catch (error) {
    console.error('Error parsing transaction:', error)
    throw new Error(`AI could not parse the transaction: ${error}`)
  }
}


