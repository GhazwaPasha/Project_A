'use client'

import { cn } from '@/lib/utils'

interface ProgressBarProps {
  progress: number // 0-100
  className?: string
  showPercentage?: boolean
  animated?: boolean
}

export function ProgressBar({ 
  progress, 
  className, 
  showPercentage = false,
  animated = true 
}: ProgressBarProps) {
  const clampedProgress = Math.max(0, Math.min(100, progress))
  
  return (
    <div className={cn(
      "relative w-full h-2 bg-surface-container-highest rounded-full overflow-hidden",
      className
    )}>
      <div
        className={cn(
          "h-full bg-primary rounded-full transition-all duration-300 ease-out",
          animated && "animate-pulse"
        )}
        style={{ width: `${clampedProgress}%` }}
      />
      {showPercentage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-medium text-on-surface">
            {Math.round(clampedProgress)}%
          </span>
        </div>
      )}
    </div>
  )
}
