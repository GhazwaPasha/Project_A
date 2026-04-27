import type { ComponentProps } from 'react'
import { cn } from '@/lib/utils'

/** M3-friendly pulse block for loading placeholders. */
export function Skeleton({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-surface-container-high/55 dark:bg-surface-container-high/35',
        className
      )}
      {...props}
    />
  )
}
