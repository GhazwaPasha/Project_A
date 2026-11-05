import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// From lg up the page scrolls inside its panel in the shell; on phones the window scrolls.
export const PAGE_SCROLLER = 'page-scroller'
// Where a page section docks beside the content, inside the main box. Hidden while empty.
export const PAGE_SIDE = 'page-side'
export function scrollPageToTop() {
  window.scrollTo(0, 0)
  document.getElementById(PAGE_SCROLLER)?.scrollTo(0, 0)
}
