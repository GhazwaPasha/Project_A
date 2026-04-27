'use client'

import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

/** Isolated so `providers` can `next/dynamic` it and keep devtools out of the main chunk in prod. */
export function RQDevtools() {
  return <ReactQueryDevtools initialIsOpen={false} />
}
