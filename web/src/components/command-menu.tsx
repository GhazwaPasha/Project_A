import { useNavigate } from '@tanstack/react-router'
import { CommandDialog, Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { NAV, canOpen } from '@/components/shell'
import { useApp } from '@/lib/boot'

export function CommandMenu({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const navigate = useNavigate()
  const { orgs, org, setOrg, isSuperAdmin, canSeeBooks, access } = useApp()
  const run = (fn: () => void) => { onOpenChange(false); fn() }
  const items = NAV.flatMap((g) => g.items).filter((i) => canOpen(i, access, isSuperAdmin))

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange} title="Go to" description="Go to a screen or switch organization">
      <Command>
        <CommandInput placeholder="Go to a screen" />
        <CommandList>
          <CommandEmpty>No matches.</CommandEmpty>
          <CommandGroup heading="Screens">
            {items.map((i) => <CommandItem key={i.label} onSelect={() => run(() => void navigate({ to: i.to }))}>{i.label}</CommandItem>)}
            {canSeeBooks ? <>
              <CommandItem onSelect={() => run(() => void navigate({ to: '/reports/balance-sheet' }))}>Balance Sheet</CommandItem>
              <CommandItem onSelect={() => run(() => void navigate({ to: '/reports/income-statement', search: { period: 'month' } }))}>Income Statement</CommandItem>
            </> : null}
          </CommandGroup>
          {orgs.length > 1 ? (
            <CommandGroup heading="Switch organization">
              {orgs.filter((o) => o.id !== org.id).map((o) => <CommandItem key={o.id} value={`switch ${o.name}`} onSelect={() => run(() => setOrg(o.id))}>{o.name}</CommandItem>)}
            </CommandGroup>
          ) : null}
        </CommandList>
      </Command>
    </CommandDialog>
  )
}
