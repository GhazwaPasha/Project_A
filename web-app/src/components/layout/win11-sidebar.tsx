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
  Menu
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Journal', href: '/dashboard/journal', icon: BookOpen },
  { name: 'Ledger', href: '/dashboard/ledger', icon: FileText },
  { name: 'Trial Balance', href: '/dashboard/trial-balance', icon: BarChart3 },
  { name: 'Reports', href: '/dashboard/reports', icon: PieChart },
  { name: 'Accounts', href: '/dashboard/accounts', icon: FileText },
  { name: 'Reminders', href: '/dashboard/reminders', icon: CheckSquare },
  { name: 'Period Closing', href: '/dashboard/period-closing', icon: Lock },
]

const adminNavigation = [
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
        "fixed inset-y-0 left-0 z-50 lg:relative lg:z-auto",
        open ? "w-72 translate-x-0" : "w-16 -translate-x-full lg:translate-x-0 lg:w-16"
      )}>
        <div className="flex h-full flex-col">
           {/* Header - Material Design 3 App Bar */}
           <div className="flex h-16 items-center px-2">
             {/* Drawer toggle - styled like navigation items */}
             <button
               className={cn(
                 "group relative flex items-center transition-all duration-200 w-full",
                 open ? "md-navigation-item justify-start" : "justify-center p-2",
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
                     open ? "w-4 h-4" : "w-5 h-5"
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
            "flex-1 py-4 space-y-2",
            open ? "px-3" : "px-2"
          )}>
            {/* Main Navigation */}
            <div className="space-y-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                return (
                   <Link
                     key={item.name}
                     href={item.href}
                     className={cn(
                       "group relative flex items-center transition-all duration-200",
                       open ? "md-navigation-item justify-start" : "justify-center p-2",
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
            
            {/* Admin section - Material Design 3 List Section */}
            {open && (
              <div className="pt-6">
                <div className="px-3 py-2">
                  <h3 className="md-label-small text-on-surface-variant uppercase tracking-wider">
                    Administration
                  </h3>
                </div>
                <div className="space-y-1">
                  {adminNavigation.map((item) => {
                    const isActive = pathname === item.href
                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        className={cn(
                          "md-navigation-item group relative",
                          isActive && "active"
                        )}
                      >
                        <div className="flex items-center justify-between w-full">
                          <div className="flex items-center space-x-3">
                            <item.icon className="w-4 h-4" />
                            <span className="md-label-large">{item.name}</span>
                          </div>
                          {isActive && (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </div>
                      </Link>
                    )
                  })}
                </div>
              </div>
            )}
          </nav>
          
          {/* Footer - Material Design 3 User Profile Card */}
          <div className={cn(
            "p-4",
            open ? "p-4" : "p-2"
          )}>
            <div className={cn(
              "md-card-filled transition-all duration-200",
              open ? "p-4" : "p-2"
            )}>
              <div className={cn(
                "flex items-center transition-all duration-200",
                open ? "space-x-3" : "justify-center"
              )}>
                <div className={cn(
                  "bg-primary rounded-full flex items-center justify-center transition-all duration-200",
                  open ? "w-10 h-10" : "w-8 h-8"
                )}>
                  <span className={cn(
                    "text-on-primary font-medium transition-all duration-200",
                    open ? "md-label-large" : "text-sm"
                  )}>U</span>
                </div>
                {open && (
                  <>
                    <div className="flex-1 min-w-0">
                      <p className="md-label-large text-on-surface truncate">User Name</p>
                      <p className="md-body-small text-on-surface-variant truncate">user@example.com</p>
                    </div>
                    <button className="md-button-text p-2 rounded-full hover:bg-surface-container-highest transition-colors duration-200">
                      <Settings className="w-4 h-4" />
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
