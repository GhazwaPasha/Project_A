import { create } from 'zustand'
import { User, Organization, UserProfile } from '@/types'

interface AuthState {
  user: User | null
  profile: UserProfile | null
  organizations: Organization[]
  currentOrganization: Organization | null
  isLoading: boolean
  isAuthenticated: boolean
  
  // Actions
  setUser: (user: User | null) => void
  setProfile: (profile: UserProfile | null) => void
  setOrganizations: (organizations: Organization[]) => void
  setCurrentOrganization: (organization: Organization | null) => void
  setLoading: (loading: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  profile: null,
  organizations: [],
  currentOrganization: null,
  isLoading: false,
  isAuthenticated: false,
  
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setProfile: (profile) => set({ profile }),
  setOrganizations: (organizations) => set({ organizations }),
  setCurrentOrganization: (currentOrganization) => set({ currentOrganization }),
  setLoading: (isLoading) => set({ isLoading }),
  logout: () => set({ 
    user: null, 
    profile: null, 
    organizations: [], 
    currentOrganization: null, 
    isAuthenticated: false 
  }),
}))
