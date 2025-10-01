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
  switchOrganization: (organizationId: string) => Promise<boolean>
  loadUserData: () => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
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
  
  switchOrganization: async (organizationId: string) => {
    const { organizations } = get()
    const organization = organizations.find(org => org.id === organizationId)
    
    if (organization) {
      set({ currentOrganization: organization })
      localStorage.setItem('selectedOrganizationId', organizationId)
      return true
    }
    return false
  },
  
  loadUserData: async () => {
    const { user } = get()
    if (!user) return
    
    try {
      set({ isLoading: true })
      
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
      isAuthenticated: false 
    })
  },
}))
