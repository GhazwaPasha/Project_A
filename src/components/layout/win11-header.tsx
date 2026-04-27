'use client'

import { useRouter } from 'next/navigation'
import {
  Bell,
  Settings,
  User,
  LogOut,
} from 'lucide-react'
import { authClient } from '@/lib/auth-client'
import { AIStatusBar } from '@/components/ai/ai-status-bar'
import { OrganizationSwitcher } from '@/components/ui/organization-switcher'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

/**
 * Base styles for header icon buttons live in `globals.css` (`.app-header-icon-btn`):
 * the global `button` rule uses `!important` primary fill, so utilities alone cannot win.
 */
const headerIconClassName = cn(
  'app-header-icon-btn',
  'inline-flex shrink-0 items-center justify-center',
  'transition-[color,background-color] duration-200'
)

interface Win11HeaderProps {}

export function Win11Header({}: Win11HeaderProps) {
  const router = useRouter()

  async function handleSignOut() {
    await authClient.signOut()
    router.push('/')
  }

  return (
    <header className="app-top-header sticky top-0 z-40 flex h-16 min-h-16 w-full shrink-0 items-center justify-between gap-2 px-4 md:px-6">
        {/* Left side - Organization Switcher */}
        <div className="flex min-w-0 items-center">
          <div className="hidden md:flex">
            <OrganizationSwitcher />
          </div>
        </div>
        
        {/* Center - AI Status Bar */}
        <div className="flex-1 flex justify-center px-4">
          <AIStatusBar />
        </div>
        
        {/* Right side - Action Buttons */}
        <div className="flex items-center space-x-1">
          {/* Notifications */}
          <button
            type="button"
            className={cn(headerIconClassName, 'relative')}
            aria-label="Notifications"
          >
            <Bell className="w-[18px] h-[18px] shrink-0" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-error rounded-full flex items-center justify-center">
              <span className="w-1.5 h-1.5 bg-on-error rounded-full"></span>
            </span>
          </button>
          
          {/* Settings */}
          <button
            type="button"
            className={headerIconClassName}
            aria-label="Settings"
            onClick={() => router.push('/settings')}
          >
            <Settings className="w-[18px] h-[18px] shrink-0" />
          </button>
          
          {/* User Profile */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className={headerIconClassName}
                aria-label="User profile"
                type="button"
              >
                <User className="w-[18px] h-[18px] shrink-0" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel>Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={() => void handleSignOut()}>
                <LogOut className="mr-2 h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
    </header>
  )
}
