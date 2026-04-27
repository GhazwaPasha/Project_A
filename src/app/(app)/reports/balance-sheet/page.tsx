'use client'

import { BalanceSheetReport } from '@/components/reports/balance-sheet-report'

export default function BalanceSheetPage() {
  return <BalanceSheetReport onBack={() => window.history.back()} />
}
