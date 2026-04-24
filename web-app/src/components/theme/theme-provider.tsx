'use client'

import { ThemeProvider as NextThemesProvider } from 'next-themes'
import type { ReactNode } from 'react'

/**
 * `defaultTheme` is light. Users can use system or toggled dark (next-themes: class on `html`).
 */
export function AppThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="light"
      enableSystem={false}
      storageKey="accui-color-scheme"
      disableTransitionOnChange
    >
      {children}
    </NextThemesProvider>
  )
}
