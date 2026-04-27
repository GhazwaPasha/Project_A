'use client'

import React, { Component, ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw, Home } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  retryCount: number
}

export class QueryErrorBoundary extends Component<Props, State> {
  private retryTimeoutId: NodeJS.Timeout | null = null

  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      retryCount: 0
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Query Error Boundary caught an error:', error, errorInfo)
    
    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // Auto-retry after 5 seconds for network errors
    if (this.isNetworkError(error) && this.state.retryCount < 3) {
      this.retryTimeoutId = setTimeout(() => {
        this.handleRetry()
      }, 5000)
    }
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId)
    }
  }

  private isNetworkError(error: Error): boolean {
    return (
      error.message.includes('fetch') ||
      error.message.includes('network') ||
      error.message.includes('timeout') ||
      error.message.includes('Failed to fetch')
    )
  }

  private handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      retryCount: prevState.retryCount + 1
    }))
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      retryCount: 0
    })
  }

  private handleGoHome = () => {
    this.handleReset()
    // This will be handled by the component that uses this boundary
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <QueryErrorFallback
          error={this.state.error}
          retryCount={this.state.retryCount}
          onRetry={this.handleRetry}
          onReset={this.handleReset}
          onGoHome={this.handleGoHome}
        />
      )
    }

    return this.props.children
  }
}

interface QueryErrorFallbackProps {
  error: Error | null
  retryCount: number
  onRetry: () => void
  onReset: () => void
  onGoHome: () => void
}

function QueryErrorFallback({ 
  error, 
  retryCount, 
  onRetry, 
  onReset, 
  onGoHome 
}: QueryErrorFallbackProps) {
  const queryClient = useQueryClient()
  const router = useRouter()

  const handleRetry = () => {
    // Clear all queries and retry
    queryClient.clear()
    onRetry()
  }

  const handleGoHome = () => {
    queryClient.clear()
    router.push('/home')
    onGoHome()
  }

  const isNetworkError = error?.message.includes('fetch') || 
                        error?.message.includes('network') ||
                        error?.message.includes('timeout')

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--md-sys-color-background)' }}>
      <div className="text-center max-w-md mx-auto px-6">
        <div className="w-20 h-20 bg-error-container rounded-3xl flex items-center justify-center mb-6 mx-auto">
          <AlertCircle className="w-10 h-10 text-on-error-container" />
        </div>
        
        <h3 className="md-headline-small text-on-surface mb-3">
          {isNetworkError ? 'Connection Error' : 'Something went wrong'}
        </h3>
        
        <p className="md-body-large text-on-surface-variant mb-8">
          {isNetworkError 
            ? 'Unable to connect to the server. Please check your internet connection.'
            : 'An unexpected error occurred while loading data.'
          }
        </p>

        {error && process.env.NODE_ENV === 'development' && (
          <div className="mb-6 p-4 bg-error-container/20 rounded-lg text-left">
            <p className="md-body-small text-on-error-container font-mono">
              {error.message}
            </p>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button 
            onClick={handleRetry}
            className="md-button"
            disabled={retryCount >= 3}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            {retryCount >= 3 ? 'Max Retries Reached' : 'Try Again'}
          </Button>
          
          <Button 
            onClick={handleGoHome}
            className="md-button-outlined"
          >
            <Home className="w-4 h-4 mr-2" />
            Go to Dashboard
          </Button>
        </div>

        {retryCount > 0 && (
          <p className="md-body-small text-on-surface-variant mt-4">
            Retry attempt {retryCount} of 3
          </p>
        )}
      </div>
    </div>
  )
}

// Hook for using error boundary in functional components
export function useQueryErrorHandler() {
  const queryClient = useQueryClient()

  const handleQueryError = (error: Error, queryKey: string[]) => {
    console.error('Query error:', error, 'Query key:', queryKey)
    
    // Invalidate the specific query
    queryClient.invalidateQueries({ queryKey })
    
    // If it's a network error, clear all queries
    if (error.message.includes('fetch') || error.message.includes('network')) {
      queryClient.clear()
    }
  }

  const resetQueries = (queryKey?: string[]) => {
    if (queryKey) {
      queryClient.invalidateQueries({ queryKey })
    } else {
      queryClient.clear()
    }
  }

  return { handleQueryError, resetQueries }
}
