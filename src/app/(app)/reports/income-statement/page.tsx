'use client'

import { IncomeStatementReport } from '@/components/reports/income-statement-report'

export default function IncomeStatementPage() {
  return <IncomeStatementReport onBack={() => window.history.back()} />
}
