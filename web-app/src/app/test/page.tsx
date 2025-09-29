'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase'

export default function TestPage() {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const testConnection = async () => {
      try {
        const supabase = createClient()
        const { data, error } = await supabase
          .from('organizations')
          .select('count')
          .limit(1)

        if (error) {
          setError(error.message)
        } else {
          setIsConnected(true)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      }
    }

    testConnection()
  }, [])

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Database Connection Test</h1>
      
      {isConnected && (
        <div className="p-4 bg-success/20 border border-success/30 rounded text-success">
          ✅ Successfully connected to Supabase database!
        </div>
      )}
      
      {error && (
        <div className="p-4 bg-destructive/20 border border-destructive/30 rounded text-destructive">
          ❌ Connection failed: {error}
        </div>
      )}
      
      {!isConnected && !error && (
        <div className="p-4 bg-warning/20 border border-warning/30 rounded text-warning">
          ⏳ Testing connection...
        </div>
      )}
    </div>
  )
}
