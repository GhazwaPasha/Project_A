'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import { canAccessPathname } from '@/lib/org-nav-access'
import { 
  LayoutDashboard, 
  BookOpen, 
  FileText, 
  BarChart3, 
  PieChart, 
  Users, 
  X,
  Building2,
  CheckSquare,
  Lock,
  ChevronRight,
  Menu,
  Bot,
  Package,
  Truck
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
  { name: 'Team Management', href: '/team', icon: Users },
  { name: 'Organization Settings', href: '/organization', icon: Building2 },
  { name: 'User Management', href: '/users', icon: Users },
]

interface Win11SidebarProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

function linkIsActive(pathname: string, href: string) {
  if (href === '/home') return pathname === '/home'
  return pathname === href || pathname.startsWith(`${href}/`)
}

export function Win11Sidebar({ open, onOpenChange }: Win11SidebarProps) {
  const pathname = usePathname()
  const role = useAuthStore((s) => s.currentOrgMemberRole)
  const isSuper = useAuthStore((s) => s.profile?.is_super_admin) === true
  const visibleNav = useMemo(
    () => navigation.filter((item) => canAccessPathname(item.href, role, isSuper)),
    [role, isSuper]
  )

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div 
          className="fixed inset-0 z-40 bg-scrim/50 lg:hidden"
          onClick={() => onOpenChange(false)}
        />
      )}
      
      {/* Sidebar */}
      <div className={cn(
        "app-shell-sidebar transform transition-all duration-300 ease-in-out",
        "fixed inset-y-0 left-0 z-50",
        open ? "w-72 translate-x-0" : "w-16 -translate-x-full lg:translate-x-0 lg:w-16"
      )}>
        <div className="flex h-full flex-col">
           {/* Header - Material Design 3 App Bar */}
           <div className="flex h-16 items-center justify-center px-2">
             {/* Drawer toggle - styled like navigation items */}
             <button
               className={cn(
                 "group relative flex items-center transition-all duration-200 w-full",
                 open ? "md-navigation-item justify-start" : "justify-center md-button-text p-2 rounded-full",
                 "hover:bg-transparent"
               )}
               onClick={() => onOpenChange(!open)}
               aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
             >
               <div className={cn(
                 "flex items-center w-full transition-all duration-200",
                 open ? "space-x-3 justify-between" : "justify-center"
               )}>
                 <div className="flex items-center space-x-3">
                   <Menu className={cn(
                     "transition-all duration-200",
                     open ? "w-4 h-4" : "w-4 h-4"
                   )} />
                   {open && <span className="md-label-large">Accountuitive</span>}
                 </div>
                 {open && (
                   <X className="w-4 h-4" />
                 )}
               </div>
             </button>
           </div>
          
          {/* Navigation - Material Design 3 Navigation Drawer */}
          <nav className={cn(
            "flex-1 py-1 overflow-y-auto scrollbar-hide",
            open ? "px-3" : "px-2"
          )}>
            {/* All Navigation Items */}
            <div className="space-y-1">
              {visibleNav.map((item) => {
                const isActive = linkIsActive(pathname, item.href)
                return (
                   <Link
                     key={item.name}
                     href={item.href}
                     className={cn(
                       "group relative flex items-center transition-all duration-200",
                       "md-navigation-item justify-start",
                       isActive && "active"
                     )}
                     title={!open ? item.name : undefined}
                   >
                    <div className={cn(
                      "flex items-center w-full transition-all duration-200",
                      open ? "space-x-3 justify-between" : "justify-center"
                    )}>
                       <div className="flex items-center space-x-3">
                         <item.icon className={cn(
                           "transition-all duration-200",
                           open ? "w-4 h-4" : "w-5 h-5",
                           !open && (isActive ? "text-primary" : "text-on-surface-variant hover:text-primary"),
                           !open && isActive && "!text-primary"
                         )} />
                         {open && <span className="md-label-large">{item.name}</span>}
                       </div>
                      {open && isActive && (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </div>
                  </Link>
                )
              })}
            </div>
          </nav>
        </div>
      </div>
    </>
  )
}
