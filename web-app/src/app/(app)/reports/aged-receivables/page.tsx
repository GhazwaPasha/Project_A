'use client'

import { AgedReceivablesReport } from '@/components/reports/aged-receivables-report'

export default function AgedReceivablesPage() {
  return <AgedReceivablesReport onBack={() => window.history.back()} />
}
