import { useRef, useState, type KeyboardEvent, type PointerEvent } from 'react'
import { applyPanel, readPanel, savePanel, type Panel } from '@/lib/panels'
import { cn } from '@/lib/utils'

const STEP = 16
const GLIDE_MS = 200

/** A draggable edge for its parent panel. Arrow keys also work, and double-clicking restores the default width. */
export function ResizeHandle({ panel, label, grows, className }: { panel: Panel; label: string; grows: 'left' | 'right'; className?: string }) {
  const [now, setNow] = useState(() => readPanel(panel))
  const drag = useRef<{ x: number; width: number } | null>(null)
  const frame = useRef(0)
  const set = (n: number) => {
    const width = panel.normalize(n)
    applyPanel(panel, width)
    setNow(width)
  }
  // Moves to a far-off width without a jump: the double-click reset, and Home and End.
  const glide = (to: number) => {
    cancelAnimationFrame(frame.current)
    const from = readPanel(panel)
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      set(to)
      savePanel(panel)
      return
    }
    const start = performance.now()
    const step = (time: number) => {
      const t = Math.min(1, Math.max(0, (time - start) / GLIDE_MS)) // The first frame's timestamp can predate start.
      set(from + (to - from) * (1 - (1 - t) ** 3))
      if (t < 1) frame.current = requestAnimationFrame(step)
      else savePanel(panel)
    }
    frame.current = requestAnimationFrame(step)
  }
  const onPointerDown = (e: PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return
    e.preventDefault()
    cancelAnimationFrame(frame.current)
    e.currentTarget.setPointerCapture(e.pointerId)
    drag.current = { x: e.clientX, width: e.currentTarget.parentElement?.offsetWidth ?? readPanel(panel) }
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }
  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    if (!drag.current) return
    const moved = e.clientX - drag.current.x
    set(drag.current.width + (grows === 'right' ? moved : -moved))
  }
  const endDrag = () => {
    if (!drag.current) return
    drag.current = null
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    savePanel(panel)
  }
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const wider = grows === 'right' ? 'ArrowRight' : 'ArrowLeft'
    const narrower = grows === 'right' ? 'ArrowLeft' : 'ArrowRight'
    if (e.key === 'Home' || e.key === 'End') {
      e.preventDefault()
      glide(e.key === 'Home' ? panel.min : panel.max)
      return
    }
    if (e.key !== wider && e.key !== narrower) return
    e.preventDefault()
    cancelAnimationFrame(frame.current)
    set(readPanel(panel) + (e.key === wider ? STEP : -STEP))
    savePanel(panel)
  }
  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label={label}
      aria-valuenow={now}
      aria-valuemin={panel.min}
      aria-valuemax={panel.max}
      tabIndex={0}
      title={label}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onKeyDown={onKeyDown}
      onDoubleClick={() => glide(panel.fallback)}
      className={cn('group absolute inset-y-0 z-10 grid justify-center cursor-col-resize touch-none outline-none print:hidden', className)}
    >
      <span aria-hidden className="w-0.5 h-full bg-ring/50 opacity-0 transition-opacity duration-100 group-hover:opacity-100 group-focus-visible:opacity-100 group-active:opacity-100" />
    </div>
  )
}
