import { Suspense } from 'react'
import { Win11ApprovalsPage } from '@/components/approvals/win11-approvals-page'
import { ApprovalsPageSkeleton } from '@/components/loading/app-page-skeletons'

export default function ApprovalsPage() {
  return (
    <Suspense fallback={<ApprovalsPageSkeleton />}>
      <Win11ApprovalsPage />
    </Suspense>
  )
}
