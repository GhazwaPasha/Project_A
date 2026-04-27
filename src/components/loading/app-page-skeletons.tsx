import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export function DashboardPageSkeleton() {
  return (
    <div className="space-y-6 p-6" aria-busy="true" aria-label="Loading dashboard">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="h-8 w-44" />
          <Skeleton className="h-4 w-full max-w-md" />
        </div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <Skeleton className="h-10 w-full sm:w-56 rounded-xl" />
          <div className="flex gap-2">
            <Skeleton className="h-9 w-24 rounded-lg" />
            <Skeleton className="h-9 w-28 rounded-lg" />
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="md-card-expressive border border-outline-variant/30">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-10 w-10 shrink-0 rounded-xl" />
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <Skeleton className="h-9 w-36" />
              <Skeleton className="h-4 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[0, 1].map((i) => (
          <Card key={i} className="win11-card border border-outline-variant/30">
            <CardHeader>
              <Skeleton className="mb-2 h-5 w-48" />
              <Skeleton className="h-4 w-64 max-w-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-64 w-full rounded-lg" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

function JournalEntryCardSkeleton() {
  return (
    <Card className="md-card-expressive relative overflow-hidden border border-outline-variant/30">
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-outline-variant/40" aria-hidden />
      <CardContent className="space-y-3 p-4 pl-5">
        <div className="flex items-start justify-between gap-3">
          <Skeleton className="h-6 w-20 rounded-full" />
          <Skeleton className="h-7 w-24" />
        </div>
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-4 w-[88%] max-w-full" />
        <div className="space-y-2 pt-1">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-[72%]" />
        </div>
        <Skeleton className="mt-2 h-10 w-full rounded-lg" />
      </CardContent>
    </Card>
  )
}

/** Skeleton grid for journal entry cards (matches loaded grid). */
export function JournalListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"
      aria-busy="true"
      aria-label="Loading journal entries"
    >
      {Array.from({ length: count }).map((_, i) => (
        <JournalEntryCardSkeleton key={i} />
      ))}
    </div>
  )
}

/** Route-level journal shell while the page segment loads. */
export function JournalPageSkeleton() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="mb-4 flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton className="h-7 w-48" />
              <Skeleton className="h-4 w-32" />
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-10 w-28 rounded-xl" />
              <Skeleton className="h-10 w-28 rounded-xl" />
            </div>
          </div>
        </div>
      </div>
      <div className="px-6 py-6">
        <JournalListSkeleton />
      </div>
    </div>
  )
}

function ApprovalsVoucherCardSkeleton() {
  return (
    <Card className="md-card-expressive border border-outline-variant/30">
      <CardContent className="space-y-4 p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Skeleton className="h-10 w-10 shrink-0 rounded-xl" />
            <div className="space-y-2">
              <Skeleton className="h-5 w-28" />
              <Skeleton className="h-3 w-32" />
            </div>
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-6 w-16 rounded-md" />
            <Skeleton className="h-6 w-20 rounded-md" />
          </div>
        </div>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-[78%]" />
        <div className="space-y-2 border-t border-outline-variant pt-4">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-2/3" />
        </div>
      </CardContent>
    </Card>
  )
}

/** Voucher cards only — use when the real summary/filter header is already on screen. */
export function ApprovalsVoucherGridSkeleton() {
  return (
    <div
      className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3"
      aria-busy="true"
      aria-label="Loading vouchers"
    >
      {Array.from({ length: 6 }).map((_, i) => (
        <ApprovalsVoucherCardSkeleton key={i} />
      ))}
    </div>
  )
}

/** Summary row + voucher grid (Suspense / full-page shell). */
export function ApprovalsListSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading approvals">
      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="md-card-expressive border border-outline-variant/30">
            <CardContent className="flex items-center justify-between p-4">
              <div className="space-y-2">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-8 w-12" />
              </div>
              <Skeleton className="h-8 w-8 shrink-0 rounded-lg" />
            </CardContent>
          </Card>
        ))}
      </div>
      <ApprovalsVoucherGridSkeleton />
    </div>
  )
}

/** Suspense fallback: full approvals layout shell. */
export function ApprovalsPageSkeleton() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      <div className="app-page-header sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              <Skeleton className="h-7 w-40" />
              <Skeleton className="h-4 w-72 max-w-full" />
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-10 w-28 rounded-2xl" />
              <Skeleton className="h-10 w-28 rounded-2xl" />
            </div>
          </div>
          <div className="flex flex-col gap-4 lg:flex-row">
            <Skeleton className="h-12 w-full flex-1 rounded-2xl" />
            <div className="flex flex-wrap gap-3">
              <Skeleton className="h-12 w-36 rounded-2xl" />
              <Skeleton className="h-12 w-36 rounded-2xl" />
              <Skeleton className="h-12 w-24 rounded-2xl" />
            </div>
          </div>
        </div>
      </div>
      <div className="px-6 py-6">
        <ApprovalsListSkeleton />
      </div>
    </div>
  )
}
