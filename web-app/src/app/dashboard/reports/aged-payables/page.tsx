'use client'

import { AgedPayablesReport } from '@/components/reports/aged-payables-report'

export default function AgedPayablesPage() {
  return <AgedPayablesReport onBack={() => window.history.back()} />
}
