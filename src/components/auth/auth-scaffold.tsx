'use client'

import type { ReactNode } from 'react'
import { brandTitleFont } from '@/lib/brand-title-font'

const BG_IMAGE = '/closeup-coins-stack-isolated-black-background.jpg'

export function AuthScaffold({ children }: { children: ReactNode }) {
  return (
    <div className="dark min-h-screen flex items-center justify-center p-4 pt-[min(12rem,28vh)] sm:pt-36 relative overflow-hidden bg-[#0a0a0a]">
      <h1
        className={`${brandTitleFont.className} pointer-events-none absolute left-3 right-3 top-3 z-20 text-left text-white sm:left-5 sm:top-5 sm:right-8 md:left-6 md:top-6 leading-[0.9] tracking-tight`}
        style={{
          textShadow: '0 2px 32px rgba(0,0,0,0.5), 0 4px 4px rgba(0,0,0,0.3)',
          fontSize: 'clamp(2.25rem, 11vw, 8.5rem)',
        }}
      >
        Accountuitive
      </h1>
      <div
        className="absolute inset-0 z-0 scale-105"
        style={{
          backgroundImage: `url('${BG_IMAGE}')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          filter: 'blur(10px)',
        }}
        aria-hidden
      />
      <div
        className="absolute inset-0 z-[1] bg-gradient-to-b from-black/75 via-black/65 to-black/75"
        aria-hidden
      />
      <div className="relative z-10 w-full flex flex-col items-center min-h-0">
        {children}
      </div>
    </div>
  )
}
