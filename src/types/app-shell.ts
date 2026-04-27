import type { Organization, UserProfile } from '@/types'

/** RSC payload for the signed-in app shell (profile + org list). */
export type AppShellServerBootstrap = {
  userId: string
  profile: UserProfile | null
  organizations: Organization[]
}
