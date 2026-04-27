'use client'

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ComponentType } from 'react'
import type { AccountType } from '@/types'
import { ZoomIn, ZoomOut } from 'lucide-react'
import { ForceGraph2D } from './force-graph-2d-only'

// fromKapsule() is typed with empty default props; graph props come from the underlying kapsule API.
const Fg = ForceGraph2D as ComponentType<Record<string, unknown>>

type FlatCoa = {
  id: number
  code: string
  name: string
  account_type: AccountType
  parent_id: number | null
  is_postable: boolean
  level: number
}

type GraphNode = FlatCoa

function filterFlatForGraph(accounts: FlatCoa[], searchTerm: string): FlatCoa[] {
  const t = searchTerm.trim().toLowerCase()
  if (!t) return accounts
  const byId = new Map(accounts.map((a) => [a.id, a]))
  const need = new Set<number>()
  for (const a of accounts) {
    if (a.name.toLowerCase().includes(t) || a.code.toLowerCase().includes(t)) {
      let cur: FlatCoa | undefined = a
      while (cur) {
        need.add(cur.id)
        cur = cur.parent_id != null ? byId.get(cur.parent_id) : undefined
      }
    }
  }
  return accounts.filter((a) => need.has(a.id))
}

function readCssVar(name: string, fallback: string) {
  if (typeof document === 'undefined') return fallback
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}

function typeToColorVar(type: AccountType): string {
  switch (type) {
    case 'asset':
      return '--m3-badge-asset-fg'
    case 'liability':
      return '--m3-badge-liability-fg'
    case 'equity':
      return '--m3-badge-equity-fg'
    case 'revenue':
      return '--m3-badge-revenue-fg'
    case 'expense':
      return '--m3-badge-expense-fg'
    default:
      return '--md-sys-color-on-surface-variant'
  }
}

