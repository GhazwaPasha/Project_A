'use client'

import { useState, useEffect, useRef } from 'react'
import { Win11Sidebar } from './win11-sidebar'
import { Win11Header } from './win11-header'
import { cn } from '@/lib/utils'
import { useBackgroundSync } from '@/hooks/use-background-sync'
import { OrgPathAccessGuard } from '@/components/access/org-path-access-guard'

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const layoutRef = useRef<HTMLDivElement>(null)
  
  // Disable background sync for now to prevent state persistence issues
  // TODO: Re-enable with proper configuration once tested
  // useBackgroundSync()

  useEffect(() => {
    const updateSidebarWidth = () => {
      if (layoutRef.current) {
        const sidebar = layoutRef.current.querySelector('.app-shell-sidebar') as HTMLElement
        if (sidebar) {
          const actualWidth = sidebar.offsetWidth
          layoutRef.current.style.setProperty('--sidebar-width', `${actualWidth}px`)
        }
      }
    }

    // Update on mount
    updateSidebarWidth()
    
    // Update on window resize
    window.addEventListener('resize', updateSidebarWidth)
    
    return () => {
      window.removeEventListener('resize', updateSidebarWidth)
    }
  }, [])

  // Separate effect for sidebar state changes with delay
  useEffect(() => {
    const updateSidebarWidth = () => {
      if (layoutRef.current) {
        const sidebar = layoutRef.current.querySelector('.app-shell-sidebar') as HTMLElement
        if (sidebar) {
          const actualWidth = sidebar.offsetWidth
          layoutRef.current.style.setProperty('--sidebar-width', `${actualWidth}px`)
        }
      }
    }

    // Delay the update to allow CSS transition to complete
    const timeoutId = setTimeout(updateSidebarWidth, 350) // Slightly longer than CSS transition (300ms)
    
    return () => clearTimeout(timeoutId)
  }, [sidebarOpen])

  return (
    <div ref={layoutRef} className="app-shell">
      {/* Sidebar - Material Design 3 Navigation Drawer */}
      <Win11Sidebar 
        open={sidebarOpen} 
        onOpenChange={setSidebarOpen}
      />
      
      {/* Main content area - Material Design 3 Main Content */}
      <div className={cn("app-shell-main", !sidebarOpen && "sidebar-collapsed")}>
        {/* Header - Material Design 3 Top App Bar */}
        <Win11Header />
        
        {/* Page content - Material Design 3 Content Area */}
        <main className="flex-1 overflow-y-auto md-scrollbar relative">
          <OrgPathAccessGuard>{children}</OrgPathAccessGuard>
        </main>
      </div>
    </div>
  )
}
