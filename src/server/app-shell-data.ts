import { DataServiceAdmin } from '@/server/data-service-admin'
import type { AppShellServerBootstrap } from '@/types/app-shell'
export type { AppShellServerBootstrap } from '@/types/app-shell'

/**
 * Fetches profile + org list for the signed-in user in RSC so the client can hydrate
 * the shell without waiting for a second `loadUserData` round-trip.
 */
export async function fetchAppShellServerBootstrap(
  userId: string
): Promise<AppShellServerBootstrap> {
  const [profile, organizations] = await Promise.all([
    DataServiceAdmin.getUserProfile(userId),
    DataServiceAdmin.getUserOrganizations(userId),
  ])
  return { userId, profile, organizations }
}
