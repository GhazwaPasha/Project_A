import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// From lg up the page scrolls inside its panel in the shell; on phones the window scrolls.
export const PAGE_SCROLLER = 'page-scroller'
export function scrollPageToTop() {
  window.scrollTo(0, 0)
  document.getElementById(PAGE_SCROLLER)?.scrollTo(0, 0)
}
