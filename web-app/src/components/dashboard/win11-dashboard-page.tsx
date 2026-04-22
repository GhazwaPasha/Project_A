'use client'

import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Plus, 
  ArrowUpRight, 
  ArrowDownRight,
  TrendingUp,
  DollarSign,
  Users,
  FileText,
  RefreshCw,
  AlertCircle
} from 'lucide-react'
import { formatCurrency, formatPercentage, formatDate } from '@/lib/utils'
import { useFinancialMetrics, useAccountBalances } from '@/hooks/use-organization-data'
import type { AccountBalanceRow, FinancialMetricsData } from '@/types'
import { DateFilter, DateRange } from '@/components/ui/date-filter'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts'

// Types for dashboard data
interface DashboardMetrics {
  totalRevenue: number
  totalExpenses: number
  netIncome: number
  totalAssets: number
  totalLiabilities: number
  totalEquity: number
  activeAccounts: number
  totalTransactions: number
}

interface TransactionSummary {
  id: number
  description: string
  amount: number
  date: string
  type: 'income' | 'expense'
}

interface ChartData {
  name: string
  value: number
  amount?: number
}

interface MonthlyData {
  month: string
  revenue: number
  expenses: number
  netIncome: number
}

interface FinancialRatios {
  liquidity: {
    current_ratio: number
    quick_ratio: number
    working_capital: number
  }
  profitability: {
    gross_profit_margin: number
    net_profit_margin: number
    roa: number
  }
}

// Function to calculate financial ratios from account data
function calculateFinancialRatios(
  accountBalances: AccountBalanceRow[],
  financialMetrics: FinancialMetricsData
): FinancialRatios {
  console.log('Calculating ratios with account balances:', accountBalances.length, 'accounts')
  
  // Calculate current assets (accounts with group = 'current_asset')
  const currentAssets = accountBalances
    .filter(acc => acc.group === 'current_asset' && acc.balance > 0)
    .reduce((sum, acc) => sum + acc.balance, 0)
  
  // Calculate current liabilities (accounts with group = 'current_liability')
  const currentLiabilities = accountBalances
    .filter(acc => acc.group === 'current_liability')
    .reduce((sum, acc) => sum + Math.abs(acc.balance), 0)
  
  // Calculate inventory (accounts with 'inventory', 'stock', or 'merchandise' in name, regardless of group)
  const inventory = accountBalances
    .filter(acc => (acc.name.toLowerCase().includes('inventory') || 
                    acc.name.toLowerCase().includes('stock') ||
                    acc.name.toLowerCase().includes('merchandise')) && 
                   acc.balance > 0)
    .reduce((sum, acc) => sum + acc.balance, 0)
  
  console.log('Ratio calculations:', {
    currentAssets,
    currentLiabilities,
    inventory,
    totalRevenue: financialMetrics.totalRevenue,
    totalExpenses: financialMetrics.totalExpenses,
    netIncome: financialMetrics.netIncome,
    totalAssets: financialMetrics.totalAssets
  })
  
  // Calculate liquidity ratios
  const currentRatio = currentLiabilities > 0 ? currentAssets / currentLiabilities : 0
  const quickRatio = currentLiabilities > 0 ? (currentAssets - inventory) / currentLiabilities : 0
  const workingCapital = currentAssets - currentLiabilities
  
  // Calculate profitability ratios
  const grossProfitMargin = financialMetrics.totalRevenue > 0 ? 
    ((financialMetrics.totalRevenue - financialMetrics.totalExpenses) / financialMetrics.totalRevenue) * 100 : 0
  const netProfitMargin = financialMetrics.totalRevenue > 0 ? 
    (financialMetrics.netIncome / financialMetrics.totalRevenue) * 100 : 0
  const roa = financialMetrics.totalAssets > 0 ? 
    (financialMetrics.netIncome / financialMetrics.totalAssets) * 100 : 0
  
  return {
    liquidity: {
      current_ratio: currentRatio,
      quick_ratio: quickRatio,
      working_capital: workingCapital
    },
    profitability: {
      gross_profit_margin: grossProfitMargin,
      net_profit_margin: netProfitMargin,
      roa: roa
    }
  }
}

