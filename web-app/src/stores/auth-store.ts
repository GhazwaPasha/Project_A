import { create } from 'zustand'
import { subscribeWithSelector, persist } from 'zustand/middleware'
import { User, Organization, UserProfile } from '@/types'

interface AuthState {
  user: User | null
  profile: UserProfile | null
  organizations: Organization[]
  currentOrganization: Organization | null
  isLoading: boolean
  isAuthenticated: boolean
  lastOrganizationSwitch: number | null
  
  // Actions
  setUser: (user: User | null) => void
  setProfile: (profile: UserProfile | null) => void
  setOrganizations: (organizations: Organization[]) => void
  setCurrentOrganization: (organization: Organization | null) => void
  setLoading: (loading: boolean) => void
  switchOrganization: (organizationId: string) => Promise<boolean>
  loadUserData: () => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    subscribeWithSelector((set, get) => ({
      user: null,
      profile: null,
      organizations: [],
      currentOrganization: null,
      isLoading: false,
      isAuthenticated: false,
      lastOrganizationSwitch: null,
    
    setUser: (user) => set({ user, isAuthenticated: !!user }),
    setProfile: (profile) => set({ profile }),
    setOrganizations: (organizations) => set({ organizations }),
    setCurrentOrganization: (currentOrganization) => set({ currentOrganization }),
    setLoading: (isLoading) => set({ isLoading }),
    
    switchOrganization: async (organizationId: string) => {
      const { organizations } = get()
      const organization = organizations.find(org => org.id === organizationId)
      
      if (organization) {
        set({ 
          currentOrganization: organization,
          lastOrganizationSwitch: Date.now()
        })
        localStorage.setItem('selectedOrganizationId', organizationId)
        return true
      }
      return false
    },
  
  loadUserData: async () => {
    const { user, organizations: existingOrgs, currentOrganization: existingOrg } = get()
    if (!user) return
    
    // If we already have organizations and current org, don't set loading
    // This prevents the loading state from showing when data is already available
    const hasExistingData = existingOrgs.length > 0 && existingOrg
    
    try {
      if (!hasExistingData) {
        set({ isLoading: true })
      }
      
      // Load user profile and organizations
      const [profile, organizations] = await Promise.all([
        import('@/lib/data-service').then(module => module.DataService.getUserProfile(user.id)),
        import('@/lib/data-service').then(module => module.DataService.getUserOrganizations(user.id))
      ])
      
      set({ profile, organizations })
      
      // Set current organization from localStorage or first available
      const savedOrgId = localStorage.getItem('selectedOrganizationId')
      const currentOrg = savedOrgId 
        ? organizations.find(org => org.id === savedOrgId) || organizations[0]
        : organizations[0]
      
      if (currentOrg) {
        set({ currentOrganization: currentOrg })
      }
    } catch (error) {
      console.error('Error loading user data:', error)
    } finally {
      set({ isLoading: false })
    }
  },
  
      logout: () => {
        localStorage.removeItem('selectedOrganizationId')
        set({ 
          user: null, 
          profile: null, 
          organizations: [], 
          currentOrganization: null, 
          isAuthenticated: false,
          lastOrganizationSwitch: null,
          isLoading: false
        })
      },
    })),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        organizations: state.organizations,
        currentOrganization: state.currentOrganization,
      }),
    }
  )
)

// Optimized selectors
export const useCurrentOrganization = () => 
  useAuthStore(state => state.currentOrganization)

export const useIsLoading = () => 
  useAuthStore(state => state.isLoading)

export const useOrganizations = () => 
  useAuthStore(state => state.organizations)

export const useUser = () => 
  useAuthStore(state => state.user)

export const useIsAuthenticated = () => 
  useAuthStore(state => state.isAuthenticated)
