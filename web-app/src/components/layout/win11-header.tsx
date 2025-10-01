'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { 
  Bell, 
  Settings,
  User,
  Building2,
  MoreVertical
} from 'lucide-react'
import { AIStatusBar } from '@/components/ai/ai-status-bar'
import { OrganizationSwitcher } from '@/components/ui/organization-switcher'

interface Win11HeaderProps {}

export function Win11Header({}: Win11HeaderProps) {
  return (
    <header className="md-header sticky top-0 z-40">
      <div className="flex h-16 items-center justify-between px-4 md:px-6">
        {/* Left side - App Branding */}
        <div className="flex items-center space-x-3">
          {/* App Logo */}
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Building2 className="w-4 h-4 text-on-primary" />
          </div>
          
          {/* Organization switcher - Material Design 3 Chip */}
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
            className="md-button-text p-2 rounded-full relative"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-error rounded-full flex items-center justify-center">
              <span className="w-1.5 h-1.5 bg-on-error rounded-full"></span>
            </span>
          </button>
          
          {/* Settings */}
          <button 
            className="md-button-text p-2 rounded-full"
            aria-label="Settings"
            onClick={() => window.location.href = '/dashboard/settings'}
          >
            <Settings className="w-4 h-4" />
          </button>
          
          {/* User Profile */}
          <button 
            className="md-button-text p-2 rounded-full"
            aria-label="User profile"
          >
            <User className="w-4 h-4" />
          </button>
          
          {/* More options */}
          <button 
            className="md-button-text p-2 rounded-full"
            aria-label="More options"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  )
}
