import { AsyncLocalStorage } from 'node:async_hooks'

/** Session user id for the current `/api/app-data` (or related) request. */
export const actingUserStore = new AsyncLocalStorage<string>()

export function getActingUserId(): string | undefined {
  return actingUserStore.getStore()
}
