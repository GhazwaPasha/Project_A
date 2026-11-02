import { useNavigate } from '@tanstack/react-router'
import { CommandDialog, Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { NAV } from '@/components/shell'
import { useApp } from '@/lib/boot'

export function CommandMenu({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const navigate = useNavigate()
  const { orgs, org, setOrg, isSuperAdmin, canSeeBooks } = useApp()
  const run = (fn: () => void) => { onOpenChange(false); fn() }
  const isOwner = isSuperAdmin || org.role === 'organization_owner' || org.role === 'super_admin'
  const items = NAV.flatMap((g) => g.items).filter((i) => (!i.superOnly || isSuperAdmin) && (!i.ownerOnly || isOwner) && (canSeeBooks || i.href))

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange} title="Go to" description="Go to a screen or switch organization">
      <Command>
        <CommandInput placeholder="Go to a screen" />
        <CommandList>
          <CommandEmpty>No matches.</CommandEmpty>
          <CommandGroup heading="Screens">
            {items.map((i) => <CommandItem key={i.label} onSelect={() => run(() => { if (i.to) void navigate({ to: i.to }); else location.href = i.href! })}>{i.label}</CommandItem>)}
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
