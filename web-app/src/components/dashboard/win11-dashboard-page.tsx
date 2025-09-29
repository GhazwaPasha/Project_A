'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Plus, 
  ArrowUpRight, 
  ArrowDownRight,
  TrendingUp,
  DollarSign,
  Users,
  FileText
} from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'

const mockMetrics = [
  {
    title: 'Total Revenue',
    value: 125430,
    change: 12.5,
    description: 'vs last month',
    icon: DollarSign
  },
  {
    title: 'Active Accounts',
    value: 2847,
    change: 8.2,
    description: 'vs last month',
    icon: Users
  },
  {
    title: 'Transactions',
    value: 15420,
    change: -2.1,
    description: 'vs last month',
    icon: FileText
  },
  {
    title: 'Growth Rate',
    value: 15.8,
    change: 5.3,
    description: 'vs last month',
    icon: TrendingUp
  }
]

const mockTransactions = [
  {
    id: '1',
    description: 'Office Supplies Purchase',
    amount: 245.50,
    date: '2024-12-19',
    type: 'expense'
  },
  {
    id: '2',
    description: 'Client Payment - Project Alpha',
    amount: 5000.00,
    date: '2024-12-18',
    type: 'income'
  },
  {
    id: '3',
    description: 'Software Subscription',
    amount: 99.00,
    date: '2024-12-17',
    type: 'expense'
  }
]

export function Win11DashboardPage() {
  return (
    <div className="space-y-6 p-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold win11-text-primary">Dashboard</h1>
          <p className="win11-text-secondary">
            Overview of your accounting and financial data.
          </p>
        </div>
        <Button className="win11-button-primary">
          <Plus className="mr-2 h-4 w-4" />
          Quick Entry
        </Button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {mockMetrics.map((metric) => {
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
                  {metric.title === 'Growth Rate' 
                    ? `${metric.value}%`
                    : metric.title === 'Active Accounts' || metric.title === 'Transactions'
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

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Transactions */}
        <Card className="win11-card">
          <CardHeader>
            <CardTitle className="win11-text-primary">Recent Transactions</CardTitle>
            <CardDescription className="win11-text-secondary">Your latest financial activities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockTransactions.map((transaction) => (
                <div key={transaction.id} className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium win11-text-primary">
                      {transaction.description}
                    </p>
                    <p className="text-xs win11-text-secondary">
                      {transaction.date}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${
                      transaction.type === 'income' ? 'win11-success' : 'win11-destructive'
                    }`}>
                      {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="win11-card">
          <CardHeader>
            <CardTitle className="win11-text-primary">Quick Actions</CardTitle>
            <CardDescription className="win11-text-secondary">Common accounting tasks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Button className="w-full justify-start win11-button">
                <Plus className="mr-2 h-4 w-4" />
                New Journal Entry
              </Button>
              <Button className="w-full justify-start win11-button">
                <FileText className="mr-2 h-4 w-4" />
                Create Invoice
              </Button>
              <Button className="w-full justify-start win11-button">
                <TrendingUp className="mr-2 h-4 w-4" />
                Generate Report
              </Button>
              <Button className="w-full justify-start win11-button">
                <Users className="mr-2 h-4 w-4" />
                Manage Accounts
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
