'use client'

import { useState } from 'react'
import { useAIStatusBar } from '@/contexts/ai-context'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Bot, Bell, Settings, FileText, Calendar, BarChart3 } from 'lucide-react'

export default function AIDemoPage() {
  const { 
    showNotification, 
    addBackgroundProcess, 
    updateBackgroundProcess, 
    removeBackgroundProcess,
    setUnreadNotifications,
    unreadNotifications,
    backgroundProcesses 
  } = useAIStatusBar()

  const [processId, setProcessId] = useState<string | null>(null)

  const handleTestNotification = (type: 'success' | 'warning' | 'error' | 'info') => {
    const notifications = {
      success: { title: 'Success!', message: 'Your action completed successfully' },
      warning: { title: 'Warning', message: 'Please check your input data' },
      error: { title: 'Error', message: 'Something went wrong. Please try again.' },
      info: { title: 'Info', message: 'Here is some useful information' }
    }
    
    const notification = notifications[type]
    showNotification(notification.title, notification.message, type)
  }

  const handleStartProcess = () => {
    const id = `process_${Date.now()}`
    setProcessId(id)
    addBackgroundProcess(id, 'Processing data...', '0%')
    
    // Simulate progress updates
    let progress = 0
    const interval = setInterval(() => {
      progress += 10
      updateBackgroundProcess(id, 'Processing data...', `${progress}%`)
      
      if (progress >= 100) {
        clearInterval(interval)
        setTimeout(() => {
          removeBackgroundProcess(id)
          setProcessId(null)
          showNotification('Process Complete', 'Data processing finished successfully', 'success')
        }, 500)
      }
    }, 200)
  }

  const handleAddNotifications = () => {
    setUnreadNotifications(unreadNotifications + 1)
    showNotification('New Notification', 'You have a new message', 'info')
  }

  const aiCommands = [
    {
      icon: <FileText className="w-4 h-4" />,
      command: "Show me the journal entries",
      description: "Navigate to journal page"
    },
    {
      icon: <BarChart3 className="w-4 h-4" />,
      command: "Generate income statement for last month",
      description: "Create financial report"
    },
    {
      icon: <Calendar className="w-4 h-4" />,
      command: "Remind me to close books on the 1st",
      description: "Create recurring reminder"
    },
    {
      icon: <Settings className="w-4 h-4" />,
      command: "Show me the cash account ledger",
      description: "Navigate to specific account"
    }
  ]

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">AI Status Bar Demo</h1>
        <p className="text-muted-foreground">
          Test the AI status bar functionality and see how it integrates with your application
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Notification Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Notifications
            </CardTitle>
            <CardDescription>
              Test different types of notifications
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Button 
                variant="default" 
                size="sm"
                onClick={() => handleTestNotification('success')}
              >
                Success
              </Button>
              <Button 
                variant="secondary" 
                size="sm"
                onClick={() => handleTestNotification('info')}
              >
                Info
              </Button>
              <Button 
                variant="destructive" 
                size="sm"
                onClick={() => handleTestNotification('error')}
              >
                Error
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => handleTestNotification('warning')}
              >
                Warning
              </Button>
            </div>
            
            <div className="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={handleAddNotifications}
              >
                Add Notification
              </Button>
              <Badge variant="secondary">
                {unreadNotifications} unread
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Background Process Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Background Processes
            </CardTitle>
            <CardDescription>
              Simulate background tasks and progress updates
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              onClick={handleStartProcess}
              disabled={processId !== null}
              className="w-full"
            >
              {processId ? 'Processing...' : 'Start Process'}
            </Button>
            
            {backgroundProcesses.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium">Active Processes:</h4>
                {backgroundProcesses.map((process) => (
                  <div key={process.id} className="p-2 bg-muted rounded text-sm">
                    <div className="flex justify-between items-center">
                      <span>{process.message}</span>
                      <Badge variant="outline">{process.progress}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Commands Demo */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="w-5 h-5" />
              AI Commands Demo
            </CardTitle>
            <CardDescription>
              Try these commands in the AI status bar above
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {aiCommands.map((cmd, index) => (
                <div key={index} className="p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-primary/10 rounded">
                      {cmd.icon}
                    </div>
                    <div className="flex-1 space-y-1">
                      <p className="font-medium text-sm">{cmd.command}</p>
                      <p className="text-xs text-muted-foreground">{cmd.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>How to Use the AI Status Bar</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-medium">1. Click on the AI Status Bar</h4>
            <p className="text-sm text-muted-foreground">
              Click anywhere on the status bar in the header to expand it for input
            </p>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium">2. Type Your Command</h4>
            <p className="text-sm text-muted-foreground">
              Use natural language to ask for navigation, reports, or reminders
            </p>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium">3. Press Enter</h4>
            <p className="text-sm text-muted-foreground">
              The AI will process your command and show the result
            </p>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium">4. Auto-collapse</h4>
            <p className="text-sm text-muted-foreground">
              The status bar will automatically collapse after showing the result
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
