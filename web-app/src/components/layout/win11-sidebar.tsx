'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { 
  LayoutDashboard, 
  BookOpen, 
  FileText, 
  BarChart3, 
  PieChart, 
  Users, 
  Settings, 
  X,
  Building2,
  Calendar,
  CheckSquare,
  Lock,
  ChevronRight,
  Menu,
  Bot,
  Package
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Journal', href: '/dashboard/journal', icon: BookOpen },
  { name: 'Ledger', href: '/dashboard/ledger', icon: FileText },
  { name: 'Trial Balance', href: '/dashboard/trial-balance', icon: BarChart3 },
  { name: 'Reports', href: '/dashboard/reports', icon: PieChart },
  { name: 'Accounts', href: '/dashboard/accounts', icon: FileText },
  { name: 'Inventory', href: '/dashboard/inventory', icon: Package },
  { name: 'Reminders', href: '/dashboard/reminders', icon: CheckSquare },
  { name: 'Period Closing', href: '/dashboard/period-closing', icon: Lock },
  { name: 'AI Demo', href: '/dashboard/ai-demo', icon: Bot },
  { name: 'Team Management', href: '/dashboard/team', icon: Users },
  { name: 'Organization Settings', href: '/dashboard/organization', icon: Building2 },
  { name: 'User Management', href: '/dashboard/users', icon: Users },
]

interface Win11SidebarProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function Win11Sidebar({ open, onOpenChange }: Win11SidebarProps) {
  const pathname = usePathname()

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
        "md-layout-sidebar transform transition-all duration-300 ease-in-out",
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
            "flex-1 py-1",
            open ? "px-3" : "px-2"
          )}>
            {/* All Navigation Items */}
            <div className="space-y-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href
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