export function AccountsGraphView({
  flatAccounts,
  searchTerm,
  selectedId,
  onSelect,
}: {
  flatAccounts: FlatCoa[]
  searchTerm: string
  selectedId: number | null
  onSelect: (a: FlatCoa) => void
}) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null)
  const [colors, setColors] = useState<Record<AccountType, string>>(() => ({
    asset: readCssVar('--m3-badge-asset-fg', '#1d4ed8'),
    liability: readCssVar('--m3-badge-liability-fg', '#b91c1c'),
    equity: readCssVar('--m3-badge-equity-fg', '#6d28d9'),
    revenue: readCssVar('--m3-badge-revenue-fg', '#047857'),
    expense: readCssVar('--m3-badge-expense-fg', '#c2410c'),
  }))

  useLayoutEffect(() => {
    setColors({
      asset: readCssVar('--m3-badge-asset-fg', '#1d4ed8'),
      liability: readCssVar('--m3-badge-liability-fg', '#b91c1c'),
      equity: readCssVar('--m3-badge-equity-fg', '#6d28d9'),
      revenue: readCssVar('--m3-badge-revenue-fg', '#047857'),
      expense: readCssVar('--m3-badge-expense-fg', '#c2410c'),
    })
  }, [])

  const filtered = useMemo(
    () => filterFlatForGraph(flatAccounts, searchTerm),
    [flatAccounts, searchTerm]
  )
  const idSet = useMemo(() => new Set(filtered.map((a) => a.id)), [filtered])

  const graphData = useMemo(() => {
    const nodes: GraphNode[] = filtered.map((a) => ({ ...a }))
    const links: { source: number; target: number }[] = []
    for (const a of filtered) {
      if (a.parent_id != null && idSet.has(a.parent_id)) {
        links.push({ source: a.parent_id, target: a.id })
      }
    }
    return { nodes, links }
  }, [filtered, idSet])

  const bg = readCssVar('--md-sys-color-surface-container-low', '#faf8ff')
  const linkColor = useCallback(() => readCssVar('--md-sys-color-outline-variant', 'rgba(0,0,0,0.2)'), [])

  const zoomToFit = useCallback(() => {
    fgRef.current?.zoomToFit(400, 64)
  }, [])

  const zoomBy = useCallback((factor: number) => {
    const fg = fgRef.current
    if (!fg?.zoom) return
    const current = fg.zoom()
    const next = Math.max(0.02, Math.min(80, current * factor))
    fg.zoom(next, 200)
  }, [])

  useEffect(() => {
    const t = setTimeout(() => zoomToFit(), 300)
    return () => clearTimeout(t)
  }, [graphData.nodes.length, graphData.links.length, zoomToFit])

  const handleNodeClick = useCallback(
    (node: { id?: string | number }) => {
      const id = typeof node.id === 'number' ? node.id : Number(node.id)
      if (Number.isNaN(id)) return
      const a = flatAccounts.find((x) => x.id === id)
      if (a) onSelect(a)
    },
    [flatAccounts, onSelect]
  )

  if (filtered.length === 0) {
    return (
      <div
        className="flex h-[calc(100vh-16rem)] min-h-[320px] items-center justify-center rounded-xl border border-dashed border-outline-variant bg-surface-container/40"
        role="status"
      >
        <p className="text-on-surface-variant md-body-medium">
          {searchTerm.trim()
            ? 'No accounts match your search, or the match has no path to a root in the chart.'
            : 'No accounts to display.'}
        </p>
      </div>
    )
  }

  return (
    <div className="relative h-[calc(100vh-16rem)] min-h-[320px] w-full overflow-hidden rounded-xl">
      <div
        className="absolute right-2 top-2 z-10 flex items-center gap-0.5"
        role="toolbar"
        aria-label="Zoom"
      >
        <button
          type="button"
          className="accounts-chart-view-toggle transition-colors"
          onClick={() => zoomBy(0.8)}
          title="Zoom out"
        >
          <span className="sr-only">Zoom out</span>
          <ZoomOut className="h-5 w-5" strokeWidth={1.75} aria-hidden />
        </button>
        <button
          type="button"
          className="accounts-chart-view-toggle transition-colors"
          onClick={() => zoomBy(1.25)}
          title="Zoom in"
        >
          <span className="sr-only">Zoom in</span>
          <ZoomIn className="h-5 w-5" strokeWidth={1.75} aria-hidden />
        </button>
      </div>
      <Fg
        ref={fgRef}
        graphData={
          graphData as {
            nodes: GraphNode[]
            links: { source: number; target: number }[]
          }
        }
        backgroundColor={bg}
        nodeId="id"
        linkSource="source"
        linkTarget="target"
        nodeLabel={(n: GraphNode) => `${n.code} — ${n.name}`}
        nodeRelSize={4.2}
        nodeVal={(n: GraphNode) => (n.id === selectedId ? 1.35 : 0.9)}
        nodeColor={(n: GraphNode) => {
          if (n.id === selectedId) {
            return readCssVar('--md-sys-color-primary', '#6750a4')
          }
          return colors[n.account_type] ?? readCssVar(typeToColorVar(n.account_type), '#666')
        }}
        linkColor={linkColor}
        linkWidth={0.4}
        linkDirectionalArrowLength={2.2}
        linkDirectionalArrowRelPos={0.9}
        linkDirectionalArrowColor={linkColor}
        d3AlphaDecay={0.028}
        d3VelocityDecay={0.22}
        d3AlphaMin={0.001}
        cooldownTicks={120}
        onNodeClick={handleNodeClick as (node: { id?: string | number }, ev: MouseEvent) => void}
        showPointerCursor
        enableNodeDrag
      />
      <p className="pointer-events-none absolute bottom-2 left-3 z-0 max-w-[min(100%,24rem)] text-xs text-on-surface-variant/90">
        Pan and scroll to zoom; drag nodes. Arrows: parent → child. Colors: account type; highlight shows selection.
        Search includes ancestors so matches stay connected to the rest of the chart.
      </p>
    </div>
  )
}
