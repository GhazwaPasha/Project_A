'use client'

import { useState } from 'react'
import { Win11Sidebar } from './win11-sidebar'
import { Win11Header } from './win11-header'
import { cn } from '@/lib/utils'

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="md-layout">
      {/* Sidebar - Material Design 3 Navigation Drawer */}
      <Win11Sidebar 
        open={sidebarOpen} 
        onOpenChange={setSidebarOpen}
      />
      
      {/* Main content area - Material Design 3 Main Content */}
      <div className="md-layout-main">
        {/* Header - Material Design 3 Top App Bar */}
        <Win11Header />
        
        {/* Page content - Material Design 3 Content Area */}
        <main className="flex-1 overflow-y-auto md-scrollbar relative">
          {children}
        </main>
      </div>
    </div>
  )
}
