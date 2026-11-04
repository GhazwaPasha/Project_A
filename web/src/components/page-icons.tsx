import { Link } from '@tanstack/react-router'
import { Settings, Sparkles } from 'lucide-react'
import { useAgent } from '@/lib/agent'
import { useApp } from '@/lib/boot'
import { cn } from '@/lib/utils'

const ICON = 'press relative size-[34px] shrink-0 grid place-items-center rounded-[10px] border border-border bg-card text-muted-foreground cursor-pointer hover:bg-accent hover:text-foreground'

/** The agent and settings, matching the organization switcher's height and card style. */
export function PageIcons({ className }: { className?: string }) {
  const { canSeeBooks } = useApp()
  const { open, setOpen, turns } = useAgent()
  return (
    <div className={cn('flex items-center gap-2', className)}>
      {canSeeBooks ? (
        <button onClick={() => setOpen(!open)} aria-label={turns.length ? 'Open your conversation with the agent' : 'Open the agent'} aria-expanded={open} title="Agent" className={cn(ICON, 'agent-btn')}>
          <Sparkles className="agent-glyph size-4" />
          {turns.length && !open ? <span aria-hidden className="absolute top-1 right-1 size-1.5 rounded-full bg-primary" /> : null}
        </button>
      ) : null}
      <Link to="/settings" aria-label="Settings" title="Settings" className={ICON}><Settings className="size-4" /></Link>
    </div>
  )
}
