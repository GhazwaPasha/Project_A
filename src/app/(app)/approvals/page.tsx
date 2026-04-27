import { Suspense } from 'react'
import { Win11ApprovalsPage } from '@/components/approvals/win11-approvals-page'

function ApprovalsFallback() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center p-6 text-on-surface-variant">
      Loading approvals…
    </div>
  )
}

export default function ApprovalsPage() {
  return (
    <Suspense fallback={<ApprovalsFallback />}>
      <Win11ApprovalsPage />
    </Suspense>
  )
}
