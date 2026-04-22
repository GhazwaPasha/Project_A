import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'

const inter = Inter({ subsets: ['latin'] })

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Accountuitive - Multi-Tenant SaaS Platform',
  description: 'Modern accounting software with multi-tenant support, AI integration, and comprehensive financial reporting.',
  keywords: ['accounting', 'SaaS', 'multi-tenant', 'financial reports', 'bookkeeping'],
  authors: [{ name: 'Accountuitive Team' }],
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#2196F3',
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
