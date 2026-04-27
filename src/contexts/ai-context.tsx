'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

interface AIStatusBarContextType {
  showNotification: (title: string, message?: string, type?: 'success' | 'warning' | 'error' | 'info') => void
  addBackgroundProcess: (id: string, message: string, progress?: string) => void
  updateBackgroundProcess: (id: string, message?: string, progress?: string) => void
  removeBackgroundProcess: (id: string) => void
  setUnreadNotifications: (count: number) => void
  unreadNotifications: number
  backgroundProcesses: Array<{
    id: string
    message: string
    progress: string
    startTime: Date
  }>
}

const AIStatusBarContext = createContext<AIStatusBarContextType | undefined>(undefined)

export function AIStatusBarProvider({ children }: { children: ReactNode }) {
  const [unreadNotifications, setUnreadNotifications] = useState(0)
  const [backgroundProcesses, setBackgroundProcesses] = useState<Array<{
    id: string
    message: string
    progress: string
    startTime: Date
  }>>([])

  const showNotification = useCallback((title: string, message?: string, type: 'success' | 'warning' | 'error' | 'info' = 'info') => {
    // This will be handled by the AI status bar component
    if (typeof window !== 'undefined' && (window as any).aiStatusBar) {
      (window as any).aiStatusBar.showNotification(title, message, type)
    }
  }, [])

  const addBackgroundProcess = useCallback((id: string, message: string, progress = '') => {
    setBackgroundProcesses(prev => [...prev, { id, message, progress, startTime: new Date() }])
  }, [])

  const updateBackgroundProcess = useCallback((id: string, message?: string, progress?: string) => {
    setBackgroundProcesses(prev => 
      prev.map(process => 
        process.id === id 
          ? { ...process, ...(message && { message }), ...(progress && { progress }) }
          : process
      )
    )
  }, [])

  const removeBackgroundProcess = useCallback((id: string) => {
    setBackgroundProcesses(prev => prev.filter(process => process.id !== id))
  }, [])

  return (
    <AIStatusBarContext.Provider value={{
      showNotification,
      addBackgroundProcess,
      updateBackgroundProcess,
      removeBackgroundProcess,
      setUnreadNotifications,
      unreadNotifications,
      backgroundProcesses
    }}>
      {children}
    </AIStatusBarContext.Provider>
  )
}

export function useAIStatusBar() {
  const context = useContext(AIStatusBarContext)
  if (context === undefined) {
    throw new Error('useAIStatusBar must be used within an AIStatusBarProvider')
  }
  return context
}