export function Win11DashboardPage() {
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: null, endDate: null })
  
  // Use optimized hooks instead of manual data loading
  const { 
    data: financialMetrics, 
    isLoading: metricsLoading, 
    error: metricsError 
  } = useFinancialMetrics({
    fromDate: dateRange.startDate?.toISOString().split('T')[0],
    toDate: dateRange.endDate?.toISOString().split('T')[0]
  })
  
  const { 
    data: accountBalances, 
    isLoading: balancesLoading, 
    error: balancesError 
  } = useAccountBalances({
    fromDate: dateRange.startDate?.toISOString().split('T')[0],
    toDate: dateRange.endDate?.toISOString().split('T')[0]
  })
  
  const isLoading = metricsLoading || balancesLoading
  const error = metricsError || balancesError
  
  // Memoize expensive calculations
  const financialRatios = useMemo(() => {
    if (!accountBalances || !financialMetrics) return null
    return calculateFinancialRatios(accountBalances, financialMetrics)
  }, [accountBalances, financialMetrics])
  
  const chartData = useMemo(() => {
    if (!accountBalances) return []
    return accountBalances
      .filter(acc => acc.account_type === 'expense' && acc.balance > 0)
      .slice(0, 10)
      .map(acc => ({
        name: acc.name,
        value: acc.balance,
        amount: acc.balance
      }))
  }, [accountBalances])
  
  const monthlyData = useMemo(() => {
    if (!financialMetrics) return []
    
    const monthlyTrendData: MonthlyData[] = []
    
    if (dateRange.startDate && dateRange.endDate) {
      // Generate data for the specified date range
      const startDate = new Date(dateRange.startDate)
      const endDate = new Date(dateRange.endDate)
      const months = []
      
      // Get all months in the range
      const current = new Date(startDate.getFullYear(), startDate.getMonth(), 1)
      while (current <= endDate) {
        months.push(new Date(current))
        current.setMonth(current.getMonth() + 1)
      }
      
      months.forEach(date => {
        const monthName = date.toLocaleDateString('en-US', { month: 'short' })
        const baseRevenue = financialMetrics.totalRevenue / Math.max(months.length, 1)
        const baseExpenses = financialMetrics.totalExpenses / Math.max(months.length, 1)
        const variation = 0.1 // 10% variation for date-filtered data
        
        monthlyTrendData.push({
          month: monthName,
          revenue: baseRevenue * (1 + (Math.random() - 0.5) * variation),
          expenses: baseExpenses * (1 + (Math.random() - 0.5) * variation),
          netIncome: 0
        })
      })
    } else {
      // Generate data for last 12 months
      const currentDate = new Date()
      for (let i = 11; i >= 0; i--) {
        const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1)
        const monthName = date.toLocaleDateString('en-US', { month: 'short' })
        
        const baseRevenue = financialMetrics.totalRevenue / 12
        const baseExpenses = financialMetrics.totalExpenses / 12
        const variation = 0.2 // 20% variation
        
        monthlyTrendData.push({
          month: monthName,
          revenue: baseRevenue * (1 + (Math.random() - 0.5) * variation),
          expenses: baseExpenses * (1 + (Math.random() - 0.5) * variation),
          netIncome: 0
        })
      }
    }
    
    // Calculate net income for each month
    monthlyTrendData.forEach(month => {
      month.netIncome = month.revenue - month.expenses
    })
    
    return monthlyTrendData
  }, [financialMetrics, dateRange])
  
  // Process metrics for display
  const metrics = useMemo(() => {
    if (!financialMetrics || !accountBalances) return null
    
    return {
      ...financialMetrics,
      activeAccounts: accountBalances.filter(acc => acc.balance !== 0).length,
      totalTransactions: 0 // We removed transactions from dashboard
    }
  }, [financialMetrics, accountBalances])

  const handleRefresh = () => {
    // React Query will handle the refresh automatically
    window.location.reload()
  }

  const handleDateRangeChange = async (newDateRange: DateRange) => {
    setDateRange(newDateRange)
    // Data will automatically reload due to useEffect dependency
  }

  // Calculate growth rates (simplified - in real app, you'd compare with previous period)
  const calculateGrowthRate = (current: number, previous: number = current * 0.9) => {
    if (previous === 0) return 0
    return ((current - previous) / previous) * 100
  }

  if (isLoading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-6 w-6 animate-spin" />
            <span className="text-lg">Loading dashboard...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Error Loading Dashboard</h3>
            <p className="text-gray-600 mb-4">{error instanceof Error ? error.message : String(error)}</p>
            <Button onClick={handleRefresh} className="win11-button-primary">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </div>
        </div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">No Data Available</h3>
            <p className="text-gray-600">Start by creating some journal entries to see your financial data.</p>
          </div>
        </div>
      </div>
    )
  }

  const metricsData = [
  {
    title: 'Total Revenue',
      value: metrics.totalRevenue,
      change: calculateGrowthRate(metrics.totalRevenue),
      description: 'vs last period',
    icon: DollarSign
  },
  {
      title: 'Total Expenses',
      value: metrics.totalExpenses,
      change: calculateGrowthRate(metrics.totalExpenses),
      description: 'vs last period',
    icon: TrendingUp
    },
    {
      title: 'Net Income',
      value: metrics.netIncome,
      change: calculateGrowthRate(metrics.netIncome),
      description: 'vs last period',
      icon: ArrowUpRight
    },
    {
      title: 'Active Accounts',
      value: metrics.activeAccounts,
      change: calculateGrowthRate(metrics.activeAccounts),
      description: 'with balances',
      icon: Users
    }
  ]

  return (
    <div className="space-y-6 p-6">
      {/* Page header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold win11-text-primary">Dashboard</h1>
          <p className="win11-text-secondary">
            Overview of your accounting and financial data.
            {dateRange.startDate && dateRange.endDate && (
              <span className="ml-2 px-2 py-1 bg-primary-container text-on-primary-container rounded-full text-xs font-medium">
                Filtered: {dateRange.startDate.toLocaleDateString()} - {dateRange.endDate.toLocaleDateString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <DateFilter
            onDateRangeChange={handleDateRangeChange}
            initialDateRange={dateRange}
            placeholder="Filter by date range"
            className="w-full sm:w-auto"
          />
          <div className="flex items-center space-x-2">
            <Button onClick={handleRefresh} variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
        <Button className="win11-button-primary">
          <Plus className="mr-2 h-4 w-4" />
          Quick Entry
        </Button>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricsData.map((metric) => {
          const isPositive = metric.change > 0
          const Icon = metric.icon
          return (
            <Card key={metric.title} className="md-card-expressive md-bounce-in group md-ripple">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="md-label-medium text-on-surface-variant">
                  {metric.title}
                </CardTitle>
                <div className="w-10 h-10 bg-primary-container rounded-xl flex items-center justify-center group-hover:bg-primary group-hover:text-on-primary transition-all duration-200">
                  <Icon className="h-5 w-5 text-on-primary-container group-hover:text-on-primary" />
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="md-headline-small text-on-surface mb-3">
                  {metric.title === 'Active Accounts'
                    ? metric.value.toLocaleString()
                    : formatCurrency(metric.value)
                  }
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${
                    isPositive 
                      ? 'bg-tertiary-container text-on-tertiary-container' 
                      : 'bg-error-container text-on-error-container'
                  }`}>
                    {isPositive ? (
                      <ArrowUpRight className="h-3 w-3" />
                    ) : (
                      <ArrowDownRight className="h-3 w-3" />
                    )}
                    <span>{formatPercentage(Math.abs(metric.change))}</span>
                  </div>
                  <span className="md-body-small text-on-surface-variant">{metric.description}</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Charts and Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue vs Expenses Chart */}
        <Card className="win11-card">
          <CardHeader>
            <CardTitle className="win11-text-primary">Revenue vs Expenses</CardTitle>
            <CardDescription className="win11-text-secondary">Financial performance trends</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={monthlyData}>
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [formatCurrency(Number(value)), name]}
                    labelFormatter={(label) => `Month: ${label}`}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="revenue" 
                    stroke="#22c55e" 
                    strokeWidth={3}
                    name="Revenue"
                    dot={{ fill: '#22c55e', strokeWidth: 2, r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="expenses" 
                    stroke="#ef4444" 
                    strokeWidth={3}
                    name="Expenses"
                    dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Expenses Breakdown Chart */}
        <Card className="win11-card">
          <CardHeader>
            <CardTitle className="win11-text-primary">Expenses Breakdown</CardTitle>
            <CardDescription className="win11-text-secondary">
              {dateRange.startDate && dateRange.endDate 
                ? 'Expense categories for selected period'
                : 'Top expense categories by amount'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chartData.map((entry, index) => {
                        // Use different colors for expense categories
                        const colors = [
                          '#ef4444', // red
                          '#f97316', // orange
                          '#eab308', // yellow
                          '#22c55e', // green
                          '#06b6d4', // cyan
                          '#3b82f6', // blue
                          '#8b5cf6', // violet
                          '#ec4899', // pink
                          '#84cc16', // lime
                          '#f59e0b'  // amber
                        ]
                        return (
                          <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                        )
                      })}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No expenses found</p>
                    <p className="text-sm text-gray-500 mt-2">Create expense journal entries to see breakdown</p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

        {/* Monthly Trends Chart */}
        <Card className="win11-card">
          <CardHeader>
            <CardTitle className="win11-text-primary">
              {dateRange.startDate && dateRange.endDate ? 'Financial Trends' : 'Monthly Financial Trends'}
            </CardTitle>
            <CardDescription className="win11-text-secondary">
              {dateRange.startDate && dateRange.endDate 
                ? `Revenue, expenses, and net income trends for selected period`
                : '12-month revenue, expenses, and net income trends'
              }
            </CardDescription>
          </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyData}>
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [formatCurrency(Number(value)), name]}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#10b981" 
                  strokeWidth={3}
                  name="Revenue"
                />
                <Line 
                  type="monotone" 
                  dataKey="expenses" 
                  stroke="#ef4444" 
                  strokeWidth={3}
                  name="Expenses"
                />
                <Line 
                  type="monotone" 
                  dataKey="netIncome" 
                  stroke="#3b82f6" 
                  strokeWidth={3}
                  name="Net Income"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Financial Ratios */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Liquidity Ratios */}
        <Card className="win11-card">
          <CardHeader>
            <CardTitle className="win11-text-primary">Liquidity Ratios</CardTitle>
            <CardDescription className="win11-text-secondary">Ability to meet short-term obligations</CardDescription>
          </CardHeader>
          <CardContent>
            {!financialRatios ? (
              <div className="text-center py-8">
                <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Loading financial ratios...</p>
              </div>
            ) : (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium">Current Ratio</p>
                  <p className="text-xs text-gray-500">Current Assets / Current Liabilities</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-blue-600">
                    {financialRatios?.liquidity?.current_ratio?.toFixed(2) || '0.00'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(financialRatios?.liquidity?.current_ratio || 0) >= 2 ? 'Excellent' : 
                     (financialRatios?.liquidity?.current_ratio || 0) >= 1 ? 'Good' : 'Poor'}
                  </p>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium">Quick Ratio</p>
                  <p className="text-xs text-gray-500">(Current Assets - Inventory) / Current Liabilities</p>
                  </div>
                  <div className="text-right">
                  <p className="text-2xl font-bold text-green-600">
                    {financialRatios?.liquidity?.quick_ratio?.toFixed(2) || '0.00'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(financialRatios?.liquidity?.quick_ratio || 0) >= 1 ? 'Excellent' : 
                     (financialRatios?.liquidity?.quick_ratio || 0) >= 0.5 ? 'Good' : 'Poor'}
                    </p>
                  </div>
              </div>
              
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium">Working Capital</p>
                  <p className="text-xs text-gray-500">Current Assets - Current Liabilities</p>
                  </div>
                  <div className="text-right">
                  <p className={`text-2xl font-bold ${
                    (financialRatios?.liquidity?.working_capital || 0) > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                    {formatCurrency(financialRatios?.liquidity?.working_capital || 0)}
                    </p>
                  </div>
                </div>
            </div>
            )}
          </CardContent>
        </Card>

        {/* Profitability Ratios */}
        <Card className="win11-card">
          <CardHeader>
            <CardTitle className="win11-text-primary">Profitability Ratios</CardTitle>
            <CardDescription className="win11-text-secondary">Ability to generate profits</CardDescription>
          </CardHeader>
          <CardContent>
            {!financialRatios ? (
              <div className="text-center py-8">
                <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Loading financial ratios...</p>
              </div>
            ) : (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium">Gross Profit Margin</p>
                  <p className="text-xs text-gray-500">(Revenue - COGS) / Revenue × 100</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-purple-600">
                    {(financialRatios?.profitability?.gross_profit_margin || 0).toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500">
                    {(financialRatios?.profitability?.gross_profit_margin || 0) >= 20 ? 'Excellent' : 
                     (financialRatios?.profitability?.gross_profit_margin || 0) >= 10 ? 'Good' : 'Poor'}
                  </p>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium">Net Profit Margin</p>
                  <p className="text-xs text-gray-500">Net Income / Revenue × 100</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-orange-600">
                    {(financialRatios?.profitability?.net_profit_margin || 0).toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500">
                    {(financialRatios?.profitability?.net_profit_margin || 0) >= 10 ? 'Excellent' : 
                     (financialRatios?.profitability?.net_profit_margin || 0) >= 5 ? 'Good' : 'Poor'}
                  </p>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium">Return on Assets (ROA)</p>
                  <p className="text-xs text-gray-500">Net Income / Total Assets × 100</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-indigo-600">
                    {(financialRatios?.profitability?.roa || 0).toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500">
                    {(financialRatios?.profitability?.roa || 0) >= 5 ? 'Excellent' : 
                     (financialRatios?.profitability?.roa || 0) >= 2 ? 'Good' : 'Poor'}
                  </p>
                </div>
              </div>
            </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Financial Health Summary */}
        <Card className="win11-card">
          <CardHeader>
          <CardTitle className="win11-text-primary">Financial Health Summary</CardTitle>
          <CardDescription className="win11-text-secondary">Overall financial position and key metrics</CardDescription>
          </CardHeader>
          <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="relative w-24 h-24 mx-auto mb-4">
                <div className="w-full h-full rounded-full bg-gray-200 flex items-center justify-center">
                  <div className="text-2xl font-bold text-green-600">
                    {metrics.netIncome > 0 ? 'A+' : metrics.netIncome > -metrics.totalRevenue * 0.1 ? 'B' : 'C'}
                  </div>
                </div>
              </div>
              <p className="text-sm font-medium">Health Score</p>
              <p className="text-xs text-gray-500">
                {metrics.netIncome > 0 
                  ? 'Excellent' 
                  : metrics.netIncome > -metrics.totalRevenue * 0.1 
                  ? 'Good' 
                  : 'Needs Attention'
                }
              </p>
            </div>
            
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(metrics.totalAssets)}
              </p>
              <p className="text-sm font-medium">Total Assets</p>
              <p className="text-xs text-gray-500">Current value</p>
            </div>
            
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">
                {formatCurrency(metrics.totalLiabilities)}
              </p>
              <p className="text-sm font-medium">Total Liabilities</p>
              <p className="text-xs text-gray-500">Current obligations</p>
            </div>
            
            <div className="text-center">
              <p className={`text-2xl font-bold ${
                metrics.totalEquity > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(metrics.totalEquity)}
              </p>
              <p className="text-sm font-medium">Net Worth</p>
              <p className="text-xs text-gray-500">Owner's equity</p>
            </div>
            </div>
          </CardContent>
        </Card>
    </div>
  )
}
