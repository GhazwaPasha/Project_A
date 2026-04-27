'use client'

import { TrialBalanceReport } from '@/components/reports/trial-balance-report'

export default function TrialBalancePage() {
  return <TrialBalanceReport onBack={() => window.history.back()} />
}
