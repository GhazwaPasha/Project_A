'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import { canAccessPathname } from '@/lib/org-nav-access'
import { brandTitleFont } from '@/lib/brand-title-font'
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  BarChart3,
  PieChart,
  Users,
  Building2,
  CheckSquare,
  Lock,
  ChevronRight,
  Bot,
  Package,
  Truck,
  Crown,
} from 'lucide-react'

const navigation = [
  { name: 'Home', href: '/home', icon: LayoutDashboard },
  { name: 'Journal', href: '/journal', icon: BookOpen },
  { name: 'Ledger', href: '/ledger', icon: FileText },
  { name: 'Trial Balance', href: '/trial-balance', icon: BarChart3 },
  { name: 'Reports', href: '/reports', icon: PieChart },
  { name: 'Accounts', href: '/accounts', icon: FileText },
  { name: 'Inventory', href: '/inventory', icon: Package },
  { name: 'Suppliers', href: '/suppliers', icon: Truck },
  { name: 'Approvals', href: '/approvals', icon: CheckSquare },
  { name: 'Period Closing', href: '/period-closing', icon: Lock },
  { name: 'AI Demo', href: '/ai-demo', icon: Bot },
  { name: 'Super Admin', href: '/super-admin', icon: Crown },
  { name: 'Team Management', href: '/team', icon: Users },
  { name: 'Organization Settings', href: '/organization', icon: Building2 },
  { name: 'User Management', href: '/users', icon: Users },
]

function linkIsActive(pathname: string, href: string) {
  if (href === '/home') return pathname === '/home'
  return pathname === href || pathname.startsWith(`${href}/`)
}

export function Win11Sidebar() {
  const pathname = usePathname()
  const role = useAuthStore((s) => s.currentOrgMemberRole)
  const isSuper = useAuthStore((s) => s.profile?.is_super_admin) === true
  const visibleNav = useMemo(
    () => navigation.filter((item) => canAccessPathname(item.href, role, isSuper)),
    [role, isSuper]
  )

  return (
    <div className="app-shell-sidebar">
      <div
        className="app-shell-sidebar-brand app-top-header flex h-16 w-full min-h-16 shrink-0 items-center px-4 md:px-6"
      >
        <span
          className={cn(
            brandTitleFont.className,
            'w-full min-w-0 truncate text-xl font-extrabold leading-none tracking-tight text-on-surface sm:text-2xl',
          )}
        >
          Accountuitive
        </span>
      </div>

      <nav className="flex-1 overflow-y-auto py-1 scrollbar-hide" style={{ backgroundColor: 'var(--md-sys-color-surface)' }}>
        <div className="space-y-1 px-3">
          {visibleNav.map((item) => {
            const isActive = linkIsActive(pathname, item.href)
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'group relative flex items-center transition-all duration-200',
                  'md-navigation-item justify-start',
                  isActive && 'active'
                )}
              >
                <div className="flex w-full items-center justify-between space-x-3">
                  <div className="flex min-w-0 items-center space-x-3">
                    <item.icon className="h-4 w-4 shrink-0" />
                    <span className="app-shell-nav-label truncate">{item.name}</span>
                  </div>
                  {isActive && <ChevronRight className="h-4 w-4 shrink-0" />}
                </div>
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
