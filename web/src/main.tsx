import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import { MotionConfig } from 'motion/react'
import { BootProvider } from '@/lib/boot'
import { queryClient } from '@/lib/data'
import { router } from '@/router'
import './index.css'
import './theme.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <MotionConfig reducedMotion="user">
        <BootProvider>
          <RouterProvider router={router} />
        </BootProvider>
      </MotionConfig>
    </QueryClientProvider>
  </StrictMode>,
)
