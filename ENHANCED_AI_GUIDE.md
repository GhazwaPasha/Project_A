# Enhanced AI Assistant - User Guide

## Overview
Your accounting application now features a powerful, context-aware AI assistant that understands your current workflow and can perform intelligent actions. The AI uses Mistral API and maintains awareness of your current page, data, and application state.

## Key Features

### 🧠 Context Awareness
The AI always knows:
- Which page you're currently viewing
- Your current account balances and recent transactions
- Available reports and their parameters
- Your reminders and upcoming deadlines
- Application state and user context

### 🎯 Single Prompt → Action Design
Unlike chatbots, this AI is designed for immediate, actionable responses:
- **One question** → **One clear answer + action**
- No long conversations or context switching
- Focused on getting things done quickly

## What You Can Ask

### 📊 Navigation Commands
- "Show me the general ledger"
- "Go to reports page"
- "Take me to the trial balance"
- "Navigate to reminders"
- "Open the chart of accounts"

### 📈 Report Generation
- "Generate a profit and loss for this quarter"
- "Show me the balance sheet as of today"
- "Create a cash flow report for the last 6 months"
- "Generate trial balance for December 2024"
- "I need a budget variance report"

### ⏰ Reminder Management
- "Remind me to close books on March 31st"
- "Set a reminder for quarterly tax filing next week"
- "Create a recurring monthly reminder for reconciliation"
- "Remind me tomorrow to review accounts receivable"

### 💰 Data Queries
- "What's my current cash balance?"
- "Show me recent transactions"
- "Are my books balanced?"
- "What accounts have high activity this month?"
- "How many journal entries were posted today?"

### 🔍 Smart Assistance
- "How do I post an adjusting entry?"
- "What reports do I need for year-end?"
- "Help me understand the cash flow statement"
- "What's the difference between accounts payable and receivable?"

## How It Works

### 1. Context Injection
Before processing your request, the AI receives:
```
- Current page: "ledger"
- Account balances: {...}
- Recent transactions: [...]
- Date range: "Jan 1 - Dec 31, 2024"
- Available actions: ["filter", "export", "drill_down"]
```

### 2. Intent Recognition
The AI classifies your request:
- **NAVIGATION**: Moving between pages
- **REPORTING**: Generating financial reports
- **REMINDER**: Creating tasks and reminders
- **DATA_QUERY**: Asking about specific data
- **GENERAL**: Help and guidance

### 3. Smart Parameter Detection
When you say "profit and loss for Q1", the AI automatically:
- Identifies report type: profit_loss
- Calculates date range: Jan 1 - Mar 31, 2024
- Sets appropriate parameters
- Navigates to reports page
- Generates the report

### 4. Contextual Responses
Responses are tailored to your current situation:
- If you're on the dashboard: "I can see your current cash position is $X..."
- If you're viewing a specific account: "Based on this account's activity..."
- If books are out of balance: "I notice your trial balance isn't in balance..."

## Example Interactions

### Scenario 1: Month-End Reporting
**You:** "I need month-end reports"
**AI:** "I'll generate your standard month-end reports. Navigating to reports page and creating:
- Trial Balance for November 2024
- Profit & Loss for November 2024  
- Balance Sheet as of November 30, 2024"
*[Navigates to reports page and sets up all three reports]*

### Scenario 2: Quick Data Check
**You:** "Are my books balanced?"
**AI:** "Yes, your trial balance is in balance. Total debits: $45,230.50, Total credits: $45,230.50. Last transaction posted: Nov 28, 2024."

### Scenario 3: Smart Navigation
**You:** "Show me account 1000"
**AI:** "Navigating to the General Ledger and filtering for account 1000 (Cash - Operating). Current balance: $12,450.33"
*[Navigates to ledger page and applies account filter]*

### Scenario 4: Deadline Management
**You:** "Remind me about year-end closing"
**AI:** "Created reminder: 'Begin year-end closing procedures' for December 15, 2024. This will give you 2 weeks before year-end to complete all necessary adjustments."

## Advanced Features

### 🔄 Auto-Context Updates
The AI automatically stays current with:
- Page changes (updates context when you navigate)
- Data changes (refreshes when new transactions are posted)
- Time-based updates (understands "this month", "last quarter", etc.)

### 🎯 Smart Defaults
- No date specified? AI suggests current month/quarter
- Vague requests? AI provides specific, actionable suggestions
- Missing information? AI tells you exactly what it needs

### 📊 Integrated Actions
The AI doesn't just talk - it actually:
- Changes pages and applies filters
- Sets report parameters and generates reports
- Creates properly formatted reminders
- Applies date ranges and account filters

## Tips for Best Results

### ✅ Do This:
- Be specific about what you want: "trial balance for October"
- Use accounting terms the AI understands: "A/R aging", "P&L", "cash flow"
- Mention time periods: "this month", "Q4 2024", "as of today"
- Ask for actions: "show me", "generate", "create reminder"

### ❌ Avoid This:
- Long conversational messages
- Multiple requests in one message
- Vague timeframes without context
- Asking for features that don't exist in the app

## Troubleshooting

### "AI doesn't understand my request"
- Try using more specific accounting terminology
- Include time periods or date ranges
- Break complex requests into simpler parts

### "Wrong page or report generated"
- The AI learns from your corrections
- Be more specific about which page/report you want
- Check that the feature exists in your application

### "Missing context or data"
- The AI only knows what's loaded in your current session
- Try refreshing data or changing pages to update context
- Some data might require specific permissions

## Privacy & Security

- All AI processing uses your configured Mistral API key
- Context data stays within your application session
- No conversation history is stored
- Each interaction is independent and secure

## What's Next?

The AI assistant will continue to learn and improve:
- Better understanding of your specific workflows
- Enhanced integration with new features
- Smarter context awareness
- More sophisticated report generation

---

**Need Help?** Ask the AI: "How do I use the AI assistant?" for quick guidance within the application.
