'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Bot, Loader2, CheckCircle, AlertCircle, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAIProcessor } from '@/hooks/use-ai-processor'
import { useAIStatusBar } from '@/contexts/ai-context'

interface AIStatusBarProps {
  className?: string
}

export function AIStatusBar({ className }: AIStatusBarProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [statusMessage, setStatusMessage] = useState('Your AI Sidekick - Ready')
  const [isShowingNotification, setIsShowingNotification] = useState(false)
  
  const inputRef = useRef<HTMLDivElement>(null)
  const notificationTimeoutRef = useRef<NodeJS.Timeout>()
  const statusTimeoutRef = useRef<NodeJS.Timeout>()
  
  const { processCommand, isProcessing: aiProcessing } = useAIProcessor()
  const {
    unreadNotifications,
    backgroundProcesses,
    setUnreadNotifications,
    addBackgroundProcess,
    updateBackgroundProcess,
    removeBackgroundProcess,
  } = useAIStatusBar()

  // Handle AI processor state changes
  useEffect(() => {
    if (aiProcessing) {
      setIsProcessing(true)
      setStatusMessage('🤖 AI is thinking...')
    }
  }, [aiProcessing])

  // Auto-collapse after 5 seconds when showing response
  useEffect(() => {
    if (statusMessage.includes('✅') || statusMessage.includes('📍') || statusMessage.includes('📊')) {
      statusTimeoutRef.current = setTimeout(() => {
        if (!isExpanded && !isProcessing) {
          setStatusMessage('Your AI Sidekick - Ready')
        }
      }, 5000)
    }
    
    return () => {
      if (statusTimeoutRef.current) {
        clearTimeout(statusTimeoutRef.current)
      }
    }
  }, [statusMessage, isExpanded, isProcessing])

  // Handle input submission
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    
    const command = inputValue.trim()
    if (!command) {
      collapseToNormal()
      return
    }

    setIsProcessing(true)
    setStatusMessage('🤖 Processing...')
    
    try {
      const response = await processCommand(command)
      setStatusMessage(response.message || 'Command processed successfully')
      setInputValue('')
    } catch (error) {
      setStatusMessage(`❌ ${error instanceof Error ? error.message : 'Processing error'}`)
    } finally {
      setIsProcessing(false)
    }
  }, [inputValue, processCommand])

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLDivElement>) => {
    setInputValue(e.target.textContent || '')
  }

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      collapseToNormal()
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  // Expand for input
  const expandForInput = () => {
    if (!isExpanded && !isProcessing) {
      setIsExpanded(true)
      setInputValue('')
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    }
  }

  // Handle click to expand
  const handleClick = () => {
    if (!isExpanded && !isProcessing) {
      expandForInput()
    }
  }

  // Collapse to normal
  const collapseToNormal = () => {
    setIsExpanded(false)
    setInputValue('')
    setIsProcessing(false)
    if (!isShowingNotification) {
      updateStatus()
    }
  }

  // Update status based on current state
  const updateStatus = () => {
    if (backgroundProcesses.length > 0) {
      const process = backgroundProcesses[backgroundProcesses.length - 1]
      const message = process.message || 'Background process running'
      const progress = process.progress || ''
      
      if (message.toLowerCase().includes('sync')) {
        setStatusMessage(`🔄 ${message} ${progress}`)
      } else if (message.toLowerCase().includes('backup')) {
        setStatusMessage(`💾 ${message} ${progress}`)
      } else if (message.toLowerCase().includes('report')) {
        setStatusMessage(`📊 ${message} ${progress}`)
      } else {
        setStatusMessage(`⚙️ ${message} ${progress}`)
      }
    } else if (unreadNotifications > 0) {
      if (unreadNotifications === 1) {
        setStatusMessage('🔔 1 unread notification')
      } else {
        setStatusMessage(`🔔 ${unreadNotifications} notifications`)
      }
    } else {
      setStatusMessage('Your AI Sidekick - Ready')
    }
  }

  // Handle focus out
  const handleFocusOut = () => {
    if (isExpanded && !inputValue.trim()) {
      collapseToNormal()
    }
  }

  // Show notification
  const showNotification = (title: string, message?: string, type: 'success' | 'warning' | 'error' | 'info' = 'info') => {
    const icons = {
      success: '✅',
      warning: '⚠️',
      error: '❌',
      info: '📢'
    }
    
    const icon = icons[type]
    let displayMessage = `${icon} ${title}`
    
    if (message && message.length > 50) {
      displayMessage += `: ${message.substring(0, 47)}...`
    } else if (message) {
      displayMessage += `: ${message}`
    }
    
    setStatusMessage(displayMessage)
    setIsShowingNotification(true)
    
    if (notificationTimeoutRef.current) {
      clearTimeout(notificationTimeoutRef.current)
    }
    
    notificationTimeoutRef.current = setTimeout(() => {
      setIsShowingNotification(false)
      if (!isExpanded && !isProcessing) {
        updateStatus()
      }
    }, 4000)
  }

  useEffect(() => {
    if (backgroundProcesses.length === 0) return
    if (!isExpanded && !isProcessing && !isShowingNotification) {
      updateStatus()
    }
  }, [backgroundProcesses, isExpanded, isProcessing, isShowingNotification])

  // Expose methods for parent components
  useEffect(() => {
    // This would be used by parent components to control the status bar
    if (typeof window !== 'undefined') {
      (window as any).aiStatusBar = {
        showNotification,
        addBackgroundProcess,
        updateBackgroundProcess,
        removeBackgroundProcess,
        setUnreadNotifications
      }
    }
  }, [])

  return (
    <div 
      className={cn(
        "ai-status-bar",
        isExpanded && "expanded",
        className
      )}
      onClick={handleClick}
    >
      <div className="relative">
        <div
          className={cn(
            "ai-status-bar-container relative h-9",
            "flex items-center px-3 py-1.5",
            "rounded-lg border",
            "bg-[var(--md-sys-color-surface-container-highest)]",
            "border-[var(--md-sys-color-outline)]",
            "hover:bg-[var(--md-sys-color-surface-container-high)]",
            "hover:border-[var(--md-sys-color-outline)]",
            "focus-within:bg-[var(--md-sys-color-surface-container-highest)]",
            "focus-within:border-[var(--md-sys-color-primary)]",
            "focus-within:ring-1 focus-within:ring-primary/30",
            isProcessing && "cursor-not-allowed opacity-75",
            isExpanded ? "w-96" : "w-80"
          )}
          onClick={handleClick}
        >
          {/* Content area */}
          <div className="flex-1 flex items-center">
            {isExpanded ? (
              <div
                ref={inputRef}
                contentEditable
                suppressContentEditableWarning
                onInput={handleInputChange}
                onKeyDown={handleKeyPress}
                onFocus={expandForInput}
                onBlur={handleFocusOut}
                className={cn(
                  "w-full outline-none text-on-surface placeholder:text-on-surface-variant",
                  "selection:bg-primary/25 dark:selection:bg-primary/35",
                  isProcessing && "cursor-not-allowed",
                  !inputValue && "empty"
                )}
                style={{ minHeight: '20px' }}
                data-placeholder="You Say, I do"
              />
            ) : (
              <div className="w-full text-center text-on-surface font-medium text-sm">
                {statusMessage}
              </div>
            )}
          </div>
          
          {/* Status indicators */}
          <div className="flex items-center space-x-1 ml-2">
            {isProcessing && (
              <Loader2 className="w-4 h-4 text-on-surface-variant animate-spin" />
            )}
            
            {!isExpanded && !isProcessing && (
              <Bot className="w-4 h-4 text-on-surface-variant" />
            )}
            
            {isExpanded && !isProcessing && (
              <div
                onClick={(e) => {
                  e.stopPropagation()
                  collapseToNormal()
                }}
                className="flex cursor-pointer items-center justify-center rounded p-1 transition-colors hover:bg-black/5 dark:hover:bg-white/10"
              >
                <X className="w-3 h-3 text-on-surface-variant" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
